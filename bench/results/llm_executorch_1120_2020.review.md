# Advice review sheet (executorch, 2026-11-20T20:20:56)

Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.

## U-BENCH-0000 - FAIL
findings: open/high/A2, short/high/A3, mousebite/low/B2, mousebite/low/A2, spur/low/A1, mousebite/low/B3, copper/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one low-severity mousebite (notches or missing copper), and one low-severity spur (small copper protrusion), in zones A2, B2, and A1 respectively.",
  "likely_causes": [
    "under-etch residue; resist defect; conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse; rework by cutting the bridge; clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short and mousebite defects, and check the etch time and concentration for short defects.",
  "log_entry": "A2 B2 A1 short/low mousebite/copper FAIL high low low high medium."
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
  "summary": "Unit failed with one high-severity short, one high-severity copper, and one high-severity pin-hole in zone B1.",
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
  "verify": "Re-inspect the next 5 units for short, one high-severity short, one high-severity copper, and one high-severity pin-hole in zone B1; check etch time and concentration before rework; clean the environment before rework.",
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 10 units.",
  "log_entry": "U-BENCH-0002 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone C3.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "C3-0003 FAIL short/medium high/medium high-severity defect(s) - 3 short defects in last 50 units."
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
  "summary": "Multiple high-severity defects found, including short, open, and mousebite, with high severity and high confidence.",
  "likely_causes": [
    "short",
    "open",
    "mousebite"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the bridge",
    "check etch time and concentration"
  ],
  "verify": "Verify the next 5 units for short, open, and mousebite defects, and check the etch time and concentration before rework.",
  "log_entry": "U-BENCH-0004 FAIL short open mousebite high high"
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 10 units.",
  "log_entry": "U-BENCH-0005 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one medium-severity mousebite, one high-severity spur, and one medium-severity copper.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "clean artwork",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Verify the next 5 units for short after rework by cutting the bridge, mousebite after inspection, spur after cleaning artwork, and copper after rework by cutting the bridge.",
  "log_entry": "U-BENCH-0006 FAIL short/high B1; 3 short in last 50 units."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone C1.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 10 units.",
  "log_entry": "C1-0007 FAIL open/high C1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity mousebite (notches or missing copper along a trace edge) in zone B1.",
  "likely_causes": [
    "resist nick",
    "film edge damage",
    "over-etch at edges"
  ],
  "recommended_actions": [
    "inspect resist integrity and film edges",
    "check handling"
  ],
  "verify": "Re-inspect the next 5 units for mousebite after the correction.",
  "log_entry": "B1-0008 FAIL mousebite/high B1; 3rd mousebite in last 50 units; inspect resist integrity and film edges."
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
  "summary": "Multiple high-severity defects found, including short, spur, and pin-hole, with one high-severity open in zone B1.",
  "likely_causes": [
    "short",
    "spur",
    "pin-hole",
    "copper"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the bridge",
    "clean artwork",
    "check etch time and concentration"
  ],
  "verify": "Verify the next 5 units for short, spur, and pin-hole defects, and check etch time and concentration.",
  "log_entry": "U-BENCH-0009 FAIL short/spur/pin-hole/copper/ mousebite high-severity defects high-severity open in zone B1; 3rd short in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0010 - FAIL
findings: open/high/B1, short/high/B1, mousebite/low/A3, spur/high/A2, copper/high/A2
backend: executorch valid=True fallback=False
```json
{
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone A2.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects, and check the etch time and concentration before rework.",
  "log_entry": "A2 B1 A2 U-EXAMPLE FAIL short/mousebite/spur high high high high high FAIL: 4 high-severity defect(s)"
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
  "summary": "Unit failed with one high-severity short, one medium short, one low spur, one low pin-hole, one low open.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris",
    "resist nick"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect resist coat",
    "clean phototool",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, one high short, one low spur, one low pin-hole, one low open.",
  "log_entry": "U-BENCH-0011 FAIL short/medium spur/low pin-hole/low open high high"
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone C1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "clean artwork",
    "check etch uniformity",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects, and check the etch uniformity of the line before rework.",
  "log_entry": "C1-0012 FAIL short/high mousebite/low/medium high-severity defect(s) in zone C1; 3 short in last 50 units; check etch uniformity of the line before rework."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone A1.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and verify the next 5 units for mousebite and pin-hole defects.",
  "log_entry": "U-BENCH-0013 FAIL open/high A1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small hole inside a copper area) in zone C1.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole defects, and check etchant strength and rinse after rework.",
  "log_entry": "C1-0014 FAIL short high spur high pin-hole high-severity defects; 3 short, 2 spur, 1 pin-hole in last 50 units; check etchant strength and rinse after rework."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B1.",
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small hole inside a copper area) in zone B2.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole after correction.",
  "log_entry": "B2-0016 FAIL short/spur/pin-hole high; 3rd short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean artwork."
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
  "summary": "Unit failed with multiple high-severity open (break in a copper trace) in zones A2, A3, B2, and B3.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean the environment",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check etch time and concentration for the next 5 units.",
  "log_entry": "U-BENCH-0017 FAIL open high A2 A3 B2 B3; 3rd open in last 50 units; check etch time and concentration; clean the environment; rework by cutting the bridge;"
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity mousebite (notches or missing copper), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small hole inside a copper area) in zone B1.",
  "likely_causes": [
    "under-etch residue; resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse; rework by cutting the bridge; clean the line"
  ],
  "verify": "Verify the next 5 units for short, mousebite, spur, and pin-hole defects after rework.",
  "log_entry": "B1 FAIL short/mousebite/spur/pin-hole high-severity"
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B1.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and verify the next 10 units for mousebite and spur defects.",
  "log_entry": "U-BENCH-0019 FAIL open/high B1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone B2.",
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
  "verify": "Re-inspect the next 5 units for short after the correction, and check the etchant strength and rinse before rework.",
  "log_entry": "U-BENCH-0020 FAIL short high B2; 3rd short in last 50 units; check etchant strength and rinse before rework."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity mousebite (notches or missing copper), and one high-severity spur (small copper protrusion), in zone B2.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur, and verify the integrity of the resist coat before rework or cleaning.",
  "log_entry": "U-BENCH-0021 FAIL open/high B3; 3 open in last 50 units."
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
  "summary": "Multiple high-severity defects found, including short, mousebite, and spur, with high likelihood of causing defects.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the spur",
    "check etch time and concentration"
  ],
  "verify": "Verify the next 5 units for short, mousebite, and spur defects, and rework by cutting the spur if found.",
  "log_entry": "U-BENCH-0022 FAIL short, mousebite, spur; 3rd short in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity copper (isolated stray copper) in zone B1.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and isolated stray copper defects in zone B1; 2nd unit failed with one high-severity short in zone B2; 1st unit failed with one high-severity spur in zone B1; 3rd unit failed with one high-severity isolated stray copper in zone B1.",
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, one high-severity open, and one high-severity spur in zone B2.",
  "likely_causes": [
    "short",
    "mousebite",
    "open",
    "spur"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the short",
    "rework by cutting the spur",
    "check etch time and concentration"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, open, and spur defects, and check etch time and concentration before rework.",
  "log_entry": "B2-0024 FAIL short, mousebite, open, spur; 3 short, 2 mousebite, 1 open, 1 spur; check etch time and concentration before rework."
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone B1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etch uniformity",
    "clean artwork",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects, and check the etch uniformity of the line.",
  "log_entry": "B1-0025 FAIL short, mousebite, spur; 3rd short in last 50 units; check etch uniformity."
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
  "summary": "Multiple short defects found in zone B1, with 5 high-severity short defects.",
  "likely_causes": [
    "under-etch residue",
    "resist residue",
    "conductive debris",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Verify the next 5 units for short defects, and rework by cutting the bridge if the count exceeds 2.",
  "log_entry": "B1-0026 FAIL short high B1; 5 short defects in last 50 units; rework by cutting the bridge if count exceeds 2."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one medium short (resist pinhole), and one high mousebite (notches or missing copper along a trace edge) in zone B1.",
  "likely_causes": [
    "under-etch residue; resist defect; conductive debris"
  ],
  "recommended_actions": [
    "check etch uniformity; clean artwork; rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B1-0027 FAIL short/high short/B1; 3rd short in last 50 units; check etch uniformity and clean artwork."
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone A1.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean artwork",
    "check etch uniformity",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur in zone A1, and check etch uniformity before rework.",
  "log_entry": "A1-B1-0028 FAIL short, mousebite, spur high; 3 short in last 50 units; check etch uniformity."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2.",
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
  "verify": "Verify the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0029 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |
