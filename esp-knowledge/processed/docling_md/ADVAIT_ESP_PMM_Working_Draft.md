## ESP Pumps Operations, AI Modelling &amp; Assistant Development

Introduction deck for software-background AI interns joining the ADVAIT ESP Asset Performance Monitoring &amp; Management program

Equipment domain → data model → AI advisor

## Build useful AI on trustworthy plant data Intern outcome

## Electrical Submersible Pumps

Rick von Flatern Senior Editor

More than 90% of all producing oil wells require some form of artificial lift to increase the flow of fluids from wells when a reservoir no longer has sufficient energy to naturally produce at economic rates or to boost early production to improve financial performance. One of the most versatile and adaptable rtficial lit methods is eletric submersible umpi.ng

Deployed in an estimated 150,000 to 200,000 wells worldwide, electric submersible pumps (ESPs) consist of multiple centrifugal pump stages mounted in series within a housing mated to a submersible electric motor. These pumps are connected to surface controls and electric power by armor-protected cables. Surface electric drives power and control ESP systems, which are able to lift from 16 to 4,770 m³/d [100 to 30,000 bbl/d], a pump rate operation range that surpasses the performance of other pumptype artificial lift systems such as rod pumps, progressing cavity pumps and hydraulic lift.

## ESP Origins

In 1911, 18-year-old Russian engineer Armais Arutunoff invented the first electric motor that operated in water. He added a drill and a centrifugal pump to the motor, inventing what is now known as the electric submersible pump. Arutunoff immigrated to the US, where he founded Russian Electrical Dynamo of Arutunoff, or REDA. Electric submersible pumps are now operating in onshore and offshore fields throughout the world.

## Anatomy of an ESP System

<!-- image -->

Figure 1. Typical ESP configuration. Downhole ESP components include motor, protectors, pump sections, pump intakes, power cables, gashandling equipment and downhole sensors (not shown). Surface components include pump-control equipment such as variable-speed drives and an electric power supply.

manufactured and quantifies the relationship between pump horsepower, An ESP is a multistage centrifugal pump whose stages are stacked; the efficiency, flow rate and head relative to the operating flow rate. The pump

Electric submersible pump systems comprise both downhole and surface components (Figure 1). The overall length and diameter of ESP downhole equipment are designed based on the horsepower necessary to deliver the

operating requirements of the well and completion design dictate the num- recommended operating range is defined for each pump stage in the catalog ber of stages. Each stage contains a rotating impeller and stationary diffusers typically cast from high-nickel iron to minimize abrasion or corrosion damage. As well fuid flows into the first stage of the ESP, it passes through an impeller, and the fluid is centrifuged radially outward, gaining energy in the form of velocity. The centrifugal pump is driven by an induction motor that can attain operating speeds of more than 5,000 rpm when using a vari-

After it exits the impeller, the fluid is forced to make a sharp turn to enter the diffuser. As it travels through this section, the fluid is diffused, and its velocity is converted to pressure. The fluid, which now has a slightly higher pressure than when it entered the first stage, enters the next impeller and diffuser stage to repeat the process. The fluid passes through all stages of the pump, incrementally gaining pressure in each stage until it achieves a total developed head, or designated discharge pressure, and has sufficient energy to travel to the surface of the well.

A pump's operational performance is illustrated in its pump performance curve (Figure 2). A performance curve is generated for each pump

Oilfield Review 2015.

<!-- image -->

Figure 2. Pump performance curve. Such curves are generated to chart a pump's ability to displace fluids and to determine the number of pump stages required to achieve a desired production rate. The head capacity curve (blue) shows the amount of lift at a given flow rate. The horsepower requirements of the pump (red) across a range of flow capacities are derived from performance testing. The pump efficiency (green) is calculated from the head, flow capacity, fluid specific gravity and horsepower. The

## What interns need to deliver

Software capability only becomes valuable when it respects equipment physics and operating reality.

<!-- image -->

## 1

## Understand the ESP

Components and flow path Parameters that matter Normal operating envelope

## 2 Model the asset

Tag mapping and calculations Fault patterns and labels Health index and risk scoring

