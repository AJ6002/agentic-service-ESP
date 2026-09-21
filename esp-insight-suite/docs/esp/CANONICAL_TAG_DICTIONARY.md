# ESP-PMM — Canonical OT Tag Dictionary

Contract: `src/domain/esp/tag-dictionary.ts` (`CanonicalSignal`, `SignalMapping`,
`CANONICAL_SIGNALS`, `REQUIRED_SIGNAL_IDS`).

ESP-PMM defines a **fleet-wide canonical signal vocabulary** and, per well, a **mapping**
from each canonical signal to a concrete OT source. OTConnex acquires and stores the live
and historical time series. ESP-PMM stores the mapping and quality metadata only — raw
history is never copied into asset-definition tables.

---

## 1. Canonical signal catalogue (as seeded in code)

`R` = required for a governed definition.

| Canonical ID | Name | Category | Typical source asset | Unit | Type | R | Expected range | Primary analytics use |
|---|---|---|---|---|---|---|---|---|
| ESP.RUN_STATUS | Run status | Run state | VSD | bool | bool | ✓ | 0–1 | Availability, uptime, all surveillance |
| ESP.OPERATING_STATE | Operating state | Run state | VSD | enum | enum | ✓ | — | State machine, exception engine |
| ESP.START_STOP_EVENT | Start / stop event | Run state | VSD | event | bool | ✓ | 0–1 | Starts per day, reliability |
| ESP.FREQUENCY | Drive output frequency | Drive | VSD | Hz | float | ✓ | 20–70 | Affinity scaling, pump curve, TDH |
| ESP.MOTOR_SPEED | Motor speed | Drive | Motor | rpm | float | | 0–4200 | Affinity scaling |
| ESP.MOTOR_CURRENT | Motor current (average) | Electrical | VSD | A | float | ✓ | 0–200 | Motor loading, gas and wear diagnostics |
| ESP.PHASE_CURRENT_A/B/C | Phase currents | Electrical | VSD | A | float | | 0–200 | Current imbalance check |
| ESP.MOTOR_VOLTAGE | Motor voltage | Electrical | VSD | V | float | ✓ | 0–4160 | Motor loading, cable drop |
| ESP.PHASE_VOLTAGE_AB | Phase voltage A-B | Electrical | VSD | V | float | | 0–4160 | Voltage imbalance check |
| ESP.ACTIVE_POWER | Active power | Electrical | VSD | kW | float | | 0–500 | Energy intensity, motor loading |
| ESP.POWER_FACTOR | Power factor | Electrical | VSD | – | float | | 0–1 | Electrical health |
| ESP.CURRENT_LEAKAGE | Current leakage | Electrical | Downhole gauge | mA | float | | 0–100 | Insulation degradation |
| ESP.VSD_TRIP_CODE | VSD trip code | Drive | VSD | code | string | ✓ | — | Trip diagnostics, reliability |
| ESP.WHP | Wellhead / tubing pressure | Pressure | Wellhead | psi | float | ✓ | 0–5000 | Pressure analysis, TDH |
| ESP.CASING_PRESSURE | Casing / annulus pressure | Pressure | Wellhead | psi | float | ✓ | 0–5000 | Gas diagnostics, fluid level |
| ESP.PIP | Pump intake pressure | Pressure | Downhole gauge | psi | float | ✓ | 0–5000 | Pressure analysis, gas diagnostics, drawdown |
| ESP.PDP | Pump discharge pressure | Pressure | Downhole gauge | psi | float | ✓ | 0–6000 | Pump performance, head per stage |
| ESP.DOWNHOLE_TEMP | Downhole (intake) temperature | Temperature | Downhole gauge | °F | float | ✓ | 0–400 | PVT, reliability |
| ESP.MOTOR_TEMP | Motor winding / oil temperature | Temperature | Downhole gauge | °F | float | ✓ | 0–450 | Thermal margin, reliability |
| ESP.VIBRATION | Vibration (XY) | Vibration | Downhole gauge | g | float | | 0–5 | Mechanical diagnostics |
| ESP.LIQUID_RATE | Liquid rate | Production | MPFM | bpd | float | ✓ | 0–12000 | Operating point, ROR compliance |
| ESP.OIL_RATE | Oil rate | Production | Production system | bopd | float | ✓ | 0–10000 | Deferment, economics |
| ESP.WATER_RATE | Water rate | Production | Production system | bwpd | float | | 0–12000 | Water cut |
| ESP.GAS_RATE | Gas rate | Production | MPFM | Mscf/d | float | | 0–20000 | GVF, gas diagnostics |
| ESP.WATER_CUT | Water cut | Fluid properties | Production system | % | float | ✓ | 0–100 | Fluid density, TDH |
| ESP.GOR | Producing GOR | Fluid properties | Production system | scf/stb | float | | 0–5000 | GVF, gas diagnostics |
| ESP.CHOKE_POSITION | Choke position / size | Surface / choke | Choke | /64 in | float | | 0–128 | Backpressure analysis |
| ESP.FLUID_LEVEL | Fluid level | Pressure | Well | ft | float | | 0–15000 | Inflow calibration |
| ESP.TEST_SEPARATOR_DATA | Separator / well test data | Test data | Test separator interface | mixed | float | | — | Model calibration |
| ESP.DQ_HEARTBEAT | Data-quality heartbeat | Data quality | Downhole gauge | s | float | ✓ | 0–3600 | Confidence gating, all analytics |

