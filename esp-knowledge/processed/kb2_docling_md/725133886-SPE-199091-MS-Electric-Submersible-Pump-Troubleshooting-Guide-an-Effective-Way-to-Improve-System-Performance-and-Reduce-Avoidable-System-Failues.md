## SPE-199091-MS

## Electric Submersible Pump Troubleshooting Guide, an Effective Way to Improve System Performance and Reduce Avoidable System Failures

Walter Nunez and Jessica Del Pino, OXY - Occidental de Colombia; Sebastian Gomez, Douglas Rosales, Juan Puentes, and Hamilton Rivera, Baker Hughes

Copyright 2020, Society of Petroleum Engineers

This paper was prepared for presentation at the SPE Latin American and Caribbean Petroleum Engineering Conference originally scheduled to be held in Bogota, Colombia, 17 - 19 March 2020. Due to COVID-19 the physical event was postponed until 27 - 31 July 2020 and was changed to a virtual event. The official proceedings were published online on 20 July 2020.

This paper was selected for presentation by an SPE program committee following review of information contained in an abstract submitted by the author(s). Contents of the paper have not been reviewed by the Society of Petroleum Engineers and are subject to correction by the author(s). The material does not necessarily reflect any position of the Society of Petroleum Engineers, its officers, or members. Electronic reproduction, distribution, or storage of any part of this paper without the written consent of the Society of Petroleum Engineers is prohibited. Permission to reproduce in print is restricted to an abstract of not more than 300 words; illustrations may not be copied. The abstract must contain conspicuous acknowledgment of SPE copyright.

## Abstract

The Oil and Gas industry in recent years have been a great challenge for operators and aervice companies as well. This situation resulted in great opportunities to find efficiencies that can enhancement production, avoid down times and optimize operation in Electric Submersible Pump Systems (ESP). Keeping this on mind, one of the main drivers is implement procedures that can extent ESP run life, and one of the key challenges is to identify any trouble that can impact ESP performance timely so it can implement solutions to avoid failures.

The main objective was to develop a troubleshooting manual that could be used for any engineer to identify likely conditions that could be affecting negatively ESP performance and to implement solutions to minimize failure or damage beyond repair in ESP equipment.

A jointly team composed by the operator and the service company developed a troubleshooting manual to the proper identification of likely conditions that could be impacting the production and performance of ESP systems. This was achieved using monitoring information, tear down evidence, setting configuration and building a database with all the information in order to group similar cases to identify the best ways to respond to any anomaly in ESP behavior.

This procedure was implemented in the field that have an average of 450 active wells with 93% being ESP systems, by socializing it with all the parties that participate in ESP troubleshooting to guarantee a proper handling of any occurrence.

The main purpose of the creation of this procedure was to avoid failures associated with ESP operation conditions that could result in early failure; this is measured with the Failure Index (IF) that means the number of average interventions in an ESP field related to the average number of active wells in the same period.

The implementation resulted in awareness in all the personnel that when best practices are followed there are better chances of field KPI improvements and savings, in this case the Failure Index of the field was reduced from 0.4 to 0.18 attributed to technology and best practices implementation as well.

<!-- image -->

This paper aims to present the most relevant analyzed cases, the procedures implemented and the results in FI after implementation as well of recommendations to any party interested in implement similar projects in their operations.

## Summary

In  recent  years  the  oil  and  gas  industry  has  been  a  major  challenge  for  operators  and  also  for  service companies.  This  situation  resulted  in  great  opportunities  to  find  efficiencies  that  can  enhancement production, avoid downtime and optimize the operation of electro-submersible pumping systems (ESP). With this in mind, one of the main actions is to implement procedures that can extend the useful life of the ESP, and one of the key challenges is to identify any problem that may affect the performance of the ESP in time, so that solutions that avoid failures can be implemented.

The main objective was to develop a troubleshooting manual that could be used for any engineer to identify likely conditions that might be adversely affecting ESP performance and implement solutions to minimize failures or damage beyond repair on equipment.

A joint team, composed by the operator and the service company, developed a troubleshooting manual for the proper identification of the likely conditions that could be affecting the production and performance of ESP systems. This was achieved using monitoring information and evidence of the failure analysis, to set up the configuration and build a database with all the information to group similar cases that allow identifying the best ways to take action to any anomalies in ESP behavior.

This procedure was implemented in the field that has an average of 450 active wells with 93% of ESP systems, socializing it with all the parties involved in ESP problems solving to ensure proper handling of any event.

The main objective of drafting this manual is to avoid failures associated with ESP operating conditions that could result in an early failure, this is measured by the Failure Index (IF) which means the number of average interventions in a ESP field related to the average number of active wells in the same period.

The implementation resulted in awareness among all personnel to follow best practices according to the manual developed, ensuring possibilities of improving KPIs, eliminating downtime and consequently obtaining savings in the field. The field failure rate was reduced from 60% to a value of 0.18 attributed to the implementation of technology and also to the implementation of these best practices.

This document aims to present the most relevant analyzed cases, the procedures implemented and the results in FI after implementation, as well as guidelines to any party interested in implementing similar projects in their operations.

## Introduction

Caño Limón is an oil production field, located in Northwestern Colombia, in the Llanos Basin. It currently has 450 active wells with electro-submersible equipment installed, handling between 50 BFPD and 30,000 BFPD in conditions of high sand production and high water cuts. These characteristics represent a challenge for companies that supply ESP. Among the major operational challenges that Caño Limón has faced in ESP lifting systems, it is to increase the Run Life of ESP equipment and their reliability. The operator has defined several strategies in order to reduce the failure rate. One of these strategies was focused on the adequate and prompt diagnosis of the operational condition of the equipment in order to make appropriate decisions regarding the operation of the equipment, this task falls to the joint work of the operator maintenance team and the specialists of the companies that provide ESP systems.

Due to the great diversity of well flows that exist in the field and the conditions of the applications such as: depth, sand production, water cuting, gas and temperature it becomes difficult to have a standard procedure that covers all conditions when diagnosing a problem in each well. Under this scenario it is possible to generate misdiagnoses that lead to making inappropriate decisions and therefore to increase operating costs and even generate unnecessary well interventions.

## Current situation and challenges

During the operation of the ESP artificial lifting system, several working groups from both the operating company and the ESP equipment suppliers companies are involved, among the main groups are:

- Production group
- Artificial lifting group
- Maintenance group
- Monitoring group

With the learning curve that has been developed throughout the life of the field, it has been identified that there is no standardized methodology to be able to diagnose in an easy and accurate way the possible failures of electrosumerible pumping systems. Improvement opportunities have been identified that could help optimize the accuracy of diagnoses. Some examples could be misdiagnoses in the behavior of wells with ESP or long periods in their definition and non-effective communication between the groups involved in the operation.

## Methodology

Within the monitoring work of ESP equipment, situations arise in which a correct management of the information of the operating parameters, alarm programming and creation of standards for the response to certain behaviors of the equipment may result in increased the system's useful lifespan. In view of these conditions, it was decided to document most of the conditions that may arise during the operation of the systems and share it with the personnel in charge of the operation and monitoring of them, in order to provide the necessary tools for an adequate response to the conditions presented.

Next,  we  will  present  the  documented  conditions,  their  main  characteristics,  the  tests  that  can  be performed in order to confirm the condition, as well as possible solutions to them.

## 1. Fluid recirculation

It occurs as a result of holes at some point in the production pipe, corrosion, ″jetting″ , severe wear on the gaskets of the production pipe or in applications with ″Y-tool″ due to dismantling of ″ the blanking plug″ . The parameters generally behave as follows:

| Parameter                     | Effect             |
|-------------------------------|--------------------|
| PI (Pump intake pressure)     | Increases          |
| PdP (Pump discharge pressure) | Decreases          |
| Q (Surface Flow)              | Decreases          |
| WHP (Wellhead Pressure)       | Decreases / Stable |
| M. Temp (Motor temperature)   | Increases          |
| M. Amps (Motor Current)       | Decreases / Stable |

Figure 1-General behavior of recirculation equipment variables. Source Occidental Colombia

<!-- image -->

