<!-- image -->

## ARTICLE IN PRESS

Ocean Engineering xxx (xxxx) xxx

Contents lists available at ScienceDirect

## Ocean Engineering

journal homepage: www.elsevier.com/locate/oceaneng

## Electric submersible pump vibration analysis under several operational conditions for vibration fault differential diagnosis

Galdir Reges a,* , Marcio Fontana a , Marcos Ribeiro b , Tiago Silva a , Odilon Abreu a , Ricardo Reis a , Leizer Schnitman a

- a Universidade Federal da Bahia, Mechatronics Program (PPGM), CTAI, Rua Prof. Aristides Novis, 02, Federaç ˜ ao, Salvador/BA, CEP 40210-630, Brazil b Petrobras Research and Development Center (CENPES/PETROBRAS), Av. Hor ´ acio Macedo, 950, Cidade Universit ´ aria, Ilha do Fund ˜ ao, Rio de Janeiro/RJ, CEP 21941-915, Brazil

## A R T I C L E  I N F O

Keywords: Vibratory behavior Synchronous frequency variation Differential diagnosis Correlation analysis Temperature influence

## 1. Introduction

Electrical submersible pumps (ESPs) are the second most common artificial  lifting  method  applied  worldwide  (Liang  et  al.,  2015), deployed in, it is estimated, 150,000 to 200,000 wells (Flatern, 2015). Electrical  submersible  pumps  account  for  approximately  10%  of  the world ' s crude oil production (Takacs, 2017). These systems are ideally suited to pumping high volumes at high pressure, and the petroleum industry applies the method to pump petroleum at a high flow rate in offshore applications.

An  electrical  submersible  pump  is  composed  of  several  smalldiameter centrifugal stages (typically 4 -9 in.) that are mounted serially, with an operational frequency range varying from 30 Hz to 60 Hz. In  a  submerged  ESP  installation,  a  multistage  centrifugal  pump  is coupled to a magnetic induction motor using a protector seal assembly filled with an insulating fluid that is heavier than water. The electric motor  is  cooled  by  the  oil-well  fluids  that  pass  through  the  motor

## A B S T R A C T

An Electric Submersible Pump (ESP) vibration analysis was performed, considering different wear states and operational conditions. The pumps were tested with different fluid viscosities, operating points, and speeds to evaluate their vibration behavior, with the aim of providing characteristics for non-invasive differential vibration diagnosis. A specific frequency spectrum estimation method is described, focusing on the extraction of frequency component vibration amplitudes used in the petroleum industry-standard vibration analysis. A time-interval definition  procedure  was  proposed  to  reduce  signal  amplitude  losses  due  to  variation  of  synchronous  operating frequency. The results indicate that the frequency component peak amplitudes can be more accurately identified during synchronous frequency variation by the proposed method than by typical estimation methods. In this study, an ESP vibration differential diagnosis was achieved by analyzing relations between orders of the synchronous frequency, and by distinguishing that the synchronous component amplitude rose approximately proportionally to the square of the rotating speed; this differentiates unbalance fault from a bent shaft or a misalignment. A correlation matrix analysis is provided to demonstrate that variation in the fluid-temperature difference between the pump intake and discharge is related to the vibration amplitude variation in a pump with a vibration fault.

housing. For subsea systems, the output motor power may be higher than 1000 hp. The structure can reach more than 40 m in length, and the pump can operate in a high-temperature environment, pumping fluids containing abrasives (Minette et al., 2016).

The risk of vibration problems is increased in equipment such as ESP systems due to the difference between its considerable length and its small axial diameter. The factory acceptance evaluation process of the ESP system for fault diagnosis includes an expert vibration analysis of collected accelerometer signals during a test well operation, following

The installation and intervention costs of ESP-based pumping systems are usually higher than those of other elevation methods, particularly in the case of deep-sea, underwater wells (Ribeiro et al., 2005). In addition to the high costs of installation and intervention, faults in this equipment usually cause significant production losses since they typically operate in high-production petroleum wells. A careful evaluation of  ESP  systems  before  installation  is  critical  to  prevent  premature operational failure.

* Corresponding author. E-mail address: galdir.junior@ufba.br (G. Reges).

