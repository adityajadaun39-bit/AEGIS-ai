# Contributing to AEGIS Gateway

Thank you for your interest in improving AEGIS, an information-flow security gateway for autonomous AI agents.

## Development Workflow

1. **Environment Setup:**
   Run the automated setup script for your platform:
   - Windows: `.\scripts\setup.ps1`
   - Linux/macOS: `bash scripts/setup.sh`

2. **Code Standards:**
   - Follow PEP 8 conventions.
   - Use type annotations for function signatures.
   - Ensure all public functions include brief docstrings explaining input/output types.

3. **Testing Requirements:**
   Before submitting changes, ensure all verification suites pass:
   ```bash
   python -m pytest tests/ -v
   python evaluation/run_evaluation.py
   ```

4. **Pull Request Protocol:**
   - Create focused branches: `feature/<name>` or `fix/<issue>`.
   - Ensure no credentials, API keys, or temporary database files (`*.db`) are committed.
