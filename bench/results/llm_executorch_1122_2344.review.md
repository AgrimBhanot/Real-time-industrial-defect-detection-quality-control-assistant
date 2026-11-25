# Advice review sheet (executorch, 2026-11-22T23:44:47)

Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.

## U-BENCH-0000 - FAIL
findings: open/high/A2, short/high/A3, mousebite/low/B2, mousebite/low/A2, spur/low/A1, mousebite/low/B3, copper/medium/B2
backend: executorch valid=True fallback=False
```json
{
  "summary": "Multiple defects found, including short, mousebite, and open copper traces.",
  "likely_causes": [
    "short",
    "mousebite",
    "open"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "rework by cutting the short bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and open defect after short repair.",
  "log_entry": "U-BENCH-0000 FAIL short, mousebite, open; 3rd short in last 50 units; rework by cutting the short bridge; check etch time and concentration."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity copper (isolated stray copper), one high-severity spur (small copper protrusion from a trace), and one high-severity pin-hole (small hole inside a copper area) in zone B2.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris",
    "resist pinhole"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, one high-severity",
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
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Verify the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity mousebite (notches or missing copper along a trace edge), one high-severity spur (small copper protrusion from a trace), one high-severity open (break in a copper trace) in zone C1.",
  "likely_causes": [
    "under-etch residue",
    "resist defect",
    "conductive debris"
  ],
  "recommended_actions": [
    "check etchant strength and rinse",
    "rework by cutting the bridge",
    "clean the line",
    "inspect resist coat"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, spur, and open after the correction, and check etch time and concentration before rework.",
  "log_entry": "U-BENCH-0003 FAIL short high mousebite high spur high open high high"
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
    "check etch time and concentration",
    "inspect handling and phototool cleanliness"
  ],
  "verify": "Verify the next 5 units for short, open, and mousebite defects, and rework by cutting the bridge, and check etch time and concentration.",
  "log_entry": "U-BENCH-0004 FAIL short open mousebite high-confidence high-severity high-confidence"
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
    "resist flaw"
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
  "summary": "Unit failed with short, mousebite, spur, and copper defects in zones B1, C2, B2, and A1.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur",
    "copper"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect resist integrity and film edges",
    "clean phototool",
    "rework by cutting the bridge"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, spur, and copper defects in zones B1, C2, B2, and A1.",
  "log_entry": "B1 C2 B2 A1 short(mousebite spur copper) FAIL short(mousebite spur copper)"
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
    "resist flaw",
    "dust on phototool"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect handling and phototool cleanliness",
    "quarantine the lot"
  ],
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "C1-B1-0.5938-0.4978-0.4427-0.6424-0.5633-0.02-1.02-1.02-1.02-1"
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
  "summary": "Unit failed with one high-severity mousebite, one high-severity spur, and one high-severity pin-hole in zone B1.",
  "likely_causes": [
    "resist nick",
    "film edge damage",
    "over-etch at edges",
    "resist defect"
  ],
  "recommended_actions": [
    "inspect resist integrity and film edges",
    "check handling",
    "clean artwork",
    "clean phototool"
  ],
  "verify": "Re-inspect the next 5 units for mousebite, spur, and pin-hole defects, and check handling and phototool cleanliness.",
  "log_entry": "B1-0008 FAIL mousebite, spur, pin-hole; 3rd mousebite in last 50 units; check handling and phototool cleanliness."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge), one high-severity spur (small copper protrusion), and one high-severity pin-hole (small hole inside a copper area) in zone B1.",
  "likely_causes": [
    "short",
    "spur",
    "pin-hole"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "rework by cutting the bridge",
    "clean the line",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole defects, and check etch time and concentration.",
  "log_entry": "B1-0009 FAIL short spur pin-hole high-severity defects; 3 short, 1 spur, 1 pin-hole in last 50 units; check etch time and concentration."
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
  "log_entry": "U-BENCH-0010 FAIL short/low spur/high high high"
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
  "summary": "Unit failed with one high-severity open, short, mousebite, spur, and short defects in zones A1, B1, B2, B2, and B1 respectively.",
  "likely_causes": [
    "over-etching",
    "scratch or handling damage",
    "resist nick",
    "film edge damage"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect resist integrity and film edges",
    "check handling",
    "clean the environment"
  ],
  "verify": "Verify the next 5 units for open after the correction, short defects after rework, mousebite and spur defects after cleaning the artwork, and short defects after rework.",
  "log_entry": "U-BENCH-0011 FAIL open short mousebite spur short; 3 high-severity defect(s) in zones A1, B1, B2, B2, and B1 respectively; check etch time and concentration; inspect resist integrity and film"
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
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur in zone C1; check etch uniformity and clean artwork.",
  "log_entry": "C1-0012 FAIL short/high mousebite/low spur; 3 short in last 50 units; check etch uniformity and clean artwork."
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
  "verify": "Re-inspect the next 5 units for open after the correction, and verify the next 10 units for mousebite and pin-hole defects.",
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
    "clean the line"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, and pin-hole after correction.",
  "log_entry": "C1-0014 FAIL short/high spur/low P66 0.6263; 3rd short in last 50 units; check etchant strength and rinse; rework by cutting the bridge; clean the line."
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
backend: template valid=False fallback=True
```json
{
  "summary": "FAIL: 2x open, 2x short, 2x mousebite, 2x spur, 1x copper, 1x pin-hole; worst is high open in zone A2.",
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
  "log_entry": "U-BENCH-0017 FAIL open/high A2; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity short (unintended copper bridge) in zone B3.",
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
  "log_entry": "B3-0018 FAIL short/under-etch B3; 3rd short in last 50 units; check etchant strength and rinse."
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
  "verify": "Re-inspect the next 5 units for open after the correction, and verify the integrity of the resist coating on the next 3 units.",
  "log_entry": "U-BENCH-0019 FAIL open/high A1; 3 open in last 50 units."
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone B2.",
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
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur defects in zone B2; 2nd unit failed with one high-severity short in zone B1.",
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
  "summary": "Multiple defects present, most severe being short (unintended copper bridge between conductors) in zone B2.",
  "likely_causes": [
    "short",
    "mousebite",
    "copper",
    "pin-hole"
  ],
  "recommended_actions": [
    "rework by cutting the bridge",
    "clean phototool",
    "inspect resist coat",
    "check etch time and concentration"
  ],
  "verify": "Verify the next 5 units for short after the rework.",
  "log_entry": "B2 short high B1 high B2 high B3"
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
  "summary": "Unit failed with one high-severity short, one high-severity spur, and one high-severity copper in zone B1.",
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
  "verify": "Re-inspect the next 5 units for short, spur, or copper defects in zone B2; 2nd unit failed with one high-severity short, one high-severity spur, and one high-severity copper in zone B1.",
  "log_entry": "U-BENCH-0023 FAIL short/high spur/copper in zone B1; 2nd unit failed with one high-severity short, one high-severity spur, and one high-severity copper in zone B1; check etch uniformity and clean artwork."
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
  "summary": "Multiple defects present, with short and open defects being the most severe.",
  "likely_causes": [
    "short",
    "open",
    "mousebite",
    "copper"
  ],
  "recommended_actions": [
    "clean the environment",
    "rework by cutting the bridge",
    "check etch time and concentration",
    "inspect resist integrity and film edges"
  ],
  "verify": "Verify the next 5 units for short, open, and mousebite defects before rework.",
  "log_entry": "U-BENCH-0024 FAIL short open mousebite high B2; 3rd short in last 50 units; short and open defects are the most severe; check etch time and concentration."
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
  "verify": "Verify the next 5 units for short defects, and rework by cutting the bridge if multiple short defects are found.",
  "log_entry": "B1-0026 FAIL short high B1; 5 short defects in last 50 units; rework by cutting the bridge."
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
  "summary": "Unit failed with one high-severity short, one high-severity spur, and one high-severity pin-hole in zone B2.",
  "likely_causes": [
    "short",
    "spur",
    "pin-hole"
  ],
  "recommended_actions": [
    "check etch time and concentration",
    "inspect resist coat",
    "clean artwork"
  ],
  "verify": "Re-inspect the next 5 units for short, spur, or pin-hole after correction.",
  "log_entry": "U-BENCH-0027 FAIL short/high B2; 3rd short in last 50 units; check etch time and concentration; clean artwork."
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
  "summary": "Unit failed with one high-severity short, one high-severity mousebite, and one high-severity spur in zone B2.",
  "likely_causes": [
    "short",
    "mousebite",
    "spur"
  ],
  "recommended_actions": [
    "clean artwork",
    "rework by cutting the spur",
    "rework by cutting the short"
  ],
  "verify": "Re-inspect the next 5 units for short, mousebite, and spur, and check etch time and concentration before rework.",
  "log_entry": "B2-0028 FAIL short/spur/mousebite high; 3rd short in last 50 units; check etch time and concentration before rework."
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
  "verify": "Re-inspect the next 5 units for open after the correction, and check the etch time and concentration for the next 5 units.",
  "log_entry": "U-BENCH-0029 FAIL open/high B2; 3rd open in last 50 units; check etch time and concentration."
}
```
| grounded | actionable | correct | concise |
|---|---|---|---|
|  |  |  |  |
