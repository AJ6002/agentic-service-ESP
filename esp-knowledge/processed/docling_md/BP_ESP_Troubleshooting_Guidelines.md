# BP0757: ESP Current Predictions and Troubleshooting Guidelines

<!-- Page 1 -->
BP0757  
 
 
Final Revision 2  
 
 
25th November 2004 
 
 
Prepared by:  Reviewed by:  Accepted by  
 
 
Mark Denny (BP)  
ESP Engineer Wytch Farm  
 
 
Alasdair Pirie (Helix -RDS)  
Petroleum Engineer  
 
 
 
 
  
 
John Davies (BP)  
 
Adam Downie (Helix -RDS)  
 
Mike Hefley (BP)  
 
Yvonne Hepburn (BP)  
 
 
  
 
Geoff Weighill (BP)  
 ESP Current 
Predictions and 
Troubleshooting 
Guidelines

<!-- Page 2 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 2 of 55 25-November -2004

<!-- Page 3 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 3 of 55 25-November -2004   
 
 
 
 
Document No:   BP0757  
 
Document Type:   FINAL REPORT  
 
Title:    ESP Current Predictions and Troub leshooting  
 
2 25-Nov-2004  MS Word  FINAL 2  
(Format 
Changes)  M Denny / A. 
Pirie  G Weighill  
1 23-Sep-2004  MS Word  FINAL  M Denny / A. 
Pirie J Davies,  
A Downie  
M Hefley,  
Y Hepburn,  G Weighill  
0 July 2003  MS Word  DRAFT  M Denny    
       
Rev Date  Format  Description  Originator  Reviewed  Accepted  
 
 
 
 
DISTRIBUTION LIST:  
 
Name  Copy No.  
 
Geoff Weighill   A4 Ring Binder (001)  
  A5 Wire Bound (002 -010) 
  MS Word File  
  PDF File  
 
 
 
  
 
COVER / APPROVAL / AMENDMENT SHEET

<!-- Page 4 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 4 of 55 25-November -2004  CONTENTS  
 
1.0 INTRODUCTION ................................ ................................ ................................ ............. 5 
2.0 ESP SYSTEMS OVERVIEW ................................ ................................ ........................... 6 
2.1 ESP SYSTEM DESIGN ................................ ................................ ................................ ....... 6 
2.1.1  ESP Optimisa tion Lifecycle ................................ ................................ .................. 7 
2.1.2  General Design Considerations ................................ ................................ ........... 7 
2.2 ESP SIZING ................................ ................................ ................................ ......................... 8 
2.2.1  Initial design ................................ ................................ ................................ .......... 8 
2.2.2  Optimising the design ................................ ................................ ........................... 9 
2.2.3  Final checks ................................ ................................ ................................ .......... 9 
2.3 ESP COMMISIONING AND  PUMP STARTING ................................ ................................ 10 
2.4 SAMPLE ESP SUMMARY S HEET ................................ ................................ .................... 12 
2.5 ESP OPERATIONS ................................ ................................ ................................ ........... 13 
2.5.1  Pump starting ................................ ................................ ................................ .....13 
3.0 CURRENT LOADING PRED ICTIONS IN ESP SYSTE MS................................ ........... 14 
3.1 SECTION INTRODUCTION ................................ ................................ .............................. 14 
3.2 EXAMPLE 1 - NORMAL O PERATION ................................ ................................ .............. 15 
3.3 EXAMPLE 2 - UNDERSIZ ED PUMP ................................ ................................ ................. 23 
3.4 EXAMPLE 3 - OVERSIZE D PUMP ................................ ................................ ................... 27 
3.5 EXAMPLE 4 - VARIABLE  SPEED SYSTEM ................................ ................................ .....31 
4.0 TROUBLESHOOTING ................................ ................................ ................................ ..39 
4.1 NORMAL OPERATION - GENERAL ................................ ................................ ................. 39 
4.1.1  Power Cable Losses ................................ ................................ .......................... 39 
4.2 UNDERSIZED PUMP ................................ ................................ ................................ ........ 40 
4.2.1  Pump Operating Conditions – Upthrust ................................ ............................. 40 
4.2.2  Overloaded Motor ................................ ................................ ............................... 40 
4.2.3  Correctiv e Action Possible ................................ ................................ ................. 41 
4.2.4  Considerations when Inflow Performance Uncertainties Exist ........................... 43 
4.3 OVERSIZED PUMP ................................ ................................ ................................ ........... 44 
4.3.1  Increased Power and Current Requirements ................................ ..................... 44 
4.3.2  Transformers ................................ ................................ ................................ ......45 
4.3.3  Pump Operatin g Conditions - Downthrust ................................ .......................... 46 
4.3.4  Well Pump Off and Gas Locking ................................ ................................ ........ 46 
4.3.5  Underload Protection ................................ ................................ .......................... 48 
4.3.6  Deadheading ................................ ................................ ................................ ......48 
4.4 VARIABLE SPEED DRIVE  SYSTEMS ................................ ................................ .............. 51 
4.4.1  Effects of Variable Speed Systems on Pump s................................ ................... 51 
4.4.2  Affinity Laws ................................ ................................ ................................ .......51 
4.4.3  Effects of Variable Speed Systems on Motors ................................ ................... 52 
4.4.4  Summary of Frequency Change Effects ................................ ............................ 53 
4.4.5  Analysis of Frequency Change Effects on Well Performance ........................... 53 
4.4.6  Potential VSD Benefits – Changing Well Conditions ................................ ......... 54 
4.4.7  Additional VSD Benefits and Considerations ................................ ..................... 55

<!-- Page 5 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 5 of 55 25-November -2004  INTRODUCTION  
This document is intended as a guide to Petrol eum Engineers and Well Service Engineers to 
help them understand electrical current loading on electrical submersible pump (ESP) 
systems and use this to optimise performance, troubleshoot problems and design suitable 
replacement units for workovers. The do cument fills a gap in the industry documentation and 
is not intended to cover all aspects of ESP system design covered in vendor manuals and 
artificial lift publications.  
The document focuses on the electrical system and uses worked examples to determine 
motor current using pump and motor charts and basic field data. The section on 
troubleshooting examines how to apply the information from the worked examples to various 
operational problems.  
The worked examples make reference to various equipment specificat ions; pump and 
protector curves, motor curves and other miscellaneous information. It is recognised that 
these data will not apply to every ESP installation, however the examples are structured so 
that data can be substituted. The worked examples also all begin with a list of well data that 
should be available to the wellsite engineer.  
The main application for this document is BP -TNK operations in Russia, hence some 
references are made to Russian equipment, e.g. Borets motor curves. However the structure 
of the examples is such that any vendor specifications and curves can be applied to the 
principles demonstrated. The majority of the BP Russian ESP operations do not have 
downhole pressure gauges, therefore pressure gauge information is not covered within th is 
document.

<!-- Page 6 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 6 of 55 25-November -2004  1.0 ESP SYSTEMS OVERVIEW  
 
1.1 ESP SYSTEM DESIGN  
 
An effective ESP artificial lift system cannot be designed in isolation; all components of the 
production system are mutually influential.  Unless the interactions between, and limitations 
of, each component part of the whole are considered, the system will at best be sub -optimal 
and at worst may fail.  
 
By way of example, the size of the tubing will influence the ESP performance.  The pressure 
losses and potential erosion in undersize tubing  is well understood.  However if the tubing is 
too large the flow velocity may not be sufficiently above the slip velocity resulting in water 
hold-up.  Pump sizing software does not account for hold -up and in an extreme case the 
pump could be required to s upport a column of water in a dry well, the pump will be 
understaged, operate in severe downthrust, suffer motor cooling problems, fail to produce the 
rates anticipated and perhaps fail prematurely.  
 
Similarly motors which are not matched to the surface el ectrical systems may be limited in 
voltage or current and hence frequency of operation (in variable frequency systems) 
potentially limiting the flexibility to tune the pump to changing reservoir conditions.  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
 
 
 
 
 Reservoir  
 Well &  
Completion                       
                 ESP  Surface  
Facilities  
 
 
 
 
 
Optimised  
System  
Design

<!-- Page 7 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 7 of 55 25-November -2004  1.1.1  ESP Optimisation Li fecycle  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
1.1.2  General Design Considerations  
 
In general the larger the diameter of the pump the more efficient it will be, however if the well 
performance is uncertain consideration should be also given to the shape of the pump curve.  
 
Highly eff icient pumps often suffer from poor performance outside a narrow recommended 
operating range.  For new wells where the likely inflow performance is uncertain, a pump with 
a slightly lower peak efficiency but a flat efficiency profile across a broad allowab le operating 
range would be preferable.  
 
Generally the larger the diameter of the motor the more efficient it will be, and, for the same 
power output, shorter. This will reduce the susceptibility to damage in transit and whilst RIH.  
 
Motor winding insulati on degrades at a rate proportional to it's operating temperature, 
operating motors at less than 100% full load current load factors will reduce the internal 
winding temperature and increase its operational life.  If workover costs are high it is generally 
cost effective to over -specify the motor.  
 
Because of thrust issues, the same considerations do not apply to pumps. If in doubt about 
well performance the pump should be specified slightly smaller than the expected well rate, 
as the well can choked into th e range of the pump, whereas if the pump is too large no action 
can be taken to reduce thrust loading.  
    Design  
Re-design  
optimise  
Inspect  
diagnose  
Operate  
monitor  Installation

<!-- Page 8 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 8 of 55 25-November -2004  In high angle wells labyrinth seals should be avoided, whereas in vertical wells bag seals can 
be the less reliable option particularly if the well flui ds are aggressive to elastomers.  Tandem 
seals can be run to increase reliability.  
 
In high GOR wells, gas separators and gas handlers can be deployed either individually or in 
series. If the well is packerless annulus venting options can also reduce the f ree gas 
percentage at the pump intake.  Mixed flow stage designs are less susceptible to gas locking 
than equivalent radial stages and should be sized to operate at total fluid (liquid and gas) flow 
rates at the upper end of their recommended flow rate ran ge where they suffer less head 
degradation due to gas.  
 
In wells producing solids mixed flow stages are preferred, and the vendor should be consulted 
regarding abrasion resistant pump bushings and impellor coatings.  Potentially more serious 
than long -term erosion of the pump is the potential for plugging and sticking (refer to 
operations section for procedure when attempting to free a stuck ESP).  
 
1.2 ESP SIZING  
 
1.2.1  Initial design  
 
• Choose a production rate based on well PI, reservoir pressure and bubble point (d esign 
rate may be determined by other factors such as erosion limits, reservoir management 
issues etc, however in this section it is assumed that the design basis is bubble point).  
• Determine bottom hole flowing pressure at perforation depth.  
• Set the pump d epth such that the pressure at the pump intake is at the limit of free gas 
handling capacity of the pump.  
• Check the head requirement of the pump and choose the stage count and frequency 
such that the pump is operating at its best efficiency point. The freq uency should ideally 
be as close as possible to 60hz to get the maximum power from the motor (below 60 Hz 
the power available is: rated hp x [running frequency / 60], and above 60hz motor 
current is derated to reduce heating effect).  
• The expected changes i n water cut, reservoir pressure and other production constraints 
during the entire ESP installation life must be considered during the design process.  
• Check the expected motor loading.  
• If the load is too high the initial production rate is too high and sho uld be dropped 
slightly.  
• If the load is low, there is potential to increase the design flowrate, however if the 
flowrate takes the flowing pressure below bubble point a smaller motor may be possible.

