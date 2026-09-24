# ADVAIT ESP-PMM — Complete Frontend Component Analysis Index

This directory (`ui-analysis/`) provides a complete, runtime-accurate component analysis of the entire **ADVAIT ESP-PMM** codebase written in **simple, plain English**.

---

## Document Index & Reading Order

For a new developer joining the project, read the documentation files in the following order:

1. **[route-tree.md](route-tree.md)** — Explains all 36 page routes in the application and how they link together.
2. **[shell.md](shell.md)** — Describes the top navigation header, sidebar rail, and main layout container.
3. **[usage-matrix.md](usage-matrix.md)** — Answers which component appears on which page route.
4. **Domain Component Deep Dives**:
   - [`AdvisorPanel.md`](components/esp/AdvisorPanel.md): Automated diagnostic advisor panel.
   - [`AppShell.md`](components/esp/AppShell.md): Outer layout frame wrapper.
   - [`EspWellVisual.md`](components/esp/EspWellVisual.md): Interactive underground ESP pump drawing.
   - [`FleetTable.md`](components/esp/FleetTable.md): 25-well operational surveillance table.
   - [`PressureProfile.md`](components/esp/PressureProfile.md): Reservoir to wellhead pressure graph.
   - [`charts.md`](components/esp/charts.md): Time-series trend graph wrapper.
   - [`ui.md`](components/esp/ui.md): Status pills, KPI cards, and section headers.
   - [`CurvePlot.md`](components/esp/engineering/CurvePlot.md): Pump performance curves ($H-Q$, $P-Q$, $\eta-Q$).
   - [`GovernedContextPanel.md`](components/esp/engineering/GovernedContextPanel.md): Calculation-grade validation guard panel.
   - [`governance.md`](components/esp/engineering/governance.md): Calculation grade badges (`A1-D`).
5. **[INVENTORY.md](components/ui/INVENTORY.md)** — Inventory table of all 46 shadcn/Radix UI primitive components.
6. **Data Contracts**:
   - [`types.md`](data-contracts/types.md): Data types and shapes explained simply.
   - [`data-files.md`](data-contracts/data-files.md): Overview of mock data files.
   - [`consumers.md`](data-contracts/consumers.md): Type to component mapping matrix.

---

## Summary of Findings

- **Total Page Routes**: 36 routes managed by TanStack Router.
- **Custom Domain Components**: 10 primary components under `src/components/esp/`.
- **UI Primitives**: 46 reusable shadcn/Radix primitives under `src/components/ui/`.
- **Data Model**: Pure in-memory deterministic functions for operational surveillance; Supabase catalog queries for governed equipment data.
- **Unused Components**: 0 (all components are actively used).
