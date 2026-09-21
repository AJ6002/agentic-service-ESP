#!/usr/bin/env python3
"""
snapshot_builder.py
-------------------
Engineering Context Curator — Session Compressor + Canon Builder

Merges new session facts into an existing project_snapshot.md file,
preserving all unresolved issues, constraints, rejections, and incrementing
the version counter.

Usage:
    python snapshot_builder.py \\
        --session-facts session_facts.json \\
        --snapshot project_snapshot.md \\
        [--project-name "My Project"] \\
        [--objective "Deploy ML models to PLC runtime."] \\
        [--current-state "Downloader complete. Cache complete."] \\
        [--next-task "Design integration test suite."]

session_facts.json schema:
{
  "adrs": [
    {
      "id": "ADR-001",
      "title": "Use local disk cache with S3 as source of truth",
      "decision": "Store ML model packages in local disk cache on the PLC.",
      "reason": "PLC operates in offline environments.",
      "alternatives": [
        {"name": "Azure Blob Storage", "reason_rejected": "Requires network."},
        {"name": "Redis", "reason_rejected": "Requires network connection."}
      ],
      "status": "Accepted"
    }
  ],
  "constraints": [
    {
      "name": "ARM PLC Hardware",
      "limit": "Target runtime is ARM-based PLC architecture.",
      "type": "Hardware",
      "non_negotiable": true,
      "source": "Hardware specification",
      "impact": "x86-only binaries will not execute."
    }
  ],
  "rejected": [
    {
      "name": "Redis Cache",
      "considered_for": "ML model package storage",
      "why_rejected": "Requires persistent network connection.",
      "can_reconsider": "Conditional on cloud-only deployment."
    }
  ],
  "open_issues": [
    {
      "title": "Rollback Strategy",
      "question": "What is the rollback mechanism when a newly deployed model fails?",
      "status": "Unresolved",
      "impact": "Failed deployments have no recovery path.",
      "assigned_to": "Unassigned"
    }
  ],
  "risks": [
    {
      "name": "Large Package Download Latency",
      "description": "Large model packages may cause long download times.",
      "severity": "Medium",
      "likelihood": "High",
      "impact": "Deployment operations may time out.",
      "mitigation": "NONE",
      "status": "Open"
    }
  ],
  "standards": [
    {
      "name": "Use Real S3 in All Tests",
      "rule": "All tests must use a real S3 bucket.",
      "applies_to": "Testing | CI",
      "rationale": "Mocked S3 previously masked compatibility failures.",
      "exceptions": "NONE"
    }
  ]
}
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_version(snapshot_text: str) -> int:
    """Extract the current version number from the snapshot header."""
    match = re.search(r"#\s+PROJECT SNAPSHOT v(\d+)", snapshot_text)
    return int(match.group(1)) if match else 0


def extract_section(snapshot_text: str, section_name: str) -> str:
    """Extract the raw content of a named ## section from the snapshot."""
    pattern = rf"##\s+{re.escape(section_name)}\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, snapshot_text, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_open_issue_titles(snapshot_text: str) -> set:
    """Extract all Open Issue titles from the snapshot to avoid duplicates."""
    section = extract_section(snapshot_text, "Open Issues")
    titles = re.findall(r"###\s+Open Issue:\s+(.+)", section)
    return set(t.strip() for t in titles)


def extract_constraint_names(snapshot_text: str) -> set:
    """Extract constraint names to avoid duplicates."""
    section = extract_section(snapshot_text, "Constraints")
    names = re.findall(r"###\s+Constraint:\s+(.+)", section)
    return set(n.strip() for n in names)


def extract_rejected_names(snapshot_text: str) -> set:
    """Extract rejected solution names to avoid duplicates."""
    section = extract_section(snapshot_text, "Rejected Solutions")
    names = re.findall(r"###\s+Rejected:\s+(.+)", section)
    return set(n.strip() for n in names)


def extract_adr_ids(snapshot_text: str) -> set:
    """Extract ADR IDs to avoid duplicates."""
    ids = re.findall(r"###\s+(ADR-\d+):", snapshot_text)
    return set(ids)


def extract_risk_names(snapshot_text: str) -> set:
    """Extract risk names to avoid duplicates."""
    section = extract_section(snapshot_text, "Risks")
    names = re.findall(r"###\s+Risk:\s+(.+)", section)
    return set(n.strip() for n in names)