<!-- Page 9 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 9 of 55 25-November -2004  1.2.2  Optimising the design  
 
• Iterate through the loop again . 
• Note if the rate is decreased the bottom hole flowing pressure will increase, so the 
pump can be raised in the well to keep the same intake pressure and vice versa.  
• The final optimal solution is when:  
o The pump is operating at its free gas limit for pump intake pressure (minimum 
cable voltage losses and tubing friction losses, maximum gas lift effect above 
and below the pump).  
o The motor is fully loaded (motors are increasingly inefficient below 65% of full 
load, and larger motors are more expensive).  
o The p ump flowrate is as close as possible to the BEP of the pump (minimum 
conversion losses, shaft hp to hydraulic hp).  
o The motor is at or is close to 60hz (no derating of the motor, for heating or 
running less than 60hz).  
 
1.2.3  Final checks  
 
• Finally double check th at at the design operating point the following parameters are 
acceptable:  
o Cable heating  
o Cable voltage drop  
o Available surface voltage  
o Motor and pump shaft torque  
o Pump housing differential burst pressure  
o Pump position in the well with regard to any wellp ath doglegs.  
• Make adjustments as necessary to address these limits.

<!-- Page 10 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 10 of 55 25-November -2004  1.3 ESP COMMISIONING AND PUMP STARTING  
 
• An ESP system encompasses, electrical, mechanical, instrument, process, well and 
reservoir engineering disciplines.  
• The commissioning engineer should  be familiar with all aspects of these disciplines in 
as much as they affect the performance and operation of the system.  
• Where this is not possible a single lead engineer MUST be delegated for the 
commissioning process and all decision making regarding th e operation of the ESP, 
until steady state flow has been established and the well handed over to operations.  
• To allow timely decision making, large committees of individual discipline engineers 
should be avoided, particularly when starting high hp systems (>500 hp) where 
irreversible damage can be caused by a relatively short period (30 -35 minutes) of 
incorrect operation.  
• A well handover package from the rig should document all operations carried out and 
the final condition of the well.  
• Following workover t he reinstatement of process electrical and instrument services 
should be witnessed along with any pressure, insulation and function tests.  
• It is recommended that downhole gauges be installed in ESP wells ideally providing 
tubing and annulus pressure, ESP s uction and discharge pressure and motor 
temperature.  Where installed this data must be available and on line prior to startup. If 
downhole monitoring is not available then startup must be monitored using motor 
current and frequency, well head pressure and  surface flowrate.  
 
The final line up and start of the pump should be the responsibility of the lead engineer. It is 
recommended that a checklist be completed including:  
 
• Tree and annulus valve status.  
• Process valve alignment.  
• Confirmation of flowline pres sure test.  
• Confirmation of instrument and control function tests.  
• Electrical insulation and motor balance readings.  
• Transformer tap changer settings.  
• Normal pressure signature of SSSV.  
• VSD setup parameters.  
• Motor controller setup.  
 
When starting the pump, the theoretical head/flow curve for the pump should be available with 
the head axis plotted in pressure units calculated using the s.g. of the completion fluid.  
Where a VSD is employed multifrequency head curves should be available covering the 
range of o perating frequencies expected.  Comparison of the head curve with the observed 
downhole pressures allows rapid confirmation of correct pump rotation.

<!-- Page 11 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 11 of 55 25-November -2004  Where any doubt exists the pump should be reversed and readings of:  
• Pump intake pressure.  
• Pump discharge pressure.  
• Motor current.  
• Wellhead pressure.  
• Wellhead temperature.  
should be compared at the same frequency of operation to determine the correct rotation. The 
correct rotation will be obvious given two or more of these readings.  
 
Repeated changes of rotati on should not be necessary and must be avoided as they can be 
extremely detrimental to the longevity of the pump.  (Most high load thrust bearing systems 
are designed to operate in a particular direction).  
 
In general the larger and more axial the pump sta ge design, the greater the difference 
between correct and incorrect rotation.  Smaller radial stage pumps can draw similar loadings 
in each direction but in general fail to establish much differential pressure.  In assessing pump 
performance consideration should be given other factors including the possibility of incorrect 
gauge calibration, pump sticking, pump plugging, incorrect process valve alignment etc.  
 
When handing the well over to operations a detailed summary of the installed system and its 
operat ing constraints should be compiled including a detailed description of; the installed 
ESP, surface equipment, transformer ratios, well and reservoir data and most importantly, 
comments detailing critical start -up or operating issues.

<!-- Page 12 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 12 of 55 25-November -2004   
1.4 Sample ESP Summary S heet 
 
Recent Well Data  
 
Well PI BHCIP  W. Cut  Oil Rate  Water Rate  Run-Life 
IF-19 7.90 2158  86.2%  1388  8646  847 days   
 
Operating Guidelines and Ranges  
 
Minimum Suction Pressure (psi) = 632  
♦ Well on line following workover.  Gauge system is Exal, use bende r for earth fault detection.  
♦ No issues with this well, new pump should start ok and run in current limit.  
♦ This pump is shaft limited, it will break above 100 motor amps!!!  
♦ Only suction pressure & temp are correct Exal gauge, ignore other data.  
Startup Guid elines and Tips  
 
♦ Set frequency to 65hz and start up into current limit, check downhole flow on Exal screen.  
♦ Leave well to stabilise and set frequency to final stable freq. + 2hz.  
♦ Underload set to 80% of I limit.  
 
 
ESP Trip Details at 18th June 2003  
 
High Wellhead Trip Pressure (bar) =   90  VSD Underload Current =   756 
Low Wellhead Trip Pressure (bar) =   10  VSD Overload Current =                1047  
 
 
Installed Equipment Details  
 
Pump:   HN15000 69 -COM   Max Motor Amps:   99.4 Drive Type: C/LIFT 1040  
Trans  Ratio:  9.58   Motor:    840HP  Max Drive Amps:  952 
(Motor Amps = Drive Amps/Trans Ratio)

<!-- Page 13 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 13 of 55 25-November -2004  1.5 ESP OPERATIONS  
 
1.5.1  Pump starting  
 
This is the aspect of ESP operation posing the greatest potential risk to the pump, particularly 
if a site/plant shutdown requires the  starting of a number of ESP’s in succession (5 or more).  
Detailed pump operating limits should be available for reference, local to the motor controller 
or VSD.  Where permanent downhole gauges are employed the data should be also be 
displayed locally, pr eferably with a real time trending facility.  Downhole data should be 
relayed to the CCR where as a minimum, alarms should be programmed on; downhole (or 
motor winding) temperature, earth leakage, and wellhead (high and low) pressure.  
Prior to starting the  pump, the cause of the trip should be determined and if appropriate 
rectified.  If the cause of the trip cannot be determined one start attempt may be made but 
repeated starts (on a tripping system) must be avoided.  Sufficient time should be allowed 
betw een a trip and an attempt to restart for the pressure across the pump to equalise.  The 
fluid column will naturally backflow through a recently stopped pump, causing the unit to 
backspin.  Starting a pump whilst it is backspinning risks overloading the sha ft causing torsion 
failure (at the splined connection between the pump and seal section).  
The well should be lined up to the flowline system and the choke partially closed.  Floating 
impellor pumps in particular should be started against a choke to ensure the impellors are 
seated against their respective downthrust washers; to prevent recycling, increase pump 
efficiency and avoid impellors running against their upthrust washers, which are small with 
limited bearing capacity.  Once the pump is running, check s should immediately be made to 
confirm the well is flowing by:  
• Comparing running current against the normal motor current.  
• Checking for wellhead pressure rise and fall whilst fully opening choke.  
• Checking for wellhead temperature rise.  
 
Once the pump is s tarted it may take some time for the wellbore to clean up to steady state 
conditions.  During the wellbore cleanup the pump loading will vary, as soon as this phase is 
complete the motor controller or VSD should be programmed with an underload based upon 
the actual loading and frequency of the motor.  Setting underload protection prior to 
establishing steady state flow risks an unnecessary trip and restart on the ESP.

<!-- Page 14 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 14 of 55 25-November -2004  CURRENT LOADING PRED ICTIONS IN ESP SYSTE MS 
1.6 SECTION INTRODUCTION  
This section con tains four worked examples of how to calculate the motor current using pump 
and motor charts and basic well data. The examples are:  
• Normal Operation  
• Undersized Pump  
• Oversized Pump  
• Variable Speed Drive  
Each example follows a similar format to determine the power required by the pump at a 
given flow rate using the motor curve to determine current demanded by the motor. The aim 
is to enable the PE / Well Service Engineer to understand pump electrical performance to 
help optimise the pump system, troubleshoot p roblems and design optimum pump systems 
for future replacement.  
The fluid in the pump during operation is at reservoir conditions (approximately) therefore the 
flowrate must be quoted at reservoir conditions. This document uses reservoir standard cubic 
metres per day as the flowrate unit, designated as rm3/d. The gas oil ratio figures are supplied 
as standard cubic meters of gas per standard cubic metre of oil (scm/scm).

<!-- Page 15 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 15 of 55 25-November -2004  1.7 EXAMPLE 1 - NORMAL OPERATION  
The information contained within Section 1.7 is an example of how to calculate the predicted 
motor current for a given ESP system at a specific flowrate and surface voltage. The example 
utilises a correctly designed ESP system, i.e. the pump is correctly matched to the well 
performance and the motor is of suitable size for the pump. This example is therefore 
intended to illustrate current prediction in a correctly designed ESP system which is operating 
within its recommended range.  
1.7.1  Available Data  
Section 1.7.1  contains information which is typically available to the wellsite petroleum 
engineer, most of which is required for current calculation. The information required and how 
it is used will become evident as the example progresses.  
The following is a summary of the most recent well test data:  
Oil Rate 
(rm3/d) Water Rate 
(m3/d) GOR 
(scm/scm)  Reservoir 
Temperature 
(degF)  Oil 
Specific 
Gravity  ESP 
Frequency 
(Hz) 
110 0 53 150 0.92 60 
Table 1: Example 1 well test data  
 
The table bel ow contains a summary of the ESP system in the well:  
Pump Type  Alnas 362 S700  
Number of pump stages  242 
Motor Type  Borets 32 -117 B5  
Motor Nameplate Power (kW) @ 60Hz  38.4 
Motor Nameplate Voltage (V) @ 60Hz  1080  
Motor Nameplate Current (A)  28.9 
Power Cable Type  No. 4 Cu  
Length of cable from surface switchboard 
to motor (ft)  7600  
Applied Surface Voltage (V)  1172  
Table 2: Example 1 ESP data  
 
The pump curve can be seen below in Figure 1, and the composi te motor curve can be seen 
below in Figure 2.

<!-- Page 16 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 16 of 55 25-November -2004  Figure 1: Alnas 362 S700 Pump performance curve for single stage at 60Hz (3500 RPM) 
and SG=1.0  
Borets 32-117 B5
05101520253035404550556065707580859095100
20 30 40 50 60 70 80 90 100 110 120
Output Power % RatedInput Power, Efficiency and PF (%)
05101520253035404550
Current (A)
Input Power (%) Power Factor (%) Efficiency (%) Current A
 
Figure 2: Motor Composite Curve for Borets 32 -117 B5 motor  
  
0   25   50   75   100   125   150   175   0   25   50   75   100   125   150   175   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
S700    10%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.25   0.50   0.75   1.00   1.25   Fluid Specif  ic Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60  
Hz   
Head  Efficiency  
BHP

<!-- Page 17 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 17 of 55 25-November -2004  1.7.2  Worked Example Data Flow  
The calculation is worked through in detail in the following sections, however a summary of 
the data flow is presented here for reasons of clarity. The individual steps required to 
calculate the current in the above ESP system are as follows:  
• Determine power required by each pump stage at the specified flowrate. This is 
achieved using the pump curve  
• Multiply power per stage by number of stages to determine total power required by the 
pump  
• Determine power req uired by protector by using protector loading curve  
• Add protector and pump power requirements to obtain total system power requirements. 
This is equivalent to the motor output power required  
• Use motor curve to determine current required by motor to delive r power output.

<!-- Page 18 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 18 of 55 25-November -2004  1.7.3  Determine Power Required by Pump  
The first step in determining the required current is to calculate the total power required by the 
pump to flow the well at the test rate of 110 m3/day. This is calculated using the following 
formula:  
Total pump power required = BHP/stage x fluid SG x No of stages  
The pump chart is used to obtain the BHP per stage required for a given flowrate, as is 
demonstrated by the red solid lines in Figure 3 below. It can be seen that the p ower required 
per stage is 0.2 BHP. This is the value of BHP required, at this flowrate, for a single stage at 
60 Hz with a fluid SG of 1.0. This is then input into the equation mentioned previously as 
follows:  
Total pump power required  = BHP/stage x flui d SG x No of stages  
    = 0.2 x 0.92 x 242  
    = 44.5 BHP.   
 
 
Figure 3: Determining pump stage BHP and head at a specific flowrate  
 
 
1.7.3.1  Power Required by Protector  
The next step in the current calculation is to determine the power w hich will be consumed by 
the pump protector, or seal section. To determine the BHP required by the protector, the total 
head from the pump requires to be established. Referring to the pump curve in Figure 3 
above, the head generate d per stage (at a specific flowrate at 60 Hz) can be determined as 
demonstrated by the blue dashed lines. In this example the head per stage is 6.25 metres. As 
the pump has 242 stages, the total head generated is simply:  
Total head  = head per stage x No o f stages    0   25   50   75   100   125   150   175   0   25   50   75   100   125   150   175   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
S700    10%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.25   0.50   0.75   1.00   1.25   Fluid Specif  ic Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60  
Hz   
Head  
BHP Efficiency

<!-- Page 19 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 19 of 55 25-November -2004  = 6.25 x   242  
= 1512.5 metres.  
The power consumed by the protector can then be established from the protector loading 
curve. Referring to the generic protector curve shown below in Figure 4, the power required 
by the prot ector in this example is approximately 3.2 BHP, as illustrated by the red lines. 
Individual component protector curves should be utilised for actual field use, however in the 
absence of this data for small to medium ESP systems a figure of less than 5 BHP is 
sufficient.      
   
 
Figure 4: Generic Protector Loading Curve  
 
1.7.4  Total System Power Required  
The total power required by the ESP system (i.e. pump and protector) is simply the total of the 
pump power required and the protector p ower required. This is as follows:  
Total power required  = pump power + protector power  
   = 44.5 + 3.2  
   = 47.7 BHP.  
Converting to kW gives:  
1 HP = 0.746 kW, therefore  
Power in kW   = 0.746 x 47.7  
   = 35.6 kW.  
This is the total power input required by t he pump system, i.e. the power which is required to 
be delivered by the motor to the pump.  01234
0 500 1000 1500 2000 2500 3000 3500 4000 4500 5000
Total Dynamic Head in MetresHorsepower

<!-- Page 20 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 20 of 55 25-November -2004  1.7.5  Determine Motor Current Required  
The power required to be delivered by the motor has been calculated above as 35.6 kW. The 
current required to supply this power can be established in one of two ways:  
1. The composite motor curve can be consulted to provide a figure for current. For this 
method to be effective the voltage supplied to the motor terminals must be the 
nameplate value at the frequency of operation  
2. The current  can be calculated from the formula:  
−  Current (A) = [Output power (kW) x 1000] / [1.73 x V x Eff x PF]  
  Where Eff and PF can be obtained from the motor composite curve.  
 
The simplest manner in which to estimate current required is to use method 1, the mot or 
composite curve. The estimated current is determined by simply reading from the graph the 
current required for the appropriate motor output power which was previously calculated as 
35.6kW. This is equivalent to approx 93% of the motor rating of 38.4kW. The current required 
can then be simply read from the chart. The value obtained in this example is 
approximately 27 Amperes, which is illustrated by the pink lines in Figure  2.   
Note:  The calculation of the figure of 27A is the entire focus of this document, i.e. how to use 
basic well and ESP data to obtain the theoretical value of current which a given ESP system 
will require for a specified flowrate. It must also be noted that this calculated figure will rarely 
match the actual measured figure exactly due to the various tolerances and uncertainties 
involved, e.g. well test and instrument accuracy etc.  
 
1.7.6  Power Cable Losses  
To ensure that the nameplate voltage is supplied to the motor terminals, power cable voltage 
losses, for the relevant cable type, must be calculated and allowed for. This is achieved using 
a chart as shown below in Figure 5 (for actual field use the cable manufacturer’s chart should 
be used). Using the current figure of 27 A which was obtained previously, a value of voltage 
drop (per 1000ft of cable) of 10.5 V is obtained (at 77 °F), as is illustrated by the black lines in 
Figure 5.  
It is then further necessary to correct for the temperature of the c onductor as per Table 3 
below. The reservoir temperature in the well is 150 °F, so the temperature correction factor is 
1.15. The total voltage drop over the cable is given by:  
Voltage drop  = (Voltage drop per 1000 ft x cable lengt h x temperature                 
correction)/1000  
    = (10.5 x  7600 x 1.15)/1000  
   = 91.8 V.  
 
Therefore the total surface voltage required for this system to ensure nameplate voltage is 
delivered to the motor is:  
Surface voltage  = motor nameplate voltag e + cable losses  
   = 1080 + 91.8  
   ≈ 1172V.

<!-- Page 21 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 21 of 55 25-November -2004   
Figure 5: Chart to determine 3 phase Voltage drop in a power cable at 77 °F  
 01020304050
0 10 20 30 40 50 60 70 80 90 100 110 120 130 140 150
Current (Amperes)Volts Drop per 1000 ftNo 6 Cu
No 4 Cu
No 2 Cu
No 1 Cu
No 1/0 Cu

<!-- Page 22 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 22 of 55 25-November -2004    
Conductor Temperature  Voltage Drop Multiplier  
131°F (55 °C) 1.12 
149°F (65 °C) 1.15 
167°F (75 °C) 1.19 
185°F (85 °C) 1.23 
203°F (95 °C) 1.27 
221°F (105 °C) 1.31 
239°F (115 °C) 1.35 
257°F (125 °C) 1.39 
275°F (135 °C) 1.42 
293°F (145 °C) 1.46 
302°F (150 °C) 1.48 
 
Table 3: Voltage drop multipliers   
 
1.7.7  Conclusions  
 
• This is a well desi gned system which is operating close the pump best efficiency point 
(BEP)  
• The motor is well matched to the pump in that it is operating relatively close to (and less 
than) the motor nameplate power  
• The ESP system is appropriately designed and sized for the  well inflow performance.

<!-- Page 23 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 23 of 55 25-November -2004  1.8 EXAMPLE 2 - UNDERSIZED PUMP  
The following is an example of current calculation in an undersized pump system, i.e. the 
pump has insufficient flow capacity for the well inflow performance. This example uses the 
same equipment as example 1 but in a different well.  
 
1.8.1  Available Data  
The following is a summary of the most recent well test data:  
Oil Rate 
(rm3/d) Water Rate 
(m3/d) GOR 
(scm/scm)  Reservoir 
Temperature 
(degF)  Oil 
Specific 
Gravity  ESP 
Frequency 
(Hz) 
155 0 90 185 0.92 60 
Table 4: Example 2 well test data  
 
The table below contains a summary of the ESP system in the well:  
Pump Type  Alnas 362 S700  
Number of pump stages  242 
Motor Type  Borets 32 -117 B5  
Motor Nameplate Power (kW) @ 60Hz  38.4 
Motor Namep late Voltage (V) @ 60Hz  1080  
Motor Nameplate Current (A)  28.9 
Power Cable Type  No. 4 Cu  
Length of cable from surface switchboard 
to motor (ft)  9200  
Applied Surface Voltage (V)  1238  
Table 5: Example 2 ESP data  
 
The pump curve c an be seen below in Figure 6, and the composite motor curve can be seen 
below in  Figure 7.

<!-- Page 24 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 24 of 55 25-November -2004  Figure 6: Alnas 362 S700 Pump performance curve for single stage at 60Hz (3500 RPM) 
and SG=1.0  
 Figure 7: Motor Composite Curve for Borets 32 -117 B5 motor  
 
1.8.2  Determine Power Required by Pump  
As with example 1, the first step in determining the required current is to calculate the total 
power required by the pump to f low the well at the test rate of 155 m3/day.  Borets 32-117 B5
05101520253035404550556065707580859095100
20 30 40 50 60 70 80 90 100 110 120
Output Power % RatedInput Power,Efficiency and PF (%)
05101520253035404550
Current (A)
Input Power (%) Power Factor (%) Efficiency (%) Current A 
0   25   50   75   100   125   150   175   0   25   50   75   100   125   150   175   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
S700    10%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.25   0.50   0.75   1.00   1.25   Fluid Specif  ic Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60  
Hz   
Head  
BHP Efficiency

<!-- Page 25 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 25 of 55 25-November -2004  In an identical manner to example 1, the pump chart is used to obtain the BHP required and 
head generated per stage. As illustrated by the red solid lines in Figure 8 below the BHP per 
stage in this example is 0.25 BHP. The total pump power required is then:  
Total pump power required  = BHP/stage x fluid SG x No of stages  
    = 0.25 x 0.92 x 242  
    = 55.7 BHP.   
 
 
Figure 8: Determining pump stage BHP and head a t a specific flowrate  
 
1.8.2.1  Power Required by Protector and Total System Power Required  
The head generated per stage in this example is determined as approximately 2.5 metres, as 
illustrated by the blue dashed lines on Figure 8. The tot al head generated is therefore:  
Total head  = head per stage x No of stages  
= 2.5 x  242  
= 605 metres.  
Referring to the generic protector loading curve shown in Figure 4, the power required by the 
protector is determined as approxi mately 2.9 HP.  
The total power required by the pump and protector is therefore  
Total power  = pump power + protector power  
  = 55.7 + 2.9  
  = 58.6 HP.  
Converting this to kW gives 58.6 x 0.746 = 43.7 kW.  
    0   25   50   75   100   125   150   175   0   25   50   75   100   125   150   175   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
S700    10%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.25   0.50   0.75   1.00   1.25   Fluid Specif  ic Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60  
Hz   
Head  
BHP Efficiency

<!-- Page 26 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 26 of 55 25-November -2004  1.8.3  Determine Motor Current Required  
The required curre nt is determined in exactly the same manner as for example 1. The motor 
power requirement has been calculated as 43.7kW, which is equivalent to 114% of the motor 
rating of 38.4kW. As illustrated in  Figure 7 by the pink lines, it c an be seen that a value of 
approximately 34 Amperes  is obtained for this power requirement.    
The current required by this ESP system operating in this configuration is 34A.  
1.8.4  Power Cable Losses  
As per example 1, the chart shown in Figure 5 is consulted to obtain the voltage drop per 
1000 ft of cable, and in this instance for a current of 34 A, a figure of approximately 14 V per 
1000 ft is obtained for a No 4 cable.  
The reservoir temperature is 185 °F, therefore from Table 3 the temperature correction is 1.23.  
This data is then used to calculate the cable voltage drop as below:  
 
Voltage drop  = (Voltage drop per 1000 ft x cable length x temperature correction)/1000  
Voltage drop  = (14 x 9200 x 1.23)/1000  
  = 158.4 ≈ 158 V.  
The voltage applied to the motor terminals is then  
Motor voltage applied  = surface voltage – cable voltage drop  
   = 1238 – 158 
   = 1080 V.  
therefore the correct voltage is being applied to the motor terminals.  
 
1.8.5  Conclusions  
The following ar e the key observations regarding this ESP system. For a detailed explanation 
refer to section 2.2.  
 
• The pump is operating in an upthrust condition  
• The motor is overloaded – it is running at approximately 118% nameplate current  
• Damage will occur to either the pump, motor or both, resulting in reduced run lifetime  
• The pump in this well is of insufficient capacity. If possible it should be replaced with a 
unit with a greater flow capacity, together with a motor suitable for the pow er 
requirements  
• If the current overload has been set at 110% nameplate, the system will not run – it will 
trip as soon as flowing conditions have been established.

<!-- Page 27 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 27 of 55 25-November -2004  1.9 EXAMPLE 3 - OVERSIZED PUMP  
The final fixed speed example is a current calculation  in an oversized system, i.e. the pump 
capacity is greater than the well inflow performance can deliver.   
This example uses the same well as example 1, which had a correctly designed system which 
was matched to the well inflow performance, resulting in ef ficient ESP operation. In this 
example it will be assumed that the equipment was pulled from the well (for whatever reason), 
and replaced with inappropriate and poorly matched equipment, to demonstrate the 
contrasting power and current requirements.  
 
1.9.1  Avail able Data  
The following is a summary of the most recent well test data:  
Oil Rate 
(rm3/d) Water Rate 
(m3/d) GOR 
(scm/scm)  Reservoir 
Temperature 
(degF)  Oil 
Specific 
Gravity  ESP 
Frequency 
(Hz) 
110 0 53 150 0.92 60 
Table 6: Example 3 well test data  
 
The table below contains a summary of the ESP system in the well:  
Pump Type  Alnas 362 M3000  
Number of pump stages  166 
Motor Type  Borets 90 -117 B5  
Motor Nameplate Power (kW) @ 60Hz  108 
Motor Nameplate Voltage (V) @ 60Hz  2400  
Motor Namep late Current (A)  36.3 
Power Cable Type  No. 4 Cu  
Length of cable from surface switchboard 
to motor (ft)  7600  
Applied Surface Voltage (V)  2505  
Table 7: Example 3 ESP data  
 
The pump curve can be seen below in Figure 9, and the composite motor curve can be seen 
below in Figure 10.

<!-- Page 28 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 28 of 55 25-November -2004   
Figure 9: Alnas 362 M3000 Pump performance curve for single stage at 60Hz (3500 
RPM) and SG=1.0  
 
Figure 10: Motor Composite Curve for Borets 90 -117 B5 motor  Borets 90-117 B5
05101520253035404550556065707580859095100
0 10 20 30 40 50 60 70 80 90 100 110 120
Output Power % RatedInput Power, Efficiency and PF (%)
0.005.0010.0015.0020.0025.0030.0035.0040.0045.0050.00
Current (A)
Input Power (%) Power Factor (%) Efficiency (%) Current A 
0   100   200   300   400   500   600   700   800   0   100   200   300   400   500   600   700   800   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
M3000    10%   20%   30%   40%   50%   60%   
2.50   5. 00   7.50   10.00    12.50    15.00    
0.50   1.00   1.50   2.00   2.50   3.00   Fluid Specific Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60 Hz    
Head  
BHP Efficiency

<!-- Page 29 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 29 of 55 25-November -2004  1.9.2  Determine Power Required by Pump  
As with the previous examples, the pump chart is used to obtain the BHP required and head 
generated per stage. As illustrated by the red solid lines in Figure 11 below the BHP per stage 
in this example is 0.7 BHP. The total pump power required is then:  
Total pump power required  = BHP/stage x fluid SG x No of stages  
    = 0.7 x 0.92 x 166  
    = 107 BHP.   
 
Figure 11: Determining pump stage BHP and head at a specific flowrate  
 
1.9.2.1  Power Required by Protector and Total System Power Required  
Referring to Figure 11 above, the head generated per stage is 9.1 metres, as illustrated by 
the blue dashed li nes. As the pump has 166 stages, the total head generated is:  
Total head  = head per stage x No of stages  
= 9.1 x 166  
≈ 1511 metres.  
Referring to the generic protector loading curve shown in Figure 4, the power required by the 
protector is approximately 3.2 HP.  
The total power required by the pump and protector is therefore  
Total power  = pump power + protector power  
  = 107 + 3.2  
  = 110.2 HP.  
Converting this to kW gives 110.2 x 0.746 ≈ 82.2 kW.  
 0   100   200   300   400   500   600   700   800   0   100   200   300   400   500   600   700   800   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
M3000    10%   20%   30%   40%   50%   60%   
2.50   5. 00   7.50   10.00    12.50    15.00    
0.50   1.00   1.50   2.00   2.50   3.00   Fluid Specific Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60 Hz    
Head  
BHP Efficiency

<!-- Page 30 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 30 of 55 25-November -2004  1.9.3  Determine Motor Current Required  
The required current is determined in the same manner as the previous examples. The motor 
power requirement has been calculated as 82.2kW, which is equivalent to 76% of the motor 
rating of 108kW. As illustrated in Figure 10 by the p ink lines, a value of approximately 30 
Amperes  is obtained for the power requirement of 82.2kW previously calculated.  
The current required by this ESP system operating in this configuration is 30A.    
1.9.4  Power Cable Losses  
The chart shown in Figure 5 is consulted to obtain the voltage drop per 1000 ft of cable, and 
in this example for a current of 30 A, a figure of approximately 12 V per 1000 ft is obtained for 
a No 4 cable.  
The reservoir temperature is 150 °F, therefore from Table 3 the temperature correction is 1.15.  
This data is then used to calculate the cable voltage drop as below:  
 
Voltage drop  = (Voltage drop per 1000 ft x cable length x temperature correction)/1000  
Voltage drop  = (12 x 7600 x 1.15)/1000  
  = 104.9 ≈ 105 V.  
The voltage applied to the motor terminals is then  
Motor voltage applied  = surface voltage – cable voltage drop  
   = 2505 – 105 
   = 2400 V.  
therefore the correct voltage is being applied to the motor terminals.  
 
 
1.9.5  Conclusions  
The follo wing are the key observations regarding this ESP system. For a detailed explanation 
refer to section 2.3. 
 
• The pump is operating in a downthrust condition and will most likely experience a 
shortened run life  
• The pump in this well  has a flow capacity greater than that required by the well inflow 
performance. If possible the pump should be replaced with a unit with a reduced flow 
capacity, together with a suitable sized motor  
• The system is so badly designed that a totally different motor of almost 3 times the 
power rating has to be used compared to the same well with a correctly designed 
system (example 1).

<!-- Page 31 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 31 of 55 25-November -2004  1.10 EXAMPLE 4 - VARIABLE SPEED SYSTEM  
This example uses an ESP system which has a variable speed controller which can operate 
from 35 Hz to 60 Hz, and is intended to demonstrate current calculation in a variable speed 
system which is operating at some frequency other than the maximum design. It is also 
intended to demonstrate how to convert the data contained within pump and motor c harts 
from the base frequency to the actual frequency of operation. The effects and potential 
benefits of variable speed systems will then be further discussed in Section 2.4. 
 
1.10.1  Available Data  
The following is a summary of the mo st recent well test data:  
Oil Rate 
(rm3/d) Water Rate 
(m3/d) GOR 
(scm/scm)  Reservoir 
Temperature 
(degF)  Oil 
Specific 
Gravity  ESP 
Frequency 
(Hz) 
600 0 40 130 0.8 53 
Table 8: Example 3 well test data  
 
The table below contains a summ ary of the ESP system in the well:  
Pump Type  Alnas 362 M3800  
Number of pump stages  155 
Motor Type  Borets 63 -117 B5  
Motor Nameplate Power (kW) @ 60Hz  75.6 
Motor Nameplate Voltage (V) @ 60Hz  2400  
Motor Nameplate Current (A)  26.2 
Power Cable Type  No. 2  Cu 
Length of cable from surface VSD to 
motor (ft)  4000  
Applied Surface Voltage (V)  2148  
Table 9: Example 3 ESP data  
 
The pump curve can be seen below in Figure 12, and the composite motor curve can be se en 
below in Figure 13.

<!-- Page 32 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 32 of 55 25-November -2004   
0   100   200   300   400   500   600   700   800   900   1,000    0   100   200   300   400   500   600   700   800   900   1,000    Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
M3800    10%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.50   1.00   1.50   2.00   2.50   Fluid Specific Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    3500 RPM  -  60  
Hz   
Head 
BHP Efficiency  
 
Figure 12: Alnas 362 M3800 Pump performance curve for single stage at 60Hz (3500 
RPM) and SG=1.0  
 
Borets 63-117 B5
05101520253035404550556065707580859095100
0 5 10 15 20 25 30 35 40 45 50 55 60 65 70 75
Output Power KwEfficiency and PF (%)
0102030405060708090100
Input Power (kW) and Current (A)
Power Factor (%) Efficiency (%) Current A Input Power (kw)
Figure 13: Motor Composite Curve for Borets 63 -117 B5 motor at 60Hz

<!-- Page 33 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 33 of 55 25-November -2004  1.10.2  Determine Power Required by Pump  
The pump curve in Figure 12 is for an operating frequency of 60Hz. In this instance the 
operating frequency of the ESP system is 53Hz, therefore it is apparent that this curve is not 
applicable for this situation. The BHP per stage is calculated in the following manner:  
1. Convert the 53Hz flowrate to a 60Hz equivalent flowrate  
2. Determine the 60Hz equivalent BHP required per pump stage  
3. Convert the 60Hz figure to an equivalent 53Hz value.  
This will be outlined in the following sections.  
 
1.10.2.1  Convert 53Hz Flowrate to 60Hz Equivalent  
 
It is necessary to convert the 53Hz flowrate to a 60Hz equivalent to ensure that the BHP per 
stage figure is read from the correct part of the BHP curve, as the BHP  per stage varies at 
differing flowrates. This is performed by applying one of a series of equations known as the 
affinity laws to the 53Hz flowrate as follows:  
 
Flowrate 1  = (Frequency 1/Frequency 2) x Flowate 2, i.e.  
Flowrate 60Hz  = (60/53) x 600  
  ≈ 680 m3/d. 
Care must be taken when applying this equation; this is discussed further in Section 2.4.  
 
 
1.10.2.2  Determine BHP Required per Stage for 60Hz Operation  
 
The BHP required per stage is then determined assuming 60Hz pump operation (as this is the 
frequency at which the chart available is based upon). The equivalent 60Hz flowrate has been 
calculated as 680 m3/d, therefore the BHP per stage is determined, as per previous 
examples, using the pump chart (a 60Hz chart is used assuming th at this is the only chart 
available to the engineer) as illustrated by the red solid lines in Figure 14 below. It can be 
seen that for a flowrate of 680m3/d at 60Hz pump operation the BHP per stage required would 
be approx 1.03 BHP .

<!-- Page 34 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 34 of 55 25-November -2004   
Figure 14: Determining pump stage BHP and head at a specific flowrate for 60Hz 
operation  
  
0   100   200   300   400   500   600   700   800   900   1,000    0   100   200   300   400   500   600   700   800   900   1,000    Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
M3800    1 0%   20%   30%   40%   50%   
2.50   5.00   7.50   10.00    12.50    
0.50   1.00   1.50   2.00   2.50   Fluid Specific Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  –  60Hz  
HHzHz    
Head  
BHP Effici ency

<!-- Page 35 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 35 of 55 25-November -2004  1.10.2.3  Convert 60Hz BHP Figure to an Equivalent 53Hz Value  
The BHP per stage assuming 60Hz ESP operation has been calculated as 1.03 BHP. To 
convert this to an equivalent figure for actual system operation of 53Hz, i.e. to calculate the 
actual pump requirement, the second of the affinity laws is applied to the 60Hz value:  
BHP 1   = (Frequency 1/Frequency 2)3 x BHP 2  
where BHP 1 is at frequency 1 and BHP 2 is at frequency 2.  
Therefore the actual pump BHP requirement per stage at 53 Hz is calculated as follows:  
BHP53Hz  = (53/60)3 x 1.03  
  ≈ 0.69 BHP/stage.  
 
The total pump power required is then:  
Total pump power required  = BHP/stage x fluid SG x N o of stages  
    = 0.69 x 0.8 x 155  
    ˜ 85.6 BHP.    
 
 
1.10.3  Power Required by Protector and Total System Power Required  
Referring again to Figure 14, it can be seen that the head generated per stage, for an 
equivalent flowrate of 680m3/d and at a frequency of 60Hz, is appro x 5.5 metres, as illustrated 
by the blue dashed lines. This head per stage value is also required to be converted to an 
equivalent 53Hz figure. This is achieved using the third and final affinity law:  
Head 1   = (Frequency 1/Frequency 2)2 x Head 2  
Therefor e the actual head per stage at 53Hz is:  
Head 53Hz  = (53/60)2 x 5.5  
  ˜ 4.3 m.  
 
As the pump has 129 stages, the total head generated is:  
Total head  = head per stage x No of stages  
= 4.3 x 155  
˜ 666.5 metres.  
Referring to the generic protector loading curve shown in Figure 4, the power required by th e 
protector is approximately 2.9 HP.  
The total power required by the pump and protector is therefore  
Total power  = pump power + protector power  
  = 85.6 + 2.9  
  = 88.5 HP.  
Converting this to kW gives 88.5 x 0.746 ≈ 66 kW.

<!-- Page 36 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 36 of 55 25-November -2004  1.10.4  Determine Motor Current Require d 
The current drawn by the motor is determined in a similar manner as the previous examples, 
i.e. from reading off the motor chart. However there are some important differences between 
operation of a fixed speed system and a variable speed system which mus t be briefly 
outlined. The first point is that operation at different frequencies requires that the voltage 
supplied to the motor is varied directly with frequency. The second point is that a motor does 
not have the same power output at all frequencies – again this varies directly with frequency. 
The motor in this example is rated at 75.6kW at 60Hz. Operation of this motor at 53Hz results 
in a new power output rating of the motor as follows:  
Power Output 1  = (Frequency 1/Frequency 2) x Power Output 2  
i.e. the power output of a motor varies directly as frequency.  
Therefore in this example, the power rating of the motor at 53 Hz is:  
Power Output 53Hz  = (53/60) x 75.6  
   = 66.8 kW = 89.5 HP.  
 
Another important point is that when a motor is operated at a differe nt frequency with the 
voltage varied directly as frequency the current rating of the motor does not change with 
frequency. Therefore in this example, it has been established that the power rating of the 
motor is 89.5 HP at 53Hz, so it follows that if the m otor load is 89.5 HP at 53Hz then the 
current required by the motor is the same value as the nameplate current quoted at 60Hz, i.e. 
26.2 A.  
To obtain the current required, it is necessary to use a motor chart which is scaled in terms of 
percentage of rated  values (for fixed speed systems the chart can be scaled in absolute 
values or percentages). Thus, in this example, the 100% output power value at 53Hz would 
correspond to the figure of 89.5 HP, quoted above. The current magnitude can then be simply 
read f rom the chart, as in the previous examples, as the current rating does not change with 
frequency.  In this case the power required by the pump, and thus power output required from 
the motor, is 88.5 HP. The motor rating at this frequency has been calculate d at 89.5 HP, 
therefore the motor output is (88.5/89.5)*100 = 99% of the rated value at 53Hz. The current 
required can then be simply read from the rescaled motor chart, which is illustrated by the 
pink lines in Figure 15 below.  
It can be seen that a value of approximately 26 Amperes  is obtained for the power 
requirement of 66 kW (or 99% rated load at 53Hz) previously calculated. This is as we would 
expect given that the motor output is 99% of that rated, therefore the current will  be 
approximately nameplate value.  
The current required by this ESP system operating in this configuration is 26 A.

<!-- Page 37 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 37 of 55 25-November -2004   
Figure 15: Current estimation from % rated motor chart  
It should be noted here that this technique is not str ictly accurate as motor efficiency 
increases with frequency, i.e. the efficiency at 53Hz will be less than that at 60Hz, however 
this effect is negligible at the typical frequencies encountered in ESP systems.  
  
1.10.5  Power Cable Losses  
The chart shown in Figure 5 is consulted to obtain the voltage drop per 1000 ft of cable, and 
in this example for a current of 26 A, a figure of approximately 6.3 V per 1000 ft is obtained for 
a No 2 cable.  
The reservoir temperature is 130 °F, therefore fr om Table 3 the temperature correction is 1.12.  
This data is then used to calculate the cable voltage drop as below:  
 
Voltage drop  = (Voltage drop per 1000 ft x cable length x temperature correction)/1000  
Voltage drop  = (6.3 x 400 0 x 1.12)/1000  
  = 28.2 ≈ 28 V.  
It was previously mentioned that in varying the frequency of an ESP system the voltage is 
varied directly as the frequency. Therefore the voltage actually supplied to a 60Hz motor 
operating at 53Hz is (53/60) x nameplate vol tage 
  = (53/60) x  2400  
  = 2120 V.  
 
The voltage applied to the motor terminals is then  Borets 63-117 B5
0.005.0010.0015.0020.0025.0030.0035.0040.0045.0050.0055.0060.0065.0070.0075.0080.0085.0090.0095.00100.00
0.00 20.00 40.00 60.00 80.00 100.00 120.00
Output Power % RatedInput Power,Efficiency and PF (%)
05101520253035404550
Current (A)
Input Power (%) Power Factor (%) Efficiency (%) Current A

<!-- Page 38 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 38 of 55 25-November -2004  Motor voltage applied  = surface voltage – cable voltage drop  
   =  2148 – 28 
   = 2120 V.  
therefore the correct voltage is being applied to the motor terminals.  
 
 
1.10.6  Conclusions  
The following are the key observations regarding this ESP system. For a detailed analysis of 
VSD (variable speed drive) systems refer to section 2.4. 
 
• In a variable speed system the principles of current calculation ar e similar in principle to 
fixed speed systems, however a few important differences exist  
• Power required and head generated per pump stage are determined using the available 
pump chart then the values obtained are converted, using affinity law equations, t o 
equivalent values for the actual frequency of ESP operation  
• When a variable speed system is used, the applied motor voltage is varied directly as 
frequency  
• The power rating of a motor varies directly with the applied frequency  
• The current required by the  motor is read from a rescaled chart in terms of percentage 
rated motor power output  
• The pump in this system is operating close the best efficiency point (BEP)  
• The motor in this system is operating at around 99% nameplate power.

<!-- Page 39 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 39 of 55 25-November -2004  2.0 TROUBLESHOOTING  
This sectio n examines how to apply the information from the worked examples in Section 3.0 
to operational problems and is structured using the same sub -categories for convenience.   
 
The focus is on operational problems impacting the electrical system including motor  
overload; transformer settings; well pump -off and gas locking; underload protection; dead 
heading and effect of VSD frequency changes on ESP performance. A brief section on 
benefits of VSD systems is also included.  
 
2.1 NORMAL OPERATION - GENERAL  
The current required for the ESP system in example 1, at flowing conditions as per Table 1, is 
approximately 27 A. This is approximately 93% of the motor nameplate current of 28.9 A. It 
must be appreciated that the current predicted will not b e a precise value, considering the 
small tolerances which are expected given the graphical methodology of determining the 
current (and also the inherent data uncertainties involved in oilfield data gathering, e.g. 
flowrate measurement tolerance etc).   
This is an example of a pump which is correctly matched to the well productivity, and also of a 
motor which is suitably sized for the pump, i.e. both pump and motor are operating at high 
efficiencies; the pump is close to the BEP and the motor is operating cl ose to nameplate 
power. In reality this sort of close match may not be achieved very often, however this serves 
to illustrate the type of operation that is possible in an ESP system. The case may be that it is 
desirable to operate at a slightly lower motor  power requirement for longevity reasons, this is 
determined on a well by well basis.  
2.1.1  Power Cable Losses  
A previously stated, the method of predicting current from the motor composite curve requires 
that voltage delivered to the downhole motor terminals is  nameplate value; 1080 V in the case 
of example 1. To achieve this voltage at the motor terminals, voltage losses in the power 
cable from surface to the motor must be calculated and allowed for.  
Voltage losses are a result of the natural resistance of the  electric cable to current flow. This 
is analogous to frictional pressure losses in a fluid carrying pipe, i.e. voltage can be 
considered equivalent to pressure, and current can be considered equivalent to fluid flow. The 
particular cable used in an ESP ap plication will depend on several factors, including the 
expected amperage, voltage drop and space available between the tubing and casing. In 
general, the cable should be selected to give less than 30 volts drop per 1000 ft of cable.

<!-- Page 40 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 40 of 55 25-November -2004  2.2 UNDERSIZED PU MP 
Example 2 illustrates the following important concepts in ESP operations:  
• Upthrust  
• Overloaded Motor  
• Corrective actions which may be taken when the two conditions above exist  
• ESP design considerations when IPR uncertainties are present.  
These issues are further discussed in the sections below.  
2.2.1  Pump Operating Conditions – Upthrust  
Key Point:   
• Pump operation outside the recommended range will most likely result in damage to the 
pump and subsequent premature failure.  
 
