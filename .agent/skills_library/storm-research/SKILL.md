---
name: storm-research
description: Use when someone asks to run Storm Research, use the storm-research skill, run the STORM method on a topic, says "storm research this" / "storm report on X" / "give me a STORM briefing on X", or wants a multi-perspective, citation-verified HTML research briefing on a topic. Runs a 4-phase pipeline: five expert lenses (Practitioner, Academic, Skeptic, Economist, Historian) -> contradiction map -> synthesized HTML report -> adversarial peer review + primary-source verification. Best for topics where multiple viewpoints and fact-checked claims matter; overkill for a simple factual lookup.
argument-hint: "[topic to research]"
---

# Storm Research (Antigravity Edition)

## What this does

Turns one topic into a verified, multi-perspective HTML briefing. It spawns five concurrent subagents, each simulating an expert lens on the topic, maps where they contradict each other, synthesizes everything into a single self-contained HTML report, then adversarially peer-reviews its own output and verifies every citation against its primary source before delivering. The output is one HTML file with no blind spots and no unchecked claims.

Run the full pipeline end to end. Do not shortcut a phase. This is heavier than a quick web lookup; that is the point.

## Portability

This skill is self-contained for Antigravity. It depends only on:
- Antigravity's native `invoke_subagent` tool for spawning concurrent research agents
- Antigravity's built-in web search/fetch tools (used inside each subagent)
- Antigravity's file write capability
- `report-template.html` in this same folder

No external scripts, APIs, paid services, or other skills are required. Drop the folder into `.agent/skills/` (project-level) or `~/.gemini/antigravity/skills/` (global) and it works.

## Runtime Note (Antigravity vs Claude)

The original Claude Code version of this skill used the `Agent` tool with `general-purpose` subagents spawned in a single message for true parallelism. Antigravity's equivalent is `invoke_subagent`, which spawns a concurrent session with a dedicated role and initial prompt per call [per Antigravity subagent docs].

- If your Antigravity runtime supports firing multiple `invoke_subagent` calls in the same turn, do that — this gives true concurrency, matching the original design intent.
- If your Antigravity runtime only allows one `invoke_subagent` call per turn, fall back to sequential invocation: call each of the five lenses one after another, collecting each result before invoking the next. The phases and output format stay identical either way — only the execution mechanics differ.
- Never simulate five lenses inside a single non-subagent response. Each lens must be a genuinely separate subagent invocation with its own isolated context and its own live web research, not a single pass pretending to be five perspectives. This is the entire point of the method: five independent research trails, not one trail wearing five hats.

## Phase 0: Scope the topic

1. If a topic was given in the invocation, use it. Otherwise ask what to research.
2. State your interpretation of the topic in one line and proceed. Only ask a clarifying question if the topic is genuinely ambiguous in a way that changes the research. Default to proceeding.
3. Identify the **reader's role** so the actionable section can target it. Infer it from the topic and any stated context; if unclear, ask in one line, or default to "a practitioner or decision-maker in this field."
4. Derive a kebab-case `topic-slug` from the topic for the filename.
5. Tell the user the pipeline is running (5 lenses, then verify). One line.

## Phase 1: Five expert lenses (subagents)

Invoke five subagents via `invoke_subagent` — concurrently if the runtime supports it in one turn, sequentially otherwise. Each gets the SAME topic framing plus its own lens. Use these exact prompts, substituting `{TOPIC}` and a one-line `{TOPIC_FRAME}` (your Phase 0 interpretation):

**1. THE PRACTITIONER** — `You are THE PRACTITIONER for: {TOPIC} ({TOPIC_FRAME}). You work with this daily. Do real web research (prioritize recent sources, case studies, practitioner threads, operator data). Surface the GAP between what hands-on operators know and what academics/pundits miss, and the practical realities (workflow friction, what actually works, where it breaks) that get ignored. Return EXACTLY: 1) CORE POSITION in 2 sentences. 2) STRONGEST EVIDENCE, 3-5 bullets each with a concrete data point/case/named source + URL. 3) THE ONE THING only a practitioner would say. Cite real sources with URLs. Under 400 words.`

**2. THE ACADEMIC** — `You are THE ACADEMIC for: {TOPIC} ({TOPIC_FRAME}). You care about peer-reviewed evidence and effect sizes, not anecdotes. Do real web research (peer-reviewed studies, arXiv, university and research-institute reports, journals). Answer: what does the rigorous evidence ACTUALLY say vs popular belief, and where does it CONTRADICT the hype. Return EXACTLY: 1) CORE POSITION in 2 sentences. 2) STRONGEST EVIDENCE, 3-5 bullets each tied to a named study/report + URL with the actual finding/effect size. 3) THE ONE THING only an academic would say. Flag where evidence is thin or contested, and note peer-review status (published vs preprint). Under 400 words.`

