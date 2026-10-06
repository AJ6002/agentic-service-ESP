# The Hybrid Plan — Contract + Compute, Interleaved

Both views merged into one sequence. Each sprint delivers a piece of the output contract **and** the compute that fills it.

Rules:

- Every sprint names its **repo**.
- Every file is a **bracketed reference** — the IDE resolves it.
- Storage is named at every step.
- No time estimates.

---

## Sprint 0 — Freeze the Output Contract

**Repo: Agent (authoring), Shared (review)**

| # | Task | Ref |
| --- | --- | --- |
| 0.1 | Write the 7-step diagnostic contract as a document — the exact section names, field names, and order | (ref: diagnostic contract doc) |
| 0.2 | Define the JSON shape of `ranked_hypotheses` — with `rank`, `claim`, `signature_match`, `supporting_signals`, `contradicting_signals`, `confidence`, `confirmation_test`, `kb_citation` | (ref: diagnostic contract doc) |
| 0.3 | Define the JSON shape of `impact` — production delta, thermal margin, mechanical margin, escalation condition | (ref: diagnostic contract doc) |
| 0.4 | Define the JSON shape of `proof_overlay_chart` payload — channels, window, inflection timestamp, annotation, citation | (ref: diagnostic contract doc) |
| 0.5 | Review with the dashboard team — confirm the frame shapes are renderable | (ref: shared contract doc) |

**Exit:** one document that both teams agree is the target output.

**Storage:** version-controlled markdown. No runtime footprint.

---

## Sprint 1 — Contract Changes in Code

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 1.1 | Extend the advisory contract — replace flat `hypotheses` with structured `ranked_hypotheses` | (ref: advisory contract) |
| 1.2 | Add `impact` field to the advisory contract | (ref: advisory contract) |
| 1.3 | Add `proof_overlay_chart` to the card registry with its payload spec | (ref: card registry) |
| 1.4 | Add `trajectory`, `inflection_points`, `co_movement_events` fields to the evidence formatter output contract | (ref: evidence formatter contract) |

**Repo: Dashboard**

| # | Task | Ref |
| --- | --- | --- |
| 1.5 | Mirror the new advisory shape in the frontend frame types | (ref: frontend frame types) |
| 1.6 | Mirror the new card type in the frontend card registry reader | (ref: frontend card reader) |

**Exit:** both repos compile with the new shapes. Existing tests still pass with empty values for the new fields.

**Storage:**

- All new fields are per-query ephemeral — carried in the existing Advisory frame and Evidence Pack
- No new tables, no new Redis keys

---

## Sprint 2 — Trigger Surface (Step 1)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 2.1 | In the OP03 plan, ensure the events query and ML results query run first and their timestamps are captured | (ref: OP03 objective manifest) |
| 2.2 | Add a `trigger` section to the formatter output — the triggering event ID, timestamp, type, severity | (ref: evidence formatter) |
| 2.3 | Update the OP03 XAI prompt — lead the assessment with the trigger | (ref: OP03 narrator prompt) |
| 2.4 | Verify: a real trip produces a diagnosis whose first line names the trigger and its time | (ref: acceptance test) |
| 2.5 | Verify: no trigger present → clean refusal, no fabricated trigger | (ref: acceptance test) |

**Exit:** every OP03 output begins with the trigger.

**Storage:**

- Trigger data read from `events` and `ml_results` (existing tables)
- Stored inside the Evidence Pack as a new `trigger` field
- No new table

---

## Sprint 3 — Deterministic Layers (Steps 2 & 3)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 3.1 | Add a per-well baseline config — nominal values and tolerances per signal | (ref: baseline config folder) |
| 3.2 | Author baselines for the 13 canonical wells | (ref: baseline config folder) |
| 3.3 | Add trajectory compute — for each signal in the window, produce start, end, delta, percent, rate of change, duration | (ref: evidence formatter) |
| 3.4 | Add inflection detection — walk the window, find where each signal's slope changes beyond a threshold | (ref: evidence formatter) |
| 3.5 | Add co-movement detection — find moments where three or more signals inflect within a small window | (ref: evidence formatter) |
| 3.6 | Add threshold config — inflection sensitivity, co-movement tolerance, minimum signal count | (ref: diagnostic config) |
| 3.7 | Verify: a synthetic gas-lock window produces the correct inflection and co-movement | (ref: formatter test) |
| 3.8 | Verify: a stable window produces no inflection and no co-movement | (ref: formatter test) |

**Exit:** every OP03 output carries trajectory, inflection, and co-movement for all relevant signals.

**Storage:**

- Baselines and thresholds: agent repo config folder, version-controlled
- Computed fields: per query, inside the Evidence Pack
- No new tables

---