The first observation in example 2 is t hat the pump is not operating within its recommended 
envelope. In the pump curve of Figure 8, the recommended operating range is the shaded 
area in the centre of the figure, ranging approximately from 70 to 140 m3/d on the x -axis. If a 
pump is operating to the right of this interval, as in this instance, the pump is said to be in 
upthrust, whereas if the pump is operating to the left of this interval the pump is said to be in 
downthrust.  
The overall thrust on an impeller is the net  resulting force of the upward acting fluid pressure 
on the base of the impeller, the downward acting fluid pressure on the top of the impeller and 
the upward acting momentum of the fluid within the stage. When operating in the 
recommended range, most stag es are designed to be in light to moderate downthrust. 
Downthrust increases as the flow through the stage decreases (or as the operating point 
moves toward the left -hand side of the pump curve). The method of handling pump thrust 
varies depending on whethe r fixed or floating impellers are employed, however the net result 
is that operation in severe downthrust or upthrust will have a negative impact on pump 
longevity.  
This pump is operating in upthrust conditions, which, if not addressed, will most likely r esult in 
premature failure of the thrust bearings or some other component of the pump.  
 
2.2.2  Overloaded Motor  
Key Points:  
• Overload protection is designed to protect the motor from overloading and overheating 
and is generally set at 110% nameplate current value  
• If a system repeatedly trips on overload the setting should not be simply raised, the root 
cause of the problem should be addressed.  
 
The second problem with this ESP system is that the motor is overloaded. The nameplate 
current is the maximum recommended  current at which the motor should operate, therefore in 
a correctly designed ESP application the motor will operate at some value of current less than 
nameplate. In this instance the motor is operating at approximately 34 A, which is equivalent 
to 118% of  nameplate. This is a result of the power capabilities of the motor and the hydraulic 
power requirements of the pump being considered separately as opposed to being part of one

<!-- Page 41 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 41 of 55 25-November -2004  system, and consequently the two requirements have not been considered in tande m and are 
poorly matched. This situation presents two main problems:  
• The excessive current will most likely result in the premature failure of the motor  
• The current is above the level which should cause overload protection trips  
The switchboard, or surface  power controller, will have protection trips set at pre -established 
levels. Overload trips are generally set at 110% nameplate current, therefore the current 
levels experienced in the system described above are greater than this level. If the overload 
in this system has been set at 110% nameplate current it is apparent that it will immediately 
trip once flow has been established. Simply raising the overload until the system does not trip 
will result in a system which is operating outside its design limits and will result in premature 
motor failure. Potential action to alleviate this problem is described in the next section.  
 
2.2.3  Corrective Action Possible  
Key Points:  
• Upthrust conditions can be alleviated by choking the production rate back  
• Choking the well will  most likely also result in the BHP requirements decreasing, 
therefore reducing the motor loading  
• Restricting flowrate is uneconomic; a correctly designed system would allow the well to 
deliver maximum production.   
 
As discussed above, the ESP system in t his example has been poorly designed and is 
operating in a manner which is likely to result in premature failure of the pump or motor or 
both. The manner in which this should be addressed is relatively simple. As the pump is 
operating in upthrust, or on th e right hand side of the recommended operating range on the 
pump curve, it can be appreciated that a shift to the left on this curve would result in the pump 
at least operating in an improved condition. The pump curve x -axis parameter is flowrate, 
therefor e it can be seen that to move the operating point of the pump to the left, a reduction in 
flowrate is necessary. This can be achieved by simply choking back the well, resulting in an 
increased wellhead pressure and a reduced flowrate. Shifting the operatin g point by choking 
the well back to flow at 110 m3/d is illustrated in the pump curve in Figure 16 below:

<!-- Page 42 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 42 of 55 25-November -2004   
Figure 16: Altering Operating Point by Restricting Flow  
 
In this instance, choking the well bac k to a rate of 110m3/d would shift the pump operating 
point to approximately the best efficiency point (BEP), i.e. the highest point on the efficiency 
curve. The pump would now be operating as recommended, and the likelihood of premature 
failure has been g reatly reduced.  
The second issue with this ESP system is the overloading of the motor. It can be seen in 
Figure 16 above that the power requirement per stage has been reduced from 0.25 
BHP/stage to 0.2 BHP/stage. The pump power req uired is now:  
Total pump power required  = BHP/stage x fluid SG x No of stages  
    = 0.2 x 0.92 x 242  
    = 44.5 BHP.   
 
 
Total head    = head per stage x No of stages  
= 6.25 x 242  
= 1512.5 metres,  
from Figure 4 protector power  = 3.2 HP  
 
Total power    = pump power + protector power  
    = 44.5 + 3.2  
    = 47.7 HP.  
Converting this to kW gives 47.7 x 0.746 = 35.6 kW.  
  
    0       25       50       75       100       125       150       175       0       25       50       75       100       125       150       175       Eff       Hp       Meters        
Flow    -    Cubic Meters per Day        
S700        10%       20%       30%       40%       50%       
2.50       5.00       7 .50       10.00        12.50        
0.25       0.50       0.75       1.00       1.25       Fluid Specif    ic Gravity 1.00        Pump Performance    
Curve        1 Stage(s)        
3500 RP M    -    60    
Hz       
Head  
BHP Efficiency

<!-- Page 43 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 43 of 55 25-November -2004  This motor load of 35.6 kW is equivalent to 93% motor rating. Referring back to the motor 
curve in  Figure 7, the current obtained for this loading is approx 26 A, or 90% nameplate 
current. the pump and motor would now be operating in their respective correct ranges, 
therefore mitigating the risk of premature failure. However, this has been achie ved at the cost 
of reduced production; a correctly designed system would have allowed the higher production 
rate of 155m3/d with the ESP system functioning correctly.  
 
 
2.2.4  Considerations when Inflow Performance Uncertainties Exist  
Key Point:  
• Where there is si gnificant doubt as to inflow performance, it is preferable to undersize 
an ESP system as oppose to oversize.  
 
Section 2.2.3  demonstrates actions which may be followed to alleviate problems encountered 
when well performance is st ronger than predicted, and ultimately too strong for the ESP 
system deployed in the well (i.e. the pump is undersized). This results in a reduced production 
rate due to restricting the flowrate, however the pump will be operating correctly and risk of 
prem ature failure (due to upthrust at least) is minimised.  
If the situation is considered where the inflow performance is overestimated and the well 
performance is too weak for the ESP installed in the well, the pump will then be oversized and 
will be operati ng in downthrust, again presenting a risk of premature pump failure due to 
operating outside the recommended range envelope. In the upthrust scenario, measures can 
be taken to move the operating point inside, or at least towards, the pump operating envelop e 
by choking the well back as described above. However, in the case of an oversized pump 
operating in downthrust, the reservoir cannot supply enough fluids for the pump design 
criteria and there is no action which can be implemented to alleviate this probl em (excepting 
stimulation treatments etc). Therefore in the oversized pump scenario the options are to either 
work the well over, replacing the pump with an alternative design, or accept that the operating 
conditions of the pump are likely to result in pre mature pump failure.  
This demonstrates the requirement for accurate IPR data when planning an ESP system 
design. It also emphasizes that should any significant doubt exist as to the inflow performance 
of a well, it is prudent to undersize a pump as oppose to oversize due to the easier corrective 
action which may be taken if the IPR is not as predicted.

<!-- Page 44 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 44 of 55 25-November -2004  2.3 OVERSIZED PUMP  
Example 3 illustrates the following important concepts in ESP operations:  
• Increased power requirements between different ESP systems in the same well  
• Transformers and their use in ESP systems  
• Downthrust  
• Well pump off and gas locking  
• Underload protection  
These issues are further discussed in the sections below.  
 
2.3.1  Increased Power and Current Requirements  
Key Point:  
• The poorly designed system in example 3 has a surface current requirement (for the 
same applied surface voltage) of 237% of that of the efficient design in example 1, for 
the same well and flowrate. This illustrates the potential cost reductions that can be 
achieved in inefficient ESP systems.      
 
Example 3 used the same well as example 1 with the intent of demonstrating the contrasting 
power requirements of two different ESP designs (one correctly designed and the other poorly 
designed) in the same well, delivering the same productio n rate.  
Given that example 3 uses the same well as example 1, the lift requirements of the examples 
are identical. Therefore it is necessary to use 2 systems which deliver identical pump head 
values. This is achieved by selecting the appropriate number of  stages for the M3000 pump in 
example 3 which delivers an equal amount of head as that generated by the S700 pump used 
in example 1. In section 1.7.3.1  in example 1, the total head generated at 110 m3/d was 
established as 1512.5  m. From the M3000 curve in Figure 9 above a head of 9.1 m /stage 
can be determined for the M3000 at 110 m3/d, therefore the number of stages required to 
generate the same head at the same flowrate is 1512.5/9.1 ≈ 166 stages.  
The c ontrasting power requirements, for the same well at the same flowrate but with different 
ESP systems, can be seen in Table 10 below:  
 Example 1  Example 3  
Pump Power Required (kW)  35.6 82.2 
Current Required (A)  27 30 
Surface Volt age (V)  1172  2505  
 
Table 10: Contrasting power requirements of Examples 1 and 3  
The difference in pump power required is clearly apparent. However the difference in supplied 
electrical power is not so readily observed until the ef fects of the different surface voltages 
required, and subsequent transformer usage, have been evaluated.

<!-- Page 45 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 45 of 55 25-November -2004  2.3.2  Transformers  
Between the ESP system and the electrical power supply (i.e. from national power system on 
land systems and from the rig supply on offsh ore systems) there will invariably be a 
transformer used to alter the voltage to that which is required by the ESP system. This is 
because ESP systems generally require voltages which are different from the available power 
supply voltage. Transformers whic h increase voltage are known as step up transformers, and 
transformers which decrease the voltage are known as step down. The current in the different 
transformer sections varies inversely as the voltage, i.e. in a step up transformer the output 
voltage wi ll be greater than the input voltage but the output current will be decreased 
accordingly with regard to the input current. Transformers generally operate at relatively high 
efficiencies, between 97 and 99%, therefore transformer power losses can be ignore d for 
most ESP system calculations.  
 
In the event that current is measured prior to the transformer, the actual downhole current can 
be calculated from the following:  
Is = Ip x (N p/Ns)  
Where  Ip = primary current (surface supplied to transformer)  
 Is = do wnhole current (after transformer)  
 Np = number turns on the primary side of the transformer  
 Ns = number of turns on the secondary side of the transformer  
 
 
The ratio N p/Ns is also known as the transformation ratio, or turns ratio. Where the input and 
output voltages are known this can be calculated as follows:  
(Np/Ns) = (V p/Vs) 
Where  Vp = primary voltage (input side of transformer)  
 Vs = secondary voltage (output, or ESP, side of transformer)  
To obtain the different input electrical currents required in  the respective examples, it is first 
required to calculate the transformation ratio of each transformer utilised. If we assume that 
the input voltage for each system is 380V (primary voltage), the transformation ratio of the 
transformer used in example 1 can be calculated as follows:  
TR  = (Np/Ns) = (V p/Vs) 
 = 380/1172  
 = 0.324.  
