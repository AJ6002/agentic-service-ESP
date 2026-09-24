# ESP Insights

ADVAIT ESP-PMM Lovable Prompt Pack

Purpose: Use these prompts in Lovable to build complete clickable mockups for the ADVAIT ESP Performance Monitoring and Management module.

Important context for every prompt:

- ADVAIT Platform already exists.

- OTConnex is the existing ADVAIT capability for bringing OT, SCADA, historian, VSD, sensor, and field data into the platform.

- Asset ConneX is the existing ADVAIT capability for building asset hierarchy, asset templates, equipment templates, tag templates, and master asset data.

- The ESP-PMM module should reuse ADVAIT platform capabilities wherever possible instead of rebuilding ingestion, asset hierarchy, user management, notifications, workflows, or base dashboard infrastructure.

- ESP-PMM is an APM domain module inside ADVAIT Asset Performance Suite.

## Prompt 1 - Project Foundation

Build a complete high-fidelity web application mockup for "ADVAIT ESP Performance Monitoring and Management", an Asset Performance Management module for upstream oil and gas customers operating Electric Submersible Pump fleets.

This is not a landing page. The first screen must be the actual operations application: an ESP Fleet Cockpit.

Use the existing ADVAIT platform as the foundation:

- OTConnex brings real-time and historical OT data from SCADA, historians, VSD/VFD systems, downhole gauges, surface sensors, and production systems.

- Asset ConneX manages asset hierarchy, asset templates, equipment templates, ESP component templates, tag templates, and master asset data.

- ESP-PMM consumes these ADVAIT services and adds ESP-specific asset performance, calculations, surveillance, diagnostics, reliability, and recommendations.

Design the application for four user groups:

- Operations users who need live monitoring, alarms, operating states, and recommended actions.

- Artificial lift and production engineers who need design cases, pump curves, TDH, PIP, operating point, frequency scenarios, and model-vs-actual comparison.

- Maintenance and reliability users who need run-life, failure modes, teardown findings, bad actors, and intervention planning.

- Management users who need fleet health, production deferment, availability, opportunity value, and weekly scorecards.

Create a serious industrial operations UI. It should feel like a professional APM product for oilfield engineers and control-room users. Use dense but readable layouts, strong tables, trend panels, engineering charts, status indicators, exception queues, and drill-down workflows. Avoid marketing-style hero sections, decorative cards, and generic SaaS visuals.

Use this navigation:

- Fleet Cockpit

- Well Monitor

- Engineering Workbench

- Design Cases

- Exceptions

- Troubleshooting

- Reliability

- Reports

- Administration

Use sample data for 3 fields and 25 ESP wells. Include wells in these conditions:

- Normal running

- Outside recommended operating range

- Suspected gas interference

- Suspected pump wear

- Motor overload

- High motor temperature

- VSD trip

- Downhole gauge communication issue

- Vibration warning

- Stopped planned

- Stopped unplanned

The app should include realistic oilfield units and ESP terms: Hz, A, V, psi, degF, bpd, bopd, PIP, discharge pressure, TDH, BEP, ROR, motor load, motor temperature, vibration, run life, VSD trip code, production deferment, and ESP health index.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/da99f371-e472-4670-8519-5bf0c0531f1e).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
