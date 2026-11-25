# Advice review sheet (executorch, 2026-11-25T21:30:11)

Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.

## U-BENCH-0000 - FAIL
findings: open/high/A2, short/high/A3, mousebite/low/B2, mousebite/low/A2, spur/low/A1, mousebite/low/B3, copper/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone A2.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the short and spur defects.",
  "log_entry": "U-BENCH-0000 FAIL open/high A2; 3 short defects in last 50 units; check etch time and concentration for short and spur defects."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone C3.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the short defect.",
  "log_entry": "U-BENCH-0001 FAIL open/high C3; 3rd short in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2, one medium-severity mousebite, and one medium-severity spur.",
  "likely_causes": [
    "over-etching",
    "resist nick",
    "resist pinhole",
    "under-etch residue"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean phototool",
    "check etch uniformity"
  ],
  "verify": "Verify the next 5 units for open after the correction, mousebite, and spur, and check etch time and concentration before re-inspecting the next 5 units for open after the correction, mousebite, and spur.",
  "log_entry": "U-BENCH-0002 FAIL open/high B2; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone C1.",
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
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "C1-0003 FAIL short/high C1; 3rd short in last 50 units; check etchant strength and rinse."
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
  "summary": "Unit failed with multiple high-severity defects: open, short, spur, and pin-hole in zones A2, B2, B1, C2, and A1.",
  "likely_causes": [
    "over-etching",
    "resist nick",
    "resist defect",
    "under-etch residue"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "rework by cutting the short bridge",
    "clean the line",
    "clean the artwork"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and clean the phototool after short and spur defects.",
  "log_entry": "U-BENCH-0004 FAIL open, short, spur, pin-hole high high high high; 3rd short in last 50 units; check etch time and concentration; clean the line and phototool after short and spur defects."
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
  "summary": "Unit failed with one high-severity open, one high-severity spur, and one high-severity mousebite in zone B2.",
  "likely_causes": [
    "open",
    "spur",
    "mousebite"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean the environment"
  ],
  "verify": "Re-inspect the next 5 units for open, spur, or mousebite after correction.",
  "log_entry": "B2-0005 FAIL open/spur/mousebite high; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur, one medium-high mousebite, one medium-high pin-hole.",
  "likely_causes": [
    "under-etching",
    "resist nick",
    "film edge damage",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean artwork",
    "clean phototool"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole after correction.",
  "log_entry": "B1-0006 FAIL short/ spur/ mousebite/ pin-hole; 3 short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean artwork; clean phototool; inspect resist coat; clean the line."
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "C1-B1-OPEN high C1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity high-copper (isolated stray copper) and one high-severity high-spur (small copper protrusion from a trace) in zones B1 and B2.",
  "likely_causes": [
    "incomplete etch",
    "contamination",
    "resist nick",
    "film edge damage"
  ],
  "recommended_actions": [
    "check rinse and strip steps",
    "inspect resist integrity and film edges",
    "clean the environment",
    "check etch uniformity"
  ],
  "verify": "Re-inspect the next 5 units for high-copper and high-spur defects, and check handling and phototool cleanliness.",
  "log_entry": "U-BENCH-0008 FAIL copper/high B1."
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
  "summary": "Multiple defects found, prioritizing the most severe ones: short, spur, and mousebite.",
  "likely_causes": [
    "short",
    "spur",
    "mousebite"
  ],
  "recommended_actions": [
    "clean the line",
    "clean artwork",
    "cut the spur",
    "clean the artwork"
  ],
  "verify": "Verify the short defect by checking etchant strength and rinse; rework by cutting the bridge; clean the phototool.",
  "log_entry": "U-BENCH-0009 FAIL short spur mousebite; 2nd short, 1st spur, 1st mousebite; clean the line, clean artwork, cut the spur, clean the artwork, rework by cutting the bridge, clean the phototool."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity open (break in a copper trace) in zones B1, A2, and A3.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "inspect resist integrity and film edges"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and open defects in zones B1, A2, and A3, and quarantine the lot if all defects are present.",
  "log_entry": "U-BENCH-0010 FAIL open/high B1; 3 open in last 50 units."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0011 - FAIL
findings: open/high/A1, short/high/C1, mousebite/medium/B1, spur/low/B1, short/high/A3, copper/low/B2, pin-hole/low/B2
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 2x short, 1x open, 1x mousebite, 1x spur, 1x copper, 1x pin-hole; worst is high open in zone A1.",
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
  "log_entry": "U-BENCH-0011 FAIL open/high A1; 3 open in last 50 units."
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
  "summary": "Multiple high-severity defects found, with short and mousebite defects being the most severe.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur",
    "copper"
  ],
  "recommended_actions": [
    "clean the environment",
    "check etch time and concentration",
    "inspect resist integrity and film edges",
    "check handling"
  ],
  "verify": "Re-inspect the next 5 units for short and mousebite defects, and check handling for all defects.",
  "log_entry": "U-BENCH-0012 FAIL short/mousebite/spur/copper; 3 short, 1 mousebite, 1 spur, 1 copper; clean the environment, check etch time and concentration, inspect resist integrity and film edges, check handling, rework by cutting the bridge for short defects."
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
  "summary": "Multiple defects found, prioritizing the most severe ones.",
  "likely_causes": [
    "open",
    "mousebite",
    "spur",
    "copper"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean phototool",
    "check rinse and strip steps"
  ],
  "verify": "Verify the next 5 units for the same defects, and check the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0013 FAIL open high mousebite high spur high copper high mousebite high pin-hole low; 3rd open in last 50 units; check etch time and concentration; clean phototool; inspect resist integrity and film edges; check handling; clean artwork; clean environment."
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
  "summary": "Unit failed with one high-severity open, one high-severity short, and one high-severity spur in zones C2, C1, and A2.",
  "likely_causes": [
    "over-etching",
    "resist flaw",
    "resist residue",
    "under-etching"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, short after rework, and spur after cleaning artwork.",
  "log_entry": "U-BENCH-0014 FAIL open/high C2; 3 open in last 50 units."
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
  "verify": "Verify the next 5 units for open after the correction, and check the etch time and concentration before re-inspecting the unit.",
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2, one high-severity short (unintended copper bridge) in zone B2, and one high-severity spur (small copper protrusion) in zone B1.",
  "likely_causes": [
    "over-etching",
    "under-etching",
    "resist defect"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, short after the rework, spur after the rework, and copper after the rework.",
  "log_entry": "U-BENCH-0016 FAIL open/high B2 short/high B2 spur/high B1 copper/high B2 short/high B2 spur/high B1."
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
  "summary": "Multiple defects found, prioritizing short and open due to high severity and high count.",
  "likely_causes": [
    "short",
    "open"
  ],
  "recommended_actions": [
    "clean the line",
    "rework by cutting the short bridge",
    "clean the artwork"
  ],
  "verify": "Verify the next 5 units for short and open, and check the etch time and concentration for all units.",
  "log_entry": "U-BENCH-0017 FAIL short open medium high count 2; 2nd short bridge found; clean the line and artwork."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0018 - FAIL
findings: open/high/C1, short/high/B1, mousebite/low/A1, spur/medium/A1, pin-hole/low/A2, open/high/B3, short/high/B3, spur/low/B3
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 2x open, 2x short, 2x spur, 1x mousebite, 1x pin-hole; worst is high open in zone C1.",
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
  "log_entry": "U-BENCH-0018 FAIL open/high C1; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone A1.",
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
  "log_entry": "U-BENCH-0019 FAIL open/high A1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B2, one high-severity short in zone A3, and one high-severity pin-hole in zone B2.",
  "likely_causes": [
    "over-etching",
    "under-etching",
    "resist flaw"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "clean the environment",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the next 5 units for short after the rework.",
  "log_entry": "U-BENCH-0020 FAIL open/high B2 short/medium high B2; 3rd short in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0021 - FAIL
findings: open/high/B3, short/high/B2, mousebite/high/A2, mousebite/medium/A1, spur/medium/B1, pin-hole/low/C1
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 2x mousebite, 1x open, 1x short, 1x spur, 1x pin-hole; worst is high open in zone B3.",
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone B2.",
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
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B2-0022 FAIL short/under-etch residue/conductive debris/pin-hole."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone C2.",
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check etch time and concentration for the next 5 units.",
  "log_entry": "U-BENCH-0024 FAIL open/high B2; 1st open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity open (break in a copper trace) in zone B1.",
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
  "log_entry": "U-BENCH-0025 FAIL open/high B1; 1st open in last 50 units; check etch time and concentration."
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
  "summary": "Multiple high-severity defects found, including short, mousebite, and open, with high severity and high count.",
  "likely_causes": [
    "short",
    "mousebite",
    "open"
  ],
  "recommended_actions": [
    "clean the environment",
    "re-inspect the next 5 units for short and mousebite",
    "rework by cutting the short bridge",
    "clean the line"
  ],
  "verify": "Verify the integrity of the short and mousebite defects by re-inspecting the next 5 units for short and mousebite.",
  "log_entry": "U-BENCH-0026 FAIL short/mousebite/open/high B1; 3rd short in last 50 units; re-inspect next 5 units for short and mousebite; clean the environment."
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
  "summary": "Unit failed with multiple high-severity defects: short, spur, and mousebite in zones B1, B2, and B3 respectively.",
  "likely_causes": [
    "spur",
    "mousebite",
    "pin-hole"
  ],
  "recommended_actions": [
    "clean artwork",
    "rework by cutting the spur",
    "clean the line",
    "clean the phototool"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and mousebite defects in zones B1, B2, and B3 respectively, and check etch time and concentration before rework.",
  "log_entry": "U-BENCH-0027 FAIL short spur mousebite high B1 B2 B3; 3 short, 1 spur, 1 mousebite, 1 pin-hole in last 50 units; check etch time and concentration before rework."
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "C1-B2 FAIL open/scratch/defect high; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with two high-severity open (break in a copper trace) and one high-severity mousebite (notches or missing copper along a trace edge) in zones A2, C2, and A1.",
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
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check etch time and concentration before the next unit.",
  "log_entry": "U-BENCH-0029 FAIL open/high mousebite/C spur/C copper; 3rd open in last 50 units; check etch time and concentration before the next unit."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |
