# Advice review sheet (executorch, 2026-11-26T01:16:15)

Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.

## U-BENCH-0000 - FAIL
findings: open/high/A2, short/high/A3, mousebite/low/B2, mousebite/low/A2, spur/low/A1, mousebite/low/B3, copper/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge) in zone A3.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework by cutting the bridge.",
  "log_entry": "U-BENCH-0000 FAIL short/under-etching/medium B3; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0001 - FAIL
findings: open/high/C3, short/high/B1, copper/low/B2, pin-hole/medium/B3, spur/high/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge), one high-severity copper, one medium-high pin-hole, one high-severity spur in zone B2.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean artwork",
    "clean phototool"
  ],
  "verify": "Re-inspect the next 5 units for short, copper, pin-hole, spur in zone B2.",
  "log_entry": "U-BENCH-0001 FAIL open/high C3; 3 open in last 50 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0002 - FAIL
findings: open/high/B2, mousebite/medium/B2, spur/medium/B2, pin-hole/low/A2, copper/medium/C2, spur/medium/B3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (break in a copper trace) in zone B2.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot",
    "clean the environment"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "U-BENCH-0002 FAIL open/high B2; check etch time and concentration for the next 5 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0003 - FAIL
findings: open/high/C2, open/high/B2, short/high/C1, short/high/A3, mousebite/high/A3, spur/high/A2, spur/medium/A2, copper/high/A1, pin-hole/medium/A1, open/high/B3, open/high/C3, short/high/C3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge) in zone C3.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "U-BENCH-0003 FAIL short high C3; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0004 - FAIL
findings: open/high/A2, short/high/B1, open/high/B2, short/high/C2, mousebite/low/A2, mousebite/low/A1, spur/high/A1, copper/medium/C3, pin-hole/low/A2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge between conductors) in zone B1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "B1 SHORT high (base) - rework by cutting the bridge."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0005 - FAIL
findings: open/high/B2, spur/high/B2, copper/medium/C1, pin-hole/low/C3, mousebite/high/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity spur, one medium-copper, one low pin-hole, one high mousebite in zone B2.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "clean B2, C1, C3 environment",
    "inspect resist coat",
    "check etch time and concentration"
  ],
  "verify": "Re-inspect the next 5 units for spur, copper, pin-hole, mousebite in zone B2.",
  "log_entry": "B2, C1, C3, C3 FAIL spur, copper, pin-hole, mousebite in zone B2; clean B2, C1, C3 environment; inspect resist coat; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0006 - FAIL
findings: short/high/B1, mousebite/medium/C2, spur/high/B2, copper/medium/B2, pin-hole/medium/A1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short, mousebite, spur, pin-hole in zone B2.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect resist integrity and film edges",
    "clean phototool",
    "check handling"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, spur, pin-hole in zone B2.",
  "log_entry": "U-BENCH-0006 FAIL short, mousebite, spur, pin-hole in zone B2; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0007 - FAIL
findings: open/high/C1, mousebite/high/B1, spur/medium/B2, copper/high/A2, pin-hole/medium/C2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (break in a copper trace) in zone C1.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "C1 FAIL open/high C1; check etch time and concentration for the next 5 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0008 - FAIL
findings: mousebite/medium/B2, spur/medium/B2, pin-hole/low/B1, copper/high/B1, spur/high/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity mousebite, one high-severity spur, one medium-high spur in zone B2.",
  "likely_causes": [
    "resist nick",
    "film edge damage",
    "over-etch at edges",
    "resist defect"
  ],
  "recommended_actions": [
    "inspect resist coat",
    "check etch uniformity",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for mousebite, spur, and pin-hole defects in zone B1, and check etch uniformity in zone B2.",
  "log_entry": "U-BENCH-0008 FAIL mousebite, spur, pin-hole, and copper in zone B1; check etch uniformity in zone B2."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0009 - FAIL
findings: open/high/B1, short/high/B1, spur/medium/C1, spur/high/C1, pin-hole/low/A2, copper/low/B1, mousebite/medium/C2, short/high/C2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge between conductors) in zone C2.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "U-BENCH-0009 FAIL short high C2; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0010 - FAIL
findings: open/high/B1, short/high/B1, mousebite/low/A3, spur/high/A2, copper/high/A2
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 1x open, 1x short, 1x spur, 1x copper, 1x mousebite; worst is high open in zone B1.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "under-etching"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "check etchant strength and rinse"
  ],
  "verify": "Re-inspect the next 5 units for open.",
  "log_entry": "U-BENCH-0010 FAIL open/high B1; 3 open in last 50 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0011 - FAIL
