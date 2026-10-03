## Recommended Practice on Electric Submersible System Vibrations

API RECOMMENDED PRACTICE 11S8 SECOND EDITION, OCTOBER 2012

<!-- image -->

## Recommended Practice on Electric Submersible System Vibrations

Upstream Segment

API RECOMMENDED PRACTICE 11S8 SECOND EDITION, OCTOBER 2012

<!-- image -->

## Special Notes

API publications necessarily address problems of a general nature. With respect to particular circumstances, local, state, and federal laws and regulations should be reviewed.

Neither  API  nor  any  of  API's  employees,  subcontractors,  consultants,  committees,  or  other  assignees  make  any warranty or representation, either express or implied, with respect to the accuracy, completeness, or usefulness of the information contained herein, or assume any liability or responsibility for any use, or the results of such use, of any information  or  process  disclosed  in  this  publication.  Neither  API  nor  any  of  API's  employees,  subcontractors, consultants, or other assignees represent that use of this publication would not infringe upon privately owned rights.

API publications may be used by anyone desiring to do so.  Every effort has been made by the Institute to assure the accuracy and reliability of the data contained in them; however, the Institute makes no representation, warranty, or guarantee in connection with this publication and hereby expressly disclaims any liability or responsibility for loss or damage resulting from its use or for the violation of any authorities having jurisdiction with which this publication may conflict.

API  publications  are  published  to  facilitate  the  broad  availability  of  proven,  sound  engineering  and  operating practices.  These  publications  are  not  intended  to  obviate  the  need  for  applying  sound  engineering  judgment regarding when and where these publications should be utilized. The formulation and publication of API publications is not intended in any way to inhibit anyone from using any other practices.

Any manufacturer marking equipment or materials in conformance with the marking requirements of an API standard is  solely  responsible  for  complying  with  all  the  applicable  requirements  of  that  standard.  API  does  not  represent, warrant, or guarantee that such products do in fact conform to the applicable API standard.

Users of this  Recommended Practice should not rely  exclusively  on  the  information  contained  in  this  document. Sound business, scientific, engineering, and safety judgment should be used in employing the information contained herein.

All rights reserved. No part of this work may be reproduced, translated, stored in a retrieval system, or transmitted by any means, electronic, mechanical, photocopying, recording, or otherwise, without prior written permission from the publisher. Contact the Publisher, API Publishing Services, 1220 L Street, NW, Washington, DC 20005.

## Foreword

Nothing contained in any API publication is to be construed as granting any right, by implication or otherwise, for the manufacture, sale, or use of any method, apparatus, or product covered by letters patent. Neither should anything contained in the publication be construed as insuring anyone against liability for infringement of letters patent.

Shall: As used in a standard, 'shall' denotes a minimum requirement in order to conform to the specification.

Should: As used in a standard, 'should' denotes a recommendation or that which is advised but not required in order to conform to the specification.

This  document  was  produced  under  API  standardization  procedures  that  ensure  appropriate  notification  and participation  in  the  developmental  process  and  is  designated  as  an  API  standard.  Questions  concerning  the interpretation of the content of this publication or comments and questions concerning the procedures under which this  publication  was  developed  should  be  directed  in  writing  to  the  Director  of  Standards,  American  Petroleum Institute, 1220 L Street, NW, Washington, DC 20005. Requests for permission to reproduce or translate all or any part of the material published herein should also be addressed to the director.

Generally, API standards are reviewed and revised, reaffirmed, or withdrawn at least every five years. A one-time extension of up to two years may be added to this review cycle. Status of the publication can be ascertained from the API  Standards  Department,  telephone  (202)  682-8000.  A  catalog  of  API  publications  and  materials  is  published annually by API, 1220 L Street, NW, Washington, DC 20005.

Suggested revisions are invited and should be submitted to the Standards Department, API, 1220 L Street, NW, Washington, DC 20005, standards@api.org.

## Contents

