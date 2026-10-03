## Recommended Practice for Electrical Submersible Pump Teardown Report

API RECOMMENDED PRACTICE 11S1 THIRD EDITION, SEPTEMBER 1997

EFFECTIVE DATE: DECEMBER 15, 1997

<!-- image -->

## Recommended Practice for Electrical Submersible Pump Teardown Report

## Exploration and Production Department

API RECOMMENDED PRACTICE 11S1 THIRD EDITION, SEPTEMBER 1997

EFFECTIVE DATE: DECEMBER 15, 1997

<!-- image -->

Institute

Helping You Get The Job Done Right.M

## SPECIAL NOTES

API publications necessarily address problems of a general nature. With respect to particular circumstances, local, state, and federal laws and regulations should be reviewed.

API is not undertaking to meet the duties of employers, manufacturers, or suppliers to warn and properly train and equip their employees, and others exposed, concerning health and safety risks and precautions, nor undertaking their obligations under local, state, or federal laws.

Information concerning safety and health risks and proper precautions with respect to particular materials and conditions should be obtained from the employer, the manufacturer or supplier of that material, or the material safety data sheet.

Nothing contained in any API publication is to be construed as granting any right, by implication or otherwise, for the manufacture, sale, or use of any method, apparatus, or product covered by letters patent. Neither should anything contained in the publication be construed as insuring anyone against liability for infringement of letters patent.

Generally, API standards are reviewed and revised, reaffirmed, or withdrawn at least every five years. Sometimes a one-time extension of up to two years will be added to this review cycle. This publication will no longer be in effect five years after its publication date as an operative API standard or, where an extension has been granted, upon republication. Status of the publication can be ascertained from the API Authoring Department [telephone (202) 682-8000]. A catalog of API publications and materials is published annually and updated quarterly by API, 1220 L Street, N.W., Washington, D.C. 20005.

This document was produced under API standardization procedures that ensure appropriate notification and participation in the developmental process and is designated as an API standard.  Questions  concerning the interpretation  of  the  content  of  this  standard  or  comments and questions concerning the procedures under which this standard was developed should be directed in writing to the director of the Authoring Department (shown on the title page of this document), American Petroleum Institute, 1220 L Street, N.W., Washington, D.C. 20005. Requests for permission to reproduce or translate all or any part of the material published herein should also be addressed to the director.

API standards are published to facilitate the broad availability of proven, sound engineering and operating practices. These standards are not intended to obviate the need for applying  sound  engineering  judgment  regarding  when  and  where  these  standards  should  be utilized. The formulation and publication of API standards is not intended in any way to inhibit anyone from using any other practices.

Any  manufacturer  marking  equipment  or  materials  in  conformance  with  the  marking requirements of an API standard is solely responsible for complying with all the applicable requirements of that standard. API does not represent, warrant, or guarantee that such products do in fact conform to the applicable API standard.

All rights reserved. No part of this work may be reproduced, stored in a retrieval system, or transmitted by any means, electronic, mechanical, photocopying, recording, or otherwise, without prior written permission from the publisher. Contact the Publisher, API Publishing Services, 1220 L Street, N.W., Washington, D.C. 20005.

Copyright © 1997 American Petroleum Institute

## FOREWORD

This recommended practice is under the jurisdiction of the American Petroleum Institute (API) Subcommittee on Field Operating Equipment.

This recommended practice shall become effective on the date printed on the cover but may be used voluntarily from the date of distribution.

API publications may be used by anyone desiring to do so. Every effort has been made by the Institute to assure the accuracy and reliability of the data contained in them; however, the Institute makes no representation, warranty, or guarantee in connection with this publication and hereby expressly disclaims any liability or responsibility for loss or damage resulting from its use or for the violation of any federal, state, or municipal regulation with which this publication may conflict.

Suggested revisions are invited and should be submitted to the director of the Exploration and Production Department, American Petroleum Institute, 1220 L Street, N.W., Washington, D.C. 20005.

## CONTENTS

|                                                                                                                                                                         |                                                                                                                                  | Page   |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|--------|
| 1                                                                                                                                                                       | SCOPE. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . 1    |
| 2                                                                                                                                                                       | ADDITIONAL INFORMATION. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                          | . 1    |
| APPENDIX A-RECOMMENDED PRACTICE FOR API RP 11S1 TEARDOWN REPORTING DATABASES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . .                                                                                                                              | 11     |
| APPENDIX B-TEARDOWN REPORT QUERIES. . . . . . . . . . . . . . . . . . . . . .                                                                                           | . . . . . . .                                                                                                                    | 23     |
| Figures                                                                                                                                                                 |                                                                                                                                  |        |
| 1                                                                                                                                                                       | Typical Motor Section................................................................................................            | 3      |
| 2                                                                                                                                                                       | Typical Seal Chamber Section Types.........................................................................                      | 5      |
| 3                                                                                                                                                                       | Typical Pump Section.................................................................................................            | 7      |
| 4                                                                                                                                                                       | Typical Gas Separator Section Types.........................................................................                     | 9      |
| A-1                                                                                                                                                                     | Relationship Diagram for Teardown Reporting ......................................................                               | 15     |
| A-2                                                                                                                                                                     | Recommended Observation Codes for ESP Teardown...........................................                                        | 16     |
| A-3                                                                                                                                                                     | Pertinent Data...........................................................................................................        | 18     |
| A-4                                                                                                                                                                     | Teardown Observation Data.....................................................................................                   | 19     |
| A-5                                                                                                                                                                     | Pertinent Data (Equipment Identification)...............................................................                         | 20     |
| A-6                                                                                                                                                                     | Common Terms for Remarks Teardown Observation Code Breakdown Table......                                                         | 21     |
| A-7                                                                                                                                                                     | Common Terms for Remarks Observation Code Breakdown.................................                                             | 22     |
| A-8                                                                                                                                                                     | Reason for Pump Pull...............................................................................................              | 22     |
| A-9                                                                                                                                                                     | Failure Codes............................................................................................................        | 22     |
| B-1                                                                                                                                                                     | Example 1: Teardown Report Queries.....................................................................                          | 25     |
| B-2                                                                                                                                                                     | Example 2: Teardown Report Queries.....................................................................                          | 27     |

## Recommended Practice for Electrical Submersible Pump Teardown Report

## 1 Scope

This recommended practice covers a recommended electrical submersible pump teardown report form. It also includes equipment schematic drawings which may provide assistance in identifying equipment components. It should be noted that these schematics are for generic equipment components, and there may be differences between manufacturers on the exact description or configuration of the assemblies.

## 2 Additional Information

In  order  to  properly  interpret  the  information  gathered using this API recommended practice, the following data also should be provided:

- a. Equipment amp charts.
- b. Production data prior to failure.
- c. Information  on  any  unusual  conditions  such  as  sand  or scale production, power interruptions, bad weather or storms, changes in chemical treatments, etc.
- d. Equipment  pull  and  run  reports,  service  reports,  and equipment test records.

## Form 1-Motor Inspection Report

Operator: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ E.S.P. Manufacturer:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Lease: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Well:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ S/N: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ HP: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Voltage: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ AMPS: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Model: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date Installed: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date Pulled: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Run Time: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

1. HEAD:

Terminal cavity:

OK \_\_\_\_\_

- [ ] Burned \_\_\_\_\_

Cavity corroded:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Evidence of water track:

Yes \_\_\_\_\_

No \_\_\_\_\_

Head corroded:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

2. BASE:

Corroded: Base blushing: Filter (if applicable):

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

OK \_\_\_\_\_

- [ ] Worn \_\_\_\_\_

- [ ] OK \_\_\_\_\_

- [ ] Plugged \_\_\_\_\_

- [ ] Dirty \_\_\_\_\_

3. HOUSING CONDITION:

OK: \_\_\_\_\_

Corroded:

Yes \_\_\_\_\_

No \_\_\_\_\_

Pressure test:

Passed: \_\_\_\_\_ Failed \_\_\_\_\_

Scaled on OD:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Thickness:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Acid soluble:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Coating:

- [ ] OK \_\_\_\_\_

Bad \_\_\_\_\_ (REM)

4. SHAFT CONDITION:

Turns OK: Broken: Shaft high strength: Spline Condition: Twisted: Corroded: Extension:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Yes \_\_\_\_\_

No \_\_\_\_\_

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Yes \_\_\_\_\_

No \_\_\_\_\_

- [ ] OK \_\_\_\_\_

- [ ] Out of Spec. \_\_\_\_\_

Burned:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

5. COUPLING:

OK \_\_\_\_\_

- [ ] Worn \_\_\_\_\_

- [ ] Broken \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

6. THRUST BEARING ASSEMBLY:

Thrust bearing:

OK \_\_\_\_\_

Down thrust:

Negligible \_\_\_\_\_

- [ ] Moderate \_\_\_\_\_ Severe \_\_\_\_\_

Hi-load bearing:

Yes \_\_\_\_\_

No \_\_\_\_\_

Bearing collapsed:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Thrust Runner:

Thrust runner:

OK \_\_\_\_\_

Down thrust:

Negligible \_\_\_\_\_

Moderate \_\_\_\_\_ Severe \_\_\_\_\_

7. ROTOR BEARING ASSEMBLY:

- [ ] OK \_\_\_\_\_

Heat noted:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Spun:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Thrust Washers:

- [ ] OK \_\_\_\_\_

- [ ] Brittle \_\_\_\_\_

Cut \_\_\_\_\_

Impressioned \_\_\_\_\_

Rotor bearing sleeve:

- [ ] OK \_\_\_\_\_

Worn \_\_\_\_\_

Discolored:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

8. STATOR:

Electrical:

- [ ] (A - B)

- [ ] (A - C)

- [ ] (B - C)

Phase to phase

\_\_\_\_\_

\_\_\_\_\_

\_\_\_\_\_

Phase to ground

\_\_\_\_\_

\_\_\_\_\_

\_\_\_\_\_

Megohm reading:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Hypot test:

- [ ] OK \_\_\_\_\_

- [ ] Failed \_\_\_\_\_

Burned top end turn: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Burned bottom end turn: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Burned leads: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Laminations:

Burned:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Location:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

- [ ] ID: OK \_\_\_\_\_

- [ ] Worn \_\_\_\_\_

9. POTHEAD CONNECTOR ASSEMBLY:

Plug IN: \_\_\_\_\_

Tape IN: \_\_\_\_\_

- [ ] OK \_\_\_\_\_

Burned \_\_\_\_\_

Damaged \_\_\_\_\_

Pothead:

OK \_\_\_\_\_

- [ ] Damaged \_\_\_\_\_

- [ ] Heat noted \_\_\_\_\_

'O' Ring:

- [ ] OK \_\_\_\_\_

- [ ] Hard \_\_\_\_\_

- [ ] Seized \_\_\_\_\_

- [ ] Cut \_\_\_\_\_

Melted \_\_\_\_\_

Terminal block:

- [ ] OK \_\_\_\_\_

- [ ] Stained \_\_\_\_\_