findings: open/high/A1, short/high/C1, mousebite/medium/B1, spur/low/B1, short/high/A3, copper/low/B2, pin-hole/low/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge), one medium-scope mousebite, one low-copper spur.",
  "likely_causes": [
    "under-etching",
    "resist pinhole",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects, and check etch time and concentration.",
  "log_entry": "U-BENCH-0011 FAIL short mousebite spur: one high-severity defect(s) in zone A1, one medium-scope defect(s) in zone B1, one low-copper defect(s) in zone B2."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0012 - FAIL
findings: open/high/C2, short/high/C1, mousebite/high/B1, spur/medium/A1, copper/low/B2, pin-hole/low/C1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short in zone C1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "C1-0012 FAIL short high C1; check etchant strength and rinse."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0013 - FAIL
findings: open/high/C3, mousebite/high/B2, pin-hole/low/B2, copper/medium/A1, spur/high/C2, mousebite/medium/A1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (break in a copper trace) in zone A1.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0013 FAIL open/high A1; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0014 - FAIL
findings: open/high/C2, short/high/C1, spur/high/B2, pin-hole/low/B1, spur/high/A1, short/high/A2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge between conductors) in zone A2.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework by cutting the bridge.",
  "log_entry": "U-BENCH-0014 FAIL short high A2; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0015 - FAIL
findings: open/high/B2, spur/medium/B2, pin-hole/low/B3, copper/high/B1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (break in a copper trace) in zone B1.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the next 10 units for spur and pin-hole defects in zone B2.",
  "log_entry": "U-BENCH-0015 FAIL open/high B2; 3 open in last 50 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0016 - FAIL
findings: open/high/B2, short/high/B2, spur/high/B1, pin-hole/medium/B3, copper/high/C2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge), one medium-severity spur, one high-severity pin-hole in zone B3.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "clean artwork",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole defects, and clean the line if any defects are found.",
  "log_entry": "U-BENCH-0016 FAIL short, spur, pin-hole in B3; check etchant strength and rinse; clean artwork; rework by cutting the bridge; clean the line if any defects are found."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0017 - FAIL
findings: open/high/A2, open/high/A3, short/high/A3, short/high/B2, mousebite/medium/A2, mousebite/medium/A3, spur/medium/A3, spur/medium/B3, copper/medium/C2, pin-hole/low/A2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge) in zone A3.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "U-BENCH-0017 FAIL short medium A3; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0018 - FAIL
findings: open/high/C1, short/high/B1, mousebite/low/A1, spur/medium/A1, pin-hole/low/A2, open/high/B3, short/high/B3, spur/low/B3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short (unintended copper bridge between conductors) in zone B3.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Verify the next 5 units for short after rework.",
  "log_entry": "U-BENCH-0018 FAIL short high B3; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0019 - FAIL
findings: open/high/A1, mousebite/high/B2, copper/low/B1, pin-hole/low/A2, spur/medium/B3, copper/high/B3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (break in a copper trace) in zone A1.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "U-BENCH-0019 FAIL open/high A1; check etch time and concentration for the next 5 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0020 - FAIL
findings: open/high/B2, short/high/A3, pin-hole/medium/B2, copper/high/C1, pin-hole/low/B2, short/high/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short (unintended copper bridge between conductors) in zone B2.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework by cutting the bridge.",
  "log_entry": "U-BENCH-0020 FAIL short high B2; check etchant strength and rinse; rework by cutting the bridge."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0021 - FAIL
