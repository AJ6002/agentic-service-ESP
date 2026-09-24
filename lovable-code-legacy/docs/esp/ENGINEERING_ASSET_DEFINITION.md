# ESP-PMM — Engineering Asset Definition

Authoritative contract: `src/domain/esp/asset-definition.ts`
Signal contract: `src/domain/esp/tag-dictionary.ts`
Validation / readiness: `src/domain/esp/validation.ts`
Demo data builder: `src/data/esp/asset-definitions.ts`

The Engineering Asset Definition is the governed input foundation of ESP-PMM. Every
surveillance rule, engineering calculation, exception, reliability metric, advisory
message and (later) ML feature is derived from an **approved revision** of this record.
No calculation in ESP-PMM may consume ungoverned inputs.

---

## 1. Field-level provenance model

Every engineering value is wrapped in `EngField<T>`:

```
EngField<T> = { value: T | null, unit?: string, provenance: Provenance }
```

`value === null` means *missing*, never zero and never "unknown default".

`Provenance` carries: `sourceClass`, `sourceRef`, `sourceTimestamp`,
`effectiveFrom` / `effectiveTo`, `revision`, `enteredBy`, `approvedBy`,
`confidence` (`high | medium | low`), `required`, `validation`
(`valid | warning | error | unverified`) and free-text `notes`.

### Source classes (`SourceClass`)

| Class | Meaning | Trust for calculation |
|---|---|---|
| `Customer` | Supplied by the operator (well file, completion report, allocation) | Authoritative for identity/geometry |
| `OEM` | Vendor catalogue / nameplate / certified curve | Authoritative for equipment limits |
| `Engineering` | Value derived or selected by an ESP engineer | Authoritative once approved |
| `Field Test` | Dated measurement (well test, gradient survey, fluid lab) | Authoritative as of its test date |
| `OT` | Live signal via OTConnex mapping | Live only, never stored as definition truth |
| `Calculated` | ESP-PMM engine output | Requires calculation version + input snapshot |
| `Inferred` | Filled from fleet/analogue reasoning | Flags reduced confidence |
| `Default` | Placeholder / site standard | Blocks READY readiness where required |

### Data-class separation (non-negotiable)

- **Customer data** — identity, hierarchy, geometry, completion, allocation basis.
- **Design data** — the design case as engineered and approved (`DesignBasis`).
- **Engineering data** — envelopes, calculation configuration, correlations, curve selection.
- **Live data** — OT time series; ESP-PMM holds only the *mapping* (`SignalMapping`).
- **Calculated data** — derived results; never written back into definition fields.

A definition field is never silently overwritten by a live or calculated value.

---

## 2. The 16 sections

Section keys are `AssetDefinitionSectionKey`; labels in `SECTION_LABELS`.

1. **Customer / site / governance** (`governance`, `GovernanceContext`) — customer,
   business unit, asset/field/block/country/region/basin, field & pad IDs, customer well
   name, ADVAIT well ID, aliases and legacy IDs, environment, timezone, unit system,
   currency, asset criticality, production priority, data/engineering/operations/
   reliability owners, effective dates, source documents.
   *Required:* customer, field, ADVAIT well ID, unit system, criticality, owners.
2. **Asset hierarchy & relationships** (`hierarchy`, `AssetNode[]`) — Asset ConneX-owned
   IDs referenced by ESP-PMM: `assetId`, `parentAssetId`, `level` (`AssetLevel`),
   `assetClass` (`AssetClass`), `relationshipType` (`contains`, `installed-in`,
   `connected-to`, `powers`, `measures`, `protects`, `bypasses`), nameplate identity
   (make/family/model/serial/part), series or diameter, rating, material spec, install and
   commissioning dates, `status`, document reference, `stringOrder` for the downhole string.
   *Required:* one Well node, one ESP Assembly node, pump / intake / protector / motor /
   cable nodes, VSD node.
3. **Well / completion / geometry** (`geometry`, `WellGeometry`) — well and trajectory
   type, surface coordinates, depth datum and reference elevation, total MD/TVD, deviation
   survey reference, packer depth, perforation top/bottom (MD and TVD), completion
   interval, **pump setting depth MD/TVD**, producing and static fluid level, annulus
   pressure reference, wellhead configuration, choke size, flowline context, separator
   pressure, known restrictions, MAWP, plus repeatable `casingSections[]` and
   `tubingSections[]` (OD/ID, weight, grade or material, roughness, top/bottom depths).
   *Required:* total MD/TVD, perforation depths, pump setting MD/TVD, at least one tubing
   section (TDH cannot be computed without tubing ID and pump setting TVD).
