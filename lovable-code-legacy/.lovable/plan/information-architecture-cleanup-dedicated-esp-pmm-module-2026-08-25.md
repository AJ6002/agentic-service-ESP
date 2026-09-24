# Information Architecture Cleanup — Dedicated ESP-PMM Module

Scope decision: this becomes a **dedicated ESP Performance Monitoring & Management module**. The generic multi-asset (SRP / CNG Compressor / Natural Flow) framing is removed, not extended.

## What the audit found

The engineering knowledge is good; the way it is exposed and stored has drifted into parallel stacks that overlap in meaning. Confirmed by reading the routes, nav and data modules:

1. **Three competing engineering areas in navigation**
   - `/engineering/*` — generic multi-asset landing, asset registry, templates, readiness
   - `/asset-definitions/*` — the governed database-backed ESP catalog / installed fleet / provenance (10 sections)
   - `/asset-definition/*` — the earlier per-well 16-section versioned workspace, still labelled "Asset Definition (legacy)" in the rail

   The sidebar offers "Engineering Configuration", "Asset Definitions" and "Asset Definition (legacy)" as siblings, so nothing reads as authoritative.

2. **Three unconnected data layers for the same wells**
   - Supabase `esp_*` tables (reconciled CCED/OEM catalog) — read only by `/asset-definitions/*`
   - `src/data/esp/asset-definitions.ts` (local versioned per-well definitions) — read only by `/asset-definition/*`
   - `src/data/apm/engineering-registry.ts` + `assets.ts` (generic portfolio summaries incl. SRP-017, CNG-CMP-01, NF-001) — read only by `/engineering/*` and the cockpit portfolio strip

   ESP-104 exists in all three with no shared key, so readiness/completeness numbers come from different truths.

3. **Duplicated / now-unneeded contracts** — `src/domain/apm/registry.ts` and `asset-type-registry.ts` both export the asset-type plugin list; `types.ts` and `core.ts` are parallel import surfaces; the whole plugin abstraction exists to serve asset types we are now dropping.

4. **Flat, inconsistent routes** — 37 files in one directory; `wells` vs `assets`, `asset-definition` vs `asset-definitions`; `workbench` / `design-cases` outside the engineering area they belong to.

5. **Docs drift** — `docs/esp/*` describes the local 16-section model, with no mapping to the shipped database schema.

## Recommended structure — ESP only

### A. Product identity

- Title returns to **ADVAIT ESP Performance Monitoring & Management (ESP-PMM)**, subtext "ESP fleet surveillance & governed engineering definitions · Asset ConneX master data · OTConnex measurements".
- Landing page returns to **ESP Fleet Cockpit**; the multi-asset "APM portfolio" strip is removed and replaced by an ESP fleet strip (wells by field, states, envelope compliance).
- Wording across screens goes back to wells/ESP systems rather than generic "assets".

### B. Remove the multi-asset framework

Delete (not hide): SRP, CNG Compressor and Natural Flow engineering definitions, demo assets, the asset-type plugin registry, templates page and the type dispatcher route.

```text
remove  src/domain/apm/            (types, core, registry, asset-type-registry, srp-*, cng-*, helpers)
remove  src/data/apm/              (assets.ts, engineering-registry.ts)
remove  src/components/apm/EngineeringWorkspace.tsx  (generic; ESP workspace replaces it)
remove  routes: engineering.templates, engineering.assets*, engineering.index (generic versions)
```

Anything ESP-specific that lives in those files (readiness computation, section descriptor pattern, revision comparison UI) is kept by moving it into the ESP domain/components rather than deleted.

### C. One ESP engineering home

```text
/                                Fleet Cockpit
/wells, /wells/$wellId           Well Monitor
/exceptions /troubleshooting /reliability /reports

/engineering                     ESP Engineering Configuration home (readiness + entry points)
  /engineering/catalog           Equipment catalog (OEM/reference master)
      pumps | curves | motors | intake-gas | protectors | cables | vsd-power | sensors
  /engineering/installations     Installed ESP fleet
      /engineering/installations/$systemId   tabs: assembly · well & completion · fluid/PVT · design limits
  /engineering/definition/$wellId  Per-well governed definition workspace (16 sections, revisions, tag mapping)
  /engineering/governance        tabs: sources · validation · data quality · import
  /engineering/workbench         Calculations, curves, TDH, scenarios
  /engineering/design-cases
/administration
```

- `/asset-definitions/*` pages move to `catalog` / `installations` / `governance` — same code, correct place.
- `/asset-definition/$wellId` becomes `/engineering/definition/$wellId` and loses the "legacy" label; it is the per-well view, while catalog/installations are the reference and fleet views.
- `well`, `fluid`, `limits`, `assembly` stop being top-level pages and become tabs of one installation record.
- Old URLs (`/asset-definitions/*`, `/asset-definition/*`, `/workbench`, `/design-cases`) keep working via redirects.

### D. One ESP data spine

Add `src/data/esp/well-index.ts`: canonical well id → { field, pad, operations series key, installed system id, catalog model ids, definition revisions }.

- Supabase `esp_*` tables remain the system of record for reference and installed engineering data.
- The local versioned definition data stays as the revision/provenance layer, looked up through the same well id and badged as demo revisions.
- Operations demo series stay separate, joined only by well id.
- Cockpit / Well Monitor / Workbench read readiness and catalog facts through this index, so each number has one source.

### E. Navigation

Two workspaces stay. Operations rail: Fleet Cockpit · Well Monitor · Exceptions · Troubleshooting · Reliability · Reports. Configuration rail: Engineering Home · Equipment Catalog · Installed Fleet · Well Definition · Governance · Workbench · Design Cases · Administration. No duplicates, no "legacy", every item a distinct kind of data.

## Technical notes

- Route work is file moves plus thin redirect routes; page bodies are reused, not rewritten.
- No database schema change. Additive only: the `well-index` resolver and `docs/esp/DATA_MODEL_MAP.md` mapping each of the 16 definition sections to the `esp_*` tables/columns for the later backend handoff.
- Provenance, reliability-class and "no synthetic curve" rules are untouched.
- Operations pages change only for wording and links into engineering.

## Sequencing

1. Remove multi-asset framework; restore ESP-PMM identity and cockpit strip.
2. Reorganise engineering routes with redirects and the new rail.
3. Merge well/fluid/limits/assembly into installation tabs; governance tabs.
4. Add `well-index`, point cockpit/monitor/workbench at it, refresh `docs/esp/*` including the data-model map.