## 3 Build the assistant

Explain anomalies Recommend safe actions Generate work notes and reports

Project success metric: reduce avoidable downtime and turn operator experience into repeatable, auditable decision support.

## Why ESP exists in oil production

When reservoir energy is not enough, artificial lift supplies the missing pressure to move fluids to surface.

## ESP = electric motor + multistage centrifugal pump downhole

High-volume artificial lift for wells that cannot flow economically by natural reservoir pressure.

The system converts electrical energy into hydraulic head inside the well.

Typically selected for moderate-to-high liquid rate wells where rodpump or gas-lift economics are weak.

Software analogy: ESP is a cyber-physical production service with hard constraints

Source: Electrical Submersible Pumps Manual snippets; ESP Run Life Factors slide deck.

## ife e Factors

of an ESP is based on many factors

different and may have a combination of factors SP run life

will be determined by the limiting factor in the well

<!-- image -->

Centrilift

## ESP system anatomy

Separate the asset into surface power/control, downhole hydraulic string and well/reservoir context.

## Downhole assembly

Motor Protector / seal section Intake or gas separator Multistage pump Cable, check valve, drain valve Downhole gauges

<!-- image -->

## Surface system

Transformer VSD / switchboard Junction box Wellhead SCADA / RTU / historian Power quality monitoring

## How the ESP actually pumps

Each stage adds a small pressure increase; many stages stacked together create the total developed head.

<!-- image -->

This motion is caused by centrifugal force. The other motion moves in direction tangential to the outside diameter of the impeller. As a result of these two components is the actual direction of flow. The diffuser's function is to change the velocity energy into pressure energy.

There are two general types of design for submersible pumps. The smaller flow pumps are mostly of radial flow design. Figure 2-a shows such a stage configuration. In this type the impeller discharges the fluid in mostly a radial direction. As the pumps reach design flows of approximately 300 M3/d in the 400 series pumps and 550 M3 /d in the larger diameter pumps, the design changes to a mixed flow. Figure 2-b shows this configuration. The impeller in this stage design imparts a direction to the fluid that contains substantial axial direction as well as radial direction.

<!-- image -->

## ELECTRICAL SUBMERSIBLEPUMP (ESP)

CENTRIFUGALPUMPSTAGES

Figure 2-a Figure 2-b

<!-- image -->

In many of the pump designs, the impeller is free to float axially on the shaft and the individual impeller stage is absorbed on specially designed pads found on the diffuser. A specially designed thrust bearing contained in the seal section carries only the thrust of the pump shaft. This configuration is called a floating stage design. The benefit of this design is that many stages can be stacked together without having to fix the impellers axially on the shaft with precise alignment. As a result, pumps can be manufactured having hundreds of individual stages.

## Pump curve is the operating contract

## Rick von Flatern

The AI model must know whether the current point is inside the recommended operating range, not just whether values are high or low.

Senior Editor

More than 90% of all producing oil wells require some form of artificial lift to increase the flow of fluids from wells when a reservoir no longer has sufficient energy to naturally produce at economic rates or to boost early production to improve financial performance. One of the most versatile and adaptable artificial lift methods is electric submersible pumping.

Deployed in an estimated 150,000 to 200,000 wells worldwide, electric submersible pumps (ESPs) consist of multiple centrifugal pump stages mounted in series within a housing mated to a submersible electric motor. These pumps are connected to surface controls and electric power by armor-protected cables. Surface electric drives power and control ESP systems, which are able to lift from 16 to 4,770 m³/d [100 to 30,000 bbl/d], a pump rate operation range that surpasses the performance of other pumptype artificial lift systems such as rod pumps, progressing cavity pumps and hydraulic lift.

## ESP Origins

In 1911, 18-year-old Russian engineer Armais Arutunoff invented the first electric motor that operated in water. He added a drill and a centrifugal pump to the motor, inventing what is now known as the electric submersible pump. Arutunoff immigrated to the US, where he founded Russian Electrical Dynamo of Arutunoff, or REDA. Electric submersible pumps are now operating in onshore and offshore fields throughout the world.

## Anatomy of an ESP System

