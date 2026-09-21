---
name: curator
description: >-
  Lists all recorded engineering decisions (ADRs), constraints, rejected
  solutions, open issues, risks, and validation standards extracted from the
  current session. Read-only — does NOT write any files. Use when the user
  wants to review what has been captured so far, verify the current project
  knowledge state, or audit facts before generating a snapshot. Triggers on
  "show decisions", "list constraints", "what have we rejected", "show open
  issues", "what do we know", "curator", "review context", "audit facts".
---

# Curator

Lists all engineering facts recorded in the current session. **Read-only —
no files are written.**

> **Trigger:** `/curator`

---

## What This Skill Does

Scans the current conversation and displays a structured read-only report of
all captured engineering knowledge. This is a review tool — use it to verify
what has been extracted before running `/snapshot`.

---

## Step 1 — Scan and Categorize

Scan the entire conversation and identify all items belonging to each category
using the rules below. Do NOT write any files.

| Category | Extract when you see |
|---|---|
| **ADR** | "we decided", "we chose", "going with", "the approach is" |
| **Constraint** | hardware specs, memory limits, network restrictions — hard limits only |
| **Rejected** | "can't use", "ruled out", "won't work because", "rejected" |
| **Open Issue** | "haven't decided", "still open", "TBD", "need to figure out" |
| **Risk** | "worried about", "could fail", "latency concern", "edge case" |
| **Standard** | "always use real", "no mocks", "must test with", "production-sized" |

---

## Step 2 — Display the Curator Report

Output the following structured report in the chat. Do NOT write to any file.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗂  CURATOR REPORT — Current Session
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 DECISIONS (ADRs)
────────────────────
[For each ADR:]
• ADR-[N]: [Title]
  Decision   : [What was decided]
  Reason     : [Why]
  Alternatives: [Options that were ruled out]
  Status     : Accepted | Proposed

[If none found:]
  — None recorded this session.

🔒 CONSTRAINTS
────────────────────
[For each constraint:]
• [Name] ([Type])
  Limit  : [The hard limit]
  Impact : [What breaks if violated]

[If none found:]
  — None recorded this session.

🚫 REJECTED SOLUTIONS
────────────────────
[For each rejection:]
• [Name]
  For    : [What it was considered for]
  Reason : [Why it was rejected]
  Reconsider? [Yes / No / Conditional on X]

[If none found:]
  — None recorded this session.

❓ OPEN ISSUES
────────────────────
[For each open issue:]
• [Title]
  Question : [Full unresolved question]
  Impact   : [What breaks if unresolved]
  Assigned : [Who / Unassigned]
  Status   : Unresolved

[If none found:]
  — None recorded this session.

⚠️  RISKS
────────────────────
[For each risk:]
• [Name] — Severity: [High|Medium|Low]
  Description : [What could go wrong]
  Impact      : [What degrades]
  Mitigation  : [Plan or NONE]
  Status      : [Open|Mitigated|Accepted]

[If none found:]
  — None recorded this session.

📐 VALIDATION STANDARDS
────────────────────
[For each standard:]
• [Name]
  Rule    : [Imperative statement]
  Applies : [Testing | CI | Code Review | etc.]
  Reason  : [Why this standard exists]

[If none found:]
  — None recorded this session.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: [N] ADRs · [N] Constraints · [N] Rejected
         [N] Open Issues · [N] Risks · [N] Standards

Run /snapshot to write project_snapshot.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 3 — Prompt Next Action

After displaying the report, ask:

> Is anything missing or incorrectly categorized? You can correct it here before
> running `/snapshot` to write the file.

---

## Rules

- This skill is **read-only**. It never writes `session_facts.json` or
  `project_snapshot.md`.
- If an item is ambiguous, show it under the most likely category and flag it
  with `⚠️ Unconfirmed` so the user can verify.
- If `project_snapshot.md` already exists in the project root, prepend the
  report with the current snapshot version so the user knows what is already
  saved:

```
📄 Existing snapshot: project_snapshot.md (v[N] — last updated [date])
   New facts extracted this session will be ADDED to the existing snapshot
   when you run /snapshot.
```