findings: open/high/B3, short/high/B2, mousebite/high/A2, mousebite/medium/A1, spur/medium/B1, pin-hole/low/C1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short, mousebite, and pin-hole defects in zones B2, A2, and C1 respectively.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "clean artwork",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and pin-hole defects in zones B2, A2, and C1 respectively.",
  "log_entry": "U-BENCH-0021 FAIL short, mousebite, and pin-hole defects in zones B2, A2, and C1 respectively; check etchant strength and rinse; clean artwork; rework by cutting the bridge."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0022 - FAIL
findings: open/high/B3, short/high/B2, mousebite/low/A2, spur/high/C2, copper/high/B1, pin-hole/low/B3, mousebite/medium/C2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short, mousebite, and spur defects in zone B2.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the bridge",
    "clean artwork"
  ],
  "verify": "Verify the next 5 units for short, mousebite, and spur defects in zone B2.",
  "log_entry": "U-BENCH-0022 FAIL short, mousebite, and spur defects in zone B2; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0023 - FAIL
findings: open/high/C2, short/high/B2, spur/low/B2, copper/high/B1, pin-hole/medium/C2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short, one high-severity spur, one medium-severity copper in zone B1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "clean artwork",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and copper defects in zone B1.",
  "log_entry": "U-BENCH-0023 FAIL open/high C2; 3 open in last 50 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0024 - FAIL
findings: open/high/B2, short/high/B2, mousebite/medium/A3, copper/medium/A2, pin-hole/low/A2, mousebite/high/B2, spur/low/C3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short, one medium short, one high mousebite, one medium mousebite, one low pin-hole, one high spur.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, spur, mousebite, and pin-hole defects.",
  "log_entry": "U-BENCH-0024 FAIL short, mousebite, spur, mousebite, pin-hole; clean phototool; inspect resist coat; rework by cutting the bridge; clean the line; clean artwork."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0025 - FAIL
findings: open/high/B1, short/high/B1, mousebite/high/C1, spur/medium/B2, copper/high/B2, pin-hole/low/C2, spur/medium/B1
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity short, one high-severity mousebite, one high-severity spur, one high-severity copper.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the bridge",
    "clean artwork",
    "clean phototool"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, spur, and copper defects.",
  "log_entry": "U-BENCH-0025 FAIL short, mousebite, spur, copper; check etch time and concentration; inspect resist coat; clean phototool; clean environment."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0026 - FAIL
findings: open/high/B2, short/high/B1, short/high/B2, mousebite/high/B1, copper/high/B1, pin-hole/medium/A2, spur/medium/A1, short/high/B3
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short (unintended copper bridge between conductors) in zone B1.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Verify the next 5 units for short (unintended copper bridge between conductors) before rework.",
  "log_entry": "B1-0026 FAIL short (unintended copper bridge between conductors) in zone B1; check etchant strength and rinse."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0027 - FAIL
findings: open/high/B2, short/high/B1, short/high/B1, spur/medium/B3, pin-hole/low/C1, copper/high/B2, mousebite/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short (unintended copper bridge between conductors) in zone B1.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after rework.",
  "log_entry": "B1 SHORT un-intended copper bridge between conductors; check etchant strength and rinse; rework by cutting the bridge; clean the line."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0028 - FAIL
findings: open/high/C1, short/high/A2, mousebite/high/A1, spur/medium/B1, pin-hole/low/A1, copper/low/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: short, mousebite, and pin-hole defects in zone A1.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and pin-hole defects in zone A1.",
  "log_entry": "A1 SHORT MOUSEBITE PIN-HOLE FAIL short, mousebite, and pin-hole in zone A1; clean phototool; inspect resist coat."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0029 - FAIL
findings: open/high/A2, open/high/C2, mousebite/high/C2, spur/high/A3, spur/high/A1, copper/high/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "FAIL: one high-severity open (copper trace), one high-severity mousebite, one high-severity spur, one high-severity copper.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean artwork",
    "check rinse and strip steps"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, mousebite along the edge, spur on the edge, and copper along the trace.",
  "log_entry": "U-BENCH-0029 FAIL one high-severity open, one high-severity mousebite, one high-severity spur, one high-severity copper."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |
