# AEGIS Capstone Submission & Competition Checklist

## 1. Deliverables Inventory

| Category | Item | Location | Status |
|---|---|---|---|
| **Codebase** | Core Gateway & API | `backend/` | Complete |
| **Packaging** | Pyproject & Lockfile | `pyproject.toml`, `requirements.lock` | Complete |
| **Scripts** | One-Click Setup | `scripts/setup.ps1`, `scripts/setup.sh` | Complete |
| **Testing** | 100+ Test Suite | `tests/` | Passing (106/106) |
| **Evaluation** | Security Scenarios | `evaluation/run_evaluation.py` | 100% (10/10) |
| **Benchmark** | Latency & Accuracy | `evaluation/run_benchmark.py` | 100% (300/300) |
| **Concurrency**| 50-Worker Load Test | `evaluation/run_load_test.py` | 0 lock errors |
| **Dashboard** | SOC Streamlit UI | `frontend/dashboard.py` | Complete |
| **Paper Draft**| IEEE Academic Paper| `papers/aegis_paper.md` | Complete |
| **Citations** | BibTeX Database | `papers/references.bib` | Complete (20 citations) |
| **Governance** | Open Source Suite | `LICENSE`, `CONTRIBUTING.md`, etc. | Complete |
| **Presentation**| Slide Guide & Script | `plans/PRESENTATION_PPT_GUIDE.md` | Complete |
| **Viva Prep** | Defense Q&A | `plans/VIVA_DEFENSE_GUIDE.md` | Complete |

## 2. Pre-Presentation Sanity Steps

1. Run verification script:
   ```powershell
   .\scripts\run_all_evaluations.ps1
   ```
2. Start backend server:
   ```powershell
   uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```
3. Launch SOC dashboard:
   ```powershell
   streamlit run frontend/dashboard.py --server.port 8501
   ```
4. Verify browser access at `http://localhost:8501`.