Figure 2 shows the evidence after the extraction of the Bottomhole equipment.

Figure 2-Evidence of extraction of Bottomhole equipment with drilling. Source Baker Hughes.

<!-- image -->

## Recommended tests

Pipe integrity test by closing the wellhead valve verifying the stability in the pressure data. In wells where there is a nipplesilla, run the tool through slickline , inject fluid and check if the pressure is maintained up to that point. As a precautionary measure, it is recommended to avoid operating equipment with fluid velocities through  the  annular  pipe-casing  above  12  ft  /  s,  especially  in  applications  where  erosion  or  corrosion problems have been evidenced. Additionally it is recommended to avoid excessive frequency increase.

Possible solutions: Once this condition arises, it is necessary to perform the well intervention to make a pump change ( Well Service - WS). To avoid recurrence, a strategy for the review and inspection of pipe quality, "blanking Plu"g settlement tests, a strategy for corrosion management and avoiding prolonged pipe reuse.

## 2. Worn pump

It is presented as a consequence of wear associated with the useful life of the equipment, by deposit of scales, asphaltens, paraffins or by wear of the stages associated with sand production. The parameters generally behave as follows:

Figure 3 shows the general behavior of the equipment variables in a worn pump event:

| Parameter                     | Effect                  |
|-------------------------------|-------------------------|
| PI (Pump intake pressure)     | Increases               |
| PdP (Pump discharge pressure) | Decreases               |
| Q (Surface Flow)              | Progressively decreases |
| WHP (Wellhead Pressure)       | Decreases               |
| M. Temp (Motor temperature)   | Increases               |
| M. Amps (Motor current)       | Decreases               |

Figure 3-General behavior of the equipment variables in a worn pump event. Source Occidental Colombia

<!-- image -->

Figure 4, shows the evidence found during disassembly of the bottomhole equipment, where severe erosive wear and / or loss of material can be seen. This condition generates accelerated loss of efficiency in the pump triggering a drop in the production rate.

Recommended tests: Not applicable.

Figure 4-Evidence found during disassembly of the Bottomhole equipment, where severe erosive wear, loss of material can be seen. Source Baker Hughes.

<!-- image -->

It is advisable not to operate the equipment with frequencies greater than 60 Hz in wells with high sand content.

Possible solutions: Once this condition arises it is necessary to perform the well service intervention. To avoid recurrence, a strategy is needed to study a redesign considering the origin of the fault, for example: Scale, abrasive sand, formation fines or other solids such as paraffins and / or asphaltenes. Additionally, in these redesigns it is necessary to consider the frequency of operation of the ESP equipment and evaluate the installation of additional controls to the ESP such as a sand control system.

## 3. Broken shaft

It occurs as a result of catastrophic damage to the pump shaft caused by restriction of rotation, fatigue, back spin, wear due to high life or defects in the material. The parameters generally behave as follows:

Figure 5 shows the trend presented by the equipment parameters during this condition:

| Parameter                     | Effect                                                                                                                         |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| PI (Pump intake pressure)     | Increases                                                                                                                      |
| PdP (Pump discharge pressure) | Decreases                                                                                                                      |
| Q (Surface Flow)              | Decrease / Absence of flow                                                                                                     |
| WHP (Wellhead Pressure)       | Decreases                                                                                                                      |
| M. Temp (Motor temperature)   | Increases                                                                                                                      |
| M. Amps (Motor current)       | It decreases significantly, A reference in most cases would be for the field ≈ 30%, but may vary according to the application. |

Figure 5-Trend presented by the equipment parameters during broken shaft condition. Source Occidental Colombia

<!-- image -->

Figure 6 shows the evidence found during the disassembly of the equipment:

Figure 6-Evidence found during disassembly of equipment with broken shaft. Source Baker Hughes.

<!-- image -->

In wells where the motor load is low, the current drop may become imperceptible. In case of having a sensor, the hypothesis can be validated using the ESP pump intake pressure variable (PIP for its acronym in English).

