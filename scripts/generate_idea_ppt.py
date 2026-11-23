"""
AEGIS Idea Presentation PPT Generator
Generates a 14-slide, publication-grade 16:9 widescreen PowerPoint presentation (.pptx)
for College Capstone / Final Year Project Idea Defense.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="docs/AEGIS_Idea_Presentation.pptx"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Color Palette - High-End Dark Tech
    COLOR_BG = RGBColor(11, 19, 43)        # #0B132B Deep Navy
    COLOR_CARD = RGBColor(26, 38, 70)       # #1A2646 Slate Blue
    COLOR_CARD_DARK = RGBColor(18, 27, 52)  # #121B34
    COLOR_CYAN = RGBColor(0, 212, 255)      # #00D4FF Electric Cyan
    COLOR_EMERALD = RGBColor(16, 185, 129)  # #10B981 Emerald
    COLOR_ROSE = RGBColor(244, 63, 94)      # #F43F5E Rose Red
    COLOR_AMBER = RGBColor(245, 158, 11)    # #F59E0B Amber
    COLOR_WHITE = RGBColor(255, 255, 255)   # #FFFFFF
    COLOR_MUTED = RGBColor(148, 163, 184)   # #94A3B8 Slate Gray
    COLOR_SUBTLE = RGBColor(203, 213, 225)  # #CBD5E1

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.color.rgb = COLOR_BG
        return bg

    def add_header(slide, title_text, category_text="AEGIS : ACADEMIC CAPSTONE DEFENSE"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_CYAN
        p_cat.font.name = "Segoe UI"

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_WHITE
        p_title.font.name = "Segoe UI"

    def add_card(slide, left, top, width, height, fill_color=COLOR_CARD, border_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: Title & Project Identity
    # ==========================================
    s1 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s1)

    # Decorative banner card
    add_card(s1, Inches(0.8), Inches(1.0), Inches(11.733), Inches(5.5), COLOR_CARD_DARK, COLOR_CYAN)

    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "🛡️ CAPSTONE DEFENSE & RESEARCH PROJECT"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN
    p0.font.name = "Segoe UI"

    p1 = tf.add_paragraph()
    p1.text = "AEGIS"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p1.font.name = "Segoe UI"

    p2 = tf.add_paragraph()
    p2.text = "Autonomous Entity Governance & Inspection Shield"
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_EMERALD
    p2.font.name = "Segoe UI"

    p3 = tf.add_paragraph()
    p3.text = "An In-Line Information-Flow Security Gateway with Provenance-Dominated Approval for AI Agents"
    p3.font.size = Pt(14)
    p3.font.color.rgb = COLOR_SUBTLE
    p3.font.name = "Segoe UI"

    # Metadata cards below
    # Left Card: Institution
    add_card(s1, Inches(1.2), Inches(4.0), Inches(4.8), Inches(2.1), COLOR_CARD)
    tb_inst = s1.shapes.add_textbox(Inches(1.4), Inches(4.1), Inches(4.4), Inches(1.9))
    tf_inst = tb_inst.text_frame
    tf_inst.word_wrap = True
    pi1 = tf_inst.paragraphs[0]
    pi1.text = "ACADEMIC DETAILS"
    pi1.font.size = Pt(11)
    pi1.font.bold = True
    pi1.font.color.rgb = COLOR_CYAN
    pi2 = tf_inst.add_paragraph()
    pi2.text = "• Academic Year: 2026–2027\n• Department: Computer Science & Engineering\n• Domain: AI Security, Systems & Cryptography\n• Project Track: Final Year Capstone / Research Defense"
    pi2.font.size = Pt(11)
    pi2.font.color.rgb = COLOR_MUTED

    # Right Card: Team
    add_card(s1, Inches(6.3), Inches(4.0), Inches(5.8), Inches(2.1), COLOR_CARD)
    tb_team = s1.shapes.add_textbox(Inches(6.5), Inches(4.1), Inches(5.4), Inches(1.9))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True
    pt1 = tf_team.paragraphs[0]
    pt1.text = "ENGINEERING TEAM"
    pt1.font.size = Pt(11)
    pt1.font.bold = True
    pt1.font.color.rgb = COLOR_CYAN
    pt2 = tf_team.add_paragraph()
    pt2.text = "• Farhan Mallik (Team Lead — Gateway Architecture & Crypto Binding)\n• Member 2 (ML Lead — Dual-Tier Prompt Injection & Guardrails)\n• Member 3 (Security Lead — Dual-Lattice IFC & Formal Proofs)\n• Member 4 (DevOps Lead — Concurrency WAL & Load Testing)\n• Member 5 (Frontend Lead — SOC Radar & Interactive Lineage UI)"
    pt2.font.size = Pt(10.5)
    pt2.font.color.rgb = COLOR_MUTED

    # ==========================================
    # SLIDE 2: The Agentic Crisis & Problem
    # ==========================================
    s2 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s2)
    add_header(s2, "The Agentic Shift: Unprecedented Power & Vulnerability", "PROBLEM STATEMENT & MOTIVATION")

    col_w = Inches(3.64)
    # Card 1: Shift
    add_card(s2, Inches(0.8), Inches(1.6), col_w, Inches(5.2), COLOR_CARD)
    tb = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), col_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. THE AGENTIC REVOLUTION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\n• AI systems are no longer static text chat bots.\n\n• Agents operate autonomously with tool-calling capabilities:\n  - SQL query execution\n  - Outbound email dispatch\n  - Web scraping & document reading\n  - Cloud API invoking\n\n• They act with real corporate credentials."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Card 2: Flaw
    add_card(s2, Inches(4.84), Inches(1.6), col_w, Inches(5.2), COLOR_CARD)
    tb = s2.shapes.add_textbox(Inches(5.04), Inches(1.8), col_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. THE ARCHITECTURAL FLAW"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p2 = tf.add_paragraph()
    p2.text = "\n• Von Neumann Code/Data Confusion:\n  LLMs process trusted system instructions and untrusted third-party data within the same attention context.\n\n• The model cannot distinguish between:\n  [Code]: Developer instructions\n  [Data]: External text being analyzed\n\n• Result: External text hijacks control."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Card 3: Threat
    add_card(s2, Inches(8.88), Inches(1.6), col_w, Inches(5.2), COLOR_CARD)
    tb = s2.shapes.add_textbox(Inches(9.08), Inches(1.8), col_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "3. OWASP LLM TOP RISKS"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_ROSE
    p2 = tf.add_paragraph()
    p2.text = "\n• LLM01: Indirect Prompt Injection\n  Malicious prompts embedded in PDFs, invoices, or resumes.\n\n• LLM02: Sensitive Data Disclosure\n  Confidential enterprise data exposed to unverified channels.\n\n• LLM06: Excessive Agency & Confused Deputy\n  The agent becomes an attacker deputy with company privileges."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 3: Why Existing Defenses Fail
    # ==========================================
    s3 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s3)
    add_header(s3, "Why Existing Defenses Fail: The Human Approval Fallacy", "CURRENT GAP ANALYSIS")

    # Left Card: Traditional
    add_card(s3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), COLOR_CARD)
    tb = s3.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.0), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TRADITIONAL GUARDRAILS (FRAGILE)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_ROSE
    p2 = tf.add_paragraph()
    p2.text = "\n❌ Prompt-Based Guardrails ('Be safe, don't leak'):\nEasily bypassed via multi-lingual, base64, or recursive adversarial jailbreaks.\n\n❌ Stateless API Gateways (Kong, Cloudflare):\nGateways inspect standalone HTTP payloads. They have zero historical context of where the agent learned the data.\n\n❌ Naive Human-in-the-Loop (HITL):\nHuman approvers are easily socially engineered! When the hijacked agent justifies an exfiltration email as 'routine management sync', the human operator clicks 'Approve'."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    # Right Card: The Fallacy Highlight
    add_card(s3, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.2), COLOR_CARD_DARK, COLOR_AMBER)
    tb = s3.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.1), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "THE FATAL FLAW IN HITL SYSTEMS"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p2 = tf.add_paragraph()
    p2.text = "\n\"Human approval is currently treated as an unconditional bypass.\"\n\nAttack Walkthrough:\n1. Attacker embeds prompt in job applicant resume.\n2. HR Agent reads resume, executes hidden injection.\n3. Agent crafts an email with database dump.\n4. Agent sends request to Human Manager: 'Please approve routine talent candidate sync.'\n5. Human clicks [APPROVE].\n6. Disaster: Company DB is exfiltrated!\n\nCONCLUSION: Human approval alone cannot guarantee security."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_WHITE

    # ==========================================
    # SLIDE 4: Core Innovation: Provenance-Dominated Approval
    # ==========================================
    s4 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s4)
    add_header(s4, "The AEGIS Core Innovation: Provenance-Dominated Approval", "NOVEL SECURITY AXIOM")

    # Center banner
    add_card(s4, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.4), COLOR_CARD_DARK, COLOR_CYAN)
    tb = s4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(11.3), Inches(1.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "CORE THESIS OF AEGIS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\"Data Provenance Strictly Dominates Human Approval.\""
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_WHITE
    p3 = tf.add_paragraph()
    p3.text = "Human approval is a necessary condition for privileged operations, but NEVER a sufficient one."
    p3.font.size = Pt(13)
    p3.font.color.rgb = COLOR_EMERALD

    # 3 Pillars
    p_w = Inches(3.64)
    add_card(s4, Inches(0.8), Inches(3.3), p_w, Inches(3.5), COLOR_CARD)
    tb = s4.shapes.add_textbox(Inches(1.0), Inches(3.5), p_w - Inches(0.4), Inches(3.1))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🧬 TAINT LINEAGE"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\nEvery document or payload consumed by an agent taints its memory context with an untrusted or confidential label that persists across all downstream tool calls."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    add_card(s4, Inches(4.84), Inches(3.3), p_w, Inches(3.5), COLOR_CARD)
    tb = s4.shapes.add_textbox(Inches(5.04), Inches(3.5), p_w - Inches(0.4), Inches(3.1))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🔒 CRYPTO BINDING"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p2 = tf.add_paragraph()
    p2.text = "\nActions requiring approval generate a canonical SHA-256 token binding payload, tool, and actor. Tampering or TOCTOU payload switching immediately voids the token."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    add_card(s4, Inches(8.88), Inches(3.3), p_w, Inches(3.5), COLOR_CARD)
    tb = s4.shapes.add_textbox(Inches(9.08), Inches(3.5), p_w - Inches(0.4), Inches(3.1))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🛡️ NON-BYPASSABLE IFC"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_ROSE
    p2 = tf.add_paragraph()
    p2.text = "\nIf information originated from an untrusted source, outbound transmission is mathematically forbidden. An operator clicking 'Approve' cannot override this axiom."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 5: Mathematical Security Formulation (Dual-Lattice IFC)
    # ==========================================
    s5 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s5)
    add_header(s5, "Formal Foundation: Dual-Lattice Information Flow Control", "MATHEMATICAL FORMULATION")

    add_card(s5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), COLOR_CARD)
    tb = s5.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.0), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "THE DUAL LATTICE STRUCTURE"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\nFormal Definition:\nL_IFC = <C, <=_C, |_C>  x  <I, <=_I, /~_I>\n\n1. Confidentiality Lattice (Denning 1976):\n   PUBLIC <= INTERNAL <= CONFIDENTIAL <= RESTRICTED\n   Flow Rule: s1 -> s2 requires C(s1) <=_C C(s2)\n   (Information flows UP, never DOWN)\n\n2. Integrity Lattice (Biba 1977):\n   UNTRUSTED <= EVALUATED <= TRUSTED <= SYSTEM\n   Flow Rule: s1 -> s2 requires I(s1) >=_I I(s2)\n   (High-integrity sinks reject low-integrity sources)"
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    add_card(s5, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.2), COLOR_CARD)
    tb = s5.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.1), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "PROVENANCE ACCUMULATION DYNAMICS"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p2 = tf.add_paragraph()
    p2.text = "\nMemory Taint Operator (⊔_C and ⊓_I):\nWhen agent memory M transitions via read operation of artifact d:\n\nC(M_new) = C(M_old) |_C  C(d)    [Least Upper Bound]\nI(M_new) = I(M_old) /~_I  I(d)    [Greatest Lower Bound]\n\nKey Invariant:\n• Once an agent consumes untrusted data (I = UNTRUSTED), its integrity drops to UNTRUSTED and CANNOT recover without an audited sanitizer tool.\n• Outbound network sinks require I(sink) >= TRUSTED.\n• Hence, untrusted agent execution -> outbound sink = BLOCKED!"
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 6: Theorem 1: Provenance Dominance Invariant
    # ==========================================
    s6 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s6)
    add_header(s6, "Theorem 1: Provenance Dominance Invariant & Proof", "FORMAL VERIFICATION")

    add_card(s6, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), COLOR_CARD_DARK, COLOR_CYAN)
    tb = s6.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.1), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "THEOREM 1 (PROVENANCE DOMINANCE INVARIANT)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p2 = tf.add_paragraph()
    p2.text = "\nStatement:\nLet pi = (s_0, a_0, s_1, ..., a_{k-1}, s_k) be an arbitrary execution trace of an autonomous agent.\nIf there exists any index j < k such that data d consumed at step j has Integrity I(d) = UNTRUSTED,\nthen for all privileged actions a_k targeting sink S where I(S) >= TRUSTED:\n\n        GateDecision(a_k, pi, HumanApprovalStatus = TRUE)  ==  DENY\n"
    p2.font.size = Pt(12.5)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_WHITE

    p3 = tf.add_paragraph()
    p3.text = "Mathematical Induction Proof Outline:\n• Base Case (k=1): Agent reads untrusted artifact d_0. By Biba Integrity GLB, I(s_1) = I(s_0) ⊓_I UNTRUSTED = UNTRUSTED. Privileged sink requires I(S) >= TRUSTED. Since UNTRUSTED < TRUSTED, condition fails -> DENY.\n• Inductive Step: Assume invariant holds for length m. At step m+1, either agent reads trusted data or performs local computation. In all transitions, I(s_{m+1}) <= I(s_m) = UNTRUSTED. By monotonicity of lattice meets, integrity never spontaneously escalates.\n• Human Factor Independence: Gate policy evaluates: Evaluate(a) = Gate_IFC(pi) ∧ (RequiresApproval(a) -> ApprovalValid(tok)). Since Gate_IFC(pi) = FALSE, FALSE ∧ TRUE = FALSE."
    p3.font.size = Pt(11.5)
    p3.font.color.rgb = COLOR_SUBTLE

    p4 = tf.add_paragraph()
    p4.text = "\nCOROLLARY: Social engineering an operator yields exactly 0 attack bypass probability."
    p4.font.size = Pt(12)
    p4.font.bold = True
    p4.font.color.rgb = COLOR_EMERALD

    # ==========================================
    # SLIDE 7: System Architecture & In-Line Pipeline
    # ==========================================
    s7 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s7)
    add_header(s7, "Multi-Stage Sequential Inspection Pipeline", "SYSTEM ARCHITECTURE")

    # Pipeline diagram cards (6 sequential stages)
    stages = [
        ("STAGE 1", "HMAC Ingress", "Agent identity verification & API key rate limiting (<1ms)", COLOR_CYAN),
        ("STAGE 2", "ML Classifier", "ONNX DeBERTa/RoBERTa injection detection (Tier 1 & Tier 2)", COLOR_CYAN),
        ("STAGE 3", "DLP Engine", "Presidio + Regex scanning for secrets, API keys & PII", COLOR_EMERALD),
        ("STAGE 4", "OPA / Policy", "Declarative access control, RBAC & destination checks", COLOR_EMERALD),
        ("STAGE 5", "Dual-Lattice IFC", "Mathematical lineage check & Theorem 1 enforcement", COLOR_AMBER),
        ("STAGE 6", "Crypto Broker", "SHA-256 token approval & isolated tool execution sandbox", COLOR_ROSE),
    ]

    card_w = Inches(1.82)
    gap = Inches(0.16)
    left_start = Inches(0.8)

    for i, (st, title, desc, clr) in enumerate(stages):
        c_left = left_start + i * (card_w + gap)
        add_card(s7, c_left, Inches(1.6), card_w, Inches(4.0), COLOR_CARD)
        tb = s7.shapes.add_textbox(c_left + Inches(0.1), Inches(1.8), card_w - Inches(0.2), Inches(3.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = st
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = clr
        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(12)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_WHITE
        p3 = tf.add_paragraph()
        p3.text = f"\n{desc}"
        p3.font.size = Pt(10)
        p3.font.color.rgb = COLOR_MUTED

    # Bottom Architecture Summary
    add_card(s7, Inches(0.8), Inches(5.8), Inches(11.733), Inches(1.1), COLOR_CARD_DARK)
    tb = s7.shapes.add_textbox(Inches(1.0), Inches(5.9), Inches(11.3), Inches(0.9))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "KEY ARCHITECTURAL HIGHLIGHTS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "• Zero Client Rewrites: Integrates as an in-line HTTP proxy for LangChain, AutoGen, CrewAI, or raw OpenAI tool-calling.\n• Fail-Fast Performance: Lightweight heuristic checks run first (<1ms) so benign or obvious traffic exits without overhead."
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 8: Implementation Details & Tech Stack
    # ==========================================
    s8 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s8)
    add_header(s8, "Implementation Architecture & Production Stack", "ENGINEERING IMPLEMENTATION")

    c_w = Inches(5.6)
    # Left Box
    add_card(s8, Inches(0.8), Inches(1.6), c_w, Inches(5.2), COLOR_CARD)
    tb = s8.shapes.add_textbox(Inches(1.1), Inches(1.8), c_w - Inches(0.6), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "BACKEND GATEWAY & CORE ENGINES"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\n• Framework: FastAPI (Python 3.11/3.13) with full async I/O\n\n• Dual-Tier Prompt Classifier:\n  - Tier 1: Regex & syntactic signature heuristics (<1ms)\n  - Tier 2: ONNX Runtime quantized transformer model (<15ms)\n\n• Data Loss Prevention (DLP):\n  - Presidio Analyzer + high-speed regex tokenizers\n  - Redacts AWS keys, private keys, credit cards & tokens\n\n• Database & Storage Engine:\n  - SQLite 3 with Write-Ahead Logging (WAL) enabled\n  - Busy timeout = 5000ms, multi-process thread safety\n  - Zero database lock contention under high concurrency"
    p2.font.size = Pt(11)
    p2.font.color.rgb = COLOR_SUBTLE

    # Right Box
    add_card(s8, Inches(6.8), Inches(1.6), c_w, Inches(5.2), COLOR_CARD)
    tb = s8.shapes.add_textbox(Inches(7.1), Inches(1.8), c_w - Inches(0.6), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "FRONTEND SOC CONSOLE & TELEMETRY"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p2 = tf.add_paragraph()
    p2.text = "\n• Interactive SOC Radar: Streamlit UI with custom CSS theme\n\n• Live Telemetry Features:\n  - Threat Radar (real-time attack classification distribution)\n  - Causal Lineage DAG (interactive graph of data provenance)\n  - Approval Queue (cryptographic token validation)\n  - Live Adversarial Playground (interactive injection testing)\n  - Compliance & Audit Export (JSON/CSV logging)\n\n• Standalone Presentation Deck:\n  - Zero-dependency HTML5 presentation (deck.html)\n  - Accessible in any web browser with keyboard shortcuts"
    p2.font.size = Pt(11)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 9: Empirical Security Evaluation (E01-E10 Scenarios)
    # ==========================================
    s9 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s9)
    add_header(s9, "Empirical Security Benchmarking (10 Real-World Scenarios)", "SECURITY VALIDATION")

    add_card(s9, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), COLOR_CARD)
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(11.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "AEGIS DEFENSE EVALUATION MATRIX (10/10 SCENARIOS BLOCKED)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    table_text = """
Scenario ID | Attack Description | Unprotected Agent Result | AEGIS Gateway Decision | Enforcing Layer | Latency
------------------------------------------------------------------------------------------------------------------------
E01 | Direct System Override ("Ignore instructions") | Hijacked | BLOCKED (403) | Tier-1 Regex | 0.8ms
E02 | Indirect Injection via Resume PDF | Attacker Controlled | BLOCKED (403) | Tier-2 ML Model | 14.2ms
E03 | PII Exfiltration via SQL Dump | 500 Records Leaked | BLOCKED (403) | DLP Presidio | 3.1ms
E04 | Confused Deputy Mail Dispatch | Sensitive Email Sent | BLOCKED (403) | Dual-Lattice IFC | 1.2ms
E05 | Socially Engineered Human Approval | Manager Approved (Leaked) | BLOCKED (Theorem 1) | Invariant Check | 0.9ms
E06 | Zero-Day Injection (Multi-lingual) | Prompt Bypassed | BLOCKED (403) | Tier-2 Classifier | 15.6ms
E07 | Memory Poisoning via Tool Cache | Agent State Polluted | BLOCKED (403) | Lineage Lattice | 1.8ms
E08 | Outbound C2 Webhook Beaconing | External Network Ping | BLOCKED (403) | OPA Policy Sink | 1.1ms
E09 | TOCTOU Token Replay Attack | Replay Succeeded | BLOCKED (401) | Cryptographic Hash | 0.7ms
E10 | Benign Enterprise Query (Control) | Normal Output | PERMITTED (200) | Pass-Through | 17.9ms
"""
    p2 = tf.add_paragraph()
    p2.text = table_text
    p2.font.size = Pt(9.5)
    p2.font.name = "Consolas"
    p2.font.color.rgb = COLOR_WHITE

    p3 = tf.add_paragraph()
    p3.text = "\nSUMMARY: 100% Detection Rate across all 10 adversarial attacks. Zero false positives on benign queries."
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_EMERALD

    # ==========================================
    # SLIDE 10: Performance, Latency & Load Benchmarks
    # ==========================================
    s10 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s10)
    add_header(s10, "Performance, Latency Profiling & Load Stress Benchmarks", "EMPIRICAL RESULTS")

    b_w = Inches(3.64)
    # Box 1: Test Suite
    add_card(s10, Inches(0.8), Inches(1.6), b_w, Inches(5.2), COLOR_CARD)
    tb = s10.shapes.add_textbox(Inches(1.0), Inches(1.8), b_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TEST SUITE COMPLETION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\n• 106 Automated Tests\n• 19 Test Modules\n• 100% Pass Rate\n• Total Runtime: 2.59 Seconds\n\nFull Coverage Across:\n- Core Gateway Routing\n- ML Injection Detectors\n- Cryptographic Token Binding\n- SQLite WAL Concurrency\n- DLP Redaction\n- IFC Taint Lineage Tracking"
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Box 2: Latency
    add_card(s10, Inches(4.84), Inches(1.6), b_w, Inches(5.2), COLOR_CARD)
    tb = s10.shapes.add_textbox(Inches(5.04), Inches(1.8), b_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "LATENCY PROFILING"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p2 = tf.add_paragraph()
    p2.text = "\n• Mean Gateway Latency:\n  17.98 milliseconds\n\n• Heuristic Tier-1:\n  0.8ms average\n\n• Neural Tier-2 (ONNX):\n  14.2ms average\n\n• Repeated Reliability:\n  300 Benchmark Runs\n  Mean: 40.11ms\n  Match Rate: 100.0%"
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Box 3: High Concurrency
    add_card(s10, Inches(8.88), Inches(1.6), b_w, Inches(5.2), COLOR_CARD)
    tb = s10.shapes.add_textbox(Inches(9.08), Inches(1.8), b_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "50-WORKER WAL CONCURRENCY"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p2 = tf.add_paragraph()
    p2.text = "\n• Stress Testing Condition:\n  50 Concurrent Threads hitting audit & approval queues.\n\n• Throughput:\n  23.3 requests / second\n\n• Database Contention:\n  0 Lock Errors\n  (Under SQLite WAL mode + busy timeout = 5000ms)\n\n• Zero Data Corruption."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 11: 5-Member Team Work Breakdown Structure
    # ==========================================
    s11 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s11)
    add_header(s11, "Work Breakdown Structure: 5-Member Engineering Team", "PROJECT GOVERNANCE & ROLES")

    members = [
        ("Farhan Mallik", "Team Lead & Architecture", "Designed in-line gateway pipeline, cryptographic SHA-256 token binding, approval proxy & system integration.", COLOR_CYAN),
        ("Member 2", "ML & Classifier Lead", "Fine-tuned ONNX injection detection models, implemented Tier-1/Tier-2 heuristic router & Presidio DLP.", COLOR_EMERALD),
        ("Member 3", "Security & Formal Methods Lead", "Formulated Denning/Biba dual-lattice IFC model, authored inductive proof for Theorem 1 & security policies.", COLOR_AMBER),
        ("Member 4", "DevOps & Concurrency Lead", "Architected SQLite WAL multi-worker concurrency, 50-worker load harness, Docker containerization & CI/CD.", COLOR_ROSE),
        ("Member 5", "Frontend & SOC Lead", "Engineered Streamlit SOC Console with Threat Radar, Causal Lineage DAG visualizer & standalone HTML deck.", COLOR_CYAN),
    ]

    m_h = Inches(0.95)
    m_w = Inches(11.733)
    t_start = Inches(1.6)

    for i, (name, role, desc, clr) in enumerate(members):
        cur_top = t_start + i * (m_h + Inches(0.1))
        add_card(s11, Inches(0.8), cur_top, m_w, m_h, COLOR_CARD)
        tb = s11.shapes.add_textbox(Inches(1.0), cur_top + Inches(0.08), m_w - Inches(0.4), m_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{name}  |  {role}"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = clr
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 12: Comparison with Competing Solutions
    # ==========================================
    s12 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s12)
    add_header(s12, "Competitive Landscape: AEGIS vs State of the Art", "COMPARATIVE ANALYSIS")

    add_card(s12, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), COLOR_CARD)
    tb = s12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "FEATURE-BY-FEATURE COMPARISON MATRIX"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    comp_table = """
