# Record Schemas

This file defines the exact field schemas for all record types produced by the
`engineering-context-curator` skill. These schemas are the enforcement contract.
Deviate from them and the snapshot becomes unstructured prose — which defeats
the entire purpose.

---

## ADR (Architecture Decision Record)

```markdown
## ADR-[N]: [Short Decision Title]

**Decision:** [What was decided — one sentence]
**Reason:** [Why this choice was made — key rationale only]
**Alternatives Considered:**
  - [Option A] — [Why rejected]
  - [Option B] — [Why rejected]
**Status:** Proposed | Accepted | Deprecated
**Session:** [Conversation context or date]
```

### Rules
- `Decision` must be a single declarative sentence.
- `Reason` must explain WHY, not WHAT.
- `Alternatives Considered` must list at least one item. If none were discussed,
  write `None recorded`.
- `Status` must be exactly one of: `Proposed`, `Accepted`, `Deprecated`.
- ADRs are never deleted. Deprecated ADRs remain visible with their status updated.

---

## Constraint

```markdown
## Constraint: [Constraint Name]

**Limit:** [What is constrained — e.g., "Maximum 256MB RAM"]
**Type:** Hardware | Memory | Network | Platform | Regulatory | Security | Other
**Non-negotiable:** Yes | Conditional
**Source:** [Where this constraint comes from — hardware spec, client requirement, etc.]
**Impact:** [What breaks or fails if this constraint is violated]
```

### Rules
- Only hard technical or business limits qualify as constraints.
- Soft preferences (e.g., "prefer PostgreSQL") are NOT constraints.
- `Non-negotiable: Yes` means this constraint cannot be relaxed under any circumstances.
- `Non-negotiable: Conditional` means it can be relaxed only with explicit approval and
  must document the condition.

---

## Rejected Solution

```markdown
## Rejected: [Name of Rejected Option]

**Considered For:** [What problem or need this was evaluated for]
**Why Rejected:** [Exact reason — not "it didn't fit" but the specific technical/
  operational/business reason]
**Session:** [When this rejection was made]
**Can Reconsider:** Yes | No | Conditional on [specific change]
```

### Rules
- Every rejection must have a `Why Rejected` entry. Never leave it blank.
- If the reason was not explicitly stated, write:
  `Why Rejected: Not explicitly stated — needs clarification before closing.`
- `Can Reconsider: No` means this is permanently ruled out.
- `Can Reconsider: Conditional on [X]` means it would be viable if [X] changes.
  Example: `Can Reconsider: Conditional on moving to cloud-only deployment.`

---

## Open Design Question

```markdown
## Open Issue: [Short Description]

**Full Question:** [The complete unresolved design question]
**Status:** Unresolved | In Progress | Blocked On [dependency]
**Impact of Leaving Unresolved:** [What fails or is risky if this is not resolved]
**Raised In:** [Session context or date]
**Assigned To:** [Agent | Human | Unassigned]
```

### Rules
- Open issues are NEVER removed until `Status` is explicitly changed to `Resolved`.
- When resolved, change status and add a `Resolution:` field — do not delete the record.
- `Impact of Leaving Unresolved` is mandatory. This prevents issues from being deprioritized
  without understanding the consequence.

---

## Risk

```markdown
## Risk: [Risk Name]

**Description:** [What could go wrong]
**Severity:** High | Medium | Low
**Likelihood:** High | Medium | Low
**Impact:** [What breaks or degrades if this risk materializes]
**Mitigation:** [Current plan to avoid or reduce impact, or NONE if unmitigated]
**Status:** Open | Mitigated | Accepted | Resolved
```

### Rules
- `Severity` reflects the impact magnitude if it occurs.
- `Likelihood` reflects how probable it is.
- `Mitigation: NONE` is valid and should be recorded honestly.
- `Status: Accepted` means the team is aware and has chosen to tolerate the risk.

---

## Engineering Standard

```markdown
## Standard: [Standard Name]

**Rule:** [The exact rule or doctrine — stated as an imperative]
**Applies To:** Testing | CI | Code Review | Deployment | Architecture | Other
**Rationale:** [Why this standard exists — what failure mode it prevents]
**Exceptions:** [Any known exceptions, or NONE]
```

### Rules
- Rules must be imperative statements: "Use real S3", not "prefer real S3".
- `Rationale` must explain the failure mode the standard prevents.
- `Exceptions: NONE` is acceptable and preferred over leaving it blank.

---

## Architecture Canon Entry

```markdown
## Canon: [Topic Name]

**Summary:** [One-paragraph description of the stable architectural truth]
**Supporting ADRs:** [List of ADR-[N] IDs that established this canon]
**Supporting Standards:** [List of Standard names that enforce this canon]
**Last Updated:** [Session or date]
```

### Rules
- Canon entries are written by the Architecture Canon Builder only after ADRs are
  in `Accepted` status.
- Canon entries are updated — not replaced — when new ADRs extend them.
- A canon entry that conflicts with an accepted ADR must be flagged immediately.