Possible solutions: Once this condition arises, it is necessary to do the well intervention to do a well service work. To avoid the recurrence of faults, it would be necessary to apply equipment operation strategies such as: Controlled starting plan, a controlled stopping plan, proper configuration of control parameters in the variable speed drive (VSD) for its acronym in English, a proper handling of the "Drawdown" and control strategy for the production of solids.

## 4. Well sanding (pump plugging)

This condition occurs when the high sand production from the formation results in the decantation of the sand along the well until it causes a partial or total obstruction of the producer interval or causes plugging in the ESP pump, restricting the movement of fluid from them. Depending on the severity, several production pipe joints can be found above the discharge of plugged ESP equipment, which may require fishing jobs to recover ESP system. The parameters generally behave as follows:

La figure 7, It shows the trend in the operating parameters during this condition:

| Parameter                     | Effect                                        |
|-------------------------------|-----------------------------------------------|
| PI (Pump intake pressure)     | Increases                                     |
| PdP (Pump discharge pressure) | Decreases                                     |
| Q (Surface Flow)              | Decrease / Absence of flow / Flow fluctuation |
| WHP (Wellhead Pressure)       | Decreases                                     |
| M. Temp (Motor temperature)   | Increases                                     |
| M. Amps (Motor current)       | Decreases                                     |

Figure 7-Tendency in the operating parameters of the ESP equipment with sanding in rigs. Source Occidental Colombia

<!-- image -->

Figure 8, shows the typical evidence found during the extraction and subsequent disassembly of the Bottomhole equipment.

Figure 8-Typical evidence found in the disassembly of the deep well equipment with sandblasted well. Source Baker Hughes.

<!-- image -->

Not all cases show evidence of sand in the pump, since it can be removed during the work being done to try to start the bottomhole equipment, for example, the recirculation of fluid in the well.

One way to validate the hypothesis is by injecting water through the anular to verify if the well receives the fluid or if, on the contrary, it is filled which infers a possible sandblasting of the producer interval.

Possible solutions: In wells considered critical, conservative acceleration ramps are recommended even from  startup.  The  ESP  service  provider  suggests  a  rate  of  100  psi/day. "Drawdow"n administration  is required and the use of high volume flow stages is suggested.

## 5. Blocking by gas

Abnormal behavior of the ESP equipment due to the presence of gas, depending on the amount of gas at the pump intake, total absence of surface flow may occur due to blockage. The parameters generally behave as follows:

Figure 9 shows a typical gas blocking trend.

| Parameter                     | Effect                                        |
|-------------------------------|-----------------------------------------------|
| PI (Pump intake pressure)     | Increases                                     |
| PdP (Pump discharge pressure) | Decreases                                     |
| Q (Surface Flow)              | Decrease / Absence of flow / Flow fluctuation |
| WHP (Wellhead Pressure)       | Decreases                                     |
| M. Temp (Motor temperature)   | Increases                                     |
| M. Amps (Motor current)       | Decreases                                     |

Figure 9-Typical gas blocking trend. Source Occidental Colombia

<!-- image -->

It is advisable to check the parameters and perform simulations in order to evaluate the selection of the type of pump admision (intake, single gas separator, double separator or triple separator), gas handling pumps or other technologies focused on mitigating this type of condition

Possible solutions: When there is a gas lock, the following maneuvers can be performed in order to degas the well:

- Crash the well until the fluid level is restored.

- Perform gas purging procedure by rapidly decreasing the turning speed of the equipment, until the pump is unable to defeat the fluid head and thus a "flushin"g effect occurs (fluid traveling in the opposite direction unlocking the pump). This maneuver must be carried out having taken every precaution and does not apply in case there is a check valve in the well.
- If the blockage continues, it can be considered to shut down the ESP equipment to wait for the pressures to be restored and this displaces the gas bubble, once the bubble is released, starting the equipment under the previous operating conditions.
- If the blockage continues, the use of a fluid recirculation may be considered.
- For the following runs, consider the design and dimensioning of the ESP equipment to deepen the equipment to ensure greater PIP and to use configurations more adjusted to the amount of free gas present in the pump. For example: "tapere"d configuration.
- Frequency increases and decreases should be calculated to keep the pressure rate over time below 25 psi/min and avoid decompression damage to the cable.
- Bottomhole  technologies  can  be  combined  with  surface  technologies  such  as  PID  controls  or hybrid controls that will help prevent the well from gasifying; and once gasified to unlock the ESP equipment.