The surface current requirement can then be calculated:  
Ip  = Is/(Np/Ns) 
Ip = 27/0.324  
Ip ≈ 83 A.

<!-- Page 46 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 46 of 55 25-November -2004  Similarly, the surface current requirement for example 3 can be calculated:  
TR = (Np/Ns) = (V p/Vs) 
 = 380/2505  
 = 0.152  
 
Ip  = Is/(Np/Ns) 
Ip = 30/0.152  
Ip ≈ 197 A.  
 
Therefore in example 3 the surface current requirement is 197 A, compared with 83 A for 
example 1, for identical electrical input supplies of 380 V. If the equipment used in example 3 
was to be replaced with the equipment originally specified in example 1, an input current 
reduction of 57% would be observed (alternatively, the ESP system in example 3 uses 237% 
more current than the ESP system in example 1 for the same flowr ate). Although the design 
in example 3 is extremely poor, this is a powerful demonstration of the current savings which 
may be achieved by appropriate equipment selection and correctly designed ESP systems. 
The principle of increased power consumption for the same work performed (and thus 
production rate obtained) is clearly demonstrated. This emphasises the need to optimise ESP 
designs in wells (considering matching the pump to the IPR and also the pump to the motor), 
particularly in regions where surface power requirements are an important economic factor.  
 
2.3.3  Pump Operating Conditions - Downthrust  
It is clear from the pump curve of Figure 11 that this pump is operating in downthrust. This is 
due to the pump capacity being greater th an the production which the well inflow performance 
can deliver. As discussed in section 2.2.4  above, there is no action (with regard to pump 
operation) which can be taken to alleviate this problem. This will most likely result in 
premature pump failure.  
 
2.3.4  Well Pump Off and Gas Locking  
Key Point:  
• Underload protection is vital in ESP systems to protect both the pump and motor from 
adverse conditions.  
 
Section 2.3.4  is designed to demonstrate one of the e ffects (gas locking) that can occur in 
oversized ESP systems, specifically with the intent of demonstrating the requirement and 
necessity of underload protection in ESP systems.  
As the pump rate in example 3 is greater than the well can deliver, this may result in the well 
being ‘pumped off’ and the pump gas locking. This may occur in an ESP whenever there is an 
excessive amount of free gas at the pump intake. Free gas (of a sufficient quantity) enters the 
intake stages and gas locks the pump; there is now  no liquid entering or being pumped by the 
ESP.     
The motor current requirements in this example were calculated as 30 A. In the situation 
where the well is being pumped off, the current would decrease gradually as the amount of

<!-- Page 47 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 47 of 55 25-November -2004  fluid available to the pu mp decreases (as the reservoir cannot sustain the pump rate and the 
intake pressure will be decreasing, increasing the proportion of free gas at the intake). At a 
certain point no fluid is available to the pump and the pump is gas locked.  
It is more appro priate to analyse this situation from a logical perspective than a purely 
mathematical calculation of current. There are two main effects to consider:  
1. A proportion of the fluid within the pump is now gas as oppose to liquid, which will result 
in a signific ant decrease in fluid SG  
2. The flowrate through the pump has dropped to zero. From the pump curve in Figure 11 
it can be seen that this results in a significant reduction in BHP/stage required.  
 
Referring to the calculation for total  power required by a pump:  
Total pump power required  = BHP/stage x fluid SG x No of stages  
It can easily be appreciated that both of the effects listed above will contribute to a large 
reduction in pump power required, as two of the terms in the right ha nd side of the above 
equation will have decreased significantly. This in turn leads to a reduction in the current 
required by the motor. The SG will have changed dramatically when the fluid traversing the 
pump changed from oil to gas – depending on tempera ture and pressure at the pump depth, 
‘typical’ gas SG figures are between 0.01 and 0.3 (these figures are considered in the 
average range – individual hydrocarbon reservoirs may vary outside this range). It can also 
be seen from the pump curve in Figure 11 that the power requirement per stage will have 
reduced from 0.7 to approximately 0.63 BHP/stage. If we assume that the fluid SG in the 
pump has an average value of 0.5, the power requirement becomes:  
Total pump power required  = 0.63 x 0.5 x 166  
    = 52.3 BHP  
    = 39 kW.  
 
If this value (which is equivalent to 36% motor rating) is then applied to the motor curve 
shown in Figure 10, an expected current of approximately 20 Amperes is obtained, which is 
equiva lent to 67% of the normal operating current as calculated in section 1.9.3 . The 
determination of absolute current requirement is irrelevant in this eventuality; the important 
principle is that the current requirement will be sig nificantly lower than during normal 
operation.  
Having established that in gas locking the current required in an ESP system is considerably 
lower than in normal operation, the significance of this must be analysed. The lowering of 
current in itself is not  so much an issue in the motor, however the reduction of required 
current is generally a result of a greatly reduced flowrate through the pump. This has two key 
implications:  
1. The pump will be operating outside it’s recommended parameters therefore damage t o 
the pump may occur  
2. The motor cooling is completely dependent on liquid flow past the motor.  
It is therefore apparent that both the pump and motor require protection from reduced current 
operation. In low or no flow conditions, motor burn out can occur in as little as one hour. 
Therefore preventing such an eventuality becomes crucial to prolonged pump and motor 
operation.

<!-- Page 48 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 48 of 55 25-November -2004  2.3.5  Underload Protection  
Key Points:  
• An underload trip setting of 80% normal operating current is generally accepted as a 
guidance point for underload setting, however this must be checked against BHP/stage 
at underload setting point on the pump curve prior to finalisation of the underload setting  
• A correctly set underload current level can automatically protect a pump from operating 
in adv erse conditions  
• Correctly utilised underload protection can safeguard a motor from overheating to 
destruction should a situation of low or no flow occur at the pump  
• The underload must be set above the idle amperage of the system – the idle amperage 
is the current the motor will draw when the pump it is attached to is performing no work. 
If the underload setting is below the idle amperage of the system, the unit may fall to the 
idle current when gas locking, for example, and eventually the motor would overhe at 
(due to no cooling liquid flow past the motor) to the extent that insulation was broken 
down resulting in catastrophic motor failure  
• The underload setting should also safeguard against deadheading, as described below.  
 
The above example clearly demonstr ates the requirement for automatic protection of ESP 
systems in the event of low currents. This is the purpose of underload protection. Underload 
protection is set to trip the pump when a certain low level of current is reached, thus 
protecting the pump fr om operating in extreme conditions and subsequent damage, and also 
protecting the motor from overheating due to low or no flow past the motor. Underload trips 
are generally set at a level of 80% of the normal operating current of the ESP system, 
however th is requires to be manually checked in individual ESP systems which may vary in 
their requirements. For example, if a pump was operating at normal conditions at the lower 
end of the pump operating range (i.e. towards the left side of, but still within, the shaded area 
in the pump curve), simply setting the underload at 80% of the normal operating current may 
allow the pump to run in quite severe downthrust conditions yet the pump would not trip on 
underload. Therefore the permissible flowrate, and hence powe r requirements, of the pump 
must be considered, with respect to the pump curve, prior to setting the underload.  
It is clear that underload protection is a vital part in the protection and correct operation of an 
ESP system, which can be summarised by the following:  
 
2.3.6  Deadheading  
Key Point:  
• Underload settings should be checked on the pump curve to ensure that they protect 
against adverse flow conditions (e.g. severe downthrust) and deadheading.  
 
When an ESP is operated against a closed (or blocked) surface valve, this is known as pump 
deadheading. Initial analysis of this situation might lead the operator to consider that this 
would result in an increased power requirement by the pump. The actual situation is just the 
opposite of this, however; once the void  between the pump and the surface closure has been 
filled and sufficiently compressed, there is then no further liquid flow through the pump, 
although a constant head is being maintained above it. Generally, the lowest power 
requirement, and therefore lowe st motor current requirement, occurs at zero flow conditions 
through the pump (as can be seen from a pump curve), therefore deadheading will result in a 
reduced current load.

<!-- Page 49 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 49 of 55 25-November -2004  Considering example 3 again, the power requirements can be determined for a dead heading 
situation (i.e. zero flow) from the pump curve as below in Figure 17. 
 
Figure 17: Determine power requirements and head for a deadheading system  
 
Total pump power required  = BHP/stage x fluid SG x No of stages  
    = 0.64 x 0.92 x 166  
    = 97.7 BHP.   
 
 
Total head    = head per stage x No of stages  
= 9.5 x 166  
= 1577 metres,  
from Figure 4 protector power  ≈ 3.2 HP  
 
Total power    = pump power + protector power  
    = 97.7 +  3.2 
    ≈ 101 HP.  
Converting this to kW gives 101 x 0.746 ≈ 75 kW, which is equivalent to 69% motor rating..  
 
Applying this power requirement to the motor curve is demonstrated in Figure 18 below:  
 0   100   200   300   400   500   600   700   800   0   100   200   300   400   500   600   700   800   Eff   Hp   Meters    
Flow  -  Cubic Meters per Day    
M3000    10%   20%   30%   40%   50%   60%   
2.50   5. 00   7.50   10.00    12.50    15.00    
0.50   1.00   1.50   2.00   2.50   3.00   Fluid Specific Gravity 1.00    Pump Performance  
Curve    1 Stage(s)    
3500 RPM  -  60 Hz    
Head  
BHP Efficiency

<!-- Page 50 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 50 of 55 25-November -2004  Figure 18: Determining current in a deadheading situation  
 
A value of approximately 28 A is obtained, which is equivalent to 93% of the normal operating 
current of 30 A. Therefore to ensure that the underload setting would protect against 
deadheading occurring in example 3 the underload setting would have to be no lower than 
93% of normal operating current. It should be considered that in this example the pump is 
running in quite severe downthrust; if the pump was operating close to the BEP the power per 
stage w ould be approximately 0.74 BHP (from Figure 17), which would result in an operating 
current of 31 A. Therefore in a correctly functioning pump of this size, the underload would 
have to be set to 90% of normal operating current to p rotect against deadheading. This 
illustrates that the pump curve should always be consulted before setting the underload trip 
level.  
In the absence of motor curves, checking that the underload setting will prevent deadheading 
can be performed by checking t he BHP per stage at zero flow conditions against the BHP per 
stage value during normal operation. For example, if the underload is set at 80% of normal 
operating current, the BHP/stage at deadhead (zero flow) conditions should be less than 80% 
of the BHP/s tage at normal operation. This will generally ensure that the underload setting will 
protect against deadheading, providing that the current curve is relatively linear (this is usually 
the case).  
In the event that a pump continually trips on underload (or  overload), this indicates a problem 
with the system, and the system should be thoroughly checked before attempting repeated 
restarts.   
 Borets 90-117 B5
05101520253035404550556065707580859095100
0 10 20 30 40 50 60 70 80 90 100 110 120
Output Power % RatedInput Power, Efficiency and PF (%)
0.005.0010.0015.0020.0025.0030.0035.0040.0045.0050.00
Current (A)
Input Power (%) Power Factor (%) Efficiency (%) Current A

