"""
ESP Platform Chart Semantic Catalog & Explainer Service
Grounded in API RP 11S, Takacs ESP Engineering, and React Dashboard Components.

Provides deterministic specifications for all frontend dashboard charts:
- Exact curve labels, colors, dashed/solid styles, and axes
- Governing physics, mathematical formulas, and units
- Operational thresholds (BEP ranges, P10-P90 corridors, trip limits)
- Physical failure mode signatures and tipping indicators
- Deterministic knowledge base query pointers for standard RAG
- Live Chart Data Factory links (zero split-brain)
"""

from typing import Dict, Any, Optional, List
import re
import logging

logger = logging.getLogger(__name__)

CHART_CATALOG: Dict[str, Dict[str, Any]] = {
    "pump-curve": {
        "id": "pump-curve",
        "title": "ESP Pump Performance Curve & Operating Envelope (H-Q & Power)",
        "aliases": [
            "pump_curve", "hq_curve", "pump_performance", "pump_performance_curve",
            "component-pump-performance", "section-pump-curve", "h-q", "head curve",
            "power curve", "bep", "efficiency curve", "10. pump performance curve",
            "in-situ h-q pump performance curve", "bep curve"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "API RP 11S / Hydraulic Institute Standards (HIS) / Takacs ESP Engineering",
        "component_file": "frontend/src/components/PumpPerformanceCurve.jsx",
        "dom_selector": '[data-component-id="pump-curve"]',
        "description": (
            "Multi-curve performance representation of the multistage downhole centrifugal pump "
            "scaled to current VFD operating frequency via Affinity Laws."
        ),
        "visual_elements": [
            {
                "name": "Head Curve H(Q)",
                "visual_style": "Cyan solid line (#00e5ff) with subtle cyan area fill",
                "axis": "Left Y-Axis: Total Dynamic Head (TDH) in feet [ft] vs X-Axis: Liquid Flow Rate [BPD]",
                "formula": "H(Q) = H_rated * (freq/60)^2 * [1.25 - 0.25 * (Q / Q_BEP)^2]",
                "physics": (
                    "Represents hydraulic lift head generated across all stages. "
                    "Scales with the square of VFD frequency (Affinity Law: H2/H1 = (N2/N1)^2)."
                ),
                "operational_meaning": "Lift capacity to overcome wellhead backpressure and fluid column."
            },
            {
                "name": "Brake Horsepower (BHP) Power Curve",
                "visual_style": "Orange dashed line (#f97316, dash 4 4)",
                "axis": "Right Y-Axis: Brake Horsepower in Horsepower [HP] vs X-Axis: Liquid Flow Rate [BPD]",
                "formula": "BHP = (Q_bpd * Head_ft * Specific_Gravity) / (135,740 * Efficiency_frac) * (freq/60)",
                "physics": "Mechanical shaft horsepower demand required from downhole motor.",
                "operational_meaning": "Ensures motor loading remains below nameplate HP and 100% full-load amps."
            },
            {
                "name": "Pump Efficiency Curve (η)",
                "visual_style": "Green solid line (#10b981)",
                "axis": "Hidden Y-Axis scaled 0% to 100% vs X-Axis: Liquid Flow Rate [BPD]",
                "formula": "η(Q) = 72% * sin((Q / 140% Q_BEP) * π)",
                "physics": "Ratio of hydraulic fluid power to mechanical shaft power.",
                "operational_meaning": "Peak efficiency minimizes heat dissipation into motor cooling shroud."
            },
            {
                "name": "Recommended Operating Range (BEP Envelope)",
                "visual_style": "Green highlighted operating window indicator",
                "axis": "X-Axis Flow Band: 80% to 115% of nominal BEP flow",
                "formula": "Q_min_rec = 0.80 * Q_BEP_rated; Q_max_rec = 1.15 * Q_BEP_rated",
                "physics": "Hydraulic envelope where axial impeller thrust forces are balanced.",
                "operational_meaning": "Prevents upthrust wear (left of BEP) and downthrust/cavitation (right of BEP)."
            },
            {
                "name": "Current Operating Point Marker",
                "visual_style": "Glowing beacon point and coordinate callout",
                "axis": "Current Flow Rate (BPD) vs Differential Head (ft)",
                "formula": "Head_ft = (Discharge_PSI - Intake_PSI) * 2.31 / Fluid_SG",
                "physics": "Real-time operating coordinate evaluated directly from live SCADA downhole gauges.",
                "operational_meaning": "Indicates whether the well is inside the safe BEP corridor or drifting off-design."
            }
        ],
        "operational_boundaries": {
            "ror_min_pct": 80.0,
            "ror_max_pct": 115.0,
            "continuous_min_pct": 35.0,
            "runout_max_pct": 135.0,
            "shutoff_risk": "Rapid overheating and fluid vaporization",
            "runout_risk": "Motor overload and downthrust cavitation"
        },
        "failure_modes": {
            "gas_locking": "Severe erratic drop in generated head with fluctuating motor current",
            "upthrust": "Low liquid rate causing upward impeller displacement and thrust bearing wear",
            "downthrust": "Excessive flow beyond BEP causing downward thrust bearing overload",
            "sand_erosion": "Progressive downward flattening of the H-Q curve over time"
        },
        "concept_kb_query": "BEP head-flow affinity law pump curve recommended operating range API RP 11S",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_hq_curve_data"
    },

    "operating-envelope": {
        "id": "operating-envelope",
        "title": "Operating Envelope & Boundary Monitoring (P10–P90)",
        "aliases": [
            "operating-envelope", "operating_envelope", "envelope", "p10-p90",
            "boundary monitoring", "7. esp operating envelope", "statistical boundary",
            "operating envelope & boundary monitoring"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "ISO 13373 Condition Monitoring / API RP 11S Baseline Corridors",
        "component_file": "frontend/src/components/OperatingEnvelope.jsx",
        "dom_selector": '[data-component-id="operating-envelope"]',
        "description": "Dynamic statistical envelope tracking current telemetry against P10-P90 normal corridors across 13 core sensor channels.",
        "visual_elements": [
            {"name": "P10 Lower Baseline Boundary", "visual_style": "Subtle grey dotted line", "axis": "Normalized Sensor Axis"},
            {"name": "P50 Historical Median", "visual_style": "Blue dashed guideline", "axis": "Normalized Sensor Axis"},
            {"name": "P90 Upper Baseline Boundary", "visual_style": "Subtle grey dotted line", "axis": "Normalized Sensor Axis"},
            {"name": "Current Operating Value", "visual_style": "Solid colored bar with status badge", "axis": "Real-time Telemetry"}
        ],
        "operational_boundaries": {
            "normal_corridor": "Between P10 and P90 baseline values",
            "deviation_threshold": "Values outside [P10, P90] flagged as OUT_OF_SPEC"
        },
        "failure_modes": {
            "drawdown": "Intake pressure breaches P10 floor while differential pressure surges",
            "thermal_overload": "Motor temperature breaches P90 ceiling continuously",
            "high_vibration": "Vibration X-axis breaches P90 threshold indicating mechanical unbalance"
        },
        "concept_kb_query": "statistical baseline operating envelope P10 P90 condition monitoring ISO 13373",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "synchronized-trends": {
        "id": "synchronized-trends",
        "title": "Multi-Parameter Synchronized Trends",
        "aliases": [
            "synchronized-trends", "synchronized_trends", "sync-trends", "time-series trends",
            "8. synchronized multi-parameter trends", "multi-parameter trends"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "API RP 11S / IEC 60034 Real-Time SCADA Synchronization",
        "component_file": "frontend/src/components/SynchronizedTrends.jsx",
        "dom_selector": '[data-component-id="synchronized-trends"]',
        "description": "Synchronized dual-axis time-series visualization tracking motor current, pressures, temperatures, and frequency.",
        "visual_elements": [
            {"name": "Motor Current Trace", "visual_style": "Yellow solid line (#eab308)", "axis": "Left Y-Axis: Amps (A)"},
            {"name": "Discharge Pressure Trace", "visual_style": "Blue solid line (#0ea5e9)", "axis": "Right Y-Axis: Pressure (PSI)"},
            {"name": "Intake Pressure Trace", "visual_style": "Cyan solid line (#38bdf8)", "axis": "Right Y-Axis: Pressure (PSI)"},
            {"name": "Drive Frequency Trace", "visual_style": "Purple solid line (#818cf8)", "axis": "Left Y-Axis: Hertz (Hz)"}
        ],
        "operational_boundaries": {
            "time_window": "6h, 12h, 24h, 7d selectable historian windows",
            "sampling_rate": "10-second rolling decimation"
        },
        "failure_modes": {
            "gas_slugging": "Synchronized cyclic dips in PIP followed by motor current fluctuations",
            "underload_trip": "Sudden drop in motor amps below minimum threshold"
        },
        "concept_kb_query": "synchronized telemetry trends SCADA cross-correlation time series API RP 11S",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "param-graphs": {
        "id": "param-graphs",
        "title": "14 Engineering Telemetry Streams & AI VSD Frequency Advisor",
        "aliases": [
            "param-graphs", "param_graphs", "14 engineering telemetry streams",
            "14 telemetry streams", "vsd advisor", "9. 14 standard engineering telemetry streams",
            "param13graphs"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "API RP 11S / VFD Drive Speed Guidelines / Proprietary AI Advisory Engine",
        "component_file": "frontend/src/components/Param13GraphsSection.jsx",
        "dom_selector": '[data-component-id="param-graphs"]',
        "description": "14 micro-charts for all SCADA telemetry channels combined with AI VSD Frequency Advisory logic.",
        "visual_elements": [
            {"name": "14 Sparkline Strips", "visual_style": "Individual dark canvas strips with colored line traces"},
            {"name": "AI VSD Recommendation Card", "visual_style": "Glassmorphic advisory card with target frequency badge"}
        ],
        "operational_boundaries": {
            "min_frequency_hz": 35.0,
            "max_frequency_hz": 65.0,
            "ramp_rate_hz_per_min": 1.0
        },
        "failure_modes": {
            "frequency_hunting": "Rapid oscillations in target frequency indicating unstable inflow",
            "deadband_breach": "Current frequency drifting outside safe hydraulic lift corridor"
        },
        "concept_kb_query": "VSD frequency control optimization ESP operating frequency API RP 11S",
        "proprietary_metric": True,
        "first_party_explanation": "AI VSD Frequency Advisor categorizes speed adjustments into OPTIMIZE_INCREASE, PROTECT_REDUCE, or HOLD_STEADY.",
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "telemetry-table": {
        "id": "telemetry-table",
        "title": "Live Telemetry Stream Matrix (14 VFD Signal Channels)",
        "aliases": [
            "telemetry-table", "telemetry_table", "live telemetry table",
            "live stream matrix", "4. live telemetry data stream matrix"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "WITSML / Modbus SCADA Industrial Signal Spec",
        "component_file": "frontend/src/components/LiveTelemetryTable.jsx",
        "dom_selector": '[data-component-id="telemetry-table"]',
        "description": "High-density tabular grid displaying all 14 engineering parameters with live values, units, and status badges.",
        "visual_elements": [
            {"name": "Channel Row Grid", "visual_style": "Monospace data cells with real-time value updates"},
            {"name": "Status Badges", "visual_style": "Green HEALTHY, Amber WARNING, Red CRITICAL pills"}
        ],
        "operational_boundaries": {
            "packet_staleness_threshold_sec": 30.0,
            "health_states": ["HEALTHY", "WARNING", "CRITICAL"]
        },
        "failure_modes": {
            "sensor_dropout": "Telemetry value frozen or reporting NULL/NaN",
            "communication_timeout": "Packet timestamp lagging real-time by >30 seconds"
        },
        "concept_kb_query": "downhole sensor instrumentation gauge telemetry matrix API RP 11S",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "diagnosis-banner": {
        "id": "diagnosis-banner",
        "title": "Active Model Diagnosis Banner & 13-Mode Fault Assessment",
        "aliases": [
            "diagnosis-banner", "diagnosis_banner", "fault assessment", "active model diagnosis",
            "5. active diagnosis & 13-mode fault assessment", "model diagnosis", "active model diagnosis banner"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "ISO 13373-1 Condition Monitoring / Multi-Layer Ensemble Classification",
        "component_file": "frontend/src/components/DiagnosisBanner.jsx",
        "dom_selector": '[data-component-id="diagnosis-banner"]',
        "description": "Real-time fault classification banner driven by the 13-mode ML diagnosis engine evaluating asset health.",
        "visual_elements": [
            {"name": "Fault Classification Pill", "visual_style": "Prominent colored badge with primary fault label"},
            {"name": "Confidence Score Indicator", "visual_style": "Percentage progress bar (0-100%)"}
        ],
        "operational_boundaries": {
            "confidence_threshold": 0.70,
            "anomaly_score_threshold": 0.50
        },
        "failure_modes": {
            "gas_interference": "Gas bubbles coalescing in pump stages causing head degradation",
            "solids_inflow": "Sand ingestion increasing motor torque and mechanical friction",
            "electrical_imbalance": "Current unbalance across phases exceeding 5%"
        },
        "concept_kb_query": "ESP fault diagnosis classifications failure modes ISO 13373 Takacs",
        "proprietary_metric": True,
        "first_party_explanation": "Multi-layer ensemble model combining physical limit checks with XGBoost classification to assign canonical fault labels.",
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "well-schematic": {
        "id": "well-schematic",
        "title": "Downhole Well Schematic Digital View",
        "aliases": [
            "well-schematic", "well_schematic", "schematic", "digital twin",
            "downhole schematic", "6. esp downhole wellbore"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "API RP 11S Downhole Completion Standards",
        "component_file": "frontend/src/components/WellSchematicView.jsx",
        "dom_selector": '[data-component-id="well-schematic"]',
        "description": "Interactive 2D digital twin illustrating downhole wellbore completion, pump setting depth, and sensor nodes.",
        "visual_elements": [
            {"name": "Wellbore Casing & Tubing", "visual_style": "Technical vector cross-section"},
            {"name": "ESP Equipment Stack", "visual_style": "Motor, seal/protector, gas separator, pump stages"}
        ],
        "operational_boundaries": {
            "submergence_min_ft": 300.0,
            "pump_setting_depth_ft": 4500.0,
            "fluid_level_tolerance_ft": 150.0
        },
        "failure_modes": {
            "insufficient_submergence": "Working fluid level dropping near pump intake causing gas ingestion",
            "casing_leak": "Unintended water ingress above pump setting depth"
        },
        "concept_kb_query": "ESP downhole completion pump setting depth perforations submergence API RP 11S",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "fleet-grid": {
        "id": "fleet-grid",
        "title": "ESP Fleet Well Health Grid & 73 Asset Registry",
        "aliases": [
            "fleet-grid", "fleet_grid", "fleet health", "73 asset registry",
            "fleet overview grid", "11. esp fleet well health overview", "fleet health grid"
        ],
        "dashboard_tab": "cockpit",
        "governing_standards": "ISO 55000 Asset Management / API RP 11S Fleet Governance",
        "component_file": "frontend/src/components/FleetHealthGrid.jsx",
        "dom_selector": '[data-component-id="fleet-grid"]',
        "description": "Fleet-wide operational grid displaying all monitored assets categorized by health score and fault severity.",
        "visual_elements": [
            {"name": "Asset Cards", "visual_style": "Grid cards with health index meter and status badges"},
            {"name": "Fleet KPI Bar", "visual_style": "Summary bar indicating healthy vs degraded well counts"}
        ],
        "operational_boundaries": {
            "critical_health_cutoff": 60.0,
            "degraded_health_cutoff": 80.0,
            "healthy_cutoff": 90.0
        },
        "failure_modes": {
            "fleet_cluster_decline": "Multiple adjacent wells exhibiting simultaneous intake pressure depletion"
        },
        "concept_kb_query": "ESP fleet reliability management health index prioritization ISO 55000",
        "proprietary_metric": True,
        "first_party_explanation": "Composite 0-100 Health Index computed from weighted penalties across thermal, electrical, hydraulic, and vibration subsystems.",
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "forensics-timeline": {
        "id": "forensics-timeline",
        "title": "Forensic Tipping Timeline (Visual 1 Synchronized Culprit Tracks)",
        "aliases": [
            "forensics-timeline", "forensics_timeline", "incident tipping timeline",
            "visual 1", "tipping timeline", "temporal causation forensics",
            "incident timeline", "tipping tracks", "incident tipping timeline (visual 1)"
        ],
        "dashboard_tab": "forensics",
        "governing_standards": "ISO 13373-2 Vibration Condition Monitoring / API RP 11S Failure Investigation",
        "component_file": "frontend/src/components/forensics/IncidentTippingTimeline.jsx",
        "dom_selector": '[data-component-id="forensics-timeline"]',
        "description": "Chronological root-cause breakdown displaying synchronized dynamic telemetry tracks against baseline corridors.",
        "visual_elements": [
            {"name": "Synchronized Sensor Tracks", "visual_style": "Multi-strip SVG time-series tracks with baseline corridors"},
            {"name": "Breakout Marker", "visual_style": "Prominent colored badge at earliest sustained divergence point"},
            {"name": "Protective Trip Line", "visual_style": "Red vertical dashed line marking pump shutdown"}
        ],
        "operational_boundaries": {
            "debounce_samples_k": 3,
            "time_windows": ["15m", "30m", "1h", "4h", "24h"]
        },
        "failure_modes": {
            "intake_breakout_lead": "Intake pressure departs baseline first (t0), followed by motor temp spike (t1) and trip (t2)",
            "vibration_cascade": "Radial vibration departs baseline leading to mechanical unbalance"
        },
        "concept_kb_query": "root cause failure analysis timeline tipping points API RP 11S ISO 13373",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_forensics_timeline_data"
    },

    "eda-analysis-panel": {
        "id": "eda-analysis-panel",
        "title": "Exploratory Data Analysis (EDA) Distribution & Correlation Matrix",
        "aliases": [
            "eda-analysis-panel", "eda_analysis_panel", "data analysis",
            "correlation matrix", "eda panel", "exploratory data analysis"
        ],
        "dashboard_tab": "data-analysis",
        "governing_standards": "SPE Subsurface Analytics / Multivariate Telemetry Correlation",
        "component_file": "frontend/src/components/analysis/DataAnalysisView.jsx",
        "dom_selector": '[data-component-id="eda-analysis-panel"]',
        "description": "Comprehensive multivariate statistical distribution view featuring sensor histograms and correlation heatmaps.",
        "visual_elements": [
            {"name": "Correlation Heatmap Matrix", "visual_style": "2D color matrix of Pearson coefficients (-1.0 to +1.0)"},
            {"name": "Parameter Distribution Histograms", "visual_style": "Frequency bar charts with kernel density overlays"}
        ],
        "operational_boundaries": {
            "correlation_high_threshold": 0.85,
            "outlier_sigma_threshold": 3.0
        },
        "failure_modes": {
            "collinearity_breakdown": "Decoupling of expected physical correlations indicating fluid property change or sensor fault"
        },
        "concept_kb_query": "multivariate statistical analysis telemetry correlation heatmaps SPE",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "diagnostics-workbench": {
        "id": "diagnostics-workbench",
        "title": "Deep Diagnostics Multi-Model Workbench",
        "aliases": [
            "diagnostics-workbench", "diagnostics_workbench", "deep diagnostics",
            "workbench", "multi-model workbench", "deep diagnostics workbench"
        ],
        "dashboard_tab": "diagnostics",
        "component_file": "frontend/src/components/DiagnosticsWorkbench.jsx",
        "dom_selector": '[data-component-id="diagnostics-workbench"]',
        "governing_standards": "ISO 13373 Diagnostic Guidelines / API RP 11S Troubleshooting",
        "description": "Specialist engineering environment combining multi-model diagnostics and acoustic trip signatures.",
        "visual_elements": [
            {"name": "Model Consensus Gauge", "visual_style": "Circular gauge showing agreement percentage among models"},
            {"name": "Subsystem Breakdown Cards", "visual_style": "Cards for Hydraulic, Electrical, Thermal, Mechanical status"}
        ],
        "operational_boundaries": {
            "ensemble_agreement_pct": 75.0,
            "subsystem_degradation_limit": 65.0
        },
        "failure_modes": {
            "electrical_tracking": "High frequency noise on motor current with harmonic distortion",
            "gas_locking_signature": "Cyclic low-load motor current swings with zero head lift"
        },
        "concept_kb_query": "deep diagnostic workbench model ensemble troubleshooting ISO 13373",
        "proprietary_metric": True,
        "first_party_explanation": "Multi-model diagnostic workbench synthesizing 5 distinct physical and statistical classification engines.",
        "data_factory_ref": "src.services.chart_factories.build_operating_envelope_data"
    },

    "forensics-studio": {
        "id": "forensics-studio",
        "title": "Temporal Causation Forensics Studio",
        "aliases": [
            "forensics-studio", "forensics_studio", "forensic studio", "causation studio"
        ],
        "dashboard_tab": "forensics",
        "governing_standards": "ISO 13373 / API RP 11S Incident Forensics",
        "component_file": "frontend/src/components/forensics/ForensicsStudio.jsx",
        "dom_selector": '[data-component-id="forensics-studio"]',
        "description": "Deep incident investigation studio providing multi-window playback and baseline replay for historical trips.",
        "visual_elements": [
            {"name": "Playback Scrubber Bar", "visual_style": "Interactive time slider with event milestone markers"},
            {"name": "Replay Track Array", "visual_style": "Synchronized time tracks animating dynamic telemetry playback"}
        ],
        "operational_boundaries": {
            "incident_replay_speed": "1x to 10x",
            "max_investigation_window": "72h"
        },
        "failure_modes": {
            "catastrophic_trip": "Sudden motor shutdown with severe thermal or electrical trip code"
        },
        "concept_kb_query": "temporal causation forensic investigation trip reconstruction API RP 11S",
        "proprietary_metric": False,
        "data_factory_ref": "src.services.chart_factories.build_forensics_timeline_data"
    }
}


def get_chart_spec(chart_id: str, query: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolves chart spec by ID, alias, or query keyword."""
    if not chart_id and not query:
        return None

    target = (chart_id or "").strip().lower()
    if target in CHART_CATALOG:
        return CHART_CATALOG[target]

    for spec in CHART_CATALOG.values():
        if target in spec["aliases"]:
            return spec

    if query:
        q_lower = query.lower()
        for spec in CHART_CATALOG.values():
            for alias in spec["aliases"]:
                if alias in q_lower:
                    return spec
            if spec["title"].lower() in q_lower:
                return spec

    return None


def resolve_chart_from_title(title_or_query: str) -> Optional[Dict[str, Any]]:
    """
    Deterministically resolves a chart catalog spec from on-screen DOM header text,
    section titles, numbering prefixes, or natural language query phrases.
    """
    if not title_or_query:
        return None

    raw = title_or_query.strip().lower()

    # Normalize: strip leading numbering like "10. ", "7. ", "9. "
    cleaned = re.sub(r"^\d+\.\s*", "", raw)
    # Remove punctuation
    cleaned_no_punct = re.sub(r"[^\w\s-]", " ", cleaned).strip()

    # 1. Exact match on slug ID
    if cleaned_no_punct in CHART_CATALOG:
        return CHART_CATALOG[cleaned_no_punct]

    # 2. Match on title or aliases
    for wid, spec in CHART_CATALOG.items():
        if wid == cleaned_no_punct:
            return spec
        spec_title_clean = re.sub(r"[^\w\s-]", " ", spec["title"].lower()).strip()
        if cleaned_no_punct == spec_title_clean or spec_title_clean in cleaned_no_punct or cleaned_no_punct in spec_title_clean:
            return spec
        for alias in spec.get("aliases", []):
            alias_clean = re.sub(r"[^\w\s-]", " ", alias.lower()).strip()
            if cleaned_no_punct == alias_clean or alias_clean in cleaned_no_punct or cleaned_no_punct in alias_clean:
                return spec

    # 3. Keyword intersection scoring
    best_match = None
    best_score = 0
    words = set(cleaned_no_punct.split())
    for wid, spec in CHART_CATALOG.items():
        spec_words = set(re.sub(r"[^\w\s-]", " ", spec["title"].lower()).split())
        for alias in spec.get("aliases", []):
            spec_words.update(re.sub(r"[^\w\s-]", " ", alias.lower()).split())
        score = len(words.intersection(spec_words))
        if score > best_score and score >= 2:
            best_score = score
            best_match = spec

    return best_match