Electric submersible pump systems comprise both downhole and surface components (Figure 1). The overall length and diameter of ESP downhole equipment are designed based on the horsepower necessary to deliver the desired flow rate.

An ESP is a multistage centrifugal pump whose stages are stacked; the operating requirements of the well and completion design dictate the number of stages. Each stage contains a rotating impeller and stationary diffusers typically cast from high-nickel iron to minimize abrasion or corrosion damage. As well fluid flows into the first stage of the ESP, it passes through an impeller, and the fluid is centrifuged radially outward, gaining energy in the form of velocity. The centrifugal pump is driven by an induction motor able speed drive. that can attain operating speeds of more than 5,000 rpm when using a vari-

After it exits the impeller, the fluid is forced to make a sharp turn to enter the diffuser. As it travels through this section, the fluid is diffused, and its velocity is converted to pressure. The fluid, which now has a slightly higher pressure than when it entered the first stage, enters the next impeller and diffuser stage to repeat the process. The fluid passes through all stages of the pump, incrementally gaining pressure in each stage until it achieves a total developed head, or designated discharge pressure, and has sufficient energy to travel to the surface of the well.

A pump's operational performance is illustrated in its pump performanufactured and quantifies the relationship between pump horsepower, efficiency, flow rate and head relative to the operating flow rate. The pump recommended operating range is defined for each pump stage in the catalog

Figure 1. Typical ESP configuration. Downhole ESP components include motor, protectors, pump sections, pump intakes, power cables, gashandling equipment and downhole sensors (not shown). Surface components include pump-control equipment such as variable-speed drives and an electric power supply.

<!-- image -->

Figure 2. Pump performance curve. Such curves are generated to chart a pump's ability to displace fluids and to determine the number of pump stages required to achieve a desired production rate. The head capacity curve (blue) shows the amount of lift at a given flow rate. The horsepower

<!-- image -->

## What the curve tells us

Flow rate vs head: hydraulic capability Horsepower: motor load requirement Efficiency: best operating zone Operating point: actual production reality Left of range: downthrust/low-flow risk; right of range:

upthrust/high-flow risk

Core AI feature: deviation from design / BEP / ROR

06 / WELL HYDRAULICS Total Dynamic Head links well conditions to pump demand TDH is where production engineering meets sensor data.

## Total Dynamic Head - What I am not going to talk about !

rger

<!-- image -->

## TDH = vertical lift + friction + wellhead pressure

Net vertical lift changes with producing fluid level. Tubing friction rises with flow rate and fluid

Wellhead pressure/backpressure shifts the required discharge pressure.

properties.

Wrong density, water cut or GOR assumptions break the model.

Implementation note: create a TDH calculation service, keep every assumption visible, and compare calculated PDP/PIP with gauge values.

Schlumberger Private

## Minimum tag universe for useful monitoring

Interns must convert raw historian tags into physics-aware features and asset-level state.

| Domain        | Typical tags                                         | Why it matters                                       |
|---------------|------------------------------------------------------|------------------------------------------------------|
| Production    | Flow rate, WHP, choke, tubing/casing pressure        | Confirms production and hydraulic loading            |
| Downhole      | PIP, PDP, motor temp, intake temp, vibration         | Early signatures of gas, wear, blockage, overheating |
| Electrical    | Voltage, current, amps imbalance, frequency, leakage | Motor health and power quality                       |
| Design static | Pump model, stages, ROR, motor HP, cable, set depth  | Benchmark for deviation and safe envelope            |
| Context       | Water cut, GOR, API, BHT, PI, reservoir pressure     | Explains why same symptoms differ by well            |

## Operating envelope: monitor, explain, act

The application should distinguish 'needs watch' from 'stop now' with traceable logic.

<!-- image -->

<!-- image -->

## Run life is limited by the weakest operating factor

Failure is rarely 'one variable high'; it is usually a context -dependent combination.

## ommon Run Life Factors

pper Sizing of Equipment ll (BHT) Temperature ce Gas cosity rrosion nd / Foreign Material Production position Tendencies ctrical Failures erational Problems Age

<!-- image -->

