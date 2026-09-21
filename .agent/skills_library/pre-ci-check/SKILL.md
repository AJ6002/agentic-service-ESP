---
name: pre-ci-check
description: Run full local pre-flight CI checks (Python pytest, TypeScript type-check, linter, build verification) before pushing to GitHub Actions.
---

# Pre-CI Verification Skill

Run this skill before pushing code to GitHub to ensure 100% green CI runs on GitHub Actions.

## Steps:
1. **Backend Verification (Python):**
   - Run active pytest test suite:
     pytest -q
   - Verify no syntax errors or breaking imports across the 22-node LangGraph pipeline.

2. **Frontend Verification (React / TypeScript):**
   - Run TypeScript type-checking:
     cd frontend && npm run build (or 
px tsc --noEmit)
   - Verify no broken JSX/TS types or unresolved module imports.

3. **Git Cleanliness Check:**
   - Run git status to ensure no temporary test residue, logs, or unignored files are staged.
   - Ensure clean diff tracing only to the user's requested changes.

4. **Report Result:**
   - If green: Confirm safe to push (git push origin <branch>).
   - If red: Isolate the exact failing line, fix it locally, and re-run.
