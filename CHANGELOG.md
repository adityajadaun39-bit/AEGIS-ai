# Changelog

All notable changes to the AEGIS Gateway project are documented in this file.

## [1.0.0] - 2026-11-18

### Added
- Dual-lattice information flow control engine (`ifc_lattice.py`) implementing Denning confidentiality and Biba integrity models.
- Two-tier threat detection pipeline (`ml_detector.py`) combining fast regex heuristics with ONNX sequence classification.
- High-entropy Data Loss Prevention scanner (`dlp_engine.py`) for API tokens, secret keys, and credentials.
- In-process declarative policy evaluation fallback in `policy_engine.py`.
- Modern SOC Console dashboard (`frontend/dashboard.py`) with lineage graphs and approval desk.
- Automated evaluation suite with 10 benchmark scenarios (`evaluation/run_evaluation.py`).
- High-concurrency load testing harness (`evaluation/run_load_test.py`) with SQLite WAL validation.
- PEP 517/621 packaging (`pyproject.toml`) and deterministic lockfile (`requirements.lock`).
- Cross-platform setup scripts (`scripts/setup.ps1`, `scripts/setup.sh`).
- Research paper draft (`papers/aegis_paper.md`) and citation database (`papers/references.bib`).

### Fixed
- Replaced hardcoded author paths with dynamic workspace resolution.
- Resolved policy evaluation mocking for headless test environments.
- Corrected database session initialization in approval stores.