[https://doi.org/10.1016/j.oceaneng.2020.108249](https://doi.org/10.1016/j.oceaneng.2020.108249)

0029-8018/© 2020 Elsevier Ltd. All rights reserved. Received 17 April 2020; Received in revised form 15 October 2020; Accepted 17 October 2020

<!-- image -->

G. Reges et al.

the recommendations found in the American Petroleum Institute ' s recommended practice document 11S8 (API RP 11S8). Despite the rigorous tests performed to detect possible faults, ESP systems still have relatively short run-lives (Borling et al., 2008; Childs et al., 2014), and vibration is the leading cause of failure (Bremmer et al., 2006; Durham et al., 1990; Yao et al., 2011).

The API RP 11S8 analysis procedure may suggest up to four different faults with the same probability of producing a symptom, so the correct fault  diagnosis  is  achieved  by  disassembling  the  equipment  and  performing an exhaustive evaluation of the many parts to differentiate the possible  failures  indicated.  Electrical  Submersible  Pump  vibration analysis studies are rare, especially using multiple operating conditions and  fluids.  In  Rauber  et  al.  (2013),  for  example,  a  system  for  the detection and diagnosis of faults ESP systems using a dataset composed of accelerometer sensor data examples from ESP string tests labeled with only three different categories of faults: normal, unbalance or misalignment. The data examples were labeled by visual inspection of the frequency spectra obtained from the Fourier transform of the raw vibration signal. The system used conventional Fourier analysis, which includes frequency spectrum estimation, to extract the root mean square (RMS) amplitude from frequencies from first and second orders (harmonics) of the shaft speed. The results showed an accuracy of around 80%. In Boldt et al. (2014), a performance analysis of automatic classifiers was presented, using a dataset composed of accelerometer sensor data examples from ESP string tests labeled with one of two categories: normal and unbalance. The study used Fourier analysis to extract the amplitude from frequencies of six different orders (harmonics) of the shaft speed. The results showed an accuracy of 98.5%. In Rauber et al. (2017),  a  comparative  study  of  classifier  architectures  for  automatic fault diagnosis was presented, using a dataset composed of accelerometer sensor data examples from ESP string tests labeled with one of four categories: normal, unbalance, misalignment, and motor rubbing. The study used Fourier analysis to extract the frequency spectra, and statistical features were computed from it. The results showed an accuracy of  around  80%.  These  cited  studies  do  not  mention  concerns  about synchronous frequency variation or strategies to reduce amplitude loss in the frequency spectrum estimation. The results of these studies indicate that the accuracy decreased with more vibration-fault categories, even  using  different  advanced  machine-learning  methods  and  architectures.  The  studies  have  in  common  that  the  labeling  process  was mainly oriented by the industry standard.

The API RP 11S8 does not describe a specific method for estimating frequency  component amplitudes in  the vibration  signals.  Therefore, technicians apply different spectrum estimation methods, with different accuracies.  Conventional  methods  consider  the  vibration  signals  as stationary,  but  variation of  the synchronous operating frequency has been observed in several ESP facility tests with different configurations. The  synchronous  operating  frequency,  or  simply  synchronous  frequency, is the shaft speed, which is approximately the motor ' s magnetic rotating field, with the difference of a slip frequency that varies with the torque  load  (Randall,  2010).  Gas  interference  or  reservoir  pressure variation are some of the causes of ESP shaft-speed variation. A signal component frequency variation over time reduces the amplitude accuracy of the frequency spectra (Brandt and Wiley, 2010).

Some of the faults covered by the API RP 11S8 analysis process could be differentiated according to the relationships between synchronous frequency orders ' amplitudes. For example, following the API procedure only, high vibrations at the synchronous frequency (1X) indicate unbalance, bent shaft, and misalignment faults. However, usually the bent shaft and misalignment faults produce high vibrations in the 2X order synchronous frequency also (Adams, 2010; Betta et al., 2002; Patel and Darpe, 2009; Scheffer and Girdhar, 2004). Observing the relationship between frequency orders can help the differential diagnosis.

This study aims to investigate ESP vibratory behavior, looking for vibration  characteristics  beyond  the  ones  observed  by  the  industry ' s recommend  practice,  API  RP  11S8,  that  can  differentiate  the  health Ocean Engineering xxx (xxxx) xxx condition of pumps and be useful for vibration fault detection and differential vibration diagnosis. Section 2 presents the experimental setup, procedures,  and  methods  of  vibration  data  acquisition  following  the industry  standard ' s  recommendations,  with  two  pumps  of  the  same model but in different unknown health states, seven different operating conditions, five different operating speeds, and two fluids of different viscosities.  Fluid  flow,  pressure,  and  temperature  data  were  also collected. A frequency spectrum estimation method is proposed in Section  2.3,  focusing  on  extracting  frequency  component  amplitudes observed in the API RP 11S8 procedure analysis and on reducing the amplitude estimation loss due to frequency variation. In Section 3, the ESPs ' vibration is analyzed by using the industry-standard analysis on the frequency spectra estimated by the proposed method. The vibration behavior is examined separately against fluid change, rotating speed change, and operating point change. In Section 3.5, a correlation analysis is performed, looking for unanticipated correlations between temperature differences and vibration amplitude.

## 2. Experimental tests and methods

## 2.1. Experimental setup

The Artificial Lift Laboratory of the Industrial Automation Technological Training Center at the Federal University of Bahia (UFBA) was used for the ESP tests. The facility was built with industrial equipment to reproduce the petroleum well-field environment in a laboratory. The facility is installed in the midspan of a spiral staircase in the Polytechnic School with 2.5 m of free diameter and 32 m of height, as shown in Fig.  1a.  The  Artificial  Lift  Laboratory  is  supported  by  Petrobras  S/A (Brazilian Petroleum Corporation) and other partners through research and development projects, mainly in the oil-lifting field.

The ESP system ' s tubular production string was designed to handle output pressures of up to 1500 psi. Allen-Bradley sensors measure the oil well temperature and pressure at the pump intake and discharge and the fluid flow at the pump discharge. The Allen-Bradley temperature sensor model was 837E-DC1BN1A1D4,  the  pressure sensor was 836EDC1ER1D4, and the fluid-flow sensor was 839E-DC1BA1A3D4. Table 1 presents information about these measurement devices.

Fig. 1b shows a schematic diagram of the experimental configuration. The ESP system pumps fluid from an artificial well to a tank at the top of the building, and the fluid flows back to the artificial well in a closed circuit. The system was instrumented to control and collect data through  a  supervisory  control  and  data  acquisition  (SCADA)  system installed in the laboratory control room. Two data acquisition systems receive  sensor  signal  data,  one  from  the  accelerometers  and  another from all other devices.

The ESP vibration acquisition was performed following the recommend practice  document  11S8  (API,  2012),  using  18  accelerometers orthogonally grouped in pairs, as shown in Fig. 2a. Six accelerometers were installed in each ESP system equipment (ID numbers 1 -6 in the motor, 7 -12 in the seal, and 13 -18 in the pump). All accelerometers were fixed in the ESP sections with a support that was designed and built for the purpose and fastened with a steel belt, as shown in Fig. 2b. The 18 accelerometers were industrial quartz shear ICP ® model 624B11 by IMI Sensors with 100 mV/g model sensitivity. Table 2 shows the accelerometers ' individual  sensitivity  from  the  manufacturer ' s  accredited calibration. During data processing, the individual calibrated sensitivity was used.

The  vibration  signal  acquisition  system  configuration  included  a computer, data acquisition hardware, accelerometers, and data acquisition software developed by our research team. The data acquisition hardware  connected  the  accelerometers  to  the  computer.  It  was composed of a data acquisition chassis and five data acquisition modules installed in the chassis. The chassis model was cDAQ-9172, and the data acquisition  modules  were  NI-9234  models,  both  from  National  Instruments  (NI).  The  chassis  provided  measurements,  timing  control, G. Reges et al.

(A)

<!-- image -->

Fig. 1. The experimental facility: a) The artificial oil wells of the Artificial Lift Laboratory installed in the midspan of a 32 m tall spiral staircase in the Polytechnic School at UFBA, b) A schematic of the experimental configuration.

<!-- image -->

Table 1 Measurement devices.

|               | Temperature sensor   | Pressure sensor   | Fluid-flow sensor   | Accelerometer                |
|---------------|----------------------|-------------------|---------------------|------------------------------|
| Range         | - 50 … + 150 ◦ C     | 0 … 1500 psi      | 0.03 … 3 m/s        | ± 490 m/s 2                  |
| Repeatability | < 0.1 ◦ C            | < 0.2%            | 0.03 m/s            | 9810 μ m/s 2 (1 - 10,000 Hz) |
| Accuracy      | < 0.2 ◦ C            | < 0.5%            | ± 10% on this range | ± 1%                         |

synchronization, and data transfer between input -output modules and an  external  computer  host.  The  NI-9234  module  was  a  four-channel dynamic signal acquisition module with 24-bit resolution, up to 51.2 kS/s  (where  kS  is  a  thousand  samples)  maximum  sampling  rate  per channel, ± 5 V input, 102 dB dynamic range, and antialiasing filters. This project used a 4267 kS/s sampling rate. A customized data-acquisition software  was  developed  in  VB.NET  language,  using  the  National  Instruments Measurement Studio. The software can be used to visualize signals  in  real-time  and  to  store  vibration  signals  with  experiment metadata, such as operating settings (speed, flow/pressure), ESP components used, accelerometer serial numbers, and sensitivities.

Two  used  Baker  Hughes  pumps  were  tested,  both  400PMXSSD models, series 400, type P4, with 70 stages. One of the pumps came from an operational oil well and the other from the owner ' s storage, and they were  in  different  health  conditions.  The  pump  model  has  a  recommended flow range from 24 to 95 m 3 /D. The best efficiency point (BEP) at 3600 RPM operating with water is 72 m 3 /D with 48% efficiency, with

0.22 kW power and 8.8 m head per stage at BEP.

Each pump was tested with two different viscous fluids. The fluids were produced by Petrobras and formulated from paraffinic petroleum mineral oils. Fluid samples were taken to measure the fluid with a digital viscometer, an SVM 3000 from Anton Paar. To take the fluid samples, the  test  oil  well  was  fed  with  each  fluid,  the  recirculating  pumping system was operated until it entered a steady state, and then samples were taken. Tables 4 and 5 show the fluids ' descriptions: the commercial product name, specific mass, and kinematic viscosity at several tested temperatures. Fluid #2 was a mixture because pure LUBRAX XP 220 is too viscous to be operated by the ESP system used in the experiments.

A set of a Baker Hughes components composed of a motor (model FMHX 18HP 465V/25A, Serie 450), a seal chamber (model FSB3XFER SB PFSA HL, Serie 400), and a gas separator (model FRX N AR) were used in all the experiments with both pumps to compare the equipment ' s vibratory influence. Table 3 presents the geometrical details of the ESP system components.

The operating performance curves of the pump (flow versus pressure at a specific speed) were adjusted to the viscosity of the fluids used in the experiments because the manufacturer ' s performance curves were based on tests with water at 20 ◦ C and 3560 rpm. As suggested in Borges et al. (2017), Turzo ' s method (Takacs, 2017) provided the best performance-curve  fitting.  Thus,  this  paper  uses  Turzo ' s  method  to obtain the performance-curve corrections. The viscosity at 50 ◦ C was used to correct the manufacturer ' s performance curves because it was the  average  pump  intake  temperature  observed  during  tests  under steady-state  conditions,  as  observed  by  the  industry  standard  and methods for correcting operating performance curves.

