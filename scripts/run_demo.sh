#!/usr/bin/env bash
# Start the operator UI. Extra args are passed through, e.g.
#   scripts/run_demo.sh --set vision.backend=groundtruth --set advisory.backend=template
#   scripts/run_demo.sh --set source.type=camera --set profile=fasteners
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec python -m qc serve "$@"
