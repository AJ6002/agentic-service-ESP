# ESP-PMM data model map

Dedicated ESP Performance Monitoring & Management module. No multi-asset framework:
every entity below is ESP-specific.

## Layers

| Layer | Location | Purpose | Persistence |
| --- | --- | --- | --- |
| Operations (OTConnex-like) | `src/data/esp/fleet.ts`, `series.ts`, `exceptions.ts`, `reliability.ts` | Deterministic demo surveillance values: state, Hz, PIP, PDP, current, health index, run life | In-memory demo only |
| Governed engineering (Asset ConneX) | Database `esp_*` tables, read via `src/lib/esp-catalog/queries.functions.ts` | OEM catalog, installed systems, well/fluid engineering, design limits, provenance, data-quality issues | Project database |
| Definition revisions | `src/data/esp/asset-definitions.ts` + `src/domain/esp/asset-definition.ts` | Versioned 16-section engineering definition contract with `EngField` provenance, completeness/readiness | In-memory demo, contract for future service |
| Join spine | `src/data/esp/well-index.ts` | Resolves a well across all three layers (`wellIndex()`, `governedInstallation()`) | Derived |

Rule: a value has exactly one owning layer. Screens resolve wells through the
spine rather than re-deriving completeness, readiness, or installed-model links.

## Route map (Configuration workspace)

```text
/engineering                          overview + hierarchy
/engineering/catalog                  equipment catalog (8 classes)
/engineering/catalog/pumps/$modelId   pump model detail + digitised curve
/engineering/installations            installed systems list
  /assembly  /well  /fluid  /limits   installed configuration tabs
/engineering/installations/$systemId  installed system detail
/engineering/definition               governed per-well revisions
/engineering/definition/$wellId       revision workspace + tag dictionary
/engineering/governance/validation    readiness gates
/engineering/governance/sources       provenance registry
/engineering/governance/quality       reconciliation queue
/engineering/governance/import        catalog import administration
/engineering/workbench                curves, TDH, scenarios
/engineering/design-cases             design vs current vs what-if
```

Operations workspace keeps `/`, `/wells`, `/wells/$wellId`, `/exceptions`,
`/troubleshooting`, `/reliability`, `/reports`.

Legacy paths `/asset-definitions/*`, `/asset-definition/*`, `/workbench`,
`/design-cases` redirect into the tree above.

## Database entities (Asset ConneX shape)

Reference master: `esp_oems`, `esp_sources`, `esp_pump_models`,
`esp_pump_curve_points`, `esp_motor_models`, `esp_gas_handling_models`,
`esp_protector_models`, `esp_cable_models`, `esp_vsd_models`,
`esp_sensor_models`, `esp_catalog_aliases`.

Installed fleet: `esp_fields`, `esp_wells`, `esp_installed_systems`,
`esp_installed_pump_sections`, `esp_well_engineering`, `esp_fluid_pvt`,
`esp_design_limits`.

Governance: `esp_data_quality_issues`.

## Provenance rules (enforced in UI)

- Reliability grades A1–D on every catalog value; no ungraded numbers.
- Catalog curve availability and digitised curve points are separate facts.
  Zero digitised points renders as "BEP/Envelope only" — never a synthetic curve.
- Floater and compression recommended operating ranges stay distinct; when the
  source states only a series flow envelope, it is labelled `(envelope)`.