- [ ] Burned \_\_\_\_\_

- [ ] Damaged \_\_\_\_\_

10. ROTORS:

Corroded:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Worn on OD:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Location of wear:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Burned on OD:

Yes \_\_\_\_\_

No \_\_\_\_\_

Location of burn: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

11. OIL CONDITION:

Clear: \_\_\_\_\_

Free water: \_\_\_\_\_

- [ ] Dark: \_\_\_\_\_

- [ ] Emulsion \_\_\_\_\_

- [ ] Solids: \_\_\_\_\_

Notes:

1. For any item not covered, use comment section or back of this page, if necessary, to document condition.

2. REM means remanufacture.

Comments &amp; Summary:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Inspected by: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Location:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Figure 1-Typical Motor Section

<!-- image -->

## Form 2-Seal Chamber Inspection Report

Operator: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

E.S.P. Manufacturer:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Lease: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Well:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

S/N: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Model:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date Installed: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date Pulled: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Run Time: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

1. HEAD:

Check valves:

- [ ] OK \_\_\_\_\_

Stuck open \_\_\_\_\_

Communication ports

open:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Plugged:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Acid soluble:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Corrosion:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

2. BASE:

OK: \_\_\_\_\_

Corroded: Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Anti-rotation pins:

OK \_\_\_\_\_

Bushing:

OK \_\_\_\_\_

Worn \_\_\_\_\_

Filter:

OK \_\_\_\_\_

Plugged \_\_\_\_\_

3. HOUSING CONDITION:

OK: \_\_\_\_\_ Corroded: Yes \_\_\_\_\_ No \_\_\_\_\_ Scaled on OD: Yes \_\_\_\_\_ No \_\_\_\_\_ Thickness:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Acid soluble: Yes \_\_\_\_\_ No \_\_\_\_\_ Vibration marks: Yes \_\_\_\_\_ No \_\_\_\_\_ Pressure test: Pass \_\_\_\_\_ Fail \_\_\_\_\_

4. SHAFT CONDITION:

- [ ] Turns OK: Yes \_\_\_\_\_ No \_\_\_\_\_ Broken: Yes \_\_\_\_\_ (REM) No \_\_\_\_\_ Shaft high strength: Yes \_\_\_\_\_ No \_\_\_\_\_ Spline Condition: Twisted: Yes \_\_\_\_\_ No \_\_\_\_\_ Corroded: Yes \_\_\_\_\_ No \_\_\_\_\_ Extension: OK \_\_\_\_\_

- [ ] Out of Spec. \_\_\_\_\_

5. COUPLING:

- [ ] OK \_\_\_\_\_

- [ ] Worn \_\_\_\_\_

- [ ] Broken \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

6. THRUST BEARING ASSEMBLY:

Thrust bearing: OK \_\_\_\_\_ Up thrust: Negligible wear \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Down thrust: Negligible wear \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Hi-Load bearing: Yes \_\_\_\_\_ No \_\_\_\_\_ Bearing collapsed: Yes \_\_\_\_\_ No \_\_\_\_\_ Thrust Runner: Thrust runner: OK \_\_\_\_\_ Up thrust: Negligible wear \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Down thrust: Negligible wear \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_

7. BAG CHAMBER ASSEMBLY:

Pressure test: OK \_\_\_\_\_ Failed \_\_\_\_\_ Bag collapsed: Yes \_\_\_\_\_ No \_\_\_\_\_ Punctured: Yes \_\_\_\_\_ No \_\_\_\_\_ Blown/ruptured: Yes \_\_\_\_\_ No \_\_\_\_\_ Deposition on OD: None \_\_\_\_\_ Type \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Fasteners: OK \_\_\_\_\_ No \_\_\_\_\_

8. MECHANICAL SEALS:

Condition: Specify Type-Circle One: Rotating element: Carbon Silicone Tungsten Stationary element: Ceramic Silicone Tungsten Top Middle Bottom OK \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Displaced \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Ran displaced \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Shaft grooved \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Spring broken \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Seal bellows OK \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Rotating element OK \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Rotating element worn \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Rotating element broken \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Stationary element OK \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Pressure test: pass/fail \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_

9. RELIEF VALVES:

- [ ] OK \_\_\_\_\_

- [ ] Failed \_\_\_\_\_

10.  LABYRINTH CHAMBER ASSEMBLY:

Breather tube:

- [ ] OK \_\_\_\_\_

- [ ] Broken \_\_\_\_\_

- [ ] Corroded \_\_\_\_\_

Communicator ports:

- [ ] OK \_\_\_\_\_

- [ ] Plugged \_\_\_\_\_

11. CONDITION OF ALL 'O' RINGS:

Top Middle Bottom Set/pliable \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Hard \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Seized \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Melted \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Cut/damaged \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_

12. OIL CONDITION:

Clear Water Dark Emulsion Solids Top bag \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Bottom bag \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Chamber \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Base \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_

Notes: 1. For any item not covered, use comment section or back of this page, if necessary, to document condition.

2. For piggy-back equalizers use a second form. When seal types are mixed, use comments to identify.

3. REM means remanufacture.

Comments &amp; Summary:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Inspected by: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Figure 2-Typical Seal Chamber Section Types

<!-- image -->

## Form 3-Pump Inspection Report

Operator: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ E.S.P. Manufacturer:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Lease: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Well:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ S/N: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Stage Type: \_\_\_\_\_\_\_\_\_\_\_\_\_\_ No. Stages: \_\_\_\_\_\_\_\_\_\_\_\_\_\_ Model: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date Installed: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date Pulled: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Run Time: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

1. HEAD:

OK: \_\_\_\_\_ Yes \_\_\_\_\_ No \_\_\_\_\_ Bolt on: \_\_\_\_\_ Screw in: \_\_\_\_\_ Bolts: OK \_\_\_\_\_ Corroded \_\_\_\_\_ Head corroded: Yes \_\_\_\_\_ No \_\_\_\_\_ Plugged: Yes \_\_\_\_\_ No \_\_\_\_\_ % \_\_\_\_\_\_ Plugged with: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

2. BASE:

OK: \_\_\_\_\_ Yes \_\_\_\_\_ No \_\_\_\_\_ Bolt on: \_\_\_\_\_ Screw in: \_\_\_\_\_ Bolts: OK \_\_\_\_\_ Corroded \_\_\_\_\_ Base corroded: Yes \_\_\_\_\_ No \_\_\_\_\_ Plugged: Yes \_\_\_\_\_ No \_\_\_\_\_ % \_\_\_\_\_\_ Plugged with: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

3. HOUSING CONDITION:

Scaled on OD: Yes \_\_\_\_\_ No \_\_\_\_\_ Thickness:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Acid soluble: Yes \_\_\_\_\_ No \_\_\_\_\_ Scarred axially: Yes \_\_\_\_\_ No \_\_\_\_\_ Depth:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Vibration marks: Yes \_\_\_\_\_ No \_\_\_\_\_ Coating: OK \_\_\_\_\_ Bad \_\_\_\_\_ (REM)

4. SHAFT CONDITION:

(If broken, describe below in detail) Turns OK: Yes \_\_\_\_\_ Broken: Yes \_\_\_\_\_ Shaft high strength: Yes \_\_\_\_\_ Spline Condition: Twisted: Yes \_\_\_\_\_ Corroded: Yes \_\_\_\_\_ Extension: OK \_\_\_\_\_ Radial wear: Yes \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

Out of Spec. \_\_\_\_\_

No \_\_\_\_\_

5. COUPLING:

OK \_\_\_\_\_ Broken \_\_\_\_\_ Scale: Yes \_\_\_\_\_ No \_\_\_\_\_ Acid soluble: Yes \_\_\_\_\_ No \_\_\_\_\_

6. SCREEN CONDITION:

Plugged: Yes \_\_\_\_\_ No \_\_\_\_\_ Plugged with: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Collapsed: Yes \_\_\_\_\_ No \_\_\_\_\_ Corroded: Yes \_\_\_\_\_ No \_\_\_\_\_ Scale: Yes \_\_\_\_\_ No \_\_\_\_\_ Acid soluble: Yes \_\_\_\_\_ No \_\_\_\_\_

7. SHAFT SUPPORT BEARING:

Upper: OK \_\_\_\_\_ Worn \_\_\_\_\_ Worn out of spec. \_\_\_\_\_ Bushing: OK \_\_\_\_\_ Worn \_\_\_\_\_ Lower: OK \_\_\_\_\_ Worn \_\_\_\_\_ Worn out of spec. \_\_\_\_\_ Bushing: OK \_\_\_\_\_ Worn \_\_\_\_\_

8. 'O' RING CONDITION:

Diffuser Housing Top Middle Bottom OK \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Hard \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Seized \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Swollen \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ Melted \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_ \_\_\_\_\_

9. CONDITION OF ALL THRUST WASHERS:

Down Thrust Washers Up Thrust Washers OK \_\_\_\_\_ \_\_\_\_\_ Slight wear \_\_\_\_\_ \_\_\_\_\_ Moderate wear \_\_\_\_\_ \_\_\_\_\_ Severe wear \_\_\_\_\_ \_\_\_\_\_ Brittle \_\_\_\_\_ \_\_\_\_\_ Missing \_\_\_\_\_ \_\_\_\_\_

10. DIFFUSERS:

OK \_\_\_\_\_ Percentage Plugged \_\_\_\_\_ % Plugged with: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Thrust wear: Slight \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Radial wear: Slight \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Spinning diffuser: Yes \_\_\_\_\_ No \_\_\_\_\_ Location: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Eccentric wear: Yes \_\_\_\_\_ No \_\_\_\_\_

11. IMPELLERS:

OK \_\_\_\_\_ Percentage Plugged \_\_\_\_\_ % Plugged with: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Thrust wear: Slight \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_ Radial wear: Slight \_\_\_\_\_ Moderate \_\_\_\_\_ Severe \_\_\_\_\_

12. SNAP RINGS:

- [ ] OK \_\_\_\_\_

- [ ] Corroded \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

Notes: 1. For any item not covered, use comment section or back of this page, if necessary, to document condition.

2. REM means remanufacture.

Comments &amp; Summary:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Inspected by: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Figure 3-Typical Pump Section

<!-- image -->

## Form 4-Gas Separator Inspection Report

Operator: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

E.S.P. Manufacturer:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Lease: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Well:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

S/N: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Model:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date Installed: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date Pulled: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Run Time: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

1. HEAD:

OK: \_\_\_\_\_

Ports plugged:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Corroded:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

2. BASE/INLET:

- [ ] Intake clear: Yes \_\_\_\_\_ No \_\_\_\_\_ Plugged: Yes \_\_\_\_\_ % \_\_\_\_\_\_ Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Intake screen: Yes \_\_\_\_\_ No \_\_\_\_\_ Screen OK: Yes \_\_\_\_\_ Screen plugged: Yes \_\_\_\_\_ Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Base corroded: Yes \_\_\_\_\_ Scaled on OD: Yes \_\_\_\_\_ Scale acid soluble: Yes \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

No \_\_\_\_\_

