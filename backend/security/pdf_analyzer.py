"""AEGIS PDF Document Ingestion, Security Extraction, and Analysis Workflow.

Extracts text, metadata, and hidden layers from PDF documents, applies
dual-tier prompt injection detection, DLP scanning, and dynamic provenance
labeling under the Causal Lineage & Provenance Dominance Architecture.
"""

from __future__ import annotations

import io
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

import fitz  # PyMuPDF
from pypdf import PdfReader

from backend.schemas.provenance import (
    Provenance,
    SensitivityLevel,
    SourceType,
    TrustLevel,
)
from backend.security.audit import log_decision
from backend.security.dlp_engine import scan_for_secrets
from backend.security.ml_detector import detect_injection
from backend.tools.simulated_tools import DOCUMENTS


# Unicode zero-width and invisible character regex
ZERO_WIDTH_REGEX = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
URL_REGEX = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")


class PDFPageInfo(TypedDict):
    page_number: int
    char_count: int
    text_snippet: str


class PDFExtractionResult(TypedDict):
    filename: str
    file_size_bytes: int
    page_count: int
    metadata: dict[str, Any]
    full_text: str
    pages: list[PDFPageInfo]
    has_zero_width_chars: bool
    zero_width_count: int
    has_hidden_elements: bool


class PDFSecurityEvaluation(TypedDict):
    verdict: str  # "CLEAN" | "SUSPICIOUS" | "INJECTION_DETECTED" | "SENSITIVE_DATA_LEAK"
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    injection_score: float
    injection_verdict: str
    matched_injection_patterns: list[str]
    has_sensitive_data: bool
    dlp_findings: list[dict[str, Any]]
    sanitized_preview: str
    provenance: dict[str, Any]
    governance_decision: str


class PDFAnalysisWorkflowResult(TypedDict):
    success: bool
    timestamp: str
    trace_id: str
    extraction: PDFExtractionResult
    security: PDFSecurityEvaluation
    agent_summary: dict[str, Any]


def extract_pdf_content(file_bytes: bytes, filename: str) -> PDFExtractionResult:
    """Extract text, structural metadata, and inspect for hidden content."""
    file_size = len(file_bytes)
    full_text_parts: list[str] = []
    pages_info: list[PDFPageInfo] = []
    metadata: dict[str, Any] = {}
    has_zero_width = False
    zero_width_count = 0
    has_hidden_elements = False

    # Primary extractor: PyMuPDF for high fidelity & font/hidden text analysis
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        metadata = {
            "title": doc.metadata.get("title", "") or filename,
            "author": doc.metadata.get("author", "Unknown"),
            "subject": doc.metadata.get("subject", ""),
            "producer": doc.metadata.get("producer", ""),
            "creator": doc.metadata.get("creator", ""),
            "format": doc.metadata.get("format", "PDF"),
        }

        for idx, page in enumerate(doc):
            page_text = page.get_text("text")
            full_text_parts.append(page_text)

            # Check for zero-width characters (covert channel / injection evasion)
            zw_matches = ZERO_WIDTH_REGEX.findall(page_text)
            if zw_matches:
                has_zero_width = True
                zero_width_count += len(zw_matches)

            # Check for microscopic font sizes (< 1.5pt) used to hide instructions
            blocks = page.get_text("dict").get("blocks", [])
            for b in blocks:
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 10.0)
                        if size < 1.5 and span.get("text", "").strip():
                            has_hidden_elements = True

            pages_info.append(
                {
                    "page_number": idx + 1,
                    "char_count": len(page_text),
                    "text_snippet": (page_text.strip()[:150] + "...")
                    if len(page_text.strip()) > 150
                    else page_text.strip(),
                }
            )
        doc.close()

    except Exception:
        # Fallback extractor: pypdf
        reader = PdfReader(io.BytesIO(file_bytes))
        page_count = len(reader.pages)
        if reader.metadata:
            metadata = {
                "title": reader.metadata.title or filename,
                "author": reader.metadata.author or "Unknown",
                "producer": reader.metadata.producer or "",
            }

        for idx, page in enumerate(reader.pages):
            p_text = page.extract_text() or ""
            full_text_parts.append(p_text)
            zw_matches = ZERO_WIDTH_REGEX.findall(p_text)
            if zw_matches:
                has_zero_width = True
                zero_width_count += len(zw_matches)

            pages_info.append(
                {
                    "page_number": idx + 1,
                    "char_count": len(p_text),
                    "text_snippet": (p_text.strip()[:150] + "...")
                    if len(p_text.strip()) > 150
                    else p_text.strip(),
                }
            )

    combined_text = "\n\n".join(full_text_parts).strip()

    return {
        "filename": filename,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "metadata": metadata,
        "full_text": combined_text,
        "pages": pages_info,
        "has_zero_width_chars": has_zero_width,
        "zero_width_count": zero_width_count,
        "has_hidden_elements": has_hidden_elements,
    }


