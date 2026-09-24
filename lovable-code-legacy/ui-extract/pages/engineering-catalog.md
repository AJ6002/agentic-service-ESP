# Equipment Catalog — `/engineering/catalog`

## Meta
- **Route**: `/engineering/catalog`
- **Title**: Master Equipment Catalog
- **Subtitle**: Governed OEM pump models, electric motors, gas separators, protectors, and cables with digitized performance specs.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 8 (Configuration Workspace)

## Shell
- **Topbar Variant**: Configuration
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Catalog Category Navigation** — `flex space-x-2 mb-3 border-b pb-2`
2. **Search & Filter Bar** — `flex justify-between items-center mb-3`
3. **Equipment Catalog Grid / Table** — `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3`

## Blocks

### Catalog Category Navigation
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Category Tabs | Nav Tabs | Top | 5 categories | `Pumps (42)`, `Motors (28)`, `Protectors (14)`, `Gas Separators (12)`, `Cables (18)` |

### Search & Filter Bar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| OEM Manufacturer Filter | Select | Left | 1 | `All OEMs`, `Schlumberger / REDA`, `Baker Hughes`, `Borets`, `Wood Group` |
| Digitization Status Filter | Select | Center | 1 | `All`, `Digitized Curves (38)`, `Pending Digitization (4)` |
| Search Input | Input | Right | 1 | Search by series name, flow range, or model ID |

### Equipment Catalog Grid
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Pump Model Card | Spec Card | Grid Items | 42 cards | Displays OEM series, stage head, BEP flow, minimum casing size, and curve status |

## Content
| Element | Label / Column / Value |
|---|---|
| Pump Card Example | **REDA DN1750** · `OEM: Schlumberger` · `BEP Flow: 1,750 bpd` |
| Spec 1 | `Series: 400 Series (4.00 in OD)` |
| Spec 2 | `Recommended Flow Range: 1,200 – 2,200 bpd` |
| Spec 3 | `Head per Stage: 28.5 ft @ 60 Hz` |
| Curve Status Pill | `Digitized (21 Data Points)` |
| Action Button | `[View Full Model Specs & Curve]` -> `/engineering/catalog/pumps/$modelId` |

## States
- **Digitization Pending State**: Cards for un-digitized pump models render a yellow `Pending Digitization` pill and disable curve preview capabilities.
- **Filter State**: Selecting OEM `Baker Hughes` filters the catalog to Centrilift pump series.
