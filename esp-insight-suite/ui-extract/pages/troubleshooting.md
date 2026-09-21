# Troubleshooting — `/troubleshooting`

## Meta
- **Route**: `/troubleshooting`
- **Title**: Guided ESP Diagnostics & VSD Trip Lookup
- **Subtitle**: Interactive diagnostic flows, trip code resolution, and root cause analysis.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 4 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Tool Switcher Bar** — `flex border-b mb-3`
2. **Left Panel: Symptom / Trip Selector** — `w-full lg:w-1/3 p-3 border-r`
3. **Right Panel: Guided Diagnostic Tree / Resolution Procedure** — `w-full lg:w-2/3 p-3`

## Blocks

### Tool Switcher Bar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Mode Selector | Tabs | Top | 2 tabs | `Guided Diagnostic Tree`, `VSD Trip Code Lookup` |

### Left Panel: Selector
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Symptom Category List | Accordion | Left | 5 categories | `Low Flow / No Flow`, `High Motor Temp`, `VSD Trip`, `Current Fluctuation`, `Vibration` |
| Trip Code Search | Search Input | Left | 1 | Search by VSD fault code (e.g. `F04`, `F12`, `F42`) |

### Right Panel: Diagnostic Flowchart
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Decision Tree Steps | Interactive Flowchart | Right | Dynamic (3–6 steps) | Step-by-step diagnostic questions with `[Yes]` / `[No]` branches |
| Root Cause Verdict | Alert Box | Bottom Right | 1 | Identified cause (e.g., `Gas Lock in Pump Stages`) |
| Remediation Steps | Checklist | Bottom Right | 1 | Ordered list of corrective procedures |

## Content
| Element | Label / Column / Value |
|---|---|
| Selected Symptom | `Symptom: Motor Current Fluctuating > 15%` |
| Step 1 Question | `"Is Pump Intake Pressure (PIP) below bubble point pressure?"` |
| Step 2 Question | `"Does current drop coincide with fluid rate drop at surface?"` |
| Final Diagnosis | **High Probability (85%)**: `Gas Interference / Free Gas at Pump Intake` |
| Recommended Procedure | 1. Flush casing gas vent valve.<br>2. Increase backpressure on annulus.<br>3. Adjust VSD speed down by 3 Hz. |

## States
- **Interactive Step State**: Clicking `[Yes]` or `[No]` updates the flowchart to reveal the next diagnostic test.
- **Trip Code Search State**: Typing `F42` instantly displays `VSD Fault 42: Overcurrent / Locked Rotor` details.