## 6. Loss of sensor data

Sudden loss of sensor data during operation. It usually occurs when equipment with low insulation or a ground phase is presented. The parameters usually behave as follows:

| Parameter                     | Effect                   |
|-------------------------------|--------------------------|
| PI (Pump intake pressure)     | Frozen reading / No data |
| PdP (Pump discharge pressure) | Frozen reading / No data |
| Q (Surface Flow)              | Does not change          |
| WHP (Wellhead Pressure)       | Does not change          |
| M. Temp (Motor temperature)   | Frozen reading / No data |
| M. Amps (Motor current)       | Frozen reading / No data |

Data loss may occur as a result of some situations, the most common are:

- Power cable hits (bottom or surface) that affect the insulation of the power cable and consequently the transmission of sensor data to the surface is lost.
- Problems with the surface electronic components of the ESP system Bottomhole sensor.
- Well  fluid  Migration  through  the  sensor  affecting  the  dielectric  properties  of  the  oil.  In  this particular case, sensor failure occurs and consequently engine failure. Migration can also occur due to mechanical seal failures due to high life among others. Figure 10 shows a sensor data loss event.
- Failure of insulation penetrators and surface connectors or gaskets.

Figure 10-Sensor data loss. Source Occidental Colombia

<!-- image -->

Figure 11 shows the typical evidence found during pulling and tear down .

Figure 11-Typical events found during pulling and tear down as a result of migration of well fluid through the sensor. Source Baker Hughes.

<!-- image -->

In wells with sensor data loss, it is recommended to avoid to the maximum vary the operating conditions of the equipment, such as frequency changes and shutdowns, in general not to make changes in the operating conditions. It is also advisable to avoid electric " stres"s conditions and overload the motor beyond 60% load. If absolutely necessary, the acceleration ramps must be carried out in a conservative manner in order to minimize electrical " stres"s on the system.

Possible solutions: First, the origin of the electrical fault must be identified, since, in the event that it is located on the surface it is repairable, in the event that the fault is located in the bottom once this condition occurs, it is necessary to make the intervention of well to do a well service job. Depending on the location of the fault in depth with an intervention taken from the string to the point of failure and cable repair is sufficient.

## 7. Reverse Spin

It is presented by inadequate identification / connection of the motor phases or by setting the direction of rotation in the drive. The parameters usually behave as follows:

| Parameter                     | Effect    |
|-------------------------------|-----------|
| PI (Pump intake pressure)     | Increases |
| PdP (Pump discharge pressure) | Decreases |
| Q (Surface Flow)              | Decreases |
| WHP (Wellhead Pressure)       | Decreases |
| M. Temp (Motor temperature)   | Increases |
| M. Amps (Motor current)       | Decreases |

In some applications it is difficult to determine this condition as the fluctuation of the parameters is minimal.

Possible solutions: Once the condition is identified, the correct surface connection and the identification of the phases must be verified from the moment of installation, it is recommended to use the color code indicated in the procedures for this purpose. Additionally, whenever a surface intervention is carried out, it must be verified before disconnection that the phases are properly marked in such a way that it is easy to reconnect them.

## 8. Power supply

If the primary source of voltage supply fluctuates, the current will oscillate in an attempt to meet the pump's power demand. The parameters usually behave as follows:

| Parameter               | Effect    |
|-------------------------|-----------|
| Voltage Unbalance Trips | Increases |
| Current Unbalance Trips | Increases |
| O-xing trips            | Increases |
| Power ridethrough trips | Increases |
| OV/UV Trips             | Increases |
| Convertor fault trips   | Increases |

Possible solutions: It is recommended to check if the power supply is given by mains or self-generation, in case it is by self-generation, factors such as synchronisms, generator load and power factor should be checked.

## 9. Closed surface valve

The  closing  of  the  surface  valve  during  the  operation  of  the  equipment  generates  a  behavior  of  the Bottomhole variables with the following characteristics:

| Parameter                     | Effect               |
|-------------------------------|----------------------|
| PI (Pump intake pressure)     | Increases            |
| PdP (Pump discharge pressure) | Increases            |
| Q (Surface Flow)              | Decrease or no fluid |
| WHP (Wellhead Pressure)       | Increases            |
| M. Temp (Motor temperature)   | Increases            |
| M. Amps (Motor current)       | Decreases            |

La Figure 12 shows the operating trends of an event of this magnitude:

Figure 12-Trends of operation of an event with closed surface valve. Source Occidental Colombia

<!-- image -->

Care should be taken with this condition for eventual operation in severe "downthrus"t.

Possible solutions: Validate that the surface line has the valves open. It is recommended to use a labeling of the valves when surface work is done, this to guarantee their correct position during operating conditions.

## 10. Closed Safety valve

The closing of the safety valve during the operation of the equipment generates the following behavior:

| Parameter                     | Effect    |
|-------------------------------|-----------|
| PI (Pump intake pressure)     | Increases |
| PdP (Pump discharge pressure) | Increases |
| Q (Surface Flow)              | Decreases |
| WHP (Wellhead Pressure)       | Increases |
| M. Temp (Motor temperature)   | Increases |
| M. Amps (Motor current)       | Decreases |

Possible Solutions: Validate that the surface line has the safety valves open. It is recommended to use a labeling of the valves when surface work is done, this to guarantee their correct position during operating conditions.

A consolidated summary of the effect on the operational parameters is presented according to the cases studied

Table 1-Summary of Effects on Operating Parameters and Recommendations.

<!-- image -->

## Additional Conditions to consider during the operation

Not all the operating conditions observed in the field meet the conditions mentioned in the previous section, for this reason, the following table was prepared that relates the possible conditions that adjust to a change in some of the operating variables, in this way it is easier to make a diagnosis from the change of each of the following parameters:

Table 2-Well Condition Diagnostic Table.

