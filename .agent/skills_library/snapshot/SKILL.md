---
name: snapshot
description: >-
  Runs the full engineering context curator pipeline. Extracts all decisions,
  constraints, rejected solutions, open issues, risks, and validation standards
  from the current session, writes them to session_facts.json, then executes
  snapshot_builder.py to produce or update project_snapshot.md. Use when the
  session is ending, a milestone is reached, or the user says "snapshot",
  "save context", "generate handoff", "write snapshot", "end of session".
---

# Snapshot

Runs the full engineering context curator pipeline and writes `project_snapshot.md`.

> **Trigger:** `/snapshot`

---

## What This Skill Does

1. Extracts all engineering facts from the current conversation
2. Writes them to `session_facts.json`
3. Runs `snapshot_builder.py` to merge with any existing snapshot
4. Produces an updated, versioned `project_snapshot.md` in the project root

---

## Step 1 — Extract All Session Facts

Scan the entire conversation. For every item that qualifies, add it to the
corresponding array in `session_facts.json`. Write this file to the project root.

```json
{
  "adrs": [
    {
      "id": "ADR-001",
      "title": "Short decision title",
      "decision": "What was decided — one sentence.",
      "reason": "Why this choice was made.",
      "alternatives": [
        { "name": "Option A", "reason_rejected": "Why it was ruled out." }
      ],
      "status": "Accepted"
    }
  ],
  "constraints": [
    {
      "name": "Constraint Name",
      "limit": "The exact hard limit.",
      "type": "Hardware | Memory | Network | Platform | Regulatory | Other",
      "non_negotiable": true,
      "source": "Where this comes from.",
      "impact": "What breaks if violated."
    }
  ],
  "rejected": [
    {
      "name": "Rejected Option Name",
      "considered_for": "What problem it was evaluated for.",
      "why_rejected": "Exact reason it was ruled out.",
      "can_reconsider": "Yes | No | Conditional on [X]"
    }
  ],
  "open_issues": [
    {
      "title": "Short issue title",
      "question": "The full unresolved design question.",
      "status": "Unresolved",
      "impact": "What breaks if this stays unresolved.",
      "assigned_to": "Unassigned"
    }
  ],
  "risks": [
    {
      "name": "Risk Name",
      "description": "What could go wrong.",
      "severity": "High | Medium | Low",
      "likelihood": "High | Medium | Low",
      "impact": "What degrades or breaks.",
      "mitigation": "Current plan or NONE",
      "status": "Open"
    }
  ],
  "standards": [
    {
      "name": "Standard Name",
      "rule": "The exact rule as an imperative statement.",
      "applies_to": "Testing | CI | Code Review | Deployment | Other",
      "rationale": "Why this standard exists.",
      "exceptions": "NONE"
    }
  ]
}
```

If a category has no items extracted from this session, write it as an empty
array `[]`. Do NOT omit the key.

---

## Step 2 — Confirm Three Values

Ask the user for the following if not already clear from context:

| Field | Example |
|---|---|
| **Project Name** | `"PLC ML Runtime"` |
| **Current State** | `"Downloader complete. Cache complete."` |
| **Next Task** | `"Design integration test suite."` |

If the user says "skip" or all three are obvious from context, proceed immediately.

---

## Step 3 — Run Snapshot Builder

Execute this command in the project root:

```bash
python .agents/skills/engineering-context-curator/scripts/snapshot_builder.py \
  --session-facts session_facts.json \
  --snapshot project_snapshot.md \
  --project-name "{{PROJECT_NAME}}" \
  --current-state "{{CURRENT_STATE}}" \
  --next-task "{{NEXT_TASK}}"
```

Replace `{{PROJECT_NAME}}`, `{{CURRENT_STATE}}`, and `{{NEXT_TASK}}` with the
values from Step 2.

---

## Step 4 — Report Result

After the script completes, report:

```
✅ Snapshot v[N] written → project_snapshot.md

Recorded this session:
  ADRs          : [N]
  Constraints   : [N]
  Rejected      : [N]
  Open Issues   : [N]
  Risks         : [N]
  Standards     : [N]
```

If `project_snapshot.md` already existed, confirm that no previous open issues
or constraints were dropped.

---

## Extraction Rules (Quick Reference)

| Category | Extract when you see |
|---|---|
| **ADR** | "we decided", "we chose", "going with", "the approach is" |
| **Constraint** | hardware specs, memory limits, network restrictions — hard limits only |
| **Rejected** | "can't use", "ruled out", "won't work because", "rejected" |
| **Open Issue** | "haven't decided", "still open", "TBD", "need to figure out" |
| **Risk** | "worried about", "could fail", "latency concern", "edge case" |
| **Standard** | "always use real", "no mocks", "must test with", "production-sized" |

---

## Failure Rules

- Cannot determine if decision is accepted → mark `"status": "Proposed"`
- Rejection reason not stated → write `"why_rejected": "Not stated — needs clarification"`
- Issue resolution unclear → treat as `"status": "Unresolved"`
- Do NOT write vague Next Task — must be one concrete executable step