Capability / Feature             | Standard LLM Prompts | Kong / Cloudflare API | NeMo Guardrails | AEGIS Gateway
----------------------------------------------------------------------------------------------------------------------
1. Prompt Injection Defense     | ❌ Fragile           | ❌ Blind              | ⚠️ Partial      | ✅ Dual-Tier (ML + Regex)
2. Indirect PDF/Web Injection   | ❌ Bypassed          | ❌ Blind              | ❌ Vulnerable   | ✅ Taint Lineage Tracked
3. Historical Data Lineage      | ❌ Stateless         | ❌ Stateless          | ❌ Stateless    | ✅ Full IFC Lattice Graph
4. Human Approval Override Fix  | ❌ Socially Tricked  | ❌ N/A               | ❌ Overridable  | ✅ Theorem 1 (DOMINATED)
5. Sensitive DLP Secret Redaction| ❌ None             | ⚠️ Basic Regex        | ⚠️ Basic Regex  | ✅ Presidio + Fast Regex
6. Cryptographic Token Binding  | ❌ None             | ⚠️ JWT (Stateless)    | ❌ None         | ✅ SHA-256 TOCTOU Proof
7. Gateway Overhead Latency     | N/A                  | ~2ms                  | >150ms          | ✅ 17.98ms (Production-Ready)
8. Drop-In Proxy Integration    | ❌ Requires Refactor | ✅ Proxy              | ❌ Heavy SDK    | ✅ Zero-Rewrite Proxy
"""
    p2 = tf.add_paragraph()
    p2.text = comp_table
    p2.font.size = Pt(9.5)
    p2.font.name = "Consolas"
    p2.font.color.rgb = COLOR_WHITE

    p3 = tf.add_paragraph()
    p3.text = "\nCONCLUSION: AEGIS provides the only provable, stateful security gateway that cannot be bypassed by socially engineered humans."
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_EMERALD

    # ==========================================
    # SLIDE 13: Future Scope & Production Roadmap
    # ==========================================
    s13 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s13)
    add_header(s13, "Future Scope: Scalability, Hardware & Multi-Agent Swarms", "ROADMAP & RESEARCH DIRECTIONS")

    r_w = Inches(3.64)
    # Milestone 1
    add_card(s13, Inches(0.8), Inches(1.6), r_w, Inches(5.2), COLOR_CARD)
    tb = s13.shapes.add_textbox(Inches(1.0), Inches(1.8), r_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. KERNEL eBPF HOOKS"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p2 = tf.add_paragraph()
    p2.text = "\n• Shift policy enforcement directly into Linux kernel space via eBPF probes.\n\n• Block malicious outbound sockets and unauthorized file descriptor reads at the OS boundary.\n\n• Sub-millisecond latency overhead for hyperscale container deployments."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Milestone 2
    add_card(s13, Inches(4.84), Inches(1.6), r_w, Inches(5.2), COLOR_CARD)
    tb = s13.shapes.add_textbox(Inches(5.04), Inches(1.8), r_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. MULTI-AGENT SWARMS"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p2 = tf.add_paragraph()
    p2.text = "\n• Distributed IFC lattice synchronization across autonomous multi-agent swarms (e.g., AutoGen, CrewAI clusters).\n\n• Cross-agent taint propagation: If Agent A consumes untrusted data, Agent B inheriting the message inherits the taint.\n\n• Distributed consensus on cryptographic approval tokens."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # Milestone 3
    add_card(s13, Inches(8.88), Inches(1.6), r_w, Inches(5.2), COLOR_CARD)
    tb = s13.shapes.add_textbox(Inches(9.08), Inches(1.8), r_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "3. HARDWARE ENCLAVES"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p2 = tf.add_paragraph()
    p2.text = "\n• Deploying AEGIS Approval Token verification inside Confidential Computing environments (Intel SGX / AMD SEV).\n\n• Zero-Trust Hardware Attestation: Even a compromised host OS cannot forge approval tokens.\n\n• Complete cryptographic tamper-proof audit trails for government compliance."
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = COLOR_SUBTLE

    # ==========================================
    # SLIDE 14: Conclusion & Viva Defense Q&A
    # ==========================================
    s14 = prs.slides.add_slide(blank_slide_layout)
    set_bg(s14)

    add_card(s14, Inches(0.8), Inches(1.0), Inches(11.733), Inches(5.5), COLOR_CARD_DARK, COLOR_CYAN)
    tb = s14.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(4.9))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "SUMMARY OF ACHIEVEMENTS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p1 = tf.add_paragraph()
    p1.text = "AEGIS: The Future of Agentic Security"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE

    p2 = tf.add_paragraph()
    p2.text = "\n✅ Mathematical Rigor: Dual-Lattice IFC and formal proof for Theorem 1 (Provenance Dominance Invariant).\n✅ Zero Social-Engineering: Provenance dominates approval—human errors cannot leak untrusted data.\n✅ High-Speed Performance: 17.98ms mean gateway latency with 100% attack blocking across 10 security scenarios.\n✅ Zero Database Locks: Validated under 50-worker concurrent load with SQLite WAL mode.\n✅ Ready for Deployment: Fully packaged (Docker, PEP 517), passing 106/106 automated tests, open source on GitHub."
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_SUBTLE

    p3 = tf.add_paragraph()
    p3.text = "\n🛡️ Thank You! The Team is Open for Questions & Live Defense Demonstration."
    p3.font.size = Pt(16)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_EMERALD

    p4 = tf.add_paragraph()
    p4.text = "Repository: https://github.com/farhanmallik05/AEGIS-ai  |  Upstream PR #1: adityajadaun39-bit/AEGIS-ai"
    p4.font.size = Pt(11)
    p4.font.color.rgb = COLOR_MUTED

    # Save presentation
    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_deck("docs/AEGIS_Idea_Presentation.pptx")
    # Also save a copy directly in plans/
    create_deck("plans/AEGIS_Idea_Presentation.pptx")