Categories (`SignalCategory`): Run state, Electrical, Drive, Pressure, Temperature,
Vibration, Production, Fluid properties, Surface / choke, Test data, Data quality.

## 2. Engineering-unit intent

Units are **canonical, not source units**. `SignalMapping.rawUnit` records what the source
delivers; `engineeringUnit` records what ESP-PMM calculations consume; `scale` and `offset`
define the conversion. Calculations never guess units — a mapping with a `rawUnit` that
cannot be reconciled to the canonical unit is a validation error. The definition-level
`unitSystem` (`Field (US oilfield)` or `Metric (SI)`) governs presentation only.

## 3. Source classes and systems

`SignalSourceSystem`: `SCADA`, `Historian`, `VSD`, `Downhole gauge`,
`Production system`, `Manual test`, `Calculated`.

Each mapping also carries `sourceClass` (`OT`, `Field Test`, `Calculated`, `Inferred`, ...)
and `confidence`, so a rate that is actually an allocated production-system value or an
inferred fallback is never treated as a measured OT reading.

## 4. Mapping metadata

Per `SignalMapping`: `canonicalId`, `wellId`, `sourceAssetId` (Asset ConneX),
`sourceSystem`, `sourceTagPath`, `connectionRef` and `protocol` (reference only — no
protocol drivers live in ESP-PMM), `rawUnit`, `engineeringUnit`, `scale`, `offset`,
`dataType`, `sampleRateSec`, `historianEnabled`, `deadband`, `rangeMin` / `rangeMax`,
alarm limits `limitLowLow` / `limitLow` / `limitHigh` / `limitHighHigh`, `required`,
`usedBy`, `fallbackSource`, `inferred`, `timeSyncRule`, `mappingStatus`
(`mapped | unmapped | partial | deprecated | inferred`), `sourceClass`, `confidence`,
`notes`.

`timeSyncRule` states how the signal is aligned to the calculation window (for example
"nearest sample within 60 s, UTC"), which is required for any multi-signal calculation
such as head per stage or GVF.

## 5. Data quality

`SignalQualityState`: `good | degraded | stale | lost | unknown`, plus `lastGoodAt`.

Quality and mapping status gate downstream work:

- required signal `unmapped` or `lost` → capabilities consuming it are **BLOCKED**;
- `partial`, `inferred`, `degraded` or `stale` → **LIMITED**, results are shown with a
  reduced-confidence marker;
- `ESP.DQ_HEARTBEAT` age above the configured window suppresses exception generation
  instead of producing false alarms.

## 6. Primary calculation consumers

- **TDH / pressure analysis** — WHP, PIP, PDP, water cut, fluid level, geometry.
- **Operating point / ROR compliance** — liquid rate, frequency, curve set, envelope.
- **Head per stage & wear detection** — PDP–PIP differential, frequency, stages, curve.
- **Gas diagnostics / GVF** — PIP, casing pressure, GOR, gas rate, motor current stability.
- **Motor loading & thermal margin** — motor current, voltage, active power, motor temp.
- **Electrical health** — phase currents/voltages, imbalance limits, leakage current.
- **Reliability** — run status, start/stop events, trip codes, vibration.
- **Economics / deferment** — oil rate, baseline and target oil, oil price.
- **AI Advisor / ML** — the full mapped set plus quality metadata; ML training eligibility
  requires all required signals `mapped` with `good` quality over the training window.