Erosion:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

3. HOUSING:

OK: \_\_\_\_\_

- [ ] Scaled: Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Thickness: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Acid soluble:

Yes \_\_\_\_\_

No \_\_\_\_\_

Corroded:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Scarred axially:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Coating:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Coating damaged:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

4. SHAFT:

(If broken, describe in detail below)

Turns OK:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Broken:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Shaft high strength:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Spline Condition:

Twisted:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Corroded:

- [ ] Yes \_\_\_\_\_

No \_\_\_\_\_

Extension:

- [ ] OK \_\_\_\_\_

- [ ] Out of Spec. \_\_\_\_\_

Radial wear:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

5. COUPLING:

- [ ] OK \_\_\_\_\_

Worn \_\_\_\_\_

Broken \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

Scale:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Acid soluble:

Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

6. RADIAL BEARINGS:

Top

Middle

Bottom

OK:

\_\_\_\_\_

\_\_\_\_\_

\_\_\_\_\_

Worn out of Spec:

\_\_\_\_\_

\_\_\_\_\_

\_\_\_\_\_

7. INDUCER SECTION:

OK: \_\_\_\_\_

Plugged:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Percentage plugged: \_\_\_\_\_\_ %

Erosion:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Down thrust washer:

- [ ] OK \_\_\_\_\_

Worn \_\_\_\_\_

- [ ] Brittle \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

8. SEPARATION SECTION/ROTOR:

OK: \_\_\_\_\_

Plugged:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Plugged with:\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Acid soluble:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

Percentage plugged: \_\_\_\_\_\_ % Erosion:

- [ ] Yes \_\_\_\_\_

- [ ] No \_\_\_\_\_

9. SNAP RINGS:

- [ ] OK \_\_\_\_\_

- [ ] Worn \_\_\_\_\_

- [ ] Broken \_\_\_\_\_

- [ ] Missing \_\_\_\_\_

Notes: For any item not covered, use comment section or back of this page, if necessary, to document condition.

Comments &amp; Summary:  \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Inspected by: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Figure 4-Typical Gas Separator Section Types

<!-- image -->

## A.1 Scope

This appendix provides recommended teardown observation  codes  to  facilitate  the  transfer  and  storage  of  electrical submersible pump teardown reporting in relational databases. The  main  purpose  of  this  section  is  to  provide  a  common foundation for electronic teardown reporting.

Alternative  methods  may  exist  for  storage  that  could  be superior to those shown in this recommended practice. Provisions to read and write to files in a common format, as shown in this appendix, are recommended to permit ease in transferring teardown data between software systems. Recommended table structures and data relationships are also provided, but these  are  not  as  critical  to  data  transfer  as  the  observation codes.

Appendix B shows examples of the many potential reports that could be generated using a teardown report database by manufacturers and producers to: 1) improve ESP run lives, 2) identify  operational  problems,  and  3)  compare  equipment performance.

## A.2 Database Tables

Database  tables  refers  to  all  tables  where  data  is  stored within a database. A table contains a set of related data. The headings in the table are defined as the fields. The information under each heading is called a record. One of the fields should always contain a unique record. This field is defined as the PRIMARY KEY. In some cases a pair of fields form this unique record in a table. One of the fields is then defined as the SECONDARY KEY. The tables are related to each other through these  keys.  Descriptions  of  the  recommended  teardown reporting for databases are split into three sections:

A.3 Pertinent  Data-General  information  related  to  the well and ESP.

A.4 Teardown Observations-Observations by each component.

A.5 Cause of the Failure-Conclusion of the primary and contributing factors resulting in the ESP failure.

In Section A.3, the data not specific to the teardown observations themselves have been called Pertinent Data.

## A.3 Pertinent Data

The pertinent data have two purposes. The first is to uniquely link the equipment teardown report to a well. This same unique (primary) key can relate the teardown data to data in other databases.  A  unique  well  identifier  (UWI)  and  a  pull  date  can uniquely define a teardown as an event. This pair uniquely identifies two teardowns from the same well or two ESP teardowns pulled on the same date at different locations. When used with a serial number, the ESP equipment is also uniquely identified.

## APPENDIX A-RECOMMENDED PRACTICE FOR API RP 11S1 TEARDOWN REPORTING DATABASES

Secondly, pertinent data should provide information that is useful in the teardown analysis, but not normally contained or easily accessible from other databases. Much of this pertinent data regarding the well completion, production rate, and the ESP equipment are valuable to both the oil company and ESP manufacturers in determining the cause of a failure. Unfortunately, these external databases are not usually shared.

Following  a  recognized  standard  database  format  allows compatibility between different database systems. This allows downloading data into a teardown database or uploading teardown data into larger database platforms.

This standard can be either PPDM or POSC. It is left up to the program developer to decide which standard to use, since a teardown database will probably be coupled with an existing database. The suggested data for proper teardown reporting  are  summarized  in  Figures A-3  through A-5,  while  the relationships between the tables are shown in Figure A-1.

## A.3.1 WELL NAME TABLE (WELLTAB)

The unique well identifier (UWI) is the primary key that ties all of the important parameters to a well. The WELLTAB Table (see Figure A-3) uses the UWI to uniquely identify the well. Items in this table should be those that do not change often, such as the physical well location. The UWI is used in other external tables such as ownership, production workover history, and/or completion databases.

## A.3.2 EVENT TABLE (EVENTTAB)

The pull date and the UWI pair should uniquely identify a teardown as an event in the EVENTTAB Table (see figure A3).  The  primary  key,  however,  is  the  EVENTID  field.  The EVENTID could be a random alphanumeric, a work order, or the  service  contract  alphanumeric.  The  values  kept  in  the EVENTTAB table relate to the information that is unique to the event. This can include the reason for the pump pull (see Figure  A-8  for  recommended  code  listing),  pump  landing depth, failure dates, and production rate data prior to failure and after initial startup.

Note: Production data could be kept on a separate table, but linked by the EVENTID.

Field  service  reports  can  be  linked  to  the  EVENTTAB table using the alphanumeric serial number from the field service report.

## A.3.3 EQUIPMENT TABLE (EQUIPTAB)

The ESP can be broken up into its main components of: pump, gas  separator,  seal,  and  motor,  and  each  component can also have multiple housing units. Combining the EVEN- TID  with  the  serial  number  identifies  the  ESP  component being torn down with the well and pull date. This combination of EVENTID and the serial number is given a unique ID defined  as  the  EQUIPID  and  is  stored  in  the  EQUIPTAB Table (see Figure A-3).

The  EQUIPID  could  be  a  random  alphanumeric  or  the teardown report alphanumeric serial number. This EQUIPID code should be linked to a table that describes the equipment in a minimum amount of detail (see A.3.4 and Figure A-5 for the recommended format for the equipment detail reporting).

Multiple  manufacturers  use  different  serial  number  conventions, which makes defining the type of equipment being described from a serial number difficult. A field  defined  as SECTID  that  universally  defines  the  ESP  components  as pump, gas separator, seal, or motor eliminates this problem. The letters P, G, S, and M are used, followed by a single-digit number. The purpose of the SECTID single-digit suffix is discussed in A.4.5.

## A.3.4 EQUIPMENT DETAIL TABLES

Details  of  the  equipment  are  maintained  in  equipment detail tables (see Figure A-5). The four tables in Figure A-5 show the recommended minimum data to define each ESP component.  Existing  manufacturers'  databases  will  dictate the  structure  of  this  information.  Manufacturers'  databases can  use  serial  numbers  to  link  the  ESP  details  within  their own databases, but these data are lost unless standard tables are created for transferring data to non-manufacturers' databases.  To  facilitate  data  exchange,  the  field  sizes  shown  in Figure A-5 should be followed.

## A.3.4.1 ESP Construction

With the large number of materials available, the details of reporting the materials used within an ESP are left up to the manufacturer;  however,  the  suggested  field  sizes  should  be maintained.

## A.3.5 OBSERVATIONS

The forms in the main body show the observations recommended by this recommended practice in a form format. Figure  A-2 shows these same observations listed with a corresponding unique code for use in a database. The structure  and  relationship  of  fields  in  the  Observation  Table (OBSTAB) are discussed below.

## A.4 Teardown Observations

All of the observations from a teardown are reported on the same table (OBSTAB-see Figure A-4). Failure observation codes can be stored in separate lookup tables based on components of the ESP. Only the observations made are kept on the database. It is assumed that if no observations were made the sub-component was in good condition. Observations can be  made  on  a  large  number  of  sub-components  that  exist within an ESP.

The fields in the OBSTAB table consist of three main components:

- a. EQUIPID (Equipment Identification).
- b. SUBID (Sub-component Identification).
- c. OBS# (Observation Number).

## A.4.1 EQUIPID

To uniquely identify any observation, a unique observation code  must  be  linked  to  the  EQUIPID  as  defined  above  in A.3.3. The EQUIPID is the primary key in the OBSTAB table.

## A.4.2 SUBID

The SUBID is a two character TEXT field that identifies the subcomponents being described by the observation. When used in combination with the OBS#,  the observations recorded become unique. Figure A-2 shows how the SUBID is broken into two groups, where each item is either:

- a. common  to  more  than  one  piece  of  ESP  equipment (SUBID defined as 'XY'), or

b. unique to an individual device (SUBID defined as 'WZ').

The variable pairs 'XY' and 'WZ' are all defined using letters from the words that describe the sub-component. The Y component of the XY pair is defined for common sub-components like B for Base, H for H ead or G for Housin G , while 'X'  is  defined  by  the  section  of  the  ESP  that  is  being described  (pump,  motor,  etc.).  For  example:  'X'  = P for P ump; G for G as  separator; S for S eal,  and M for M otor. Hence, the P ump H ead and the M otor Housin G are described as PH and MG, respectively.

For sub-components that are unique to a device, the character pair, WZ, is defined uniquely by letters in the sub-component  name.  There  is  no  direct  reference  between  the component and the sub-component. For example,  SE describes the Stator Electrical condition, while BC describes the Bag Chamber assembly condition.

## A.4.3 OBS#

OBS# describes the observation code, where '#' can be a single-digit number 1 through 9. Figure A-2 shows the recommended four-digit integer codes that correspond with the teardown reporting forms presented in the main text of this recommended  practice.  Note  that  in  each  sub-component table there is no duplication of observation codes; however, the same code can exist once in each of many sub-component tables.

To  facilitate  unique  needs  of  individual  users,  the  codes chosen are set in a recognizable pattern which is summarized in Figures A-6 and A-7. For example, all corrosion observations have the code 3700, but corrosion of one sub-component  is  distinguished  from  corrosion  in  another  by  the SUBID.

Additional component observations can be handled using this nomenclature, allowing flexibility in the system yet minimizing the effort to make queries and transfer data between software.

Concatenating the SUBID and the OBS# is an alternative method of reporting observation codes uniquely, but it is not recommended.

## A.4.3.1 Physical Measurements