## Key degradation drivers

Wrong sizing or operating outside ROR High bottom-hole / motor temperature Free gas and gas lock / gas interference Sand / solids abrasion and erosion Corrosion and scale deposition Electrical failures and power quality problems Operational cycling, frequent starts/stops

## Fault taxonomy for modelling and assistant logic

Start with failure modes operators recognize, then map them to symptoms and data signatures.

## Hydraulic

Gas interference Intake blockage Stage wear Tubing leak

## Mechanical

Broken shaft Bearing wear Vibration Misalignment

## Electrical

Overload Underload Phase imbalance Insulation leakage

## Thermal

Motor overheating Poor cooling High BHT High starts/stops

Use this taxonomy in the database, label schema, model output class names, exception workflows and assistant retrieval corpus.

Source: SPE troubleshooting guide and ESP troubleshooting matrix.

## Well / process

Reservoir pressure change Water cut shift Sand production Scale/corrosion

## Troubleshooting is pattern recognition with physics

The same symptom can mean different faults; use multiple parameters together.

<!-- image -->

## Example pattern families

Reduced/no flow + rising PIP + high temperature: blockage, broken shaft or shutdown-at-surface

Erratic amps and pressure with reduced flow: free gas at pump intake.

scenarios.

Reduced flow + elevated amps + reduced discharge pressure: possible stage wear.

Increasing frequency should raise flow, WHP, amps, PDP and temperature unless constrained.

12 / VIBRATION &amp; ELECTRICAL High-value fault signals: vibration, current, temperature For machine learning, high-frequency mechanical/electrical features can detect faults earlier than slow process tags.

<!-- image -->

Contents lists available at ScienceDirect

Ocean Engineering

journal homepage: www.elsevier.com/locate/oceaneng

Electric submersible pump vibration analysis under several operational conditions for vibration fault differential diagnosis

Galdir Regesa, , Marcio Fontana a, Marcos Ribeiro b, Tiago Silvaa, Odilon Abreua, Ricardo Reisa, Leizer Schnitmana

Universidade Federal da Bahia, Mechatronics Program (PPGM), CTAI, Rua Prof. Aristides Novis, 02, Federação, Salvador/BA, CEP 40210-630, Brazil b Petrobras Research and Development Center (CENPES/PETROBRAS), Av. Horácio Macedo, 950, Cidade Universitária, Ilha do Fundão, Rio de Janeiro/RJ, CEP 21941-915, Brazil

## ARTICLE INFO

ABSTRACT

Keywords: Vibratory behavior Synchronous frequency variation Differential diagnosis Correlation analysis Temperature influence An Electric Submersible Pump (ESP) vibration analysis was performed, considering different wear states and operational conditions. The pumps were tested with different fluid viscosities, operating points, and speeds to evaluate their vibration behavior, with the aim of providing characteristics for non-invasive differential vibration diagnosis. A specific frequency spectrum estimation method is described, focusing on the extraction of frequency component vibration amplitudes used in the petroleum industry-standard vibration analysis. A time-interval definition procedure was proposed to reduce signal amplitude losses due to variation of synchronous operating frequency. The results indicate that the frequency component peak amplitudes can be more accurately identified during synchronous frequency variation by the proposed method than by typical estimation methods. In this study, an ESP vibration differential diagnosis was achieved by analyzing relations between orders of the synchronous frequency, and by distinguishing that the synchronous component amplitude rose approximately proportionally to the square of the rotating speed; this differentiates unbalance fault from a bent shaft or a misalignment. A correlation matrix analysis is provided to demonstrate that variation in the fluid-temperature difference between the pump intake and discharge is related to the vibration amplitude variation in a pump with a vibration fault.

## 1. Introduction

Electrical submersible pumps (ESPs) are the second most common artificial lifting method applied worldwide (Liang et al., 2015), deployed in, it is estimated, 150,000 to 200,000 wells (Flatern, 2015). Electrical submersible pumps account for approximately 10% of the world's crude oil production (Takacs, 2017). These systems are ideally suited to pumping high volumes at high pressure, and the petroleum industry applies the method to pump petroleum at a high flow rate in offshore applications.

