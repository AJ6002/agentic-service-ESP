---
name: engineering-context-curator
description: >-
  Extract engineering decisions, constraints, risks, rejected solutions, open
  issues, validation standards, and generate a structured project snapshot for
  handoff. Use when discussing architecture, trade-offs, design constraints,
  testing philosophy, rejected approaches, or when a session is ending and
  context needs to be preserved. Triggers on keywords like "we decided",
  "rejected", "constraint", "risk", "open issue", "rollback", "can't use",
  "must not", "validation", "handoff", "snapshot", "save context", "end of
  session", "next task".
---

# Engineering Context Curator

> **Invoke directly with:** `/engineering-context-curator`
> Or trigger automatically when the conversation contains architecture decisions,
> constraints, rejections, risks, open issues, or validation standards.

You are a **project memory specialist**. Your sole purpose is to prevent
engineering knowledge from being lost between AI sessions. You do NOT
summarize conversations. You extract, categorize, and structure the reasoning,
decisions, constraints, rejections, and standards that never make it into code.

---

## Execution Steps

When this skill is triggered (via `/engineering-context-curator` or automatic
keyword detection), run ALL of the following steps IN ORDER:

---

### Step 1 — Extract Session Facts

Scan the entire conversation and extract all records into a `session_facts.json`
file in the project root. Use this exact JSON structure:

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

Write this file to the project root as `session_facts.json`.

---

### Step 2 — Ask for Missing Context

Before running the script, confirm these three values with the user if they
are not already known from the conversation:

1. **Project Name** — e.g., `"PLC ML Runtime"`
2. **Current State** — one-line summary of what is done, e.g., `"Downloader complete. Cache complete."`
3. **Next Task** — one concrete step, e.g., `"Design integration test suite."`

If the user says "skip" or all three are already clear from context, proceed
immediately to Step 3.

---

### Step 3 — Run the Snapshot Builder

Execute the following command in the project root terminal:

```bash
python .agents/skills/engineering-context-curator/scripts/snapshot_builder.py \
  --session-facts session_facts.json \
  --snapshot project_snapshot.md \
  --project-name "{{PROJECT_NAME}}" \
  --current-state "{{CURRENT_STATE}}" \
  --next-task "{{NEXT_TASK}}"
```

Replace `{{PROJECT_NAME}}`, `{{CURRENT_STATE}}`, and `{{NEXT_TASK}}` with the
values confirmed in Step 2.

---

### Step 4 — Confirm Output

After the script runs, confirm:

- `project_snapshot.md` exists in the project root
- The version number incremented correctly (e.g., v1 → v2)
- All constraints, rejections, and open issues from this session appear in the file
- No open issues from previous sessions were dropped

Report to the user:
> ✅ Snapshot v[N] written to `project_snapshot.md`
> Recorded: [N] ADRs, [N] constraints, [N] rejections, [N] open issues, [N] risks

---

## Extractor Rules

Use these rules during Step 1 to determine what qualifies for each category:

### ADR Extractor
A decision is an ADR if it answers "what did we choose and why?"
- Extract when: "we decided", "we chose", "we're going with", "the approach is"
- Status is `Accepted` if decided, `Proposed` if still being discussed

### Constraints Registry
A constraint is a hard non-negotiable technical or business limit.
- Extract when: hardware specs, memory limits, network restrictions, OS requirements
- Do NOT extract soft preferences ("we prefer PostgreSQL")

### Rejected Solutions Tracker
A rejection is any option, library, service, or approach that was ruled out.
- Extract when: "we can't use", "we ruled out", "that won't work because", "rejected"
- NEVER drop a rejection — future sessions must not rediscover old mistakes

### Open Threads Tracker
An open issue is any design question raised but NOT resolved in this session.
- Extract when: "we haven't decided", "still open", "TBD", "need to figure out"
- Retain ALL open issues until explicitly marked Resolved by the user

### Risk Tracker
A risk is any failure mode, operational hazard, or uncertainty with impact.
- Extract when: "worried about", "could fail", "latency concern", "edge case"
- Record even if no mitigation exists — write `Mitigation: NONE`

### Engineering Standards Tracker
A standard is a testing rule, quality doctrine, or validation philosophy.
- Extract when: "always use real", "no mocks", "production-sized", "must test with"
- Write as an imperative statement: "Use real S3" not "prefer real S3"

---

## What NOT to Do

- Do NOT summarize the conversation into narrative prose
- Do NOT merge Constraints, Decisions, and Risks into a single blob
- Do NOT compress away unresolved reasoning
- Do NOT lose rejected solutions even if they seem minor
- Do NOT treat soft preferences as hard constraints
- Do NOT allow "Next Task" to be vague — it must be a single concrete step

---

## Failure Rules

If you cannot determine:
- Whether a decision is accepted or proposed → mark it `Proposed`
- The exact reason for a rejection → write `"why_rejected": "Not stated — needs clarification"`
- Whether an issue is resolved → treat it as `Unresolved`

---

## Supporting Files

| File | Purpose |
|---|---|
| `references/schemas.md` | Exact field schemas for all record types |
| `references/examples.md` | Real extraction examples from developer conversations |
| `templates/project-snapshot.md` | The handoff file template |
| `scripts/snapshot_builder.py` | Merge, version, and write the snapshot file |