def extract_standard_names(snapshot_text: str) -> set:
    """Extract standard names to avoid duplicates."""
    section = extract_section(snapshot_text, "Validation Standards")
    names = re.findall(r"###\s+Standard:\s+(.+)", section)
    return set(n.strip() for n in names)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_adr(adr: dict) -> str:
    alts = adr.get("alternatives", [])
    if not alts:
        alts_text = "  - None recorded"
    else:
        alts_text = "\n".join(
            f"  - **{a['name']}** — {a.get('reason_rejected', 'No reason recorded')}"
            for a in alts
        )
    return (
        f"### {adr['id']}: {adr['title']}\n\n"
        f"**Decision:** {adr['decision']}\n"
        f"**Reason:** {adr['reason']}\n"
        f"**Alternatives Considered:**\n{alts_text}\n"
        f"**Status:** {adr['status']}\n"
    )


def render_constraint(c: dict) -> str:
    non_neg = "Yes" if c.get("non_negotiable", True) else "Conditional"
    return (
        f"### Constraint: {c['name']}\n\n"
        f"**Limit:** {c['limit']}\n"
        f"**Type:** {c.get('type', 'Other')}\n"
        f"**Non-negotiable:** {non_neg}\n"
        f"**Source:** {c.get('source', 'Not stated')}\n"
        f"**Impact:** {c.get('impact', 'Not stated')}\n"
    )


def render_rejected(r: dict) -> str:
    return (
        f"### Rejected: {r['name']}\n\n"
        f"**Considered For:** {r.get('considered_for', 'Not stated')}\n"
        f"**Why Rejected:** {r.get('why_rejected', 'Not stated — needs clarification.')}\n"
        f"**Can Reconsider:** {r.get('can_reconsider', 'Not stated')}\n"
    )


def render_open_issue(issue: dict) -> str:
    return (
        f"### Open Issue: {issue['title']}\n\n"
        f"**Full Question:** {issue['question']}\n"
        f"**Status:** {issue.get('status', 'Unresolved')}\n"
        f"**Impact of Leaving Unresolved:** {issue.get('impact', 'Not stated')}\n"
        f"**Assigned To:** {issue.get('assigned_to', 'Unassigned')}\n"
    )


def render_risk(risk: dict) -> str:
    return (
        f"### Risk: {risk['name']}\n\n"
        f"**Description:** {risk['description']}\n"
        f"**Severity:** {risk.get('severity', 'Unknown')}\n"
        f"**Likelihood:** {risk.get('likelihood', 'Unknown')}\n"
        f"**Impact:** {risk.get('impact', 'Not stated')}\n"
        f"**Mitigation:** {risk.get('mitigation', 'NONE')}\n"
        f"**Status:** {risk.get('status', 'Open')}\n"
    )


def render_standard(s: dict) -> str:
    return (
        f"### Standard: {s['name']}\n\n"
        f"**Rule:** {s['rule']}\n"
        f"**Applies To:** {s.get('applies_to', 'General')}\n"
        f"**Rationale:** {s.get('rationale', 'Not stated')}\n"
        f"**Exceptions:** {s.get('exceptions', 'NONE')}\n"
    )