<!-- Page 51 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 51 of 55 25-November -2004  2.4 VARIABLE SPEED DRIVE SYSTEMS  
2.4.1  Effects of Variable Speed Systems on Pumps  
Frequency changes result in specific effects on the behaviour of centrifugal pumps and 
induction motors. These have been introduced, along with the affinity laws, in section 1.10 
and will be further examined here.  
2.4.2  Affinity Laws  
Key Points:  
• The affinity law equations can be used to determine pump performance at differing 
frequencies  
• To assess the effect of altering frequency on well fluid production a system nodal 
analysis must be performed  
 
The parameters flowrate, frequency, head and BHP are related to each other in centrif ugal 
pump systems by the following three relationships which collectively are known as the affinity 
laws:  
 
Flowrate 1  = (Frequency 1/Frequency 2) x Flowate 2  
Head 1   = (Frequency 1/Frequency 2)2 x Head 2  
BHP 1   = (Frequency 1/Frequency 2)3 x BHP 2  
 
where flowrate 1 is at frequency 1, flowrate 2 is at frequency 2, head 1 is at frequency 1,  
head 2 is at frequency 2, BHP 1 is at frequency 1 and BHP 2 is at frequency 2.  
These laws allow the calculation of pump performance at frequencies other than that for 
which the pump curve is available. Care must be applied when using the affinity laws however 
in that the flow equation refers to the capacity of a centrifugal pump, i.e. this does not refer 
directly to an oil well application but instead to an unconstrained fluid source. More 
specifically this equation cannot be used to estimate the actual production change which will 
occur in an oil well as a result of a frequency change. This can only be achieved by 
performing a nodal analysis of the entire system which con siders the lift characteristics of the 
well and pump along with the inflow capability of the reservoir, i.e. the productivity of the well.  
It must also be noted that the affinity laws actually refer to frictionless incompressible flows, 
and are also strict ly speaking only valid under constant efficiency conditions. However, they 
are routinely applied in the analysis of oilfield ESP systems. In certain engineering fields the 
exponent in the BHP equation may be varied between the value of 2 and 3, although th e 
equations are generally applied as they appear above in oilfield applications.

<!-- Page 52 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 52 of 55 25-November -2004  2.4.3  Effects of Variable Speed Systems on Motors  
Key Points:  
In summation, a VSD system which varies voltage directly with frequency (as the vast 
majority of VSD systems do) r esults in a motor with the following characteristics:  
• Output power rating varies directly with frequency  
• Speed of rotation varies directly with frequency  
• Voltage rating varies directly with frequency  
• Current rating does not change with frequency  
• Torque pro duction does not change with frequency  
 
Some of the effects of frequency changes on motors have previously been introduced in 
section 1.10 and will be expanded upon here.  
The most effective manner in which to vary the speed of a n induction motor is by varying the 
applied voltage in direct proportion to the frequency, i.e. maintain the V/f ratio as constant. 
The reasoning for this methodology is as follows. A parameter known as slip is defined as the 
relative velocity between the rotating magnetic field produced by the motor stator and the 
actual rotation of the rotor. For an induction motor to be efficient it must be operated at low 
values of slip, as slip is directly proportional to heat loss in the stator windings. For a given 
torque (the actual force produced by the motor), the magnitude of slip depends directly on the 
strength of the rotating magnetic field – the higher the magnetic field strength the lower the 
slip (for any given torque) and hence the higher the efficiency of the motor. Therefore it can 
be seen that it is highly desirable to maximise the magnetic field strength to its full rated value 
in the stator at all times. The magnetic field strength varies directly with applied voltage and 
inversely with applied frequenc y, therefore it can be seen that to maintain the magnetic field 
strength at a constant (maximum rated) value at different frequencies the applied voltage 
must be varied directly with frequency. This principle is central to variable speed induction 
motor, a nd hence ESP, systems. Additionally there is a limiting magnetic field strength which 
can be applied in an induction motor, otherwise the iron core will become saturated which 
results in excessive iron and copper losses in the motor, decreasing efficiency.  This is why a 
large voltage value cannot simply be applied to the motor to increase power.  
The above conditions results in a motor which delivers constant torque at all frequencies, 
apart from very low frequencies when stator electrical losses reduce avai lable torque. This is 
normally compensated for by low speed voltage boosting, which provides the availability of 
constant torque even at low frequencies (additionally this technique also provides an 
advantage in starting in that full rated torque is availa ble at low starting frequencies with low 
currents, unlike traditional fixed speed across the line starters which typically require starting 
currents in the order of 5 to 8 times that of current rating).   
It must also be noted here that efficiency increase s with frequency, as motor power output 
varies with frequency but electrical losses generally remain fairly constant. However, the 
efficiency variation over the frequency range employed in ESP systems is relatively minor.

<!-- Page 53 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 53 of 55 25-November -2004  2.4.4  Summary of Frequency Change Eff ects 
This section is intended to list the changes which would expected for a given frequency 
change in an ESP system. The effects have been listed for a frequency increase; the effects 
of a frequency decrease are simply the opposite of those listed here. A  frequency increase in 
an ESP system will normally result in the following in an oil well:  
• Voltage will increase (it is increased in proportion to frequency)  
• Fluid production from the well will increase due to increased drawdown  
• The BHP required per pump s tage will increase  
• Current will increase   
• Head generated will increase  
• Bottom hole flowing pressure will decrease due to increased head generated  
• Well head pressure will most likely increase  
 
2.4.5  Analysis of Frequency Change Effects on Well Performance  
Altho ugh one of the affinity law equations calculates flow, this is only valid in the situation 
where there is unconstrained fluid available to the pump, i.e. the actual capacity of the pump 
as opposed to the flowrate obtained. To fully evaluate the effect whic h a frequency change 
has on production rate from a well requires a nodal analysis of the entire system, i.e. 
evaluation of vertical lift performance for the entire well at a range of production rates until the 
solution point with the inflow performance cur ve is found. This is a complex task which is 
generally performed with nodal analysis software. Superimposing the solution point on a 
pump tornado chart results in an illustration of a well’s performance at different frequencies. A 
typical chart can be seen  below in Figure 19.  
  Figure 19: Well performance solution point on tornado chart

<!-- Page 54 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 54 of 55 25-November -2004  The shape of the curve obtained in a chart as seen above will obviously vary from well to well 
depending on several parameters including well geome try, productivity, reservoir pressure 
and ESP system utilised.  
 
2.4.6  Potential VSD Benefits – Changing Well Conditions  
Key Points:  
• The increase in water cut (in the scenario outlined below) has resulted in an increase in 
motor loading which is too high for pro longed operation of the ESP  
• Reducing the frequency is possible in a VSD system which will allow continued ESP 
operation  
The ESP system in example 4 was operating close to the best efficiency point of the pump 
while the motor was operating at approx 99% rat ed power at the operating frequency of 53Hz. 
One potential advantage that a VSD can add to an ESP system is outlined below.  
Consider the situation where the water production from the well in example 4 has risen 
significantly (and perhaps unexpectedly) to a round 90%. The productivity of the well has 
remained relatively constant, therefore the production rate from the well has also remained 
constant (in reality the fluid rate will decrease due to increased hydrostatic fluid column 
pressure however for the sak e of this example we will assume that the production rate at the 
pump has remained constant). As the well fluid SG will now have significantly changed, there 
will be a corresponding change in power requirement of the ESP system. If the water SG is 
1.08, th e new composite SG of the produced fluid will be:  
(0.8 x 0.1) + (1.08 x 0.9)  
= 1.05.  
Total pump power required  = BHP/stage x fluid SG x No of stages  
    = 0.69 x 1.05 x 155  
    ≈ 112 BHP.   
Adding the 2.9 HP required by the protector results in a new tota l system power requirement 
of approx 115 BHP. It was previously established that the motor is rated at 89.5 HP at a 
frequency of 53Hz, therefore the new power requirement is approx 128% of motor power at 
53Hz. This is clearly not a desirable scenario; at 1 28% nameplate power the motor is going to 
burn out very quickly. In a fixed speed system this would undoubtedly result in a workover to 
change out the pump, motor or both. However, with a VSD in the system the frequency, or 
rotational speed, of the motor ( and hence pump) can simply be altered to reduce the loading 
of the system.  
As the frequency is reduced the power rating of the motor will decrease in proportion to the 
frequency. However due to the cubic nature of the BHP relationship in the affinity law 
equation, the pump power requirement will decrease significantly more than the motor rating 
decrease for a given frequency drop. Therefore at a certain lower operating frequency the 
pump power requirement will fall below that of the motor output, permittin g pump and motor 
operation within the recommended envelope.

<!-- Page 55 -->
BP Explo ration   Confidential  
ESP Current Predictions and Troubleshooting Guidelines  
 
 
 
  
BP0757 Final Report Rev No. 2  Page 55 of 55 25-November -2004  2.4.6.1  Discussion  
Key Points:  
• A VSD allows invaluable flexibility which can be used to maintain ESP operating 
conditions to within acceptable limits  
• A VSD can be used to ‘tune’ an ESP in situ to changi ng well conditions.  
 
It is clear that the flexibility that a VSD system provides would allow the well in this example to 
continue production when the water cut has risen to a level which would prohibit operation of 
a fixed speed system. In this example thi s has removed the requirement for a workover, 
which would otherwise be necessary in a fixed speed system.  
It could be argued in this instance that the root case of this problem was a fault of the original 
design and a fixed speed system should have been de signed to cope with high water cuts, 
i.e. include a bigger motor in the design. However real life instances are not always so clear 
cut, for example reservoir simulation may have strongly suggested that no water 
breakthrough was expected until much later, at which time a workover was planned anyway, 
or perhaps there was a long lead time on a suitable motor etc. Field planning is subject to 
inherent uncertainties which manifest themselves in a variety of ways; however the important 
principle which is demonst rated in this example is the flexibility that a variable speed system 
provides. This equally applies to inflow performance issues, i.e. the flexibility that a VSD 
provides can be used to tune the ESP in situ to well performance, or optimise the operating 
point of the pump when inflow and well performance has not materialised as predicted.  
     
2.4.7  Additional VSD Benefits and Considerations  
It is not within the scope of this document to provide a detailed explanation of variable speed 
systems and their design; however a brief overview of certain other VSD characteristics will 
be presented here.  
 
2.4.7.1  Design Considerations  
It is imperative that all components in the system including the motor, surface power supply, 
pump shaft etc are selected considering the maximum f requency. If a lower frequency is used 
in the design process the ratings of the components may be exceeded.  
2.4.7.2  Soft Start  
The greatest period of stress in an ESP system is during start up. It is readily apparent that 
starting an ESP at a lower speed (frequenc y) and therefore power, will reduce the electrical 
and mechanical stresses experienced during startup. VSD systems are routinely used to ‘soft 
start’ ESP’s at lower torque and current values than would be experienced by fixed speed 
systems, the speed can t hen be increased gradually and smoothly in an attempt to extend run 
life. 
2.4.7.3  Electrical Advantages  
A VSD can provide several electrical advantages including isolating the load (motor) from 
incoming switching and lightning transient voltages, eliminating frequ ency instabilities from 
generators and can provide some intelligent functions including automatic speed regulation, 
detection of backspin conditions and unit protection.  
2.4.7.4  Operation at Lower Speed  
In certain applications it may be advantageous to oversize th e motor and run the system at 
low speeds, for example in highly abrasive conditions. This tends to occur in situations when 
pulling costs are high and the extended run lives more than compensate for the extra cost of 
the larger motor.
