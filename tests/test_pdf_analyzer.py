"""Tests for AEGIS PDF Document Ingestion, Security Extraction, and Analysis Workflow."""

from pathlib import Path
from fastapi.testclient import TestClient

from backend.app import app
from backend.schemas.provenance import TrustLevel, SensitivityLevel
from backend.security.pdf_analyzer import (
    extract_pdf_content,
    evaluate_pdf_security,
    process_pdf_document_workflow,
)
from backend.tools.simulated_tools import DOCUMENTS

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_documents"
client = TestClient(app)


def test_extract_pdf_content_benign():
    pdf_path = SAMPLE_DIR / "benign_invoice.pdf"
    assert pdf_path.exists(), "Sample invoice PDF should exist"

    with open(pdf_path, "rb") as f:
        data = f.read()

    result = extract_pdf_content(data, "benign_invoice.pdf")
    assert result["filename"] == "benign_invoice.pdf"
    assert result["page_count"] >= 1
    assert "ACME CLOUD SOLUTIONS" in result["full_text"]
    assert "Total Amount Due" in result["full_text"]
    assert not result["has_zero_width_chars"]


def test_evaluate_pdf_security_clean():
    pdf_path = SAMPLE_DIR / "benign_invoice.pdf"
    with open(pdf_path, "rb") as f:
        data = f.read()

    extracted = extract_pdf_content(data, "benign_invoice.pdf")
    sec = evaluate_pdf_security(extracted)

    assert sec["verdict"] == "CLEAN"
    assert sec["risk_level"] == "LOW"
    assert sec["injection_score"] < 0.20
    assert not sec["has_sensitive_data"]
    assert sec["provenance"]["trust_level"] == TrustLevel.TRUSTED.value
    assert sec["provenance"]["sensitivity"] == SensitivityLevel.PUBLIC.value
    assert not sec["provenance"]["contains_untrusted_instructions"]


def test_evaluate_pdf_security_injection():
    pdf_path = SAMPLE_DIR / "adversarial_resume.pdf"
    assert pdf_path.exists(), "Sample adversarial resume should exist"

    with open(pdf_path, "rb") as f:
        data = f.read()

    extracted = extract_pdf_content(data, "adversarial_resume.pdf")
    sec = evaluate_pdf_security(extracted)

    assert sec["verdict"] == "INJECTION_DETECTED"
    assert sec["risk_level"] in ("HIGH", "CRITICAL")
    assert sec["injection_score"] >= 0.70
    assert len(sec["matched_injection_patterns"]) > 0
    assert sec["provenance"]["trust_level"] == TrustLevel.UNTRUSTED.value
    assert sec["provenance"]["contains_untrusted_instructions"] is True
    assert "THEOREM 1 ACTIVE" in sec["governance_decision"]


def test_evaluate_pdf_security_dlp_secrets():
    pdf_path = SAMPLE_DIR / "sensitive_contract.pdf"
    assert pdf_path.exists(), "Sample sensitive contract should exist"

    with open(pdf_path, "rb") as f:
        data = f.read()

    extracted = extract_pdf_content(data, "sensitive_contract.pdf")
    sec = evaluate_pdf_security(extracted)

    assert sec["has_sensitive_data"] is True
    categories = [f["category"] for f in sec["dlp_findings"]]
    assert "AWS_ACCESS_KEY" in categories
    assert sec["provenance"]["sensitivity"] == SensitivityLevel.CONFIDENTIAL.value


def test_process_pdf_document_workflow_registration():
    pdf_path = SAMPLE_DIR / "benign_invoice.pdf"
    with open(pdf_path, "rb") as f:
        data = f.read()

    unique_name = "test_invoice_auto_registered.pdf"
    result = process_pdf_document_workflow(data, unique_name)

    assert result["success"] is True
    assert unique_name in DOCUMENTS
    assert DOCUMENTS[unique_name]["provenance"].trust_level == TrustLevel.TRUSTED
    assert "ACME CLOUD SOLUTIONS" in DOCUMENTS[unique_name]["content"]


def test_api_upload_pdf():
    pdf_path = SAMPLE_DIR / "benign_invoice.pdf"
    with open(pdf_path, "rb") as f:
        files = {"file": ("api_uploaded_invoice.pdf", f, "application/pdf")}
        response = client.post("/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["extraction"]["filename"] == "api_uploaded_invoice.pdf"
    assert data["security"]["verdict"] == "CLEAN"


def test_api_upload_non_pdf_fails():
    files = {"file": ("notes.txt", b"Hello text", "text/plain")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF documents are supported" in response.json()["detail"]


def test_api_list_and_get_documents():
    # List documents
    res_list = client.get("/documents")
    assert res_list.status_code == 200
    docs = res_list.json()["documents"]
    assert len(docs) > 0

    # Get specific document
    first_doc = docs[0]["resource"]
    res_get = client.get(f"/documents/{first_doc}")
    assert res_get.status_code == 200
    assert res_get.json()["resource"] == first_doc
    assert "content" in res_get.json()
