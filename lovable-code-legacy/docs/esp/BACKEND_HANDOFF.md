# ESP-PMM — Backend Handoff (Engineering Asset Definition)

Status: **front-end mockup / domain contract only.** No backend code, database or
integration is implemented yet. This document is the implementation brief for a later
Codex build using Java and/or Python services on PostgreSQL + TimescaleDB.

Source contracts to generate from:
`src/domain/esp/asset-definition.ts`, `src/domain/esp/tag-dictionary.ts`,
`src/domain/esp/validation.ts`, demo data in `src/data/esp/asset-definitions.ts`.

---

## 1. System-of-record boundaries (binding)

- **ADVAIT Asset ConneX owns** the generic asset hierarchy, asset templates/classes and
  master asset identity. ESP-PMM **references** `assetId` / `parentAssetId` and never
  re-masters, renames or re-parents assets locally.
- **ADVAIT OTConnex owns and acquires** live and historical OT time series, connections,
  protocol drivers and historian storage. ESP-PMM holds only canonical signal definitions
  and per-well mappings.
- **ESP-PMM owns** ESP-specific engineering definitions, OEM curve sets, design cases,
  operating envelopes, calculation and surveillance configuration, reliability/lifecycle
  context, and all domain-derived results (TDH, operating point, GVF, health index,
  exceptions, deferment, readiness).
- **Raw historian time-series data must not be duplicated into asset-definition relational
  tables.** Definition tables store mappings, thresholds and dated engineering
  observations (well tests) only; series reads go to OTConnex/Timescale at query time.
- **Approved definitions are immutable.** Changes are made by creating a new revision
  (`clone -> draft -> under-review -> approved`, prior revision `superseded`). No `UPDATE`
  on approved rows; enforce with a DB trigger and an append-only audit table.
- **Derived calculation outputs must carry** `calculationVersionId`, the definition
  `definitionId` + `revision`, an input snapshot (or snapshot hash) with its timestamp,
  the method/correlation set used, resulting data-quality state and provenance/source
  class. Any historical result must be reproducible from those references.
- ESP-PMM performs **no equipment control**: no setpoint writes, no start/stop, no VSD
  commands. Restart-delay and backspin fields are configuration references for
  interpretation only.

## 2. Recommended bounded contexts

| Context | Responsibility | Key entities |
|---|---|---|
| Asset Definition | Versioned engineering record, validation, readiness | `AssetDefinition`, `AssetDefinitionRevision`, `EngFieldValue`, `SectionMeta`, `ValidationFinding`, `ReadinessResult` |
| Equipment & Hierarchy Projection | Read-only projection of Asset ConneX + ESP component inventory | `AssetNodeRef`, `EspComponentInstance`, `ComponentSpec` |
| Curve Catalogue | OEM curve sets and points, catalogue documents | `CurveSet`, `CurvePoint`, `CatalogDocument` |
| Design & Envelope | Design cases, operating envelopes, approvals | `DesignCase`, `OperatingEnvelope`, `Approval` |
| Signal Mapping | Canonical signal vocabulary and per-well mappings | `CanonicalSignal`, `SignalMapping`, `MappingHealth` |
| Well Test & Field Data | Dated observations and acceptance | `WellTest` |
| Calculation Engine | Deterministic engineering computation | `CalculationConfig`, `CalculationVersion`, `CalculationRun`, `CalculationResult` |
| Surveillance & Exceptions | Envelope evaluation, exception lifecycle | `Rule`, `Exception`, `ExceptionAction` |
| Reliability | Lifecycle events, failures, DIFA, risk factors | `LifecycleEvent`, `FailureRecord`, `RiskFactor`, `Intervention` |
| Economics | Deferment and value assumptions | `EconomicContext`, `DefermentRecord` |
| Advisory / AI Context | Assembles governed context for advisory and ML | `AdvisoryContext`, `FeatureSnapshot` |

## 3. Relational persistence guidance (PostgreSQL)

- `esp_asset_definition(definition_id PK, well_id, field_id, created_at, ...)` — one row
  per well; revisions in `esp_asset_definition_revision(revision_id PK, definition_id FK,
  revision, status, created_by/at, updated_by/at, approved_by/at, superseded_by,
  change_summary)`. Partial unique index: one `approved` revision per `definition_id`.
- Section payloads: model each section as its own table keyed by `revision_id`
  (`..._governance`, `..._geometry`, `..._reservoir`, `..._fluid`, `..._design_basis`,
  `..._components`, `..._electrical`, `..._envelope`, `..._calculation`, `..._economics`).
  Repeatables get child tables: `casing_section`, `tubing_section`, `asset_node`,
  `curve_set` + `curve_point`, `signal_mapping`, `well_test`, `lifecycle_event`,
  `risk_factor`.