To perform the experiments, each pump was installed in the test well G. Reges et al.

<!-- image -->

(B)

Fig. 2. The ESP system accelerometer installation schematics: a) Accelerometer distribution between the three main equipment, b) The accelerometer fixing with a support designed and built for the purpose, fastened with a steel belt.

<!-- image -->

Table 2 Accelerometers used for vibration signal data acquisition.

|   Acc. ID # | Location     | Axis   |   Calibrated sensitivity (mV/g) |
|-------------|--------------|--------|---------------------------------|
|          18 | Pump Top     | Y      |                              99 |
|          17 | Pump Top     | Z      |                              96 |
|          16 | Pump Middle  | Y      |                              99 |
|          15 | Pump Middle  | Z      |                              98 |
|          14 | Pump Base    | Y      |                              98 |
|          13 | Pump Base    | Z      |                              97 |
|          12 | Seal Top     | Y      |                              97 |
|          11 | Seal Top     | Z      |                              98 |
|          10 | Seal Middle  | Y      |                              99 |
|           9 | Seal Middle  | Z      |                              99 |
|           8 | Seal Base    | Y      |                              96 |
|           7 | Seal Base    | Z      |                              98 |
|           6 | Motor Top    | Y      |                             100 |
|           5 | Motor Top    | Z      |                              99 |
|           4 | Motor Middle | Y      |                              99 |
|           3 | Motor Middle | Z      |                              96 |
|           2 | Motor Base   | Y      |                              99 |
|           1 | Motor Base   | Z      |                              97 |

and tested operating with each fluid. Seven different operational points and  five  different  rotational  speeds  were  applied,  resulting  in  70 different experimental tests per pump with each fluid, a total of 140

experiments. The rotating speeds were 2400, 2700, 3000, 3300, and 3600 rpm (40, 45, 50, 55, and 60 Hz). The operating points were derived from the viscosity-corrected pump-performance curves: the minimum recommended flow (MIN), best efficiency point (BEP), maximum recommended flow (MAX), and four additional intermediate points:

1.  MIN
3.  66% of the BEP flow
2.  50% of the BEP flow
4.  83% of the BEP flow
6.  117% of the BEP flow
5.  BEP
7.  MAX

In each test, the pumping system was started at the preset speed and the flow rate was adjusted by the discharge valve so that the system reached the operating flow point to be tested. After the system entered a steady state, data collection from the measurement sensors was started. Finally, after 160 seconds of steady-state testing, the data collection was terminated, and the test procedures were restarted.

G. Reges et al.

Table 3 Geometrical details of the ESP system components.

|          | Motor    | Seal chamber   | Gas separator   | Pump     |
|----------|----------|----------------|-----------------|----------|
| Length   | 1.37 m   | 1.71 m         | 0.81 m          | 2.14 m   |
| Diameter | 11.43 cm | 11.43 cm       | 10.16 cm        | 10.16 cm |
| Weight   | 97 kg    | 72 kg          | 34 kg           | 109 kg   |

Table 4 Fluid #1: LUBRAX XP 10.

|   Temperature ( ◦ C) |   Density (kg/m 3 ) |   Visc. (Cstk) |
|----------------------|---------------------|----------------|
|                   30 |               845.9 |         14.279 |
|                   35 |               842.6 |         12.014 |
|                   40 |               839.3 |         10.212 |
|                   45 |               836.0 |          8.780 |
|                   50 |               832.7 |          7.628 |
|                   55 |               829.4 |          6.682 |
|                   60 |               826.0 |          5.914 |

## 2.2. ESP vibration analysis

In the API RP 11S8 document, which includes considerations and definitions of vibration in ESP systems, the potential sources of vibration are listed, for example, as mass unbalance of materials, misalignment of rotating components, flow disturbance from turbulence and cavitation, journal  bearing  rotation,  oil  whirl,  and  mechanical  rubbing.  This document  also  presents  relations  between  vibration  frequencies  to probable  causes.  These  vibration  frequencies  are  orders  of  the  synchronous frequency (X rpm), which is approximately the rotation speed. For example, in the API RP 11S8 document, vibrations at 2X frequency (twice the synchronous frequency), are related to bent shaft fault and misalignment fault as probable causes. In another example, vibrations at 1/2X frequency (half the synchronous frequency), are related to mechanical rub fault and bearing rotating fault as probable causes.

Operation at critical speeds is not recommended, so the vibration limit analysis must account for this possibility. Resonance occurs when the  vibration  frequency  matches  a  natural  frequency  of  the  support system, amplifying the vibration; a critical speed is one that causes this phenomenon. There are some cases of critical speeds found in the range of operation speeds recommended by the manufacturer (Castillo et al., 2019;  Minette  et  al.,  2016).  Usually,  the  vibration  increases  proportionally to the operating speed. A critical speed is a possibility when there is a sudden increase in the vibration amplitude at a specific speed followed by a drastic reduction at a higher speed.

Severe vibration can decrease the ESP system ' s run-life, as with any rotating  machinery.  For  all  ESP  components,  the  API  recommends  a maximum  vibration  velocity  of  0.156  in/s  peak  amplitude  for  each synchronous frequency (1X rpm) and 0.100 in/s peak amplitude for all other frequency components, measured in the chassis of the equipment. This limit must be applied for operation in the manufacturer ' s recommended ranges of flow, pressure, and speed.

## 2.3. Frequency spectrum estimation

Typically, the vibration frequency spectrum estimation of rotating machines operating at a fixed speed considers the vibration signals to be stationary. In this way, the linear spectrum estimator is used with the highest  signal  length  acquired.  This  ensures  the  highest  possible  frequency resolution to guarantee the maximum distinction between vibration  phenomena.  The  linear  spectrum  estimator  is  created  by applying the discrete Fourier transform (DFT) to the signal multiplied by a  window  function  of  the  analyst ' s  choice.  However,  synchronous operating  frequency  variation  was  observed  in  ESP  experiments  in different  experimental  configurations  and  laboratories.  The  variation may be caused by, for example, gas interference or variations in reservoir level. Whatever the cause, signal frequency variation may reduce the amplitude accuracy of the frequency spectra (Brandt, 2011). The signal frequency variation observed in the experiments is not easy to detect and is small relative to transient signals, but it is enough to reduce the amplitude accuracy, as will be demonstrated in the Results section.

Table 5 Fluid #2: A mix of 67% LUBRAX XP 10 and 33% XP 220.

|   Temperature ( ◦ C) |   Density (kg/m 3 ) |   Visc. (Cstk) |
|----------------------|---------------------|----------------|
|                   30 |               858.8 |         29.545 |
|                   35 |               855.6 |         24.089 |
|                   40 |               852.3 |         19.928 |
|                   45 |               849.1 |         16.701 |
|                   50 |               845.8 |         14.150 |
|                   55 |               842.5 |         12.129 |
|                   60 |               839.3 |         10.489 |

Spectral  frequency  resolution  is  a  consequence  of  the  frequency increment and the use of time-window functions. The frequency increment is the distance between two frequency values in the frequency spectrum, which is Δ f = 1 / T , so it depends only on the measurement time window, T. The use of time-window functions offers better frequency amplitude representation but causes an energy distribution of the peak amplitude by the size of the window ' s main lobe; thus, two closed-signal  frequency  components  may  superpose  each  other.  The minimum frequency resolution needed to distinguish all API RP 11S8 frequency components was estimated using equation (1).