| Parameter Condition             | Equation                                                                         | Indicates                                                                 | Condition                                                                                              |
|---------------------------------|----------------------------------------------------------------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Discharge pressure (high)       | Head Pressure + Gravity + Friction                                               | Increase in pressure on the pump or increase in fluid density on the pump | • Closed well • Block over the pump Increase in water cut Extremely high flow • Scaled pipe            |
| Discharge Pressure (Low)        | Head Pressure + Gravity + Friction                                               | Increase in pressure on the pump or increase in fluid density on the pump | Low flow on the line Hole in Pipe Gas Increase in the Pipeline                                         |
| Intake pressure (high)          | Pd, Pump Parameters (Hz, # Stages, Q, wear, viscosity, gas) input flow (Pr, PI). | High Pd or Pump does not provide dP                                       | • High Pd • Wear • Recirculation • High Gas • High viscosity • Scaled Bomb Broken Shaft                |
| Intake Pressure (Low)           | Pd, Pump Parameters (Hz, # Stages, Q, wear, viscosity, gas) input flow (Pr, PI). | High dP Pump Poor reservoir Intake flow or support pressure               | • High frequency • Pr decrement • PI decrease                                                          |
| Pump- Discharge Pressure (High) | Pump Parameters and Fluid Speed                                                  | Low flow or high frequency                                                | • Closed well • Low Flow                                                                               |
| Pump- Discharge Pressure (Low)  | Pump Parameters and Fluid Speed                                                  | High flow, low frequency or pump stages                                   | • Broken shaft • Recirculation • Low frequency • Lock on Pump intake                                   |
| Motor Temperature (High)        | Cooling and RPM                                                                  | Low or little flow through the engine                                     | • High Viscosity • Gas • Low flow or pump with zero head • Recirculation • Well Closure • Broken shaft |
| Vibration                       | “Shake” System                                                                   | Imbalance, Critical Frequency, solids, gas, heating.                      | • Solids • Gas • Pump wear Excessive Temperature Critical Frequency                                    |
| Current (high)                  | Flow                                                                             | Resistance                                                                | • Short Circuit (surface or botton Excessive Temperature • Noise data                                  |

After identifying the possible conditions that could result within the operations of electro-submersible equipment in Llanos norte fields (LLN), several workshops and trainings were carried out with the personnel in charge of monitoring, diagnosis and resolution of operational problems in order to Increase the ability of staff to identify these conditions, establish a common language and create appropriate procedures to meet the conditions mentioned.

## Results

With the diagnoses made, the correlation between the changes of parameters and abnormal conditions that could be happening at the bottomhole or on the surface is analyzed to reveal possible contributing factors that generate the low performance of the ESP and diagnose the root cause of the problem, with which can generate a modification in the parameters or appropriate configuration of control parameters of the ESP pump that lead to a solution or improvement of the problem.

Monitoring is very important to evaluate the performance of the operation in the wells and, consequently, the definition of the protection strategies of electro submersible equipment. This practice has helped to create a broader plan to diagnose and solve some common conditions in well trends according to the data obtained by the sensors / VSD, which has played a crucial role in recommending a correct approach to problem solving., prevent failures and extend the life of the equipment.

In the case of the field wells operation, substantial results have been obtained where it has gone from an average of 100 annual failures for the period of 2011-2012 to an average of 40 annual failures currently in the period of 2018- 2019. Likewise, a valuable improvement has been achieved in terms of the useful life of the ESP equipment where life expectancy has increased from 600 days for the period of 2012-2013 to the current average of 1,500 days. Consequently, a significant reduction in the failure rate has been achieved by 60% at a value of 0.18 over the past 5 years.

Figure 13-Number of Failures × Year - BHGE Provider - Data Updated July 15, 2019. source Baker Hughes.

<!-- image -->

Figure 14-Average operating time - Mobile 12 months. Source Baker Hughes.

<!-- image -->

Figure 15-ESP Failure Index, Source Occidental Colombia

<!-- image -->

## Conclusions

After the design stage and an appropriate installation procedure, efforts should be made to extend the running time of the system to the maximum, which is achieved by continuous monitoring and timely eventual adjustments in the configuration of the ESP equipment. Although the action plans may be successful, not all teams exceed the expected useful life in many cases due to conditions outside the ESP team.

This diagnostic manual serves as a tool to identify the inadequate performance of the ESP system and trends in the operating parameters that occur during the life of a ESP device, inducing the possibility of failures.

This  guide  provides  us  with  direction  for  the  analysis  of  the  operating  conditions  of  the  unit,  to subsequently define recommendations, in order to extend the useful life of the ESP and improve the failure rate in the field thus reducing the operational costs associated with the interventions The failure rate was reduced by 60% to a value of 0.18.

This document has proven to be effective for personnel involved in the operation as a quick reference guide in identifying operational problems.

For greater effectiveness in the operation, this guide should be accompanied with continuous training for all personnel. This allows to develop better skills in the interpretation of the available information and its correlation with the operational trends presented in the well.

## Recommendations

1. This guide is not intended as a final solution for diagnoses. Final decisions must be taken taking into account additional information such as the particularities of each field and the evidence collected throughout its records.
2. Before making decisions, it is recommended to consult with an expert from the service companies to obtain a feedback that includes a deeper analysis such as simulations with the ESP sizing simulators provided  by  the  service  companies,  lessons  learned  in  other  fields  and  recommendations  in  test protocols for validation of diagnoses.
3. The guide should not replace formal staff training programs. This guide should accompany them and be part of these.
4. It is important to compile in historical databases all the evidence collected throughout the record of each well. This information is useful when evaluating and understanding the particularities of each well.

## Acknowledgments

Special thanks to Occidental de Colombia LLC and Baker Hughes for allowing us to develop and publish this Project.

## References

1. 2011. Baker Hughes Centrilift Submersible Pump Handbook - 10th Edition, Baker Hughes Artificial Lift Systems.
2. 2009. Electrical Submersible Pumps Manual - Design, Operations, and Maintenance . Gabor Takacs, Gulf Professional Publishing.
3. 2015. "Run Life improvement by implementation of Artificial Lift Systems Failure Classification and Root cause Failure Classificatio"n . SPE-173913-MS.