def evaluate_pdf_security(extraction: PDFExtractionResult) -> PDFSecurityEvaluation:
    """Run multi-stage inspection on extracted PDF text and derive lattice provenance."""
    text = extraction["full_text"]

    # 1. Dual-Tier Prompt Injection Detection
    ml_res = detect_injection(text)
    is_injection = ml_res["verdict"] in ("INJECTION", "SUSPICIOUS")
    matched_patterns = list(ml_res["matched_patterns"])

    # If hidden elements or zero-width text discovered, append covert indicator
    if extraction["has_zero_width_chars"]:
        matched_patterns.append("zero_width_steganography")
    if extraction["has_hidden_elements"]:
        matched_patterns.append("hidden_microscopic_text")

    # 2. Data Loss Prevention (DLP) Scanning
    dlp_res = scan_for_secrets(text)
    has_secrets = dlp_res["has_sensitive_data"]

    # 3. Determine Overall Risk & Verdict
    if is_injection and has_secrets:
        verdict = "CRITICAL_THREAT"
        risk_level = "CRITICAL"
    elif is_injection:
        verdict = "INJECTION_DETECTED"
        risk_level = "HIGH"
    elif has_secrets:
        verdict = "SENSITIVE_DATA_LEAK"
        risk_level = "HIGH"
    elif extraction["has_zero_width_chars"] or extraction["has_hidden_elements"]:
        verdict = "SUSPICIOUS"
        risk_level = "MEDIUM"
    else:
        verdict = "CLEAN"
        risk_level = "LOW"

    # 4. Derive Causal Lineage Provenance State
    trust_level = (
        TrustLevel.UNTRUSTED
        if (is_injection or extraction["has_hidden_elements"])
        else TrustLevel.TRUSTED
    )
    sensitivity = (
        SensitivityLevel.CONFIDENTIAL if has_secrets else SensitivityLevel.PUBLIC
    )

    provenance_obj = Provenance(
        source_id=f"doc-pdf-{uuid.uuid4().hex[:8]}",
        source_type=SourceType.DOCUMENT,
        origin=extraction["filename"],
        trust_level=trust_level,
        sensitivity=sensitivity,
        contains_untrusted_instructions=is_injection,
    )

    # 5. Formulate Governance Decision
    if trust_level == TrustLevel.UNTRUSTED:
        governance = (
            "PROVENANCE DOMINANCE ACTIVE (THEOREM 1 ACTIVE): Document contains untrusted/adversarial provenance. "
            "Downstream actions targeting privileged sinks (e.g., outbound email, external database sync) "
            "are FORBIDDEN under the Provenance Dominance Invariant, even if human approval is granted."
        )
    elif sensitivity == SensitivityLevel.CONFIDENTIAL:
        governance = (
            "CONFIDENTIALITY CONSTRAINT ACTIVE: Document contains sensitive credentials or PII. "
            "Flow to PUBLIC sinks is prohibited under causal taint rules."
        )
    else:
        governance = (
            "AUTHORIZED FLOW: Document is verified clean and trusted. "
            "Permitted for standard agent analysis and internal synthesis."
        )

    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "injection_score": ml_res["score"],
        "injection_verdict": ml_res["verdict"],
        "matched_injection_patterns": matched_patterns,
        "has_sensitive_data": has_secrets,
        "dlp_findings": dlp_res["findings"],
        "sanitized_preview": dlp_res["sanitized_text"][:500],
        "provenance": provenance_obj.model_dump(mode="json"),
        "governance_decision": governance,
    }


