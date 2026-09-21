---
name: pre-ci-check
description: Run full local pre-flight CI checks (Python pytest, TypeScript type-check, linter, build verification) before pushing to GitHub Actions.
---

# Pre-CI Verification Protocol

Run the full local verification suite before pushing to GitHub to ensure 100% green GitHub Actions CI.

## Verification Checklist:
1. **Python Backend Test Suite**:
   Run pytest -v chatbot/backend/ or pytest -v tests/ and ensure all tests pass.
2. **TypeScript / Frontend Build Check**:
   Run 
px tsc --noEmit and 
pm run build in rontend/.
3. **Linter & Formatting**:
   Verify no breaking syntax or lint errors.
4. **Git Status & Unstaged Artifacts**:
   Check git status to ensure only intended code changes are staged.