## Sprint 4 — Pattern Map + KB Match (Step 4)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 4.1 | Create the pattern → taxonomy map — signal signature patterns mapped to KB fault IDs | (ref: pattern taxonomy map) |
| 4.2 | Author an initial set — gas lock, underload pump-off, overload, mechanical binding, gas interference, sand ingestion, scale, thermal runaway | (ref: pattern taxonomy map) |
| 4.3 | Add a KB adapter tool — takes a detected pattern and returns the matching fault taxonomy entry | (ref: KB gateway adapter) |
| 4.4 | Register the tool in the tool registry | (ref: tool definitions) |
| 4.5 | Add it as optional evidence to OP03 | (ref: OP03 objective manifest) |
| 4.6 | Update the XAI prompt — name the pattern and cite the KB fault ID | (ref: OP03 narrator prompt) |
| 4.7 | Verify: a matched pattern returns the correct fault taxonomy entry | (ref: adapter test) |

**Exit:** every OP03 diagnosis names the pattern and cites the KB taxonomy entry.

**Storage:**

- Pattern map: agent repo config folder, version-controlled
- KB entries: read from `kb_chunks` at runtime
- Pattern match result: per query, inside Evidence Pack as a new evidence item

---

## Sprint 5 — Ranked Hypotheses + Confirmation Tests (Step 5 & Step 7)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 5.1 | Rewrite the OP03 narrator prompt to produce `ranked_hypotheses` — each with claim, supporting signals, contradicting signals, confidence, confirmation test, KB citation | (ref: OP03 narrator prompt) |
| 5.2 | Add per-hypothesis confirmation tests drawn from the KB — specific, time-bounded, threshold-based | (ref: OP03 narrator prompt) |
| 5.3 | Add a section for "Next Diagnostic Actions" — what to check next, what's missing | (ref: OP03 narrator prompt) |
| 5.4 | Add a post-check — each hypothesis must have a confirmation test or be rejected | (ref: citation check extension) |
| 5.5 | Verify: OP03 produces ranked hypotheses with tests | (ref: acceptance test) |
| 5.6 | Verify: contradicted hypotheses are stated as contradicted, not silently dropped | (ref: acceptance test) |

**Exit:** every OP03 output has ranked hypotheses with confirmation tests and next actions.

**Storage:**

- All output: standard Advisory frame, per query
- Confirmation tests are text — no separate storage

---

## Sprint 6 — Impact Compute (Step 6)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 6.1 | Add an impact config — thermal limits, vibration limits, escalation thresholds, production baseline per well | (ref: impact config folder) |
| 6.2 | Author impact configs for the 13 wells | (ref: impact config folder) |
| 6.3 | Add impact compute — production loss, thermal margin, mechanical margin, escalation condition | (ref: evidence formatter) |
| 6.4 | Add the `impact` section to the OP03 XAI prompt | (ref: OP03 narrator prompt) |
| 6.5 | Verify: a real trip produces an impact section with the correct production delta and thermal margin | (ref: acceptance test) |
| 6.6 | Verify: a safe well produces "no escalation risk" | (ref: acceptance test) |

**Exit:** every OP03 output carries the impact section.

**Storage:**

- Impact thresholds: agent repo config folder, version-controlled
- Computed impact: per query, inside Evidence Pack
- No new table

---

## Sprint 7 — Proof Chart Card (Step 8)

**Repo: Agent**

| # | Task | Ref |
| --- | --- | --- |
| 7.1 | Define the `proof_overlay_chart` payload — channels, window, inflection timestamps, annotation, citation, evidence IDs | (ref: card contract) |
| 7.2 | Register the card type in the card registry | (ref: card registry) |
| 7.3 | Add it to OP03's `allowed_visuals` and `default_visuals` | (ref: OP03 objective manifest) |
| 7.4 | Update the visualization planner — select the proof chart when an inflection moment exists with co-movement | (ref: visualization planner) |
| 7.5 | Verify: a successful OP03 run emits the card with correct inflection timestamp | (ref: planner test) |
| 7.6 | Verify: no inflection → card omitted, not broken | (ref: planner test) |

**Exit:** every OP03 diagnosis with an inflection moment carries a proof chart spec.

**Storage:**

- Card payload: per query, in the visual frame
- Chart data is not inlined — dashboard fetches from the existing Evidence Pack
- No new storage

---

## Sprint 8 — Dashboard Rendering (Step 8 continued)

**Repo: Dashboard**

| # | Task | Ref |
| --- | --- | --- |
| 8.1 | Build a new chart component — multi-channel overlay with shaded anomaly window and annotated inflection marker | (ref: frontend chart component) |
| 8.2 | Register the component in the card renderer | (ref: frontend card renderer) |
| 8.3 | Fetch chart data from the Evidence Pack reference in the card payload | (ref: frontend API client) |
| 8.4 | Render the KB citation inline under the chart | (ref: frontend chart component) |
| 8.5 | Verify: given a real payload, the chart renders correctly | (ref: manual test) |
| 8.6 | Verify: on missing data, the card hides rather than rendering empty | (ref: manual test) |

**Exit:** the dashboard renders the proof chart for every OP03 query.

**Storage:**

- Chart data fetched from Redis (existing Evidence Pack)
- Chart not persisted — browser only

---

## Sprint 9 — Integration & Seal

**Repo: Both**