Physical  measurements  taken  are  stored  in  the  physical measurement table, PHYTAB (see Figure A-5). The EQUIPID is the primary key linking physical measurements such  as  the  phase-to-phase  and  phase-to-ground  readings from a motor to the equipment and the event.

## A.4.3.2 Added Flexibility in Observation Codes

To add flexibility to the observations, follow a recognizable pattern  as  noted  above.  Figure  A-6  describes  the  standard observations  that  are  shown  in  Figure A-2  in  increments  of 100 in the 'y' vertical axis and incrementally by 10 in the horizontal axis. Significant space is provided to allow additional categories to be added. The units digit can be also be used to provide  more  details  on  several  existing  parameters  without adding remarks. Common terms that can be used are shown in Figure A-7. These are referenced back to the relative categories where they apply using footnotes in Figure A-6.

It should be noted that for the seal condition, only the top, middle, and bottom seal are described in Figure A-6 by the 4900, 5400, and 5900 series. For additional seals, increments of 100 can be used between 4900 and 5900, where the middle seal remains the 5400 series. Note that some of this data can be lost if provisions are not made for this increase in detail.

## A.4.4 REMARKS

Remarks are important in any teardown report to allow further  description  of  the  observations,  but  remarks  are  often ignored in databases. The use of Figure A-7 to fine tune the observations can help but may not be adequate for all observations. Ideally, remarks can be made about each observation; however,  in  practice  this  is  unlikely.  Comments  regarding each sub-component are more practical. Remarks should be kept in a separate table (TDREM) and linked to the Observation Table (TDOBS) using the EQUIPID and SUBID pair.

## A.4.5 STRUCTURE OF OBSERVATION TABLE

The recommended table structure of the Observation Table (TDOBS) is shown in Figure A-4. The EQUIPID and SUBID form a unique pair. This pair is followed by a list of the observation codes that pertain to the sub-components. To minimize the number of fields, the number of observations with each EQUIPID and SUBID pair is limited to 9. Thus, if the equipment is in good shape, only the observations made will be recorded. In cases where there is no damage, the EQUIPID and  SUBID  combination  does  not  exist  and  no  record  is made.

In a few cases, the number of observations may exceed 9. Exceeding  9  observations  can  be  handled  by  ignoring  the least significant observations. Alternatively, incrementing the section ID in the EQUIPID table allows a second EQUIPID for the same EVENTID and serial number pair to be used and allows the reporting of all observations.

## A.5 Cause of ESP Failure

The  causes  of  ESP  failures  are  important  parameters  to maintain in a database, because the database takes all of the observations made and puts them together to create a single conclusion or a set of conclusions. At this point, it is more useful to identify the cause of the systems failure rather than the cause of failure in the individual components. The reason for an ESP failure can be very complex, but it is valuable to draw some conclusion based on field and teardown data and report it in a database.

The failure may be related to findings within the teardown report or could be external to it. For example, if a splice failure occurs, but a teardown was still performed, there would be no cause for the failure reported. The recommended structure  for  the  Teardown  Conclusions  Table  (CONCLTAB)  is shown in Figure A-4.

## A.5.1 EVENTID

To  uniquely  identify  the  cause  of  an  ESP  failure,  the unique  failure  observation  code  must  be  linked  to  the EVENTID. It is not critical that the piece of equipment be identified  since  the  teardown  observations  should  already contain this information.

## A.5.2 SUBIDX#