To  deal  with  signal  frequency  variation,  this  paper  proposes  to reduce the measurement time window to the minimum necessary to identify signal components. The reduction of the time window reduces the  spectral  frequency  resolution,  resulting  in  possible  difficulties  in identifying  signal  components;  in  this  case,  the  necessary  minimum frequency  resolution  must  be  estimated  to  find  the  minimum  time window.

<!-- formula-not-decoded -->

where Δ Xmin is the minimum difference between API RP 118 synchronous frequency orders (X), fo min is the minimum operating frequency tested, L m is the width of the main lobe of the window function used, and four is a scalar used to guarantee a minimum distance of two free frequency increments on both sides of each API RP 118 frequency order. The minimum time window needed is

<!-- formula-not-decoded -->

In this study, the minimum operating frequency was 40 Hz and the Hanning window was used, which has a main lobe width of two. The closest  API  RP  11S8  frequency  orders  are  0.48X  and  0.5X,  and  its respective minimum difference is 0.02. From equations (1) and (2) an estimate of a 10-second minimum time interval was obtained.

In the data processing, first, the signals are converted from volt units (V) to acceleration units (m/s 2 ) according to the individual calibrated sensitivity of each accelerometer, as shown in Table 2, and then converted from the metric system to the imperial system, which is the system used by the API RP 11S8. The direct current (DC) voltage level was removed by subtracting the mean of each signal.

With the minimum time interval Tmin determined, the accelerometer signals were processed according to the schematic diagram shown in Fig. 3 to obtain their frequency spectra.

The trapezoidal integration was used to convert acceleration units to velocity units (in/s) as the industry-recommended practice uses velocity units  to  evaluate  the  vibration.  A  Butterworth  IIR  high-pass  filter  of order two with a cut-off of 10 Hz was applied, pre- and post-integration, to  eliminate  low-frequency  anomalies  common  to  the  integration process.

The truncation required to convert the signal into a finite length G. Reges et al.

Fig. 3. The procedure used to obtain the accelerometer signal frequency spectra.

<!-- image -->

causes a leakage effect, which leads to an amplitude error in the frequency spectrum. The signals were processed with the Hanning window to reduce the leakage effect. The Hanning window balances noise injection and reduced amplitude inaccuracy. The Hanning window has a main lobe of two frequency increments, which was used to calculate the minimum time window above. The coefficients of a Hanning window are

<!-- formula-not-decoded -->

where N is the length of the window and n is the index of each coefficient. The Hanning-windowed signal was then the multiplication of the samples x ( n ) of sampled signal x with the coefficients of the Hanning window

<!-- formula-not-decoded -->

For the spectral content of the signals, the DFT was calculated for each signal by

<!-- formula-not-decoded -->

where x w ( n ) are samples of a Hanning-windowed signal with N samples, and X ( k ) are the DFT bins of x ( n ) , where k are indexes of the DFT bins, and i is the imaginary number. The discrete frequencies in the DFT are

<!-- formula-not-decoded -->

The computation of DFT is efficiently carried out by an Fast Fourier Transform (FFT) algorithm (Oppenheim, 1999).

In computing the frequency spectrum, the single-sided spectrum is adopted, as is shown in the following formula:

<!-- formula-not-decoded -->

The  windowing  process  removes  energy  from  the  signal,  proportional  to  the  sum  of  the  window-function  coefficients  used,  and  to compensate  for  this  is  necessary  to  use Aw as  a  scalar  amplitude correction factor (Brandt, 2011)

<!-- formula-not-decoded -->

which, for the Hanning window is precisely two. Then, the final spectrum is

<!-- formula-not-decoded -->

For  the  peak  amplitude  extraction  of  the  API  RP  11S8  frequency orders,  the  algorithm  first  identifies  the  synchronous  frequency  by looking  for  the  highest  peak  amplitude  in  a  10%  range  around  the equipment ' s operating speed (with the range accounting for motor frequency slip). With the synchronous frequency, the peaks of the API RP 11S8 orders are identified by searching for the highest peak amplitude within a range determined by twice the frequency increment around the synchronous frequency multiplied by the values of the API RP 11S8 orders (i.e., 1X, 2X, 0.42X to 0.48X).

## 2.4. Spectrogram

The  spectrogram  is  typically  obtained  by  applying  a  fixed-length moving window to the time-varying data sequence before computing the  spectrum,  which  is  the  short-time  Fourier  transform.  Its  timewindow  length  is  chosen  by  considering  the  trade-off  between  the time and frequency resolutions obtainable (Lee and Han, 1998).

In  this  study,  the  typical  process  to  generate  spectrograms  was applied to the raw accelerometer signal, using five times the samples of the sampling rate (4267 x 5) as the window size (5 seconds), and an overlap of 200 samples between windows.

## 2.5. Correlation analysis

Correlation analysis is a method for measuring the covariance of two random  variables  in a matched  dataset. Covariance  is typically expressed as the correlation coefficient of  two variables, X  and Y.  A correlation coefficient is a unitless number that varies from -1 to + 1. The sign of the correlation coefficient shows if the correlation is positive or negative, and the magnitude shows the correlation force between X and Y (De Lima et al., 2009). A negative coefficient indicates that as one variable increases, the other decreases; a positive coefficient indicates that as one variable increases, the other also increases.

Pearson ' s linear correlation coefficient p ( x , y ) is defined as

Pearson ' s linear correlation coefficient, one of the most frequently used linear correlation coefficients, was used here.

<!-- formula-not-decoded -->

where x i and y i are samples of x and y indexed with i , x = ∑ n i = 1 ( x i ) / n , and

## ARTICLE IN PRESS

G. Reges et al.

<!-- formula-not-decoded -->

The correlation matrix of two variables is the matrix of correlation coefficients for each pairwise variable combination:

<!-- formula-not-decoded -->

Since x and y are always directly correlated to themselves, the diagonal entries resolve to one:

<!-- formula-not-decoded -->

In this study, a correlation matrix was created using the seven sample values of variables from the experiments with seven different operating points, but at the same speed of 3600 rpm. The variables used in the matrix are well-intake fluid temperature, well-discharge fluid temperature, intake -discharge temperature difference, Z-axis accelerometer 1X order peak vibration amplitude at the top of the pump, and well-fluid flow discharge.

## 3. Results and discussion

In Section 3.1, the amplitude accuracy of the frequency spectrum estimation method is compared to the typical method applied to the quasi-stationary vibration signals acquired in the experiments. In Section  3.2,  the  vibration  of  the  pumps  is  analyzed  using  the  industrystandard process, which leads to various possible diagnostics. Sections 3.3, 3.4, and 3.5 present the search for vibration patterns beyond the typical ESP vibration analysis to provide a non-invasive fault differential diagnosis. In Section 3.3, the vibration behavior at different accelerometer positions and in the tests with different fluids is analyzed. In Section  3.4,  the  vibration  behavior  in  tests  at  different  speeds  is analyzed.  Finally,  in  Section  3.5,  the  vibration  behavior  in  tests  of different operating points is analyzed.

## 3.1. The frequency spectrum of the time-domain vibration signals

Time-domain signal stationarity is essential to the accuracy of frequency spectrum estimation, so spectrograms were used to evaluate the behavior  of  signal  components  in  time  before  performing  the  main Ocean Engineering xxx (xxxx) xxx analyses. Fig. 4 shows spectrograms of 160-second signals from the Zaxis accelerometer on top of Pumps #1 and #2, operating with Fluid #1 at 3600 rpm in the BEP. The highest magnitude is in yellow and shows the synchronous frequency vibration of the 160-second accelerometer signal. The synchronous frequency of Pump #1 varied from 56.45 Hz to 56.35 Hz, and that of Pump #2 varied from 56.75 Hz to 56.65 Hz. The slight frequency variation observed, shown in Fig. 4a and b, is probably due  to  fluid-temperature  and  viscosity  variation  during  the  data collection. This change in frequency may be relatively small, but it reduces the amplitude accuracy of a high-resolution frequency spectrum, which may impair a vibration analysis based on peak limits.

