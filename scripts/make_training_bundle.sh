#!/usr/bin/env bash
# Zip the code needed for Colab training (no data, no models) -> dist/training_bundle.zip
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dist
rm -f dist/training_bundle.zip
python3 - <<'PY'
import zipfile, pathlib
root = pathlib.Path(".")
with zipfile.ZipFile("dist/training_bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("qc", "configs", "training", "requirements", "scripts"):
        for p in root.joinpath(d).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                z.write(p)
print("dist/training_bundle.zip", pathlib.Path("dist/training_bundle.zip").stat().st_size // 1024, "KB")
PY