The sub-component field  (SUBIDx#)  is  a  two-character text field that identifies the failing sub-component where the downhole ESP fails (see the description in A.4.2).

The 'x' in the SUBIDx# name is P, C, or S, which represent the primary, contributing, and secondary failures, respectively. The '#' value is set at 1. See A.5.6.1 for more detail.

When the cause of the failure is not related to the downhole ESP (such as is the case with a cable or tubing failure), the SUBIDx# is given the value 'XF'. The 'X' denotes the location of the failure as upper, middle, or lower, using the numbers X = 1, 2, or 3 respectively. The number 4 is used for 'X' where the location is unknown or not relative to the answer. This recommended practice contains no further guidelines for detailing ESP failures external to the teardown results.

## A.5.3 PFAIL

The primary cause of failure field (PFAIL) uses the fourdigit observation codes shown in Figure A-2 and discussed in A.4.3. Figure A-9 shows some additional failure/observation codes  to  account  for  failures  not  related  to  the  downhole equipment  involved  in  the  teardown.  These  codes  are  also shown in Breakdown of Observation Codes, Figure A-6.

## A.5.4 CFAIL#

The contributing factors field (CFAIL# for # = 1) uses the four-digit observation codes shown in Figure A-2 (see A.4.3 for discussion). The field provides an important observation that contributed to the ESP's primary mode of failure. Knowing the contributing factors aids in determining the cause of the problem. Additional contributing factors could be included by adding fields to the table as discussed in A.5.6.1.

## A.5.5 SFAIL1

The  secondary  failure  field  (SFAIL#,  where  #  =  1)  is another  significant  failure  mechanism  or  observation  that appears unrelated to the primary and contributing causes of failure reported in the fields PFAIL1 and CFAIL#. If the primary failure mechanism was corrected, SFAIL# failure may become the most significant. For example, significant corrosion in the pump body can be a secondary causes of failure if the primary failure is a motor shorted out due to the contributing factor of a failed seal.

## A.5.6 CONCLUSION REMARKS

Remarks can be made to provide more insight into the failure conclusions made. The primary, contributing, and secondary failure analyses (PREM1; CREM# and SREM#, respectively) each have 240 character spaces for a brief explanation to support the conclusions made.

## A.5.6.1 Additional Failure Conclusions

Although not recommended in this recommended practice, provisions  for  additional  contributing  factors  or  secondary failures can be included. Note that there cannot be two primary causes of failure. Additional contributing or secondary failure  fields  can  be  included  as  denoted  by  the  field  name pairs  of  SUBID2#  and  CFAIL#,  or  SUBID3#  and  SFAIL# (where # is 2 for the second, 3 for the third, etc.), respectively. This recommended practice recommends only keeping track of the first set of conclusions since comments provide better insight for more detailed failure conclusions.

Figure A-1-Relationship Diagram for Teardown Reporting

<!-- image -->

| EQUIPMENT COMPONENT Sub-Component Indices P G S M   | EQUIPMENT COMPONENT Sub-Component Indices P G S M                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | EQUIPMENT COMPONENT Sub-Component Indices P G S M                                                                                                                          |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                                                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | PUMP Gas Separator Seal Section Motor Observation Code                                                                                                                     |
|                                                     | H ead Bolt on Head used Terminal Cavity Burnt Check Valve open Evidence of Water Track Plugged Communication Ports open Percent Plugged Plugged w/ Corroded Cavity Corroded Bolts Corroded                                                                                                                                                                                                                                                                                                                                                                                 | X 2810 X 3060 X 3420 X 3460 X X X 3610 X 3620 X X 3630 X X X 3660 X X X X 3700 X 3710 X X 3720                                                                             |
| XB B ase Erosion Evident X 1000                     | XB B ase Erosion Evident X 1000                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | XB B ase Erosion Evident X 1000                                                                                                                                            |
|                                                     | Plugged w/ Corroded Corroded Bolts Scaled on OD Scale is Acid Soluble Bushing Worn Housin G Coating Present Coating Damaged Leaked at Pressure test Failed Corroded Scaled on OD Acid Soluble Scale Thickness of scale Vibration Marks observed Scarred Axially Depth/Thickness: S haft Shaft Broken                                                                                                                                                                                                                                                                       | X X 3660 X X X X 3700 X 3720 X 3810 X 3820 X X 3900 X X X X 2820 X X X X 2830 3400 X X 3410 X X X X 3700 X X X X 3810 X X X X 3820 X X X X 3830 X X 4420 X X 4440 X X 4450 |
| XS                                                  | XS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | XS                                                                                                                                                                         |
|                                                     | High Strength Shaft Used Shaft Burnt Spline Corroded Radial Wear Evident Shaft extension out of Spec. Shaft Twisted Shaft Doesn't Rotate OK Spline Twisted Cou P ling                                                                                                                                                                                                                                                                                                                                                                                                      | X X X X 2000 X X X X 2840 X 3030 X X X X 3720 X X 3900 X X X X 4220 X X X X 4300 X X X X 4400 X X X X 4430                                                                 |
| XP                                                  | XP                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | XP                                                                                                                                                                         |
|                                                     | Coupling Broken Coupling Missing Coupling Scaled Scale is Acid Soluble Coupling Worn                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | X X X X 2000 X X X 2700 X X 3810 X X 3820                                                                                                                                  |
| X X X X 4210 X-B Bea R ings                         | X X X X 4210 X-B Bea R ings                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | X X X X 4210 X-B Bea R ings                                                                                                                                                |
|                                                     | Highload bearing Used Bearing Collapsed Lower Bearing Worn Lower\Bottom Bearing Worn out of Spec Middle Bearing Worn out of Spec Upper Bearing Worn Upper\Top Bearing Worn out of Spec Upper Bushing Worn Lower Bushing Worn Thrust Bearing Wear - Down Thrust - negligible Thrust Bearing Wear - Down Thrust - moderate Thrust Bearing Wear - Down Thrust - severe Thrust Runner - Down Thrust - negligible Thrust Runner - Down Thrust - moderate Thrust Runner - Down Thrust - severe Thrust Bearing Wear - Upthrust negligible Thrust Bearing Wear - Upthrust moderate | X X 2850 X X 3550 X 3910 X X 3920 X 3940 X 3950 X X 3960 X 3970 X 3980 X X 4022 X X 4025 X X 4028 X X 4032 X X 4035 X X 4038 X 4122 X 4125                                 |

Figure A-2-Recommended Observation Codes for ESP Teardown

<!-- image -->

| EQUIPMENT Sub-Component                                                                                                                                                                         | COMPONENT Indices P G S M                                   |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Specialty Description Bea R                                                                                                                                                                     | PUMP Gas Separator Seal Section Motor Observation Code ings |
| R otor B earings Heating Noted Bearing Spun Thrust Washer Cut Thrust Washer Brittle Thrust Washer Impressioned Rotor Bearing Sleeve Worn Rotor Bearing Discolored                               |                                                             |
| SE S tator: E lectrical Hypot Test Failed Burned Top End Turn Burned Bottom End Turm Burned Leads Burned Laminations Laminations Worn (Worn ID) Location of Lamination Wear P othead C ondition | X X 4410 X 4070 X X X X                                     |
| Pothead is plugin type (default Tap) Burnt pothead connector Damaged Pothead Connector Pothead Damaged Pothead Heat noted Terminal Block damage                                                 | X X X X X X X X                                             |
| Terminal Block Burnt Terminal Block Stained RO tors Corroded                                                                                                                                    | X X X X                                                     |
|                                                                                                                                                                                                 | X X X X                                                     |
| Worn on OD                                                                                                                                                                                      |                                                             |
| Location of Wear on Rotor Burned on OD                                                                                                                                                          | 3060 3570 3700 X 3900 X 4200 X 3070                         |
| Location of Burn                                                                                                                                                                                | X 3000                                                      |
| B ag C hamber Failed Pressure Test Bag Collapsed                                                                                                                                                | X 3410                                                      |
| BC Assembly Bag Punctured Bag Blown/Ruptured                                                                                                                                                    | X 3550 X 2010                                               |
| Bag in Bad Condition                                                                                                                                                                            | X 2020 X 3500 X 3430                                        |
| Fastner unsatisfactory                                                                                                                                                                          | X 3850                                                      |
| Deposit on OD of bag                                                                                                                                                                            |                                                             |
|                                                                                                                                                                                                 | X                                                           |
|                                                                                                                                                                                                 | X 1800 X 1810 X 1830 1840 X 1850                            |
| Pothead O Ring - - Hard Top - - Hard Middle - - Hard Housing - Hard Bottom - - Hard                                                                                                             | X                                                           |
| RB                                                                                                                                                                                              | 2900                                                        |
|                                                                                                                                                                                                 | X X X                                                       |
|                                                                                                                                                                                                 | 4080                                                        |
|                                                                                                                                                                                                 | 4090                                                        |
|                                                                                                                                                                                                 | 4240 2910 3480                                              |
|                                                                                                                                                                                                 | 3010 3020 3030 3040                                         |
| PC                                                                                                                                                                                              | 4210 4200                                                   |
|                                                                                                                                                                                                 | 2870 3050 3220 3200 2900 3240                               |
| RO                                                                                                                                                                                              |                                                             |
| Type of Deposit                                                                                                                                                                                 |                                                             |
|                                                                                                                                                                                                 | 3840                                                        |

Figure A-2-Recommended Observation Codes for ESP Teardown (Continued)

<!-- image -->

| EQUIPMENT COMPONENT Sub-Component Indices P G S   | EQUIPMENT COMPONENT Sub-Component Indices P G S                                                                                                              | EQUIPMENT COMPONENT Sub-Component Indices P G S   |
|---------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| Common Specialty ME                               | Description MEchanical Seals                                                                                                                                 | Separator Seal Section Motor Observation Code     |
| RV                                                | R elief V alve                                                                                                                                               | Gas                                               |
| Top Top                                           | s                                                                                                                                                            | X X                                               |
| IN SS                                             | Relief Valve Failed C hamber A ssembly Breathing Tube Broken                                                                                                 | 3440 X X                                          |
|                                                   | Communication Ports Plugged Breathing Tube Corroded                                                                                                          | 2050 3620 X 3700                                  |
|                                                   | Top Shaft Grooved Top Spring Broken Top Seal Bellows Damaged Top Rotating Element damaged                                                                    | X 4920 X 4930 X 4940 X 4950                       |
|                                                   | IN ducer Section Eroded Down Thrust Washers Missing                                                                                                          | X 1000 X 2770 3610 3630                           |
|                                                   | Plugged Percent Plugged                                                                                                                                      |                                                   |
|                                                   |                                                                                                                                                              | X                                                 |
|                                                   |                                                                                                                                                              | 3650                                              |
|                                                   | Bottom Stationary Element Bottom Seal Failed Pressure Rotating Element Carbon Rotating Element Silicone Rotating Element Tungston Stationary Element Ceramic | 4012                                              |
|                                                   | Rotating Element Broken Top Stationary Element Damaged                                                                                                       | X 4970                                            |
|                                                   | Top Seal Failed Pressure Test                                                                                                                                | X 4980 4990                                       |
|                                                   | Middle Displaced                                                                                                                                             | X X 5400                                          |
|                                                   |                                                                                                                                                              | 5410                                              |
|                                                   |                                                                                                                                                              | X 5420                                            |
|                                                   | Middle Ran Displaced Middle Shaft Grooved                                                                                                                    | X 5430                                            |
|                                                   | Middle Spring Broken                                                                                                                                         |                                                   |
|                                                   | Middle Seal Bellows                                                                                                                                          | X X 5440                                          |
|                                                   | Damaged Middle Rotating Element Middle Rotating Element Worn                                                                                                 | X 5450 5460                                       |
|                                                   | damaged                                                                                                                                                      | X                                                 |
|                                                   | Middle Rotating Element Broken Middle Stationary Element Damaged Middle Seal Failed Pressure Test                                                            | X 5470 X 5480 5490                                |
|                                                   | Bottom Displaced                                                                                                                                             |                                                   |
|                                                   |                                                                                                                                                              | X 5900                                            |
|                                                   | Bottom Ran Displaced                                                                                                                                         | X 5910                                            |
|                                                   | Bottom Shaft Grooved                                                                                                                                         | X 5920                                            |
|                                                   | Bottom Spring Broken                                                                                                                                         | X 5930 5940                                       |
|                                                   | Bottom Seal Bellows Bottom Rotating Element                                                                                                                  | X X 5950                                          |
|                                                   | Damaged Bottom Rotating Element Worn Bottom Rotating Element Broken                                                                                          | X 5960                                            |
|                                                   | damaged                                                                                                                                                      | X 5970                                            |
|                                                   | Test                                                                                                                                                         | X 5980                                            |
|                                                   | Damaged                                                                                                                                                      | X 5990 6000                                       |
|                                                   |                                                                                                                                                              | X                                                 |
|                                                   |                                                                                                                                                              | X 6010                                            |
|                                                   |                                                                                                                                                              | X 6020                                            |
|                                                   |                                                                                                                                                              | 6050                                              |
|                                                   |                                                                                                                                                              | X                                                 |
|                                                   | Stationary Element Silicone                                                                                                                                  | 6060                                              |
|                                                   |                                                                                                                                                              | X                                                 |
|                                                   | Stationary Element Tungston                                                                                                                                  | X 6070                                            |
| CA                                                |                                                                                                                                                              |                                                   |
|                                                   | Plugged w/ Down Thrust Washers Worn                                                                                                                          | X                                                 |
|                                                   | Down Thrust                                                                                                                                                  |                                                   |
|                                                   |                                                                                                                                                              | X                                                 |
|                                                   | Washers                                                                                                                                                      | X 4080                                            |
|                                                   | Brittle                                                                                                                                                      |                                                   |
|                                                   | S eparator S                                                                                                                                                 | X                                                 |
|                                                   | Eroded                                                                                                                                                       | X 1000 X 3610 3630 3660 3820                      |
|                                                   | Plugged Percent Plugged Plugged w/                                                                                                                           | X                                                 |
|                                                   | Scale is Acid Soluble T hrust W ashers Condition                                                                                                             | X X                                               |
|                                                   | ection                                                                                                                                                       | 2760                                              |
| TW                                                | Up Thrust Washers Missing Down Thrust Washers Missing Down Thrust Washers Slight                                                                             | 2770 4012                                         |
|                                                   | Wear Down Thrust Washers Moderate                                                                                                                            | 4015                                              |
|                                                   | Wear Down Thrust Washers Severe Wear                                                                                                                         | 4018                                              |
|                                                   | Down Thrust Washers Brittle                                                                                                                                  | 4080                                              |
|                                                   | Up Thrust Washers Slight Wear                                                                                                                                |                                                   |
|                                                   | Up Thrust Washers Moderate                                                                                                                                   | 4112                                              |
|                                                   |                                                                                                                                                              | 4115                                              |
|                                                   | Up Thrust Washers Severe Wear                                                                                                                                | 4118                                              |
|                                                   | Wear                                                                                                                                                         |                                                   |
|                                                   | Up Thrust Washers Brittle                                                                                                                                    | 4180                                              |

| EQUIPMENT COMPONENT Sub-Component Indices P M   | EQUIPMENT COMPONENT Sub-Component Indices P M   | EQUIPMENT COMPONENT Sub-Component Indices P M   | EQUIPMENT COMPONENT Sub-Component Indices P M   |
|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|
|                                                 |                                                 | G S                                             |                                                 |
| Common                                          | Specialty Description DU                        | PUMP Gas Separator Seal Section Motor           | Observation Code                                |
|                                                 | D iff U sers                                    |                                                 | 3630                                            |
|                                                 | Percent Plugged                                 | X X                                             |                                                 |
|                                                 | Plugged w/                                      |                                                 | 3640                                            |
|                                                 | Radial Wear - Slight                            | X                                               | 3902                                            |
|                                                 | Radial Wear - Moderate                          | X X                                             | 3905                                            |
|                                                 | Radial Wear - Severe                            |                                                 | 3908                                            |
|                                                 | Thrust Wear - Slight                            | X                                               | 4072                                            |
|                                                 | Thrust Wear - Moderate                          | X                                               | 4075                                            |
|                                                 | Thrust Wear - Severe                            | X                                               | 4078                                            |
|                                                 | Eccentric Wear (diffuser)                       | X                                               | 4260                                            |
|                                                 | Diffuser Spinning                               |                                                 | 4410                                            |
|                                                 | Location of Spinning Diffuser                   | X X                                             | 4460                                            |
|                                                 | IM pellers                                      |                                                 |                                                 |
|                                                 | IM Percent Plugged                              | X                                               | 3630                                            |
|                                                 | Plugged w/                                      | X                                               | 3640                                            |
|                                                 | Radial Wear - Slight                            | X                                               | 3902                                            |
|                                                 | Radial Wear - Moderate                          | X                                               | 3905                                            |
|                                                 | Radial Wear - Severe Thrust Wear - Slight       | X                                               | 3908                                            |
|                                                 |                                                 | X                                               | 4072                                            |
|                                                 | Thrust Wear - Moderate                          | X                                               | 4075                                            |
|                                                 | Thrust Wear - Severe                            | X                                               | 4078                                            |
| X-N                                             | S N ap Rings Broken                             | X X                                             | 2050                                            |
|                                                 | Missing                                         | X                                               | 2700                                            |
|                                                 | Corroded                                        | X X                                             | 3700                                            |
|                                                 | Worn                                            |                                                 | 4210                                            |
| X-L                                             | Oi L Condition                                  | X                                               |                                                 |
|                                                 | Top Bag - Oil -Color                            | X                                               | 2200                                            |
|                                                 | Top Bag - Water -Color                          | X                                               | 2210                                            |
|                                                 | Top Bag - Emulsion - Color                      | X                                               | 2220                                            |
|                                                 | Top Bag - Solids Present                        | X                                               | 2280                                            |
|                                                 | Bottom Bag - Oil -Color                         | X                                               | 2300                                            |
|                                                 | Bottom Bag - Water -Color                       | X                                               | 2310                                            |
|                                                 | Bottom Bag - Emulsion - Color                   | X                                               | 2320                                            |
|                                                 | Bottom Bag - Solids Present                     | X                                               | 2380                                            |
|                                                 | Chamber - Oil -Color                            | X                                               | 2400 2410                                       |
|                                                 | Chamber - Water -Color                          | X                                               |                                                 |
|                                                 | Chamber - Emulsion - Color                      | X                                               | 2420                                            |
|                                                 | Chamber - Solids Present Base - Oil -Color      | X                                               | 2480 2500                                       |
|                                                 | Base - Water -Color                             | X X X                                           | 2510                                            |
|                                                 | Base - Emulsion - Color                         | X X                                             | 2520                                            |
|                                                 | Base - Solids Present Free Water                | X X                                             | 2580 2600                                       |
|                                                 |                                                 | X                                               |                                                 |

| Attribute Name                     | Format   | Size     |   Dec Point Pos. | Optional   | Description                                                                                                            |
|------------------------------------|----------|----------|------------------|------------|------------------------------------------------------------------------------------------------------------------------|
| (WELL_INDENTIFICATION TABLE)       |          |          |                  |            |                                                                                                                        |
| UWI                                | TEXT     | 20       |                  | N          | Unique Well Identifier                                                                                                 |
| LeaseName                          | TEXT     | 20       |                  | Y          | Lease name                                                                                                             |
| Altname                            | TEXT     | 20       |                  | Y          | Alternate Well ID (for internal identification only)                                                                   |
| Field                              | TEXT     | 12       |                  | Y          | Designated Field Name                                                                                                  |
| County                             | TEXT     | 12       |                  | Y          | County parish or small designation                                                                                     |
| District                           | TEXT     | 12       |                  | Y          | District Identification                                                                                                |
| State                              | TEXT     | 12       |                  | Y          | State or Province                                                                                                      |
| Country                            | TEXT     | 12       |                  | Y          | Country                                                                                                                |
| EVENTTAB (EVENT_IDENTIFICATION     | TABLE)   |          |                  |            |                                                                                                                        |
| EVENTID                            | TEXT     | 12       |                  | N          | Counter to uniquely Identify the time and well the equipment was pulled from.                                          |
| UWI                                | TEXT     | 20       |                  | N          | Unique Well Identifier                                                                                                 |
| PullDate                           | DATE     | YY/MM/DD |                  | N          | Date equipment was run in the hole                                                                                     |
| FailDate                           | DATE     | YY/MM/DD |                  | Y          | Date Equipment was reported to fail                                                                                    |
| InDate                             | DATE     | YY/MM/DD |                  | N          | Date Equipment was pulled                                                                                              |
| Operator                           | TEXT     | 20       |                  | N          | Operator of the well                                                                                                   |
| PullRepID                          | TEXT     | 20       |                  | Y          | Pull Report ID (Could be used as EVENTID)                                                                              |
| SerOID                             | TEXT     | 20       |                  | Y          | Service Order ID (Could be used as EVENTID)                                                                            |
| Reason4Pull                        | TEXT     | 4        |                  | Y          | Code Describing Reason for Pull (See Figure 8)                                                                         |
| Deviation_Indicator                | INTEGER  | 1        |                  | Y          | Indicates if well is deviated (0= (default) straight hole;1=deviated hole depths in MD;2= deviated hole depths in TVD) |
| UnitsID                            | INTEGER  | 1        |                  | N          | 0=Imperial;1=Metric                                                                                                    |
| MotorBOT                           | NUMBER   | 10       |                5 | Y          | Depth of the bottom of the motor                                                                                       |
| OilRate                            | NUMBER   | 12       |                2 | Y          | Oil rate from last test prorated to a 24hr day                                                                         |
| WaterRate                          | NUMBER   | 12       |                2 | Y          | Water rate from last test prorated to a 24hr day                                                                       |
| GasRate                            | NUMBER   | 12       |                2 | Y          | Gas rate from last test prorated to a 24hr day                                                                         |
| Testdate                           | DATE     | YY/MM/DD |                  | Y          | Date of Production test                                                                                                |
| BHT                                | NUMBER   | 5        |                2 | Y          | Estimated Bottom hole temperature                                                                                      |
| APIOil                             | NUMBER   | 5        |                2 | Y          | API Gravity of the oil                                                                                                 |
| ViscOil                            | NUMBER   | 12       |                2 | Y          | Viscosity (cp) of oil at in situ conditions (BHT,PIP)                                                                  |
| WaterGr                            | NUMBER   | 12       |                2 | Y          | Gravity of the Water                                                                                                   |
| EQUIPTAB (EQUIPMENT_IDENTIFICATION | TABLE)   |          |                  |            |                                                                                                                        |
| EQUIPID                            | TEXT     | 12       |                  | N          | Counter to Uniquely Identify Equipment being Reported                                                                  |
| SerialNumber                       | TEXT     | 20       |                  | N          | Serial Number of component torn down                                                                                   |
| EVENTID                            | TEXT     | 12       |                  | N          | Counter to uniquely event (Link to EVENTTAB)                                                                           |
| SectionID                          | TEXT     | 2        |                  | Y          | X# where X= P ump, G S, S eal, M otor and # =0,1,2...                                                                  |
| MfgESP                             | TEXT     | 20       |                  | Y          | Manufacturer of ESP Component                                                                                          |
| TDCo                               | TEXT     | 20       |                  | Y          | Company tearing down ESP                                                                                               |
| TDLoc                              | TEXT     | 20       |                  | N          | Location of teardown                                                                                                   |
| TDRepID                            | TEXT     | 20       |                  | Y          | Teardown Report ID (Could be used as EQUIPID)                                                                          |
| TDDate                             | DATE     | YY/MM/DD |                  | Y          | Date of teardown                                                                                                       |
| MfgRep                             | TEXT     | 20       |                  | N          | Name of Teardown Company representative reviewing teardown                                                             |
| OpRep                              | TEXT     | 20       |                  | N          | Name of operator reviewing teardown                                                                                    |

Notes: 1. Liquid Rates: Metric/Imperial m 3 PD/BPD.

2. Gas Rates: 10 3 m 3 PD/MMSCFPD.

3. Temperature C/ F.

Figure A-3ÑPertinent Data

| Table                                           | Attribute Name                                  | Format                                          | Size                                            | Dec Point Pos.                                  | Optional                                        | Description                                                                       |
|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-----------------------------------------------------------------------------------|
| OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                  | OBSTAB (TEARDOWN OBSERVATIONS)                                                    |
|                                                 | EQUIPID                                         | TEXT                                            | 12                                              |                                                 | Y                                               | Counter to Uniquely Identify Equipment Component (i.e. Pump, Seal) being Reported |
|                                                 | (SUBID)                                         | TEXT                                            | 2                                               |                                                 | Y                                               | Identifies sub-component for observations                                         |
|                                                 | Obs1                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 1 for Component                                                    |
|                                                 | Obs2                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 2 for Component                                                    |
|                                                 | Obs3                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 3 for Component                                                    |
|                                                 | Obs4                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 4 for Component                                                    |
|                                                 | Obs5                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 5 for Component                                                    |
|                                                 | Obs6                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 6 for Component                                                    |
|                                                 | Obs7                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations #7 for Component                                                     |
|                                                 | Obs8                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations #8 for Component                                                     |
|                                                 | Obs9                                            | NUMBER                                          | 4                                               |                                                 | Y                                               | Observations # 9 for Component                                                    |
| MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE) | MEASTAB (TEARDOWN MEASURMENT OBSERVATION TABLE)                                   |
|                                                 | EQUIPID                                         | TEXT                                            | 12                                              |                                                 | Y                                               | Counter to Uniquely Identify Equipment Component (i.e. Pump, Seal) being Reported |
|                                                 | P2PA-B                                          | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Phase (A-B)                                                              |
|                                                 | P2PA-C                                          | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Phase (A-C)                                                              |
|                                                 | P2PB-C                                          | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Phase (B-C)                                                              |
|                                                 | P2GA                                            | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Ground (A)                                                               |
|                                                 | P2GB                                            | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Ground (B)                                                               |
|                                                 | P2GC                                            | NUMBER                                          | 5                                               | 0                                               | N                                               | Phase to Ground (C)                                                               |
| TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                | TREMTAB (TEARDOWN REMARKS TABLE)                                                  |
|                                                 | EQUIPID                                         | TEXT                                            | 12                                              |                                                 | Y                                               | Counter to Uniquely Identify Equipment Component (i.e. Pump, Seal) being Reported |
|                                                 | (SUBID)                                         | TEXT                                            | 2                                               |                                                 | Y                                               | Identifies sub-component for observation remark                                   |
|                                                 | Remark1                                         | TEXT                                            | 80                                              |                                                 | Y                                               | Comments explaining Observation #7                                                |
| CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)            | CONCLTAB (TEARDOWN CONCLUSION TABLE)                                              |
|                                                 | EVENTID                                         | TEXT                                            | 12                                              |                                                 | Y                                               | Counter to Uniquely Identify Event being Reported                                 |
|                                                 | SUBID1                                          | TEXT                                            | 2                                               |                                                 | Y                                               | Identifies Sub-Component for Primary Cause of Failure                             |
|                                                 | PRIM1                                           | NUMBER                                          | 4                                               | 0                                               | Y                                               | Primary Cause of Failure                                                          |
|                                                 | PREM1                                           | TEXT                                            | 120                                             |                                                 | Y                                               | Explaining Reasoning for Primary Failure                                          |
|                                                 | SUBID2#                                         | TEXT                                            | 2                                               |                                                 | Y                                               | Sub-Component ID for Contributing Factor                                          |
|                                                 | CONF#                                           | NUMBER                                          | 4                                               | 0                                               | Y                                               | Explanation of Contributing to Primary Failure                                    |
|                                                 | CONFR#                                          | TEXT                                            | 120                                             |                                                 | Y                                               | Explanation for Contributing Factor                                               |
|                                                 | SUBID3#                                         | TEXT                                            | 2                                               |                                                 | Y                                               | Sub-Component ID for Notable Problems                                             |
|                                                 | SECF#                                           | NUMBER                                          | 4                                               | 0                                               | Y                                               | Notable Problem (Item near Failure not related to Primary Failure)                |
|                                                 | SECFR#                                          | TEXT                                            | 120                                             |                                                 | Y                                               | Comments explaining Notable Problem                                               |

Note: BOLD text = primary key: (BRACKETED BOLD) text = secondary key.

Figure A-4ÑTeardown Observation Data

| Table                                | Attribute Name   | Format   |   Size |   Dec Point Pos. | Optional   | Description                         |
|--------------------------------------|------------------|----------|--------|------------------|------------|-------------------------------------|
| EQUIPID                              |                  |          |        |                  |            |                                     |
| PUMDT (Pump_Details)                 |                  |          |        |                  |            |                                     |
|                                      | Serial#          | TEXT     |     20 |                  | N          | Serial Number for Pump              |
|                                      | Order#           | TEXT     |     20 |                  | Y          | Order Number for Pump               |
|                                      | Model#           | TEXT     |     20 |                  | N          | Pump Model                          |
|                                      | Type             | TEXT     |     20 |                  | N          | Description of Pump                 |
|                                      | Hsg              | NUMBER   |      5 |                0 | N          | Housing Size                        |
|                                      | Stages           | NUMBER   |      5 |                0 | N          | Number of Stages                    |
|                                      | MatMfgCode1      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode2      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode3      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode4      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
| IGSDT (Intake/Gas_Separator Details) |                  |          |        |                  |            |                                     |
|                                      | Serial#          | TEXT     |     20 |                  | N          | Serial Number for Gas Separator     |
|                                      | GOrder#          | TEXT     |     20 |                  | Y          | Order Number for Gas Separator      |
|                                      | GModel#          | TEXT     |     20 |                  | N          | Gas Separator Model                 |
|                                      | GType            | TEXT     |     20 |                  | N          | Description of Gas Separator        |
|                                      | MatMfgCode1      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode2      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode3      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode4      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
| SEALDT (Seal_Chamber                 | Details)         |          |        |                  |            |                                     |
|                                      | Serial#          | TEXT     |     20 |                  | N          | Serial Number for Seal Chamber      |
|                                      | SOrder#          | TEXT     |     20 |                  | Y          | Order Number for Seal Chamber       |
|                                      | SModel#          | TEXT     |     20 |                  | N          | Seal Chamber Model                  |
|                                      | SType            | TEXT     |     20 |                  | N          | Description of Seal Chamber         |
|                                      | MatMfgCode1      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode2      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode3      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode4      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
| MOTDT (Motor                         | Details)         |          |        |                  |            |                                     |
|                                      | Serial#          | TEXT     |     20 |                  | N          | Serial Number for Motor             |
|                                      | MOrder#          | TEXT     |     20 |                  | Y          | Order Number for Motor              |
|                                      | MModel#          | TEXT     |     20 |                  | N          | Motor Model                         |
|                                      | MType            | TEXT     |     20 |                  | N          | Description of Motor                |
|                                      | HP               | NUMBER   |      5 |                0 | N          | Horsepower Rating at 60 Hz          |
|                                      | VLTS             | NUMBER   |      5 |                0 | N          | Name plate Voltage @ 60 Hz (Volts)  |
|                                      | Amps             | NUMBER   |      5 |                0 | N          | Name plate Current @ 60 Hz (Amps)   |
|                                      | MatMfgCode1      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode2      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode3      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |
|                                      | MatMfgCode4      | NUMBER   |      4 |                0 | Y          | Material Descriptors (user defined) |

Note: BOLD text = primary key: (BRACKETED BOLD) text = secondary key.

Figure A-5ÑPertinent Data (Equipment Identification)

|                                |           | 0                            | 10                          | 20                                             | 30                          | 40                             | 50                                | 60                          | 70                                    | 80                         | 90                        |
|--------------------------------|-----------|------------------------------|-----------------------------|------------------------------------------------|-----------------------------|--------------------------------|-----------------------------------|-----------------------------|---------------------------------------|----------------------------|---------------------------|
| Eroded                         | 1000      | Evident (1)                  | -                           | -                                              | -                           | -                              | -                                 | -                           | -                                     | -                          | -                         |
| Set/Pliable                    | 1300      | -                            | Top                         | -                                              | Middle                      | -                              | Bottom                            | -                           | -                                     | -                          | -                         |
| Seized                         | 1400      | Pothead                      | Top                         | -                                              | Middle                      | Hsg Bottom                     | Bottom                            | -                           | -                                     | -                          | -                         |
| Cut/Damaged                    | 1500      | Pothead                      | Top                         | -                                              | Middle                      | Hsg Bottom                     | Bottom                            | -                           | -                                     | -                          | -                         |
| Melted                         | 1600      | Pothead                      | Top                         | -                                              | Middle                      | Hsg Bottom                     | Bottom                            | -                           | -                                     | -                          | -                         |
| Swollen                        | 1700      | Pothead                      | Top                         | -                                              | Middle                      | Hsg Bottom                     | Bottom                            | -                           | -                                     | -                          | -                         |
| Hard                           | 1800      | Pothead                      | Top                         | -                                              | Middle                      | Hsg Bottom                     | Bottom                            | -                           | -                                     | -                          | -                         |
| Broken/ Damaged                | 2000      | Damaged                      | Punctured                   | Ruptured                                       | Damaged Runner              | Broken                         | -                                 | -                           | -                                     | -                          | -                         |
| Fluid Top Bag                  | 2200      | Oil Color                    | Water Color Water           | Emulsion Color Emulsion                        | -                           | -                              | -                                 | -                           | -                                     | Solids                     | -                         |
| Fluid Btm Bag                  | 2300      | Oil Color                    | Color                       | Color                                          | -                           | -                              | -                                 | -                           | -                                     | Solids                     | -                         |
| Fluid Chamber                  | 2400      | Oil Color                    | Water Color                 | Emulsion Color                                 | -                           | -                              | -                                 | -                           | -                                     | Solids                     | -                         |
| Fluid Base                     | 2500      | Oil Color                    | Water Color                 | Emulsion Color                                 | -                           | -                              | -                                 | -                           | -                                     | Solids                     | -                         |
| Free Water                     | 2600      | Present                      | -                           | -                                              | -                           | -                              | -                                 |                             |                                       |                            | -                         |
| Missing                        | 2700      | Missing                      | N/A                         | -                                              | - Coating                   | -                              | -                                 | Upthrust Washer             | Down Thrust Washer                    |                            | -                         |
| Equipment Used                 | 2800      | -                            | Bolt on Rotor Bearing       | Coating                                        | Damaged (2)                 | High Strength Shaft            | High Load Bearing                 | -                           | -                                     | Plug-in Pothead            | -                         |
| Heating                        | 2900      | Heat Noted Location of       | Discolored                  | -                                              | -                           | -                              | - Burnt Pothead                   | - Terminal Cavity           | -                                     | -                          | -                         |
| Burnt                          | 3000      | Rotor Burn (7)               | Top End Burn                | Btm End Burn Pothead                           | Leads                       | Laminations                    | Connector                         | Block                       | on OD                                 | -                          | -                         |
| Damaged/ Failed                | 3200      | Damaged                      | -                           | Connector                                      | -                           | Terminal Block                 | -                                 | - Evidence of               | - Stained                             | -                          | -                         |
| Failed Tests                   | 3400      | Leaked at                    | Pressure Test               | Valve open                                     | Fastener                    | Relief Valve                   | -                                 | Water Track                 | Terminal Block                        | Hypot Test                 | -                         |
| MISC                           | 3500      | Bag Cond.(poor)              | -                           | -                                              | -                           | -                              | Collapsed                         | -                           | -                                     | -                          | -                         |
| Plugging                       | 3600      | Filter Dirty (4)             | Plugged Corroded            | Screen/ Com'n Ports (6)                        | % Plugged (3)               | Plugged w/ (4)                 | -                                 | -                           | -                                     | -                          | -                         |
| Corrosion                      | 3700      | Corroded (6) Scale/ Deposits | Cavity                      | Corroded (Spline/Screen)                       | - Scale                     | -                              | -                                 | -                           | -                                     | -                          | -                         |
| Scaling                        | 3800      | (4,5)                        | Scale Present               | Acid Soluble Lower Bearing                     | Thickness (1) Location of   | Deposit Present Middle Bearing | Deposit Type (5)                  | - Upper \Top                | -                                     | -                          | -                         |
| Eccentric Wear                 | 3900      | Evident (9)                  | Lower Bearing Worn          | Worn Out of Spec                               | Wear (7)                    | Worn Out of Spec               | Upper Bearing Worn                | Bearing Worn Out of Spec    | Upper Bushing Worn                    | Lower Bushing Worn         | - Washer                  |
| Down Thrust Up Thrust          | 4000 4100 | - -                          | Thrust Washer Thrust Washer | Thrust Bearing Thrust Bearing Extension out of | Thrust Runner Thrust Runner | - -                            | - -                               | Washer Cut -                | Thrust Wear -                         | Washers Brittle -          | Impression -              |
| Wear                           | 4200      | Location (7)                 | Evident                     | Spec.                                          | -                           | RB Sleeve                      | -                                 | Eccentric                   | -                                     | -                          | -                         |
| Twisted                        | 4300      | Shaft Twisted                | Spline Twisted              | - Vibration                                    | -                           | - Depth of                     | -                                 | -                           | -                                     | -                          | -                         |
| Rotating                       | 4400      | Shaft Not Rotating           | Spinning                    | Marks (1)                                      | Scarred axial               | Scarring (1)                   |                                   |                             | -                                     | -                          | -                         |
| Btm Seal                       | 4900 (9)  | Displaced                    | Ran Displaced               | Shaft Grooved                                  | Spring Broken               | Seal Bellows Damaged           | Rotating Element Damaged          | Rotating Element Worn       | Rotating Element Broken               | Stationary Element Damaged | Seal Failed Pressure Test |
| Middle Seal                    | 5400 (9)  | Displaced                    | Ran Displaced               | Shaft Grooved                                  | Spring Broken               | Seal Bellows Damaged           | Rotating Element Damaged Rotating | Rotating Element Worn       | Rotating Element Broken               | Stationary Element Damaged | Seal Failed Pressure Test |
| Top                            |           | Displaced                    | Ran Displaced               |                                                |                             | Seal Bellows Damaged           | Element                           | Rotating Element Worn       | Rotating Element Broken               | Stationary Element Damaged | Seal Failed Pressure Test |
| Seal                           | 5900 (9)  | Rotating                     | Rotating                    | Shaft Grooved                                  | Spring Broken               |                                | Damaged                           |                             |                                       |                            |                           |
| Materials Mechn. Seals         | 6000      | Element Carbon               | Element Silicone            | Rotating Element Tungsten                      | -                           | -                              | Stationary Element Ceramic        | Stationary Element Silicone | Stationary Element Tungsten Equipment | -                          | -                         |
| Other (For Failure Table only) | 7000      | Splice Failure               | Cable Failure               | Motor Flat Failure                             | Pigtail Failure             | Tubing Failure                 | -                                 | -                           | Changed out (No failure evident)      | Unknown                    | Other                     |
|                                |           | 0                            | 10                          | 20                                             | 30                          | 40                             | 50                                | 60                          | 70                                    | 80                         | 90                        |

Note: For explanation of footnote, ref. 4.3.2 and Figure A-7.

Figure A-6-Common Terms for Remarks Teardown Observation Code Breakdown Table

| Final Digit   | Thickness   | Coating Description   | Plugged With   | Deposits of   | Colors           | Corrosion Descriptors   | Location Descriptors   | Rotating Description   | Wear Descriptors     |
|---------------|-------------|-----------------------|----------------|---------------|------------------|-------------------------|------------------------|------------------------|----------------------|
| For Codes #   | 1000, 3640, | 2830                  | 3600, 3640     | 3650          | 2300, 2310, 2320 | 3700, 3720              | 4200                   | 3000, 3900, 4400       | 4900 to 5900         |
| Footnote #    | 1           | 2                     | 4              | 5             |                  | 6                       | 7                      | 8                      | 9                    |
| 0             | .05 mm      | Minor                 | Asphaltine     | Asphaltine    | Clear            | Minor                   | -                      | Locked                 | Other (1)            |
| 1             | 1.0 mm      | Blistering            | Iron Sulfide   | Iron Sulfide  | White            | General                 | Inner Radius           | Other (1)              | Negligible Evenly    |
| 2             | 2.0 mm      | Flaking               | Mud            | Other (1)     | Yellow           | Other (1)               | Outer Radius           | Overly loose           | Negligible           |
| 3             | 3.0 mm      | Worn                  | Paraffin       | Paraffin      | Green            | Pitting                 | Top                    | Other (2)              | Negligible One Sided |
| 4             | 4.0 mm      | Dented/Chipped        | Rubber         | Other (2)     | Light Brown      | Other (2)               | Middle                 | Other (3)              | Moderate Evenly      |
| 5             | 5.0 mm      | Cracked               | Sand           | Other (3)     | Other (1)        | Cracking                | Bottom                 | Other (4)              | Moderate             |
| 6             | 7.0 mm      | Other (1)             | Scale          | Scale         | Dark Brown       | Other (3)               | Other (1)              | Tight Spots            | Moderate One Sided   |
| 7             | 10.0 mm     | Other (2)             | Formation      | Other (4)     | Other (2)        | Other (4)               | Other (2)              | Other (6)              | Severe Evenly        |
| 8             | 15.0 mm     | Other (3)             | Other (1)      | Other (5)     | Other (3)        | Other (5)               | Other (3)              | Hard to Rotate         | Severe               |
| 9             | >25 mm      | Severe                | Other (2)      | Other (6)     | Black            | Severe                  | Other (4)              | Other (7)              | Severe One Sided     |

Note: Other ( \_ )  available for user to define.

Figure A-7-Common Terms for Remarks Teardown Observation Code Breakdown

| Code   | Description                  | Code   | Description               |
|--------|------------------------------|--------|---------------------------|
| LPRO   | Low Production               | STIM   | Stimulation Required      |
| POFF   | Production Off               | LOGG   | Logging Well Required     |
| RSIH   | Resize (Increase Production) | COVT   | Converting Well           |
| RSDH   | Resize (Decrease Production) | TEST   | Testing Well              |
| DHSH   | Downhole Short               | TSPN   | Temporary Suspending Well |
| LPUM   | Locked Pump                  | ABAN   | Abandoning Well           |
| LOAM   | Drawing Low Amps             | OTH1   | Other (1)                 |
| HIAM   | Drawing High Amps            | OTH2   | Other (2)                 |
| HITB   | Hole in Tubing               | OTH3   | Other (3)                 |
| CSRP   | Casing Repair Required       | OTH4   | Other (4)                 |
| WKOV   | Workover                     | OTH5   | Other (5)                 |

Note: OTH# can be user-defined.

Figure A-8-Reason for Pump Pull

| PFAIL1/CFAIL1/SFAIL1 Indices      | PFAIL1/CFAIL1/SFAIL1 Indices      | 1                                 | 2      | 3     | 4     | Observation   |
|-----------------------------------|-----------------------------------|-----------------------------------|--------|-------|-------|---------------|
| Common                            | Description                       | Upper                             | Middle | Lower | Other | Code          |
| X-F                               | Cause of Failure                  |                                   |        |       |       |               |
|                                   | Splice Failure                    | X                                 | X      | X     |       | 7000          |
|                                   | Cable Failure                     | X                                 | X      | X     | X     | 7010          |
|                                   | Motor Flat Failure                | X                                 | X      | X     |       | 7020          |
|                                   | Pigtail Failure                   | X                                 | X      | X     |       | 7030          |
|                                   | Tubing Failure                    | X                                 | X      | X     | X     | 7040          |
| No Failure, Equipment Changed Out | No Failure, Equipment Changed Out | No Failure, Equipment Changed Out |        |       | X     | 7070          |
|                                   | Unknown                           |                                   |        |       | X     | 7080          |
|                                   | Other Failures                    |                                   |        |       | X     | 7090          |

Figure A-9-Failure Codes

## APPENDIX B-TEARDOWN REPORT QUERIES

Description: Plot 1 shows the distribution of failures within Field X along with the average run lives by failure. From Plot 1 we see that PUMP failures represent a significant portion of the failures (27%) and also the shortest run lives. Attention to this problem will have the largest immediate impact on improving this fields run lives and potentially its operating cost. Plot 2 shows the primary causes of PUMP failure further broken down into 4 major categories, mainly: thrust washers, diffusers, impellers, and screen type failures. It shows that the screen condition and the condition of the thrust washer represent most of the failures.

## PLOT 1: ESP FAILURES

<!-- image -->

## PLOT 2: PRIMARY CAUSE OF PUMP FAILURES

Figure B-1- Example 1: Teardown Report Queries

<!-- image -->

,, ,, , ,, ,, ,, ,, PLOT 3: BREAKDOWN OF FAILURES Description: Plot 3 breaks the PUMP failures down even further, showing that plugging and down thrust are the major components of the failures in this field PUMP failures. In addition to being one of the primary causes of failures, the trend is observed in all teardowns within the field, as Plot 3 shows. Attention can then be put on operating and design practices within the field. In a similar fashion to Plots 2 and 3 , we can progress into increasing levels of detail to determine that pothead failures are one of the main concerns in MOTOR failures. Plot 4 shows the distribution of the MOTOR failures by manufactures as related to the pothead failures only. It shows that Manufacture B has fewer pothead failures than the other two manufactures; and, if queries also showed the pothead failure problem is limited to certain wells of operating conditions, Manufacture B pumps should be the first choice in those wells. Alternatively, Manufactures A and C would have the data available to determine if design changes are warranted to address this problem.

<!-- image -->

## PLOT 4: DESCRIPTION OF POTHEAD BY MANUFACTURES

<!-- image -->

,,

,,

,,

,,

,,

,

,,

,

,,

,,

,,

,

,,

,, Number of Units

Figure B-1- Example 1: Teardown Report Queries (Continued)

<!-- image -->

## API Related Publications Order Form

- [ ] ❏ API Member (Check if Yes)

Date:

(Month, Day, Year)

Invoice To - ❏ Check here if same as 'Ship To'

Company

Name/Dept.

Address

City

State/Province

Zip

Country

Customer Daytime Telephone No.

Fax No.

(Essential for Foreign Orders)

(Essential for Foreign Orders)

- [ ] ❏ Payment Enclosed $

- [ ] ❏ Payment By Charge Account :

- [ ] ❏ MasterCard

- [ ] ❏ Visa

- [ ] ❏ American Express

Account No.

Name (As it appears on Card)

Expiration Date

Signature

- [ ] ❏ Please Bill Me

P.O. No.

Customer Account No.

State Sales Tax - The American Petroleum Institute is required to collect sales tax on publications mailed to the following states: AL,  AR, CT, DC, FL, GA, IL, IN, IA, KS, KY, ME, MD, MA, MI, MN, MO, NE, NJ, NY, NC, ND, OH, PA, RI, SC, TN, TX, VT, VA, WV, and WI. Prepayment of orders shipped to these states should include applicable  sales  tax  unless  a  purchaser  is  exempt.  If  exempt,  please  print  your  state  exemption  number  and enclose a copy of the current exemption certificate.

Exemption Number

State

Ship To - (UPS will not deliver to a P .O. Box)

Company

Name/Dept.

Address

City

State/Province

Zip

Country

Customer Daytime Telephone No.

Fax No.

## PREPAID AND CREDIT CARD ORDERS ARE NOT CHARGED FOR SHIPPING AND HANDLING TO U.S. AND CANADIAN DESTINATIONS

Quantity Order No.

G11S03

G11S22

G11S2R

G05941

G05943

G05944

G11S61

G05947

G05948

Title

RP 11S, The Operation, Maintenance and Troubleshooting of Electric Submersible

Pump Installations

RP 11S2,Electric Submersible Pump Testing, Second Edition

RP 11S2, Electric Submersible Pump Testing-Russian translation, First Edition

RP 11S3, Electric Submersible Pump Installations

RP 11S4, Sizing and Selection of Electric Submersible Pump Installations

RP 11S5, Application of Electric Submersible Cable Systems

RP 11S6, Testing of Electric Submersible Pump Cable Systems

RP 11S7, Application and Testing of Electric Submersible Pump Seal Chamber Section

RP 11S8, Electric Submersible Pump System Vibrations

Shipping and Handling All orders are shipped via UPS or First Class Mail in the U.S. and Canada. Orders to all other countries will be sent by Airmail.

Rush Shipping Charge Federal Express, $10 in addition to customer providing Federal Express account number: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_. UPS Next Day, $10 plus the actual shipping costs (1-9 items). UPS Second Day, add $10 plus the actual shipping costs (1-9 items).

Rush Bulk Orders 1-9 items, $10. Over 9 items, add $1 each for every additional item. NOTE: Shipping on foreign orders cannot be rushed without Federal Express account number.

Bill and Ship Orders U.S. and Canada, $4 per order handling fee, plus actual shipping costs. All other countries, for Airmail (standard service) add 25% of order value. All other countries, for UPS Next Day, add an additional 10% of order value.

Total

Pricing and availability subject to change without notice.

Mail Orders: American Petroleum Institute, Order Desk, 1220 L Street, N.W., Washington, DC 20005-4070 Fax Orders: (202) 962-4776 Phone Orders: (202) 682-8375

To better serve you, please refer to this code when ordering:

<!-- image -->

Unit Price

$

40.00

$

$

$

$

$

$

$

45.00

50.00

45.00

60.00

50.00

40.00

40.00

$

40.00

Subtotal

State Sales Tax (see above)

Rush Shipping Charge (see left)

Shipping and Handling (see left)

Total (in U.S. Dollars)

The American Petroleum Institute provides additional resources and programs to industry which are based on API Standards. For more information, contact:

| • Training/Workshops                              | Ph: 202-682-8490 Fax: 202-682-8222   |
|---------------------------------------------------|--------------------------------------|
| • Inspector Certification Programs                | Ph: 202-682-8161 Fax: 202-962-4739   |
| • American Petroleum Institute Quality Registrar  | Ph: 202-682-8130 Fax: 202-682-8070   |
| • Monogram Program                                | Ph: 202-962-4791 Fax: 202-682-8070   |
| • Engine Oil Licensing and Certification System   | Ph: 202-682-8233 Fax: 202-962-4739   |
| • Petroleum Test Laboratory Accreditation Program | Ph: 202-682-8129 Fax: 202-682-8070   |

In addition, petroleum industry technical, patent, and business information is available online through API EnCompass ™ . Call 1-888-604-1880 (toll-free) or 212-366-4040, or fax 212-366-4298 to discover more.

<!-- image -->

To obtain a free copy of the API Publications, Programs, and Services Catalog, call 202-682-8375 or fax your request to 202-962-4776. Or see the online interactive version of the catalog on our web site at www.api.org/cat. Φ American Petroleum Institute Helping You Get The Job Done Right.S

)

Additional copies available from API Publications and Distribution: (202) 682-8375

Information about API Publications, Programs and Services is available on the World Wide Web at: http://www.api.org

<!-- image -->

Institute

1220 L Street, Northwest Washington, D.C. 20005-4070 202-682-8000