The results show that the minimum time-signal interval presents a greater  amplitude  accuracy;  thus,  this  was  the  time-signal  interval chosen for vibration analysis in all experiments.

As shown in Section 2.3, equation (1) and equation (2) were used to obtain an estimate of a 10-second minimum time interval to identify API RP 11S8 frequency orders and to minimize frequency variation over time. Fig. 5 shows the frequency spectra obtained from a 160-second time signal and a 10-second time signal from the Z-axis accelerometer fixed on top of Pumps #1 and #2, operating with Fluid #1 at 3600 rpm at the BEP. The figure shows that API RP 11S8 synchronous operating frequency (X) orders were correctly identified by the described method of  frequency-spectra  estimation  and  amplitude  extraction  using  both time window intervals. Fig. 5a is the frequency spectrum of the 160-second time signal from Pump #1, the 1X amplitude peak of which was 0.05 in/s; the corresponding peak in the 10-second time signal was 0.08 in/s (Figs. 5c), 60% higher. In the frequency spectra from Pump #2, the 160-second time-signal 1X peak was 0.140 in/s (Fig. 5b), which was below the API RP 11S8 limit, but when using the 10-second time window, the evaluated 1X peak amplitude was 0.313 in/s (Figs. 5d), 120% higher. This reveals that the vibration in this pump was above the API RP 11S8 limit. The other API RP 11S8 frequency orders showed similar differences in amplitude using the shorter time signal.

## 3.2. API RP 11S8 vibration diagnosis of the pumps

Table 6 shows the vibration peaks of each API RP 11S8 synchronous frequency order during the two pump experiments at 3600 rpm at the BEP with Fluid #1.

Pump #1 did not show amplitudes above the vibration limits in any G. Reges et al.

Fig. 4. Spectrograms of 160-second signals from the Z-axis accelerometer on top of Pumps 1# and #2, operating with Fluid #1 at 3600 rpm at the BEP. The highest magnitude is marked in yellow and shows (a) the synchronous frequency in Pump #1 varying from 56.45 Hz to 56.35 Hz and (b) the synchronous frequency in Pump #2 varying from 56.75 Hz to 56.65 Hz. (For interpretation of the references to colour in this figure legend, the reader is referred to the Web version of this article.)

<!-- image -->

Ocean Engineering xxx (xxxx) xxx

Fig. 5. Frequency spectra from the Z-axis accelerometer on top of the two pumps operating with Fluid #1 at 3600 rpm at the BEP: (a) 160-second signal from Pump #1, (b) 160-second signal from Pump #2, (c) 10-second signal from Pump #1, (d) 10-second signal from Pump #2.

<!-- image -->

Table 6 Pump accelerometer signal synchronous frequency (X) order peak amplitudes (in/s) at 3600 rpm at the BEP with Fluid #1. Orders were observed according to industryrecommended practice 11S8. Bold case peak amplitudes are above the 11S8 vibration limit.

|         |   Acc. Id. | Location   | Axis   |   X/3 |   0.42X to 0.48X |   X/2 |    1X |    2X |    3X |   > 5X |
|---------|------------|------------|--------|-------|------------------|-------|-------|-------|-------|--------|
| Pump #1 |         18 | Top        | Y      | 0.003 |            0.003 | 0.042 | 0.053 | 0.036 | 0.006 |  0.003 |
|         |         17 | Top        | Z      | 0.003 |            0.004 | 0.073 | 0.081 | 0.053 | 0.008 |  0.005 |
|         |         16 | Middle     | Y      | 0.002 |            0.003 | 0.015 | 0.060 | 0.029 | 0.007 |  0.006 |
|         |         15 | Middle     | Z      | 0.002 |            0.004 | 0.027 | 0.103 | 0.041 | 0.008 |  0.011 |
|         |         14 | Base       | Y      | 0.004 |            0.002 | 0.035 | 0.078 | 0.028 | 0.010 |  0.003 |
|         |         13 | Base       | Z      | 0.004 |            0.005 | 0.066 | 0.095 | 0.035 | 0.012 |  0.002 |
| Pump #2 |         18 | Top        | Y      | 0.005 |            0.014 | 0.028 | 0.233 | 0.011 | 0.002 |  0.005 |
|         |         17 | Top        | Z      | 0.011 |            0.015 | 0.030 | 0.313 | 0.011 | 0.003 |  0.005 |
|         |         16 | Middle     | Y      | 0.003 |            0.004 | 0.017 | 0.144 | 0.007 | 0.003 |  0.007 |
|         |         15 | Middle     | Z      | 0.004 |            0.010 | 0.017 | 0.165 | 0.014 | 0.003 |  0.004 |
|         |         14 | Base       | Y      | 0.005 |            0.017 | 0.036 | 0.155 | 0.033 | 0.004 |  0.003 |
|         |         13 | Base       | Z      | 0.008 |            0.018 | 0.023 | 0.196 | 0.043 | 0.005 |  0.006 |

accelerometer. The highest vibration was 0.101 in/s, which was detected by the Z-axis accelerometer at the middle of the pump in the 1X order.

Pump #2 presented several 1X order peaks above the vibration limit, shown in bold in Table 6, especially at  the pump top pump, with a maximum of 0.313 in/s. This 1X-order vibration is associated with the following causes according to API RP 11S8:

1.  Mass unbalance, hydraulic unbalance, or a decentralized rotor.
3.  A misaligned coupling or shaft bearing or both.
2.  A bent shaft.

The API RP 11S8 analysis method indicates these three possible diagnostics, which may not necessarily occur simultaneously. Each may involve faults in several internal pump components, which need to be individually inspected for a more precise fault diagnostic.

However, the three diagnostic hypotheses may be further differentiated  by  analyzing  the  relationships  between  the  synchronous  frequency  order  amplitudes.  Usually,  the  bent  shaft  and  misalignment diagnostics produce similar high vibrations in the 2X order also, and a high level of axial vibration (Adams, 2010; Betta et al., 2002; Patel and Darpe, 2009; Scheffer and Girdhar, 2004). In the case of the experiments performed,  the  axial  vibration  was  not  acquired,  but  as  observed  in Table 6, the Pump #2 2X amplitude peak was much smaller than the 1X amplitude peak. Although there is a higher possibility of an unbalance fault diagnosis, the 2X amplitude higher peak at the base of Pump #2 and the 1X amplitude higher peak at the top suggest different diagnoses. That is why  a  better method  is  needed to differentiate other vibration-behavior characteristics, as described below.

## 3.3. Vibration at components and fluid change

Fig. 6 and Fig. 7 show the frequency spectra of the accelerometer signals from the ESP system ' s main equipment (motor, seal, and pump) collected at 3600 rpm at the BEP. Fig. 6a and b are spectra from signals collected during the Pump #1 experiments operating with Fluid #1, and Fig. 6c and d are from experiments with Fluid #2. Fig. 7a and b are spectra from signals collected during the Pump #2 experiments operating with Fluid #1, and Fig. 7c and d are from experiments with Fluid #2.  These  figures  show  the  vibration  peak  distribution  of  all  ESP

G. Reges et al.

Ocean Engineering xxx (xxxx) xxx

Fig. 6. Frequency spectra of the 18 accelerometers on the Pump #1 ESP system, operating at 3600 rpm at the BEP: a) and b) pumping Fluid #1, c) and d) pumping Fluid #2.

<!-- image -->

components to allow evaluation of the vibration distribution between components and the influence of the fluid.