- Field-level provenance: either sidecar columns per value
  (`<field>_value`, `<field>_unit`, `<field>_source_class`, `<field>_confidence`,
  `<field>_validation`, `<field>_source_ref`, `<field>_source_ts`) or a normalised
  `eng_field_value(revision_id, section_key, field_path, value_num, value_text,
  value_bool, unit, source_class, source_ref, source_ts, effective_from, effective_to,
  entered_by, approved_by, confidence, required, validation, notes)`. The normalised form
  is recommended: it makes completeness, source-mix and diff queries trivial.
- Effective-dated values use `effective_from` / `effective_to` with a `tstzrange` exclusion
  constraint per `(revision_id, field_path)`.
- Immutability: `BEFORE UPDATE/DELETE` trigger rejecting any change when the parent
  revision status is `approved` or `superseded`; all writes recorded in
  `esp_definition_audit` (append-only).
- Enums as PostgreSQL enum types or lookup tables mirroring the TypeScript unions
  (`source_class`, `revision_status`, `asset_class`, `relationship_type`, `inflow_model`,
  `mapping_status`, `signal_quality_state`, `lifecycle_event_type`, `risk_factor_key`).
- Derived data: `calculation_run(run_id, definition_id, revision, calculation_version_id,
  method_set, window_start, window_end, input_snapshot_hash, input_snapshot_at,
  data_quality, created_at)` plus `calculation_result` rows referencing `run_id`.
- **TimescaleDB** hypertables are for time series and derived series only
  (`esp_calc_series`, `esp_exception_event`, `esp_kpi_daily`) — reached through OTConnex
  for raw OT signals. No hypertable belongs in the definition schema.
- Indexing: `(well_id, status)`, `(definition_id, revision)`,
  `(revision_id, section_key)`, `(canonical_id, well_id)`, GIN on JSONB extras.

## 4. API resource names (read/write)

Read:
- `GET /api/esp/asset-definitions?field=&status=&readiness=` — registry rollups
  (`AssetDefinitionSummary`).
- `GET /api/esp/asset-definitions/{wellId}` — latest approved revision.
- `GET /api/esp/asset-definitions/{wellId}/revisions`
- `GET /api/esp/asset-definitions/{wellId}/revisions/{revision}`
- `GET /api/esp/asset-definitions/{wellId}/revisions/{revision}/sections/{sectionKey}`
- `GET /api/esp/asset-definitions/{wellId}/validation`
- `GET /api/esp/asset-definitions/{wellId}/readiness`
- `GET /api/esp/asset-definitions/{wellId}/diff?from=R1&to=R2`
- `GET /api/esp/asset-definitions/{wellId}/export` — canonical JSON payload.
- `GET /api/esp/signals/canonical` · `GET /api/esp/signals/mappings?wellId=`
- `GET /api/esp/curve-sets?wellId=` · `GET /api/esp/curve-sets/{curveSetId}`
- `GET /api/esp/design-cases?wellId=` · `GET /api/esp/operating-envelopes?wellId=`
- `GET /api/esp/well-tests?wellId=` · `GET /api/esp/lifecycle-events?wellId=`
- `GET /api/esp/calculation-configs?wellId=` ·
  `GET /api/esp/calculation-runs/{runId}`
- Time series proxy (OTConnex-backed, never local storage):
  `GET /api/esp/series?wellId=&canonicalId=&from=&to=&resolution=`

Write:
- `POST /api/esp/asset-definitions/{wellId}/revisions` — clone approved to new draft.
- `PATCH /api/esp/asset-definitions/{wellId}/revisions/{revision}` — draft only.
- `POST /api/esp/asset-definitions/{wellId}/revisions/{revision}/validate`
- `POST /api/esp/asset-definitions/{wellId}/revisions/{revision}/submit`
- `POST /api/esp/asset-definitions/{wellId}/revisions/{revision}/approve`
- `POST /api/esp/asset-definitions/{wellId}/revisions/{revision}/reject`
- `PUT /api/esp/signals/mappings/{wellId}/{canonicalId}` — draft revision only.
- `POST /api/esp/curve-sets` · `POST /api/esp/well-tests` ·
  `POST /api/esp/lifecycle-events`
- `POST /api/esp/calculation-runs` — compute against a named revision + version.

All write endpoints require the target revision to be `draft`; a write against an
`approved` or `superseded` revision must return `409 Conflict`.

## 5. Non-goals for the first backend increment

No closed-loop control, no setpoint writes, no protocol drivers, no reservoir simulation,
no vendor-proprietary correlations without licence, no ML remaining-useful-life model.