4. **Reservoir / inflow model** (`reservoir`, `ReservoirInflow`) — reservoir pressure,
   flowing BHP, reservoir temperature, bubble point, productivity index, AOF,
   `InflowModel` (`Linear PI | Vogel | Composite | Other`), skin/modifier, datum TVD, test
   date, test method, quality.
   *Required:* reservoir pressure, PI or AOF, inflow model, test date (PI older than the
   configured staleness window raises a warning, not an error).
5. **Fluid / PVT model** (`fluid`, `FluidPvt`) — oil API and SG, water SG, gas SG, water
   cut, produced and solution GOR, Bo, Bg, oil and water viscosity, z-factor, salinity,
   H2S, CO2, solids indicator and concentration, deposition tendencies, fluid temperature,
   PVT model, lab report reference, test date.
   *Required:* oil API/SG, water SG, gas SG, water cut, GOR, PVT model.
6. **ESP design basis** (`designBasis`, `DesignBasis`) — design case ID and revision,
   approval status/approver/date, target liquid and oil rates, min/nominal/max desired
   rate, design water cut, GOR, WHP, casing pressure, reservoir pressure, Pwf, PIP, PDP,
   frequency, TDH, pump differential, downhole pump flow, pump make/family/model/series,
   stages and sections, design BEP, ROR low/high, head per stage, pump efficiency,
   required BHP, GVF at intake, separator efficiency, motor HP/kW/V/A/Hz/service factor,
   protector and cable selection, transformer sizing, VSD sizing, assumptions, exclusions,
   engineering document reference.
   *Required:* design case ID + revision, design frequency, design TDH, target rates,
   design BEP and ROR, motor rating set.
7. **OEM curves & catalog** (`curveSets`, `CurveSet[]`) — per curve set: OEM, family,
   model, series/diameter, `curveRevision`, `effectiveDate`, base frequency, reference
   fluid SG and viscosity, test basis, BEP, ROR low/high, tolerance metadata, optional
   additional frequencies, catalogue document reference, and `points[]` of `CurvePoint`
   (`flowBpd`, `headPerStageFt`, `efficiencyPct`, `bhpPerStage`).
   *Required:* one curve set matching the installed pump model, with revision, effective
   date, base frequency and >= 5 points. Without it, Pump Performance readiness is BLOCKED.
8. **Component engineering** (`components`, `ComponentEngineering`) — nameplate and
   specification detail per component: `pump` (model, series, stage type, stages, sections,
   rated range, shaft notes), `intake` (type, gas-handling type, rated GVF, separator
   efficiency assumption), `protector` (type, configuration, chamber, thrust rating),
   `motor` (make/model/series, HP, kW, rated V/A/Hz, speed, temperature class, service
   factor), `gauge` (make/model, channels, pressure and temperature range, vibration and
   leakage capability, accuracy), `cable` (type, AWG, conductor, insulation, **length**,
   temperature and voltage rating, estimated voltage drop, MLE type), `surface`
   (transformer rating, VSD make/model/rating/control mode, junction box, switchboard).
   *Required:* pump stages, motor electrical ratings, cable size and length.
9. **Electrical / VSD / power** (`electrical`, `ElectricalSystem`) — power source, nominal
   supply voltage, transformer primary/secondary/kVA, VSD make/model/firmware and rated
   kVA/A/V, min/max/nominal frequency, output ranges, motor ratings, current and voltage
   imbalance limits, overload and underload limits, power factor, cable voltage-drop
   assumption, grounding reference, restart-delay strategy and backspin wait
   (**configuration reference only — ESP-PMM issues no control commands**), trip-code
   dictionary reference.
10. **Canonical OT tag dictionary** (`signalMappings`, `SignalMapping[]`) — see
    `CANONICAL_TAG_DICTIONARY.md`. Mapping metadata only; no historian payload.