The highest peak 1X order of ESP for Pump #1 operating with Fluid #2 was 0.155 in/s, registered by accelerometer 11 (Fig. 6c), located on the seal at the top Z-axis, and the second-highest 1X order peak was 0.152 in/s registered on the Y-axis at the same location (Fig. 6d). The overall vibration distribution was similar to the experiment with Fluid #1, except it showed a 14% higher vibration on the seal top Z-axis, which may indicate that the higher viscosity of Fluid #2 increased the vibration.

In the Pump #1 experiments with Fluid #1, the highest peak was 0.135 in/s from the 1X order of the accelerometer 11 signal (Fig. 6a), which was collected from the seal top at Z-axis. The second highest peak was 0.097 in/s from the 1X order on the Y-axis at the same location (Fig. 6b). These two peaks were below the vibration limit. However, given that the vibration amplitude of neighboring locations exhibited a decreasing  behavior,  the  high  peaks  at  the  top  of  the  seal  suggest  a possible problem in the coupling between the pump and the seal. At the seal top location, the 2X order peak was 0.040 in/s, which is about a third of the 1X order peak at the same location. This proportion suggests a bent shaft or angular misalignment faults in the coupling between the pump and the seal (Adams, 2010; Patel and Darpe, 2009), however the vibration amplitude is below the API RP 11S8 vibration limit.

In the experiment with Pump #2 and Fluid #1, the 1X order highest peak was 0.326 in/s, registered by accelerometer 11 (Fig. 7a), which was  located  on  the  seal  top  Z-axis.  This  reinforces  the  indication, observed in the Pump #1 tests using the same seal, that there may be a problem in the coupling between the pump and the seal. The second highest peak of the 1X order was 0.313 in/s, registered by accelerometer 17, which was located on the pump top Z-axis (Fig. 7a); given that this vibration peak was far from the seal, its cause is in the pump itself.

The highest 1X order peak during the experiment using Pump #2 and Fluid #2 was 0.187 in/s, registered by accelerometer 11 (Fig. 7c), which was located on the seal top Z-axis; the second highest 1X order peak was 0.186 in/s, registered by accelerometer 17, which was located on the pump top Z-axis (Fig. 7c). The overall vibration distribution was similar to the experiment with Fluid #1, but with a 41% lower vibration, which may indicate that the higher Fluid #2 viscosity reduced the vibration cause.

Comparing the results using the less viscous fluid (Fluid #1) with the results using the more viscous fluid (Fluid #2), on average there was an increase in the Pump #1 peaks. On the other way, operation with a more viscous fluid caused a reduction in the vibration peaks of Pump #2. The results suggest that, in the good-condition pump (#1), an increase in fluid viscosity amplified the vibration, perhaps causing some unbalance due to greater torsional deformation in the ESP shafts. On the other hand, a more viscous fluid may have attenuated the excessive vibration in the faulty pump, perhaps acting as a damper of its fault.

The overall vibration amplitudes at the motor and seal components, measured by accelerometers 1 -12, were different between tests using Pump #1 and Pump #2, although the components were the same in both assemblies. The motor and seal vibrations were higher when operating with Pump #2 than with Pump #1, which may indicate that these vibration results are primarily a consequence of the pump ' s operational condition.

## 3.4. Speed variation behavior

Fig. 8a and Fig. 8b show the 1X order vibration peak amplitude and its respective frequency on the pump-top, Z-axis accelerometer in the Pump #1 and Pump #2 experiments, operating at five different rotational speeds at the BEP with Fluids #1 and #2.

G. Reges et al.

Ocean Engineering xxx (xxxx) xxx

Fig. 7. Frequency spectra of the 18 accelerometers on the Pump #2 ESP system, operating at 3600 rpm at the BEP: a) and b) pumping Fluid #1, c) and d) pumping Fluid #2.

<!-- image -->

(a) pump #1

<!-- image -->

(b) pump #2

Fig. 8. Z-axis accelerometer 1X order vibration peak amplitudes at the top of the pumps operating at the BEP with Fluids #1 and #2.

An amplified vibration amplitude response was observed in the ESP between 45 Hz and 50 Hz with Pump #1 using both fluids (Fig. 8a), which indicates a resonance condition in Pump #1. Resonance conditions  with  ESP  systems  have  previously  been  identified  within  the manufacturer ' s operating speed range (Minette et al., 2016). Also, an amplified  vibration  amplitude  response  in  the  ESP  was  observed  between 50 Hz and 55 Hz with Pump #2, but only with Fluid #2 (Fig. 8b). A possible resonance condition in Pump #2, influenced by the properties of Fluid #2, needs to be further examined. Although the two pumps were identical models, they were in different states of wear; the wear state can affect the frequency response of the system, which explains the different resonance-condition possibilities.

condition and was above the industry ' s recommendation of 0.156 in/s (Fig. 8b).

One of the most common problems that causes vibration is unbalance. As described in Adams (2010), Randall (2016), and Scheffer and Girdhar (2004), the unbalance vibration amplitude varies proportionally  to  the  square  of  the  rotating  speed,  giving  the  unbalanced  mass centrifugal force, f = m ω 2 r (where m is the unbalanced mass, ω is the angular velocity, and r is the distance from the unbalanced mass to the center of rotation), is proportional to the square of the rotating speed.

The vibration amplitude of Pump #1 showed a general tendency to increase in proportion to the increase in the synchronous frequency. The vibration  amplitude  of  Pump  #2  also  showed  a  general  tendency  to increase in proportion to the increase in the synchronous frequency, but above the vibration amplitudes of Pump #1.

The  vibration  amplitude  of  Pump  #2  at  the  highest  synchronous frequency  with  both  fluids  was  not  associated  with  a  resonance G. Reges et al.

Some degree of unbalance is expected in rotating machines due to material and manufacturing imperfections. However, when the vibration is beyond a limit, the unbalance becomes a problem.

With  the  Pump  #2  vibration  peak  amplitude  above  the  recommended limit in the 1X order, the industry-recommended practice indicates unbalance, bent shaft, or misalignment as probable causes, either simultaneous or not. However, given the increase in vibration amplitude associated with the increase in synchronous operating frequency, the unbalance vibration diagnosis is more likely.

## 3.5. Flow and pressure variation behavior

Fig. 9a and Fig. 9b show the vibration peak amplitudes of 1X order at the pump-top Z-axis accelerometer on Pumps #1 and #2 during seven operating points tests at the 3600 rpm speed (60 Hz), pumping Fluids #1 and #2. Fig. 9a shows that varying the operating point had little influence on the vibration amplitude at Pump #1, regardless of the fluid used. In contrast, Fig. 9b shows considerable variation in the vibration amplitude with Pump #2, and the variation curve seems to be without tendency. As the shapes of the diffusers and impellers in Pump #2 may have been modified due to wear, with fluid dynamic consequences, it is not possible to associate a specific physical phenomenon to the great vibration peak variation shown in Fig. 9b. The variation does not seem related  only  to  the  changes  in  the  operating  point,  and  the  curve  is similar using Fluids #1 and #2.

In the Fig. 10, the -0.17 correlation value between the well-intake temperature  ( Tin )  and  the  1X  order  peak  amplitude  indicates  that there  was  no  significant  influence  between  the  intake  temperature variation and the pump vibration ' s peak amplitude. The 0.85 correlation value between the well-intake temperature and its discharge temperature ( Tdis ) is high and was expected because well-intake temperatures influence the discharge temperatures. The 0.36 correlation value between the well-discharge temperature and the 1X order peak amplitude indicates  that  the  well-discharge  temperature  had  a  more  significant influence on the 1X order peak amplitude than the intake temperature. The 0.95 correlation value between the intake -discharge temperature difference ( Tdif ) and the 1X order vibration peak amplitude is higher than any other correlation. This may indicate that the vibration amplitude variation when the operating point was varied is more related to

Correlation matrices were generated, as described in Section 2.5, to investigate possible additional effects influencing the Pump #2 amplitudes at several operating points. Fig. 10 shows correlations between pairs of variables measured during Pump #2 experiments operating at 3600 rpm: the well-intake fluid temperature ( Tin ), the well-discharge fluid  temperature ( Tdis ),  the  intake -discharge temperature difference ( Tdif ), the Z-axis accelerometer 1X order peak vibration amplitude at the pump-top (1X peak), and the well-fluid flow discharge ( Qdis ). Fig. 10 also  shows the histograms of the variables, the matrix diagonal, and scatter plots of the variable pairs. The slopes of the least-squares reference lines in the scatter plots are equal to the correlation coefficients.

<!-- image -->

the fluid temperature difference between the pump intake and discharge than other variables. Neither the intake temperature nor the discharge temperature alone showed such a high correlation with vibration.

The increased intake -discharge temperature difference in the faulty pump tests was expected because an additional part of the energy given to the fluid is transformed into heat due to the reduced efficiency of used pumps. It is well known that fluid temperature may significantly influence viscosity and may also affect the stiffness of pump components. However, both may not affect vibration in the same way. Since Pump #1 does not present vibration above the industry-standard limit and does not present much amplitude variation under fluid-temperaturedifference variation, while Pump #2 shows, this characteristic may be seen as another fault symptom in Pump #2, and that fault appears to be strongly influenced by the temperature difference between the intake and discharge.

Fig. 11a and Fig. 11b show the Z-axis accelerometer 1X order vibration peak amplitudes at the top of Pumps #1 and #2, together with the  oil  well ' s  intake  and  discharge  fluid  temperature  difference,  by operating point at 3600 rpm. Fig. 11a shows that the 1X order vibration amplitude of Pump #1 did not vary while there was substantial fluidtemperature-difference variation. Fig. 11b shows that the 1X order vibration amplitude of Pump #2 was significantly correlated to the fluidtemperature difference. Fig. 12a and Fig. 12b show the same relationships in the Fluid #2 experiments.

The temperature difference in the pump extremes can cause a difference in fluid density sufficient to create an axial unbalance, but, to this  axial  unbalance  affect  Pump  #2  only,  his  shaft  could  be  with reduced stiffness. This characteristic may reinforce the diagnostic hypothesis that this pump has unbalance, and the hypothesis that it has reduced stiffness in the shaft. This high correlation between temperature difference and 1X order vibration peak amplitude may also be used as complementary information to help in the differential diagnosis of vibration faults.

## 4. Conclusions

In this paper, an experimental investigation of the vibration behavior of two ESPs in different wear states under different operating conditions was presented. The experiments followed industry recommendations, using  an  artificial  lift  test  oil  well  and  viscous  fluids  to  reflect  field operational  conditions.  The  pumps  were  tested  with  two  different viscous fluids, seven different operating points (flow versus pressure), and five different speeds to evaluate their vibration behavior.

A frequency spectrum estimation method was described, focusing on extracting the vibration amplitude from frequency components used in API RP 11S8 analysis and minimizing the amplitude loss in signals with frequency variation. The experimental results indicated that the synchronous frequency varied during the experiments, and the API RP 11S8 frequency  components  were  effectively  identified  by  the  frequency estimation  method,  with  more  accurate  peak  amplitudes  than  those G. Reges et al.

Fig. 9. Z-axis accelerometer 1X order vibration peak amplitudes at the top of the pump by operating point, at the BEP with Fluids #1 and #2.

<!-- image -->

Ocean Engineering xxx (xxxx) xxx

Fig. 10. Experimental variable correlations from Pump #2 operating at 3600 rpm at several operating points: well-intake fluid temperature ( Tin ), well-discharge fluid  temperature  ( Tdis ),  intake -discharge  temperature  difference  ( Tdif ),  Z-axis  accelerometer  1X  order  vibration  peak  amplitude  at  the  top  of  the  pump  (1X peak), and well-discharge fluid flow ( Qdis ).

<!-- image -->

obtained using a typical method.

The vibration behavior analysis with fluid change indicated that the fluid ' s  viscosity  had  a  more  significant  influence  in  the  pump  that showed higher vibration, decreasing the amplitude. The pump that was in  good  condition,  with  low  vibration,  showed  slightly  vibration amplitude increase with the more viscous fluid but remained far from

The  results  of  the  industry-recommended  vibration  analysis  indicated  that  a  faulty  pump  exceeded  the  vibration  limit  by  more  than double  at  the  synchronous  frequency  (1X).  According  to  the  recommended  practice,  three  possible  faults  (not  necessarily  co-occurring) may be suggested: mass unbalance, bent shaft, and misalignment. The API RP 11S8 vibration analysis does not indicate a non-invasive method for  diagnostic  differentiation.  Regardless  of  the  standard  industrial analysis, the relationship of peak vibrations between orders of the synchronous frequency indicated a greater likelihood of unbalance.

(a) pump #1

The vibration behavior analysis at different operating points showed no significant amplitude variation in the pump that was in good condition  and  high  amplitude  variation  in  the  faulty  pump.  Exploratory analysis using a correlation matrix indicated that the vibration amplitude in the faulty pump was highly correlated to the fluid-temperature difference between the well ' s intake and discharge, while the discharge  temperature  and  intake  temperature  alone  showed  lower correlations with the vibration amplitude.

the  vibration  limit.  The  high-vibration  pump  showed  less  vibration amplitude when operating with the more viscous fluid but remained above the vibration limit, which may indicate that the viscosity acted as a damper to the vibration cause.

Although the increased intake -discharge temperature difference in the pump tests was expected because an additional part of the energy given to the fluid is transformed into heat due to the reduced efficiency

(b) pump #2

Fig. 11. Z-axis accelerometer 1X order vibration peak amplitudes at the top of the pump and the intake -discharge fluid temperature difference by operating point at 3600 rpm with Fluid #1.

<!-- image -->

G. Reges et al.

(a) pump #1

Ocean Engineering xxx (xxxx) xxx

<!-- image -->

(b) pump #2

Fig. 12. Z-axis accelerometer 1X order vibration peak amplitudes at the top of the pump and the intake -discharge fluid temperature difference by operating point at 3600 rpm with Fluid #2.

of used pumps, the high correlation between temperature difference and 1X order vibration peak amplitude can be applied as complementary information during vibration diagnosis.

In  future  research,  it  is  planned  to  use  more  accelerometers, including axial accelerometers, to manipulate fluid temperature, and to cause controlled faults in the pumps.

The  vibration  behavior  analysis  of  different  speeds  demonstrated that the faulty pump presented a vibration amplitude increase approximately proportional to the square of the speed, which is correlated to an unbalance fault. This characteristic may also be used for ESP differential diagnosis from the other API RP 11S8 fault options involving similar spectra, such as misalignment or a bent shaft.

## CRediT authorship contribution statement

Galdir Reges: Conceptualization, Methodology, Software, Investigation, Formal analysis, Visualization, Writing - original draft, Writing review &amp; editing. Marcio  Fontana: Conceptualization,  Supervision, Methodology,  Writing  -  original  draft,  Writing  -  review &amp; editing. Marcos Ribeiro: Project administration, Resources, Validation, Writing -  review &amp; editing. Tiago Silva: Supervision,  Data  curation. Odilon Abreu: Investigation,  Data  curation. Ricardo  Reis: Software,  Data curation. Leizer Schnitman: Project  administration,  Resources, Validation, Writing - review &amp; editing.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Acknowledgments

We thank Carlos Stenio  Pereira  Morais  from  PETROBRAS  for  his technical  assistance.  We  also  thank  Marcos  Augusto  Conceiç ˜ ao  Dos Santos from Universidade Federal da Bahia for his technical support. We gratefully  acknowledge the Research and Development Center (CENPES) by PETROBRAS for their financial support (Grant 0050.0094188.14.9)  and  the  Brazilian  agencies  CNPQ  (Conselho Nacional de Desenvolvimento Científico e Tecnol ´ ogico), CAPES (Coordenaç ˜ ao de Aperfeiçoamento de Pessoal de Nível Superior), and FAPESB (Fundaç ˜ ao de Amparo ` a Pesquisa do Estado da Bahia) for their support.

## Appendix A. Supplementary data

Supplementary data to this article can be found online at https://doi. org/10.1016/j.oceaneng.2020.108249.

## References

Adams, M.L., 2010. Rotating Machinery Vibration from Analysis to Troubleshooting. CRC Press.

Betta, G., Liguori, C., Paolillo, A., Pietrosanto, A., 2002. A DSP-based FFT-analyzer for the fault diagnosis of rotating machine based on vibration analysis. IEEE Trans. Instrum. Meas. 51, 1316 -1321. https://doi.org/10.1109/TIM.2002.807987.

[API, 2012. Recommended Practice on Electric Submersible System Vibrations API RP 11S8. American Petroleum Institute, Washington, D.C., EUA.](http://refhub.elsevier.com/S0029-8018(20)31171-9/sref2)

[Boldt, F.D.A., Rauber, T.W., Varejao, M.F., Ribeiro, M.P., 2014. Performance analysis of extreme learning machine for automatic diagnosis of electrical submersible pump conditions, 2014 12th IEEE International Conference on Industrial Informatics (INDIN).](http://refhub.elsevier.com/S0029-8018(20)31171-9/sref4)

Borling, D., Sviderskiy, S.V., Gorlanov, S.F., 2008. Pumping up the life" of electric submersible pump systems, Russian federation. Proceedings of SPE Russian Oil and Gas Technical Conference and Exhibition. (SPE-116905). https://doi.org/10.2118/ 116905-MS, 1-13.

[Borges, A.M.C., Reges, G.D., Schnitman, L., 2017. Procedimentos para validaç ˜ ao da curva de desempenho de uma bomba centrífuga submersa operando com fluido viscoso atrav ´ es de estudo comparativo, 9 o Congresso Brasileiro de Pesquisa e Desenvolvimento Em Petr ´ oleo e G ´ as.](http://refhub.elsevier.com/S0029-8018(20)31171-9/sref5)

Brandt, A., 2011. Noise and Vibration Analysis: Signal Analysis and Experimental Procedures. In: Noise and Vibration Analysis: Signal Analysis and Experimental Procedures, first ed. Wiley, West Sussex. https://doi.org/10.1002/9780470978160. Bremmer, C., Harris, G., Kosmala, A., Nicholson, B., Ollre, A., Pearcy, M., Salmas, C., Solanki, S., 2006. Evolving technologies: electrical submersible pumps. Oilfield Rev.

Castillo, M.A., Guti ´ errez, R.H.R., Monteiro, U.A., Minette, R.S., Vaz, L.A., 2019. Modal parameters estimation of an electrical submersible pump installed in a test well using numerical and experimental analysis. Ocean Eng. 176, 1 -7. https://doi.org/ 10.1016/j.oceaneng.2019.02.035.

[https://doi.org/10.1097/01.CCM.0000297163.25900.63.](https://doi.org/10.1097/01.CCM.0000297163.25900.63)

[Childs, D., Phillips, S., Norrbin, C., 2014. A lateral rotordynamics primer on electric submersible pumps (ESPs) for deep subsea applications. In: 43rd Turbomachinery &amp; 30th Pump Users Symposia. Pump &amp; Turbo 2014.](http://refhub.elsevier.com/S0029-8018(20)31171-9/sref10)

Durham, M.O., Williams, J.H., Goldman, D.J., 1990. Effect of vibration on electricsubmersible pump failures. J. Petrol. Technol. 42 https://doi.org/10.2118/16924-

De Lima, F.S., Guedes, L.A.H., Silva, D.R., 2009. Application of fourier descriptors and pearson correlation for fault detection in sucker rod pumping system. In: ETFA 2009 - 2009 IEEE Conference on Emerging Technologies and Factory Automation. IEEE, pp. 1 -4. https://doi.org/10.1109/ETFA.2009.5347072.

PA.

J. Sound Vib. 216, 585 -600. https://doi.org/10.1006/jsvi.1998.1715.

Flatern, R. Von, 2015. The defining series: electrical submersible pumps. Oilfeld Rev. Lee, C.W., Han, Y.S., 1998. The directional Wigner distribution and its applications.

Liang, X., He, J., Du, L., 2015. Electrical submersible pump system grounding: current practice and future trend. IEEE Trans. Ind. Appl. 51, 5030 -5037. https://doi.org/ 10.1109/TIA.2015.2432096.

Oppenheim, A.V., 1999. Discrete-time signal processing. Electronics and Power. https:// doi.org/10.1049/ep.1977.0078.

Minette, R.S., SilvaNeto, S.F., Vaz, L.A., Monteiro, U.A., 2016. Experimental modal analysis of electrical submersible pumps. Ocean Eng. 124, 168 -179. https://doi.org/ 10.1016/j.oceaneng.2016.07.054.

## ARTICLE IN PRESS

G. Reges et al.

- Patel, T.H., Darpe, A.K., 2009. Experimental investigations on vibration response of misaligned rotors. Mech. Syst. Signal Process. 23, 2236 -2252. https://doi.org/ 10.1016/j.ymssp.2009.04.004.
- Randall, R.B., 2010. Vibration-based condition monitoring: industrial, aerospace and automotive applications, vibration-based condition monitoring: industrial, aerospace and automotive applications. https://doi.org/10.1002/9780470977668.
- Randall, R.B., 2016. Vibration-based diagnostics of gearboxes under variable speed and load conditions. Meccanica 51, 3227 -3239. https://doi.org/10.1007/s11012-0160583-z.
- Rauber, T.W., Oliveira-Santos, T., De Assis Boldt, F., Rodrigues, A., Varejao, F.M., Ribeiro, M.P., 2017. Kernel and random extreme learning machine applied to submersible motor pump fault diagnosis. Proceedings of the International Joint Conference on Neural Networks. https://doi.org/10.1109/IJCNN.2017.7966276, 3347-3354.
- Rauber, T.W., Varej, M., Rodrigues, A., Petrobras, B.S.A., Te, C.P.D.P., Varejao, F.M., Ribeiro, M.P., Fabris, F., Rodrigues, A., Ribeiro, M.P., 2013. Automatic diagnosis of

Ocean Engineering xxx (xxxx) xxx

- submersible motor pump conditions in offshore oil exploration. Industrial Electronics Society, IECON 2013 - 39th Annual Conference of the IEEE. https://doi. org/10.1109/ICECS.2013.6815458, 477-480.
- Scheffer, C., Girdhar, P., 2004. Practical Machinery Vibration Analysis and Predictive Maintenance, Machinery Vibration Analysis &amp; Predictive Maintenance. https://doi. org/10.1016/0301-679X(78)90097-X.
- Ribeiro, M.P., Oliveira, P. da S., Matos, J.S. de, Silva, J.E.M., 2005. Field applications of subsea electrical submersible pumps in Brazil. Proc. Offshore Technol. Conf. https:// doi.org/10.4043/17415-ms.
- [Takacs, G., 2017. Electrical Submersible Pumps Manual: Design, Operations, and Maintenance, second ed. Gulf Professional Publishing.](http://refhub.elsevier.com/S0029-8018(20)31171-9/sref25)
- Yao, C., Li, M.Z., Liu, G.F., 2011. Partial friction fault diagnosis of electrical submersible pump based on support vector machines. Adv. Mater. Res. 219 -220, 1689 -1692. https://doi.org/10.4028/www.scientific.net/AMR.219-220.1689.