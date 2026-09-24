# Administration — `/administration`

## Meta
- **Route**: `/administration`
- **Title**: Administration & Platform Integration
- **Subtitle**: ADVAIT platform service integration (OTConnex & Asset ConneX), alarm rule threshold overrides, and role-based permissions.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 14 (Configuration Workspace)

## Shell
- **Topbar Variant**: Configuration
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Integration Status Cards** — `grid grid-cols-1 md:grid-cols-2 gap-3 mb-3`
2. **Platform Mapping Configuration Tabs** — `flex border-b mb-3`
3. **Configuration Details & Threshold Settings** — `w-full border rounded-sm p-4`

## Blocks

### Integration Status Cards
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| OTConnex Service Status | Status Card | Left | 1 | `Connected · 2s Scan Cycle · 340 Tags Active` |
| Asset ConneX Hierarchy | Status Card | Right | 1 | `Synced · 3 Fields · 25 Wells · 105 Components` |

### Configuration Details & Threshold Settings
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Alarm Rule Threshold Form | Form Grid | Center | 1 | Configures global defaults for `Low PIP (psi)`, `High Motor Temp (°F)`, `Overload Amps (A)` |
| Role Management List | Data Table | Bottom | 1 | User roles (`Ops Engineer`, `Artificial Lift Specialist`, `Configurator`, `Administrator`) |

## Content
| Element | Label / Column / Value |
|---|---|
| OTConnex Endpoint | `https://otconnex.advait.internal/api/v2/telemetry` |
| Asset ConneX Endpoint | `https://assetconnex.advait.internal/api/v1/hierarchy` |
| Global Alarm Thresholds | `Low PIP Limit: 250 psi` · `High Temp Limit: 210°F` · `Overcurrent Trip: 115%` |

## States
- **Form Edit State**: Changing threshold inputs activates the `[Save Changes]` button.
- **Test Connection State**: Clicking `[Test OTConnex Connection]` displays a success toast message (`"OTConnex service ping successful — latency 14ms"`).