housing. For subsea systems, the output motor power may be higher than 1000 hp. The structure can reach more than 40 m in length, and the pu d  - s   id containing abrasives (Minette et al., 2016).

An electrical submersible pump is composed of several smalldias   t (si  l ss  sially, with an operational frequency range varying from 30 Hz to 60 Hz. In a submerged ESP installation, a multistage centrifugal pump is coupled to a magnetic induction motor using a protector seal assembly filled with an insulating fluid that is heavier than water. The electric motor is cooled by the oil-well fluids that pass through the motor The installation and intervention costs of ESP-based pumping systems are usually higher than those of other elevation methods, particularly in the case of deep-sea, underwater wells (Ribeiro et al., 2005). In addition to the high costs of installation and intervention, faults in this equipment usually cause significant production losses since they typically operate in high-production petroleum wells. A careful evaluation of ESP systems before installation is critical to prevent premature operational failure.

The risk of vibration problems is increased in equipment such as ESP systems due to the difference between its considerable length and its small axial diameter. The factory acceptance evaluation process of the ESP system for fault diagnosis includes an expert vibration analysis of collected accelerometer signals during a test well operation, following

* Corresponding author.

E-mail address: galdir.junior@ufba.br(G. Reges).

https://doi.org/10.1016/j.oceaneng.2020.108249

Received 17 April 2020; Received in revised form 15 October 2020; Accepted 17 October 2020 0029-8018/© 2020 Elsevier Ltd. All rights reserved.

Source: ESP vibration analysis paper and uploaded troubleshooting guides.

<!-- image -->

## Feature direction

Order tracking around shaft speed: 1X, 2X, harmonics and sidebands.

Current signature features: imbalance, THD proxy, underload/overload, leakage trend.

RMS, peak, crest factor, kurtosis and band energy from vibration windows.

Temperature rise vs load and cooling flow as an early thermal risk indicator.

ML caution: do not train only on 'pretty' data; include startups, trips and sensor dropouts

## ADVAIT ESP-PMM data pipeline

The backend must preserve raw evidence while publishing clean features for models and assistant reasoning.

<!-- image -->

Critical principle: lineage from recommendation back to raw tags, design data and calculation version is non-negotiable.

## Feature engineering backlog

A strong ESP model starts with robust features before chasing complex algorithms.

## Hydraulic calculated

ΔPpump = PDP - PIP Head = ΔP / gradient TDH vs pump curve PIP drawdown vs IPR

## Thermal/electrical

Motor temp margin Current vs frequency Underload/overload events Voltage/current imbalance

## Operating behavior

Frequency-normalized flow Start/stop count Time outside ROR Trend slopes and rate of change

## Data quality

Sensor stale flag Dropout interpolation Unit conversion confidence Tag binding health

## AI modelling workstreams

Build models in layers: rules for transparency, ML for prediction, retrieval for assistant context.

| Layer                | Purpose                                 | Candidate methods                                    | Intern tasks                              |
|----------------------|-----------------------------------------|------------------------------------------------------|-------------------------------------------|
| Rule engine          | Known physics and operating limits      | Thresholds, state machines, pump-curve checks        | Encode ROR, TDH and trip logic            |
| Anomaly detection    | Detect abnormal behavior without labels | Isolation Forest, autoencoder, robust z-score        | Build baseline by well/pump type          |
| Failure prediction   | Estimate probability and lead time      | Gradient boosting, temporal CNN/LSTM, survival model | Create labels and evaluate lead time      |
| Fault classification | Identify likely root cause              | XGBoost, random forest, sequence classifier          | Map symptoms to fault taxonomy            |
| RAG assistant        | Explain and recommend                   | Retriever + tool calling + evidence cards            | Build prompt, citations, action templates |

## Prediction without labels is theatre

Define the exact event, prediction horizon and business metric before model training.

## Event labels

Trip event Failure pull/workover Operating exception Avoided failure / intervention Root cause after teardown

## Time horizons

Next 1 hour: trip risk Next 24 hours: severe exception Next 7 -14 days: failure risk Remaining Useful Life estimate

## Metrics

Lead time before failure False alarm rate per well-month Precision on critical alarms Production deferment avoided Operator action adoption

The Siemens ESP pilot reported failure probability forecasting 12 days before an actual failure; use that as an ambition, not as a guaranteed benchmark.

Source: Applying Artificial Intelligence to Optimize Oil and Gas Production, OTC-29384-MS.

## ESP AI Assistant: what it must do

The assistant is not a chatbot; it is an evidence-backed operational copilot.

## Observe

Read asset state, data quality, recent trends and active exceptions.

## Diagnose

Match multi-signal patterns to likely failure modes and confidence.

## Explain

## Recommend

Show evidence: tag movements, calculations, design envelope and source procedure.

Give safe next steps: monitor, adjust, inspect, escalate or plan intervention.

Every answer should include confidence, evidence and escalation criteria

## Document

Generate shift notes, exception reports and model-feedback labels.

## Guardrails for industrial AI

Wrong advice can damage equipment or stop production. Build controls from day one.

## Assistant must never

Invent missing sensor values

constraints

Recommend unsafe speed changes without

Suppress alarms because model confidence is

Hide uncertainty or source evidence

low

Override operator/company procedures

## Assistant must always

State confidence and data quality Link recommendation to tags/calculations Offer escalation route Create audit trail Support human approval before action

Industrial AI = bounded autonomy + human accountability

## Implementation backlog for interns

Each task should create reusable product capability, not isolated notebooks.

| Work item           | Output                                        | Definition of done                                                     |
|---------------------|-----------------------------------------------|------------------------------------------------------------------------|
| Asset schema        | ESP asset definition tables + sample data     | Can configure well, pump, motor, protector, cable, VSD and design case |
| Tag binding         | Historian tag dictionary + unit normalization | Raw tags map to canonical ESP variables with data-quality flags        |
| Calculation service | TDH, ΔP, head, ROR deviation, temp margins    | Values reproducible and versioned with assumptions                     |
| Fault rules         | Rule cards for 10 - 15 common patterns        | Each rule has trigger, evidence, severity and recommended action       |
| ML baseline         | Anomaly and failure-risk prototype            | Backtest notebook + API-ready scoring function                         |
| Assistant prototype | RAG + tool calling over ESP knowledge base    | Answers cite evidence and produce action-ready summary                 |

## Suggested 6-week onboarding execution plan

Ship a vertical slice that can be demonstrated with synthetic + historian-ready data.

<!-- image -->

Demo target: select one ESP well → show current operating point → identify anomaly → explain likely cause → generate recommended action note.

## Intern deliverables and quality bar

Good interns will produce product-grade assets, not just experiments.

## Data

Canonical variables Sample datasets Data quality checks

## Engineering

Calculation APIs Rule engine Test cases AI

Baseline models Evaluation reports Prompt/RAG harness

Quality bar: reproducible, versioned, explainable, testable and demo-ready

## Product

Screens/demo flow Exception workflow User documentation

## Recommended reading map

Use the sources below as the knowledge backbone for intern onboarding and RAG ingestion.

| Topic                         | Primary internal/public source                                             |
|-------------------------------|----------------------------------------------------------------------------|
| ESP basics and configuration  | SLB Defining Series: Electrical Submersible Pumps; ESP Manual introduction |
| Components                    | ESP Components Equipment Description; ESP system training decks            |
| Design and TDH                | Pressure-gradient curves and ESP Total Dynamic Head design notes           |
| Operations and run life       | ESP Run Life Factors; ESP Basic Design and Operational Factors             |
| Troubleshooting               | SPE-199091-MS troubleshooting guide; combined troubleshooting matrix       |
| AI and predictive maintenance | OTC-29384-MS Siemens AI use case; vibration analysis paper                 |
| Assistant build requirements  | ADVAIT ESP-PMM project context and current module requirements             |

## Intern mission

Turn ESP data into actionable intelligence -with physics, evidence and operational discipline built in.

## Pressure gradient curve

<!-- image -->

Best first demo: one well, one current operating point, one likely fault, one traceable recommendation.