**3. THE SKEPTIC** — `You are THE SKEPTIC for: {TOPIC} ({TOPIC_FRAME}). You think the mainstream view is overstated or wrong. Build the STRONGEST steelman bear case. Do real web research for backlash, failures, contradicting data, policy/regulatory changes, debunkings. Answer: the strongest counterargument, and what proponents conveniently ignore. Return EXACTLY: 1) CORE POSITION in 2 sentences. 2) STRONGEST EVIDENCE, 3-5 bullets each with a concrete source + URL. 3) THE ONE THING only a skeptic would say. Be rigorous, not contrarian for sport. Cite real sources with URLs. Under 400 words.`

**4. THE ECONOMIST** — `You are THE ECONOMIST for: {TOPIC} ({TOPIC_FRAME}). You follow the money. Do real web research for revenues, valuations, market size, funding flows, unit economics, incentives. Answer: who profits from the current narrative, and what financial incentives shape the research and hype. Return EXACTLY: 1) CORE POSITION in 2 sentences. 2) STRONGEST EVIDENCE, 3-5 bullets each with a real number (revenue/valuation/market size/funding) + named source + URL. 3) THE ONE THING only an economist would say (the follow-the-money insight). Cite real figures with URLs. Under 400 words.`

**5. THE HISTORIAN** — `You are THE HISTORIAN for: {TOPIC} ({TOPIC_FRAME}). You have seen disruption cycles before and look for patterns. Do real web research for genuine historical parallels (prior technologies, manias, market shifts). Answer: what parallels actually fit, and what we learn from how they played out (who won, who lost, what stabilized). Return EXACTLY: 1) CORE POSITION in 2 sentences. 2) STRONGEST EVIDENCE, 3-5 bullets each a specific historical case with dates/outcomes + a source URL. 3) THE ONE THING only a historian would say (the pattern no one else surfaces). Cite sources with URLs. Under 400 words.`

When all five return, post a 2-3 line note in chat: which way they converge, and the sharpest disagreement. Keep raw briefs out of chat (the subagents already returned them internally — reference them, don't dump them).

## Phase 2: Map the contradictions

Working only from the five briefs, determine (do this inline, no subagents):

1. **Direct conflicts** — where two or more lenses claim opposite things. Name the specific clashing claims, not just topics.
2. **Strongest vs weakest evidence** — which lens is best-supported (rank: peer-reviewed causal > official data > anecdote/analogy) and which is weakest, with why.
3. **The resolving question** — the single empirical question that would settle the biggest contradiction.
4. **Universal agreement** — what every lens confirms, even opponents. This is the likely-true load-bearing finding.
5. **The blind spot** — what NO lens addressed. This becomes the "missing 6th lens" and feeds the Frontier Question.

This map is not a separate deliverable. It is the raw material for the report's findings (supports/challenges), hidden connection, 6th-lens box, and frontier question.

## Phase 3: Synthesize the HTML report

1. Read `report-template.html` in this skill folder. Clone it; do not rebuild the CSS.
2. Fill every section. Mapping from the phases:
   - **60-second summary** — decision-maker-grade, nuance not headline. Lead with the settled fact, then the contested interpretation.
   - **5 key findings, ranked by reliability** — most important things now known, highest reliability first. Each carries a 1-10 confidence score (set in Phase 4) and Supported-by / Challenged-by chips drawn from the contradiction map.
   - **Hidden connection** — the non-obvious link from Phase 2 that only appears across all five lenses.
   - **Key assumption / missing 6th lens** — the blind spot from Phase 2, framed as the lens that could change the conclusions.
   - **Actionable insight** — 3-6 specific moves for the reader's role identified in Phase 0. Specific, not abstract.
   - **Claim safety guide** — assert / caveat / avoid, populated after Phase 4 verification.
   - **Frontier question** — the one question that would change everything.
   - **References** — every citation with a verification-status tag (set in Phase 4).
3. Write to `storm-reports/{topic-slug}-briefing.html` (relative to the current workspace root; create the folder if needed).

## Phase 4: Adversarial peer review + verification (do not skip)

This is what separates Storm Research from a normal report. Run it before delivering.

**4a. Self-review (inline).** Score each of the 5 findings 1-10 for reliability and justify. Identify the weakest link and what would verify it. Run a bias check (which lens dominated the synthesis, what got underweighted). Name the missing 6th perspective. Assign an honest overall grade.

**4b. Primary-source verification.** For every citation in the report, verify the claim against the actual source (fetch the URL, confirm the claim matches what the source actually says — not just that the URL resolves). Tag each citation as VERIFIED, PARTIALLY SUPPORTED, or UNVERIFIED. If a claim cannot be verified, either remove it, soften it to match what's actually supported, or flag it explicitly in the Claim Safety Guide as "avoid asserting."

**4c. Final delivery.** Only after 4a and 4b are complete, present the finished HTML file path to the user along with the honest overall grade from 4a and a one-line note on the single weakest point in the report.

## Anti-Patterns to Actively Resist

- Do NOT fake the five lenses in a single response without genuine separate subagent research per lens.
- Do NOT skip Phase 4 verification because the report "looks complete."
- Do NOT present the report before the traceability/verification pass is done.
- Do NOT let one lens's framing bleed into another's brief before the contradiction map — keep each lens's research independent until Phase 2.