|                                                                                                                         |                                                                                                                                               | Page    |
|-------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|---------|
| 1                                                                                                                       | Scope . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . . . 1 |
| 2                                                                                                                       | Normative References. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .             | . . . 1 |
| 3                                                                                                                       | Terms and Definitions. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .            | . . . 1 |
| 4                                                                                                                       | Vibration Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .        | . . . 4 |
| 4.1                                                                                                                     | Harmonic Motion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .         | . . . 4 |
| 4.2                                                                                                                     | Concepts of Vibration . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .           | . . . 6 |
| 4.3                                                                                                                     | Sources of Vibration . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .          | . . . 7 |
| 4.4                                                                                                                     | Control of Vibration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .         | . . . 8 |
| 4.5                                                                                                                     | Vibration in ESP Systems. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .               | . . . 9 |
| 5                                                                                                                       | Vibration Testing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       | . . 10  |
| 5.1                                                                                                                     | Vibration Limits . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      | . . 10  |
| 5.2                                                                                                                     | Measurement of Vibration . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                | . . 10  |
| Annex A (informative) Units Conversion. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . . . .                                                                                                                                       | . . 12  |
| Annex B (informative) Relationship Between Displacement, Velocity, and Acceleration. . . . .                            | Annex B (informative) Relationship Between Displacement, Velocity, and Acceleration. . . . .                                                  | . . 15  |
| Annex C (informative) Classification of Severity of Machinery Vibration . . . . . . . . . . . . . . . . . . . . .       | Annex C (informative) Classification of Severity of Machinery Vibration . . . . . . . . . . . . . . . . . . . . .                             | . . 16  |
| Bibliography . . . . . . . . . . . . . . . . .                                                                          | . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                                           | . . 18  |
| Figures                                                                                                                 | Figures                                                                                                                                       |         |
| A.1                                                                                                                     | Relation of Frequency to the Amplitudes of Displacement and Velocity (USC Units) . .                                                          | . . 13  |
| A.2                                                                                                                     | Relation of Frequency to the Amplitudes of Displacement and Velocity (SI Units) . . . .                                                       | . . 14  |
| B.1                                                                                                                     | Displacement, Velocity, and Acceleration Relationship . . . . . . . . . . . . . . . . . . . . . . . . . . .                                   | . . 15  |
| Tables                                                                                                                  | Tables                                                                                                                                        |         |
| 1                                                                                                                       | Vibration Analysis of ESP Phenomena. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                          | . . . 7 |
| A.1                                                                                                                     | Conversion Factors for Translational Velocity and Acceleration . . . . . . . . . . . . . . . . . . .                                          | . . 12  |
| A.2                                                                                                                     | Conversion Factors for Rotational Velocity and Acceleration. . . . . . . . . . . . . . . . . . . . . .                                        | . . 12  |
| A.3                                                                                                                     | Conversion Factors for Simple Harmonic Motion. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                                  | . . 13  |
| C.1                                                                                                                     | Vibration Severity Criteria (After ISO IS 2372: 1974) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                             | . . 16  |
| C.2                                                                                                                     | Vibration Severity Criteria (After Training Manual IRD Mechanalysis, Columbia, Ohio).                                                         | . . 17  |

## Recommended Practice on Electric Submersible Pump System Vibrations

## 1 Scope

This Recommended Practice (RP) provides guidelines to establish consistency in the control and analysis of electric submersible pump (ESP) system vibrations. This document is considered appropriate for the testing of ESP systems and subsystems for the majority of ESP applications.

This RP covers the vibration limits, testing, and analysis of ESP systems and subsystems.

## 2 Normative References

The following referenced documents are indispensable for the application of this document. For dated references, only the edition cited applies. For undated references, the latest edition of the referenced document (including any amendments) applies.

API Recommended Practice 11S4, Recommended Practice for Sizing and Selection of Electric Submersible Pump Installations

API Recommended Practice 11S7, Recommended Practice on Application and Testing of Electric Submersible Pump Seal Chamber Sections

ISO 2372:1974  1 , Mechanical vibration of machines with operating speeds from 10 to 200 rev/s-Basis for specifying evaluation standards (replaced by 10816-1:1995)

William T. Thompson, Theory of Vibration, Prentice-Hall, Inc., Englewood, N. J., 1965, pg. 243.

## 3 Terms and Definitions

For the purposes of this document, the following definitions apply.

## 3.1 acceleration

a

A vector quantity that specifies the time rate of change of velocity, both linear and angular. Common units are in./sec 2 (cm/sec 2 ) and radians/sec 2 .

## 3.2

## amplitude

The maximum value of a periodic quantity.

## 3.3

## angular frequency

circular frequency

The frequency multiplied by 2 π , in radians per unit time, applicable to a periodic quantity.

## 3.4

## balancing

A procedure for adjusting the mass distribution of a rotor so that rotating imbalance, as seen by vibration of the journals or the forces on the bearings at once-per-revolution, is reduced or controlled.

1 International Organization for Standardization, 1, ch. de la Voie-Creuse, Case postale 56, CH-1211 Geneva 20, Switzerland, www.iso.org.