def build_architecture_canon(adrs: list, standards: list) -> str:
    """
    Build a brief Architecture Canon summary from accepted ADRs and standards.
    This is the stable project truth that new sessions should load first.
    """
    accepted = [a for a in adrs if a.get("status") == "Accepted"]
    if not accepted and not standards:
        return "_No canon entries established yet._\n"

    lines = []
    if accepted:
        lines.append("**Accepted Architectural Decisions:**")
        for adr in accepted:
            lines.append(f"- **{adr['id']}:** {adr['decision']}")
    if standards:
        lines.append("\n**Engineering Standards:**")
        for s in standards:
            lines.append(f"- **{s['name']}:** {s['rule']}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Core merge logic
# ---------------------------------------------------------------------------

def merge_snapshot(
    existing_text: str,
    facts: dict,
    project_name: str,
    objective: str,
    current_state: str,
    next_task: str,
) -> str:
    """
    Merge new session facts into the existing snapshot, preserving all
    unresolved issues, constraints, rejections, and incrementing version.
    """
    version = parse_version(existing_text) + 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # --- Existing sets (dedup guard) ---
    existing_adr_ids    = extract_adr_ids(existing_text)
    existing_constraints = extract_constraint_names(existing_text)
    existing_rejected   = extract_rejected_names(existing_text)
    existing_issues     = extract_open_issue_titles(existing_text)
    existing_risks      = extract_risk_names(existing_text)
    existing_standards  = extract_standard_names(existing_text)

    # --- Existing section content (preserve what's already there) ---
    old_adrs        = extract_section(existing_text, "Decisions \\(ADRs\\)")
    old_constraints = extract_section(existing_text, "Constraints")
    old_rejected    = extract_section(existing_text, "Rejected Solutions")
    old_issues      = extract_section(existing_text, "Open Issues")
    old_risks       = extract_section(existing_text, "Risks")
    old_standards   = extract_section(existing_text, "Validation Standards")
    old_canon       = extract_section(existing_text, "Architecture Canon")

    # --- New records from this session ---
    new_adrs_text = ""
    all_adrs = facts.get("adrs", [])
    for adr in all_adrs:
        if adr["id"] not in existing_adr_ids:
            new_adrs_text += render_adr(adr) + "\n"

    new_constraints_text = ""
    for c in facts.get("constraints", []):
        if c["name"] not in existing_constraints:
            new_constraints_text += render_constraint(c) + "\n"

    new_rejected_text = ""
    for r in facts.get("rejected", []):
        if r["name"] not in existing_rejected:
            new_rejected_text += render_rejected(r) + "\n"

    new_issues_text = ""
    for issue in facts.get("open_issues", []):
        if issue["title"] not in existing_issues:
            new_issues_text += render_open_issue(issue) + "\n"

    new_risks_text = ""
    for risk in facts.get("risks", []):
        if risk["name"] not in existing_risks:
            new_risks_text += render_risk(risk) + "\n"

    new_standards_text = ""
    all_standards = facts.get("standards", [])
    for s in all_standards:
        if s["name"] not in existing_standards:
            new_standards_text += render_standard(s) + "\n"

    # --- Build canon from ALL adrs/standards (old + new session) ---
    new_canon = build_architecture_canon(all_adrs, all_standards)
    canon_section = new_canon if new_canon.strip() else (old_canon or "_No canon entries established yet._\n")

    # --- Assemble combined sections ---
    def combine(old: str, new: str) -> str:
        parts = [p for p in [old, new] if p.strip()]
        return "\n\n".join(parts) if parts else "_None recorded._"

    adrs_section        = combine(old_adrs, new_adrs_text)
    constraints_section = combine(old_constraints, new_constraints_text)
    rejected_section    = combine(old_rejected, new_rejected_text)
    issues_section      = combine(old_issues, new_issues_text)
    risks_section       = combine(old_risks, new_risks_text)
    standards_section   = combine(old_standards, new_standards_text)

    # --- Use existing values if CLI args are not provided ---
    if not objective:
        objective = extract_section(existing_text, "Objective") or "_Not set._"
    if not current_state:
        current_state = extract_section(existing_text, "Current State") or "_Not set._"
    if not next_task:
        next_task = extract_section(existing_text, "Next Task") or "_Not defined._"

    snapshot = f"""# PROJECT SNAPSHOT v{version}

> **Generated:** {timestamp}
> **Project:** {project_name}
> **Snapshot Purpose:** Session handoff — structured project truth for new agent sessions.

---

## Objective

{objective}

---

## Current State

{current_state}

---

## Architecture Canon

> Stable, accepted architectural truths. Load this before reading anything else.

{canon_section}

---

## Decisions (ADRs)

{adrs_section}

---

## Rejected Solutions

> These were considered and ruled out. Do not re-propose without reviewing reasons.

{rejected_section}

---

## Constraints

> Hard limits. Non-negotiable unless explicitly re-evaluated with stakeholder approval.

{constraints_section}

---

## Open Issues

> Unresolved design questions. These must remain visible until explicitly resolved.

{issues_section}

---

## Risks

{risks_section}

---

## Validation Standards

> Testing doctrine. These rules exist because of past failures. Follow them exactly.

{standards_section}

---

## Next Task

> Must be a single, concrete, executable step.

{next_task}
"""
    return snapshot


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Engineering Context Curator — Snapshot Builder"
    )
    parser.add_argument(
        "--session-facts", required=True,
        help="Path to JSON file containing new session facts."
    )
    parser.add_argument(
        "--snapshot", required=True,
        help="Path to the project_snapshot.md file (will be created or updated)."
    )
    parser.add_argument("--project-name", default="Unnamed Project")
    parser.add_argument("--objective", default="")
    parser.add_argument("--current-state", default="")
    parser.add_argument("--next-task", default="")
    args = parser.parse_args()

    # Load session facts
    facts_path = Path(args.session_facts)
    if not facts_path.exists():
        print(f"ERROR: session-facts file not found: {facts_path}", file=sys.stderr)
        sys.exit(1)

    with facts_path.open("r", encoding="utf-8") as f:
        facts = json.load(f)

    # Load existing snapshot (or start fresh)
    snapshot_path = Path(args.snapshot)
    existing_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""

    # Merge and write
    updated = merge_snapshot(
        existing_text=existing_text,
        facts=facts,
        project_name=args.project_name,
        objective=args.objective,
        current_state=args.current_state,
        next_task=args.next_task,
    )

    snapshot_path.write_text(updated, encoding="utf-8")
    version = re.search(r"# PROJECT SNAPSHOT v(\d+)", updated)
    v = version.group(1) if version else "?"
    print(f"✅ Snapshot written: {snapshot_path} (v{v})")


if __name__ == "__main__":
    main()