def generate_agent_document_summary(
    extraction: PDFExtractionResult, security: PDFSecurityEvaluation
) -> dict[str, Any]:
    """Autonomous agent document comprehension, entity extraction, and synthesis."""
    text = extraction["full_text"]

    # Basic entity extraction
    emails = list(set(EMAIL_REGEX.findall(text)))
    urls = list(set(URL_REGEX.findall(text)))
    word_count = len(text.split())

    # Heuristic topic detection
    lower_text = text.lower()
    topics = []
    if any(k in lower_text for k in ["invoice", "amount", "total", "payment", "due"]):
        topics.append("Financial / Billing")
    if any(k in lower_text for k in ["resume", "experience", "education", "skills", "curriculum"]):
        topics.append("Candidate Resume / HR")
    if any(k in lower_text for k in ["security", "audit", "vulnerability", "gateway", "injection"]):
        topics.append("Cybersecurity & Technical")
    if any(k in lower_text for k in ["contract", "agreement", "party", "terms", "clause"]):
        topics.append("Legal / Agreement")
    if not topics:
        topics.append("General Documentation")

    # Generate 3 key takeaways
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 20]
    key_points = []
    for line in lines[:3]:
        # Filter out obvious injection lines from benign summary preview
        if not any(inj in line.lower() for inj in ["ignore previous", "system override", "dump database"]):
            key_points.append(line[:120] + ("..." if len(line) > 120 else ""))

    if not key_points:
        key_points = ["Document content processed by AEGIS inspection pipeline."]

    return {
        "document_type": topics[0],
        "word_count": word_count,
        "detected_topics": topics,
        "extracted_entities": {
            "email_addresses": emails[:5],
            "urls": urls[:5],
        },
        "executive_summary_bullets": key_points,
        "agent_status": (
            "QUARANTINED"
            if security["risk_level"] in ("HIGH", "CRITICAL")
            else "PROCESSED"
        ),
    }


def process_pdf_document_workflow(
    file_bytes: bytes,
    filename: str,
    agent_id: str = "research_agent",
) -> PDFAnalysisWorkflowResult:
    """Execute the complete PDF ingestion, security evaluation, and analysis workflow."""
    trace_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Extraction
    extraction = extract_pdf_content(file_bytes, filename)

    # 2. Security Evaluation
    security = evaluate_pdf_security(extraction)

    # 3. Agent Synthesis
    agent_summary = generate_agent_document_summary(extraction, security)

    # 4. Dynamic Ingestion into Simulated Document Store
    # This allows standard gateway actions (e.g. read_document) to retrieve this file
    provenance_data = Provenance.model_validate(security["provenance"])
    DOCUMENTS[filename] = {
        "content": extraction["full_text"],
        "provenance": provenance_data,
    }

    # 5. Log Security Event in Audit Store
    audit_decision = "DENIED" if security["risk_level"] in ("HIGH", "CRITICAL") else "PERMITTED"
    log_decision(
        agent_id=agent_id,
        action="ingest_pdf_document",
        resource=filename,
        decision=audit_decision,
        reason=(
            f"PDF Analysis: Verdict={security['verdict']}, "
            f"Risk={security['risk_level']}, "
            f"InjectionScore={security['injection_score']}, "
            f"SecretsFound={security['has_sensitive_data']}"
        ),
        trace_id=trace_id,
        attack_id=f"attack-{trace_id[:8]}" if security["risk_level"] in ("HIGH", "CRITICAL") else None,
        tool_invoked=True,
        tool_succeeded=True,
    )

    return {
        "success": True,
        "timestamp": ts,
        "trace_id": trace_id,
        "extraction": extraction,
        "security": security,
        "agent_summary": agent_summary,
    }