11. **Well test / field data** (`wellTests`, `WellTestRecord[]`) — dated observations:
    test start, duration, source (`Test separator | MPFM | Manual | Group separator |
    Allocated`), method, liquid/oil/water/gas rates, water cut, GOR, WHP, casing pressure,
    PIP, PDP, frequency, motor current, flowing BHP, fluid level, `accepted` flag,
    confidence, comments. Only `accepted` tests may calibrate models.
12. **Operating envelope & limits** (`envelope`, `OperatingEnvelope`) — envelope revision,
    approval status and approver, `limitSource` (`OEM | Customer | Engineering | Site
    standard`), min/max frequency, ROR low/high, BEP reference, low-flow caution and
    trip-prevention thresholds, high-flow caution, min PIP, drawdown margin, GVF caution,
    motor load min/max, motor temperature warning/critical, vibration warning/critical,
    max WHP and PDP, starts-per-hour and per-day guidance, restart dwell, data-quality
    prerequisite, hysteresis and persistence.
    *Required and approved* — an unapproved envelope degrades surveillance readiness.
13. **Calculation configuration** (`calculation`, `CalculationConfig`) — unit system, IPR
    method, PVT correlation, multiphase correlation, friction model, fluid density method,
    separator efficiency method, curve interpolation, frequency / viscosity / gas
    correction methods, TDH method, PI method, head-to-pressure basis, calculation window,
    smoothing, minimum data quality, `calculationVersionId`, engineering owner, approval
    status, and `genericCorrelations` (true = demo/generic, never OEM-certified).
14. **Maintenance / reliability / lifecycle** (`lifecycle`, `LifecycleEvent[]` +
    `riskFactors`, `RiskFactor[]`) — event type (`Installation`, `Commissioning`,
    `Pull / workover`, `Component replacement`, `Failure`, `Trip`, `Chemical treatment`,
    `Gauge repair`, `Redesign`), date, run hours and run-life days, start/stop/trip counts,
    failure mode, suspected and confirmed root cause, failed component, intervention
    action, DIFA finding, evidence reference, repeat-failure flag, pre-failure conditions.
    Risk factors score 0-100 per `RiskFactorKey` with basis and source class.
15. **Production / economic context** (`economics`, `EconomicContext`) — baseline oil,
    allocated-oil source, deferment basis, target oil, uptime target, oil price, value
    basis, intervention cost, opportunity valuation basis, production criticality,
    ranking weight. Assumptions only — not accounting truth.
16. **Provenance & governance audit** (`provenance` section view) — derived, not stored:
    revision header (`definitionId`, `revision`, `status`, created/updated/approved
    by-and-at, `supersededBy`, `changeSummary`), source mix, completeness, OT coverage,
    validation findings and readiness by capability.

---

## 3. Required vs optional

- `Provenance.required` is the single per-field authority. Section rollups
  (`SectionMeta`) count `requiredCount` / `requiredComplete` and
  `optionalCount` / `optionalComplete`.
- A **required field with `value === null`** produces an `error` finding and reduces
  completeness; an optional gap produces at most a `warning`.
- Required OT signals are declared by `CanonicalSignal.required` / `REQUIRED_SIGNAL_IDS`.
- Readiness (`ReadinessResult`) is computed per `ReadinessCapability`
  (Basic Surveillance, Pressure Analysis, Pump Performance, Gas Diagnostics, Reliability,
  AI Advisor Context, ML Training Eligibility) as `READY | LIMITED | BLOCKED` with
  explicit `blockers[]`. Capability gating — not a single global score — is what protects
  the engineering results.

---

## 4. Revision, effective dates and immutability

- All revisions of a well share one `definitionId`; each revision has `revision`
  (`R1`, `R2`, ...) and `status` in `draft | under-review | approved | superseded`.
- Lifecycle: `clone approved -> draft -> under-review -> approved`, and the previous
  approved revision becomes `superseded` with `supersededBy` set.
- **An approved revision is immutable.** No field, curve point, mapping or envelope value
  in an approved revision may be edited. Every correction is a new revision carrying a
  `changeSummary`.
- Exactly one approved revision may be effective at a point in time. Field-level
  `effectiveFrom` / `effectiveTo` support time-varying values (water cut, PI, envelope)
  within a revision; queries are always "as of" a timestamp.
- Calculations and exceptions record which `definitionId` + `revision` +
  `calculationVersionId` produced them, so any historical result can be reproduced.
- Only `approved` revisions may drive production surveillance; drafts are for engineering
  what-if work and are labelled as such in the UI.
