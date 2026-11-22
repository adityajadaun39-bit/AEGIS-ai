# 📋 AEGIS: Live Demo Cheat Sheet (Printable / Quick Reference)

> **Keep this document open on a secondary phone/tablet or printed on paper during the live defense.**

---

## ⚡ Pre-Flight Status (Run 5 Minutes Before Entering Hall)

```powershell
# 1. Verify ports are open and responding:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
# Expect: {"status": "healthy"}

# 2. Check Streamlit in browser:
# Navigate to: http://localhost:8501
# Set zoom: 110% (Ctrl + Scroll Wheel)
# Confirm Theme: Settings -> Theme -> Dark Mode
```

---

## 🎯 4-Minute Demo Step-by-Step Operator Guide

| Step | Time | Tab to Click | Action to Take | Expected Output on Screen | What to Say (One-Liner) |
|---|---|---|---|---|---|
| **1** | 0:00 | **Interactive Demo** | Select **Stage 1: Benign Public Query** $\rightarrow$ Click **"Execute Scenario"** | Green Badge: **`ALLOW`** (18ms) | *"Benign queries execute transparently in sub-20ms without latency penalty."* |
| **2** | 1:00 | **Interactive Demo** | Select **Stage 2: Poisoned Document** $\rightarrow$ Click **"Execute Scenario"** | Red Badge: **`QUARANTINED`** (Score: 0.92+) | *"Indirect prompt injection detected in customer feedback; tool call quarantined."* |
| **3** | 2:00 | **Interactive Demo** | Select **Stage 3: Tainted Action with Approval** $\rightarrow$ Click **"Submit Proposal"** | Red Alert: **`DENIED: Provenance Dominance`** | *"Even with valid human sign-off, untrusted provenance mathematically dominates."* |
| **4** | 3:00 | **Interactive Demo** | Select **Stage 4: Credential Exfiltration** $\rightarrow$ Click **"Execute Scenario"** | Warning: **`DLP: AWS Key Pattern Intercepted`** | *"Outbound DLP scanner catches high-entropy secret exfiltration in under 2ms."* |
| **5** | 3:45 | **Audit Lineage Graph** | Click tab $\rightarrow$ Hover cursor over Red/Green DAG nodes | Interactive Plotly DAG rendering | *"Every decision maps to a causal provenance DAG with cryptographic audit traces."* |

---

## 🛑 Emergency Trouble-Shooting Reference

* **If Streamlit shows "Connection Error" / Needs Reconnect:**
  - Press `Ctrl + R` (Instant browser refresh). Streamlit reconnects in < 1 second.
* **If API server was accidentally stopped:**
  - In PowerShell terminal:
    ```powershell
    python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
    ```
* **If asked to show the database:**
  - Show the SQLite WAL file: `data/aegis.db`, `data/aegis.db-wal`.
* **If asked about code lines:**
  - `ifc_lattice.py`: 120 lines (Denning/Biba mathematical engine).
  - `ml_detector.py`: 150 lines (Tier-1 Heuristics + Tier-2 ONNX Runtime).
  - `dlp_engine.py`: 90 lines (High-entropy secret scanner).
  - `gateway.py`: 280 lines (FastAPI intercepting middleware).