| # | Task | Ref |
| --- | --- | --- |
| 9.1 | Fire "Why did FS-17 trip?" — verify all 7 sections appear | (ref: browser) |
| 9.2 | Verify: trigger, deviation, point analysis, signature, ranking, impact, next actions all present | (ref: browser) |
| 9.3 | Verify: proof chart renders with correct inflection marker | (ref: browser) |
| 9.4 | Fire "Why did FS-17 trip?" with no events in window | (ref: browser) |
| 9.5 | Verify: clean refusal, no fabricated sections, no chart | (ref: browser) |
| 9.6 | Fire "How healthy is FS-17?" — verify OP04 unaffected | (ref: browser) |
| 9.7 | Fire "What is gas lock?" — verify OP06 unaffected | (ref: browser) |
| 9.8 | Run the full regression suite | (ref: test suite) |
| 9.9 | File the seal report | (ref: report file) |

**Exit:** OP03 upgraded, no regressions, report filed.

**Storage:**

- Every run writes to the standard Evidence Pack + audit sink
- Seal report stored in agent repo reports folder

---

## Dependency Map

```
Sprint 0 (contract)
    │
    ▼
Sprint 1 (code contracts)
    │
    ├──► Sprint 2 (trigger)      ← Step 1 done here
    │
    ├──► Sprint 3 (compute)      ← Steps 2 & 3 done here
    │         │
    │         └──► Sprint 4 (pattern match)  ← Step 4
    │                   │
    │                   └──► Sprint 5 (ranking)  ← Steps 5 & 7
    │                             │
    │                             └──► Sprint 6 (impact)  ← Step 6
    │                                       │
    │                                       └──► Sprint 7 (chart card)  ← Step 8a
    │                                                 │
    │                                                 └──► Sprint 9 (integration)
    │
    └──► Sprint 8 (dashboard render)  ← can start after Sprint 1
              │
              └──► Sprint 9
```

**Critical path:** 0 → 1 → 3 → 4 → 5 → 6 → 7 → 9

**Parallel:** Sprint 2 can run in parallel with Sprint 3. Sprint 8 can run in parallel with anything after Sprint 1.

---

## Repo Distribution

| Sprint | Agent | Dashboard |
| --- | --- | --- |
| 0 | ✅ authoring | ✅ review |
| 1 | ✅ primary | ✅ mirror |
| 2 | ✅ primary | — |
| 3 | ✅ primary | — |
| 4 | ✅ primary | — |
| 5 | ✅ primary | — |
| 6 | ✅ primary | — |
| 7 | ✅ primary | — |
| 8 | — | ✅ primary |
| 9 | ✅ verify | ✅ verify |

---

## Storage Summary — Every New Data Type

| Data | Source | Storage | Lifecycle |
| --- | --- | --- | --- |
| Diagnostic contract doc | Hand-authored | Agent repo docs | Version-controlled |
| Baseline values per well | Hand-authored | Agent repo config | Version-controlled |
| Pattern → taxonomy map | Hand-authored | Agent repo config | Version-controlled |
| Impact thresholds | Hand-authored | Agent repo config | Version-controlled |
| Trigger event | `events`, `ml_results` | Existing tables | Persistent |
| Trajectory / inflection / co-movement | Computed per query | Evidence Pack | 24h TTL |
| KB fault taxonomy entry | `kb_chunks` | Postgres | Persistent |
| Ranked hypotheses | XAI output | Advisory frame | Per query |
| Confirmation tests | XAI output | Advisory frame | Per query |
| Impact compute | Computed per query | Evidence Pack | 24h TTL |
| Proof chart payload | Planner output | Visual frame | Per query |
| Chart time series | Evidence Pack | Redis (existing) | 24h TTL |
| Rendered chart | Dashboard | Browser only | Ephemeral |
| Audit trail | Every stage | Existing sink | Permanent |

**Three new config files. Three new Evidence Pack fields. One new card type. Zero new tables. Zero new services.**

---

## What This Changes About OP03

| Aspect | Before | After |
| --- | --- | --- |
| Output shape | Assessment + flat hypotheses + recommendation | 7-section structured contract |
| Evidence used | Current values + events + ML | Trajectory + inflection + co-movement + pattern + KB taxonomy |
| Hypotheses | Flat list | Ranked with evidence, tests, citations |
| Impact | Not computed | Production, thermal, mechanical |
| Visual | Generic trend card | Proof overlay chart with annotated inflection |
| Explainability | "Here's what" | "Here's what, when, why, and how to confirm" |

Same pipeline. Same adapters. Same Evidence Pack structure. Richer fields, richer output.

---

## The One-Line Answer

**Hybrid plan: nine sprints. Sprint 0 freezes the 7-step output contract as a document. Sprints 1–8 build toward it — contract changes, trigger detection, deterministic compute layers, pattern matching, ranked hypotheses, impact compute, proof chart card, dashboard rendering. Sprint 9 integrates and seals. Three new config files (baselines, patterns, impact thresholds). Three new Evidence Pack fields (trajectory, inflection, co-movement). One new card type. Zero new tables. Agent owns all compute and content sprints; dashboard owns the chart component. No time estimates, no hardcoded paths — every file is a bracketed reference the IDE resolves.**
