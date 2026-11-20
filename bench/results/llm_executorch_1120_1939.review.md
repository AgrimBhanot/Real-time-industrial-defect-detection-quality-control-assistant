# Advice review sheet (executorch, 2026-11-20T19:39:42)

Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.

## U-BENCH-0000 - FAIL
findings: open/high/A2, short/high/A3, mousebite/low/B2, mousebite/low/A2, spur/low/A1, mousebite/low/B3, copper/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, one high-severity spur, and one medium-high defect in the copper line.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, one high-severity short, one high-severity mousebite, one high-severity spur, and one medium-high defect in the copper line.",
  "log_entry": "U-BENCH-0000 FAIL short/high mousebite/spur/copper medium; 3 short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean the line; clean artwork."
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
  "summary": "Unit failed with one high-severity short, copper, and pin-hole defects in zone B2.",
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
  "verify": "Re-inspect the next 5 units for short, copper, and pin-hole defects in zone B2.",
  "log_entry": "B1-B2 short, copper, and pin-hole defects; 3 short in last 50 units; check etchant strength and rinse."
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
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0002 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0003 - FAIL
findings: open/high/C2, open/high/B2, short/high/C1, short/high/A3, mousebite/high/A3, spur/high/A2, spur/medium/A2, copper/high/A1, pin-hole/medium/A1, open/high/B3, open/high/C3, short/high/C3
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 4x open, 3x short, 2x spur, 1x mousebite, 1x copper, 1x pin-hole; worst is high open in zone C2.",
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
  "log_entry": "U-BENCH-0003 FAIL open/high C2; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone B1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after correction.",
  "log_entry": "B1 SHORT un-intended copper bridge; 3rd short in last 50 units; rework by cutting the bridge."
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
  "summary": "Unit failed with one high-severity spur, one high-severity copper, and one high-severity pin-hole in zone B2.",
  "likely_causes": [
    "spur",
    "copper",
    "pin-hole"
  ],
  "recommended_actions": [
    "clean the environment",
    "inspect resist coat",
    "check etch time and concentration"
  ],
  "verify": "Re-inspect the next 5 units for spur, copper, and pin-hole defects in zone B2.",
  "log_entry": "U-BENCH-0005 FAIL spur/copper/pin-hole high B2; 3rd spur, copper, and pin-hole in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |

## U-BENCH-0006 - FAIL
findings: short/high/B1, mousebite/medium/C2, spur/high/B2, copper/medium/B2, pin-hole/medium/A1
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 1x short, 1x spur, 1x mousebite, 1x copper, 1x pin-hole; worst is high short in zone B1.",
  "likely_causes": [
    "under-etching",
    "resist residue",
    "under-etch residue"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "check etch uniformity"
  ],
  "verify": "Re-inspect the next 5 units for short.",
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
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0007 FAIL open/high C1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity mousebite (notches or missing copper along a trace edge) in zone B2.",
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
  "log_entry": "B2-0008 FAIL mousebite/high B2; 3rd mousebite in last 50 units; check handling."
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
  "summary": "Unit failed with one high-severity short, spur, and pin-hole defects in zones B1 and C1.",
  "likely_causes": [
    "short",
    "spur",
    "pin-hole"
  ],
  "recommended_actions": [
    "clean the environment",
    "check etch time and concentration",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole defects in zones B1 and C1.",
  "log_entry": "B1-B5 FAIL short, spur, pin-hole; 3rd short in last 50 units; check etch time and concentration; clean the environment."
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
  "summary": "Unit failed with one high-severity short, mousebite, and spur defects in zones A1, A2, and B1.",
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
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects in zones A1, A2, and B1.",
  "log_entry": "U-BENCH-0010 FAIL short, mousebite, spur defects in zones A1, A2, B1; 3rd short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean the line; clean artwork."
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
  "summary": "Unit failed with one high-severity short, mousebite, and spur defects in zones C1, B1, and A1 respectively.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean the environment",
    "rework by cutting the bridge",
    "check etch time and concentration",
    "inspect resist integrity and film edges"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects in zones C1, B1, and A1 respectively.",
  "log_entry": "C1-0012 FAIL short mousebite spur; 3rd short in last 50 units; check etch time and concentration."
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
    "resist flaw"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction.",
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small copper bridge between conductors) in zone C1.",
  "likely_causes": [
    "under-etch residue",
    "resist residue",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, or pin-hole after correction.",
  "log_entry": "U-BENCH-0014 FAIL short/spur/ pin-hole high-severity; 3rd short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean the line; clean artwork."
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
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0015 FAIL open/high B1; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short, spur, and pin-hole defects in zones B2, B1, and C2.",
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
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole defects in zones B2, B1, and C2.",
  "log_entry": "U-BENCH-0016 FAIL short/spur/pin-hole high B2; 3rd short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean the line; clean artwork."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge between conductors) in zone B2.",
  "likely_causes": [
    "under-etch residue; resist residue; conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse; rework by cutting the bridge; clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B2-0017 FAIL short/under-etch B2; 3rd short in last 50 units; check etchant strength and rinse."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity mousebite (notches or missing copper), and one high-severity spur (small copper protrusion from a trace) in zone B1.",
  "likely_causes": [
    "resist nick",
    "film edge damage",
    "over-etch at edges",
    "resist defect"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B1-0018 FAIL short/ mousebite/ spur/ pin-hole high-severity; 4th short in last 50 units; clean phototool; inspect resist coat."
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
  "verify": "Re-inspect the next 5 units for open after the correction.",
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity pin-hole (small hole inside a copper area), and one high-severity copper (isolated stray copper) in zone B2.",
  "likely_causes": [
    "resist pinhole",
    "plating void",
    "dust on phototool",
    "copper (isolated stray copper)"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short and pin-hole after correction.",
  "log_entry": "U-BENCH-0020 FAIL short/high pin-hole/B2; 3rd short in last 50 units; check etch time and concentration; clean the environment."
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
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 2x mousebite, 1x open, 1x short, 1x spur, 1x copper, 1x pin-hole; worst is high open in zone B3.",
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
  "log_entry": "U-BENCH-0022 FAIL open/high B3; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity short, spur, and copper defects in zones C2 and B1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris",
    "resist residue"
  ],
  "recommended_actions": [
    "check etch uniformity",
    "clean artwork",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and copper defects in zones C2 and B1.",
  "log_entry": "U-BENCH-0023 FAIL short, spur, and copper defects in zones C2 and B1; 3 short defects in last 50 units; check etch uniformity and clean artwork."
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
    "clean the environment"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0024 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short, mousebite, and spur defects in zones B1 and C1.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean the environment",
    "inspect resist coat",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects in zones B1 and C1.",
  "log_entry": "B1-0025 FAIL short, mousebite, spur; 3rd short in last 50 units; clean the environment."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone B1.",
  "likely_causes": [
    "under-etch residue; resist residue; conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B1-0026 FAIL short high B1; 3rd short in last 50 units; check etch strength and rinse."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small hole inside a copper area) in zone B1.",
  "likely_causes": [
    "spur",
    "pin-hole",
    "short"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge",
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short after the correction.",
  "log_entry": "B1-0027 FAIL short/spur/pin-hole; 4th short in last 50 units; clean phototool."
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
  "summary": "Unit failed with one high-severity short, mousebite, and spur defects in zones A1, B1, and B2.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean phototool",
    "inspect resist coat",
    "rework by cutting the bridge for short defects"
  ],
  "verify": "Re-inspect the next 5 units for short defects after short defects are reported.",
  "log_entry": "U-BENCH-0028 FAIL short high A1 B1; 3 short defects in last 50 units; clean phototool."
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
  "verify": "Re-inspect the next 5 units for open after the correction.",
  "log_entry": "U-BENCH-0029 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |
