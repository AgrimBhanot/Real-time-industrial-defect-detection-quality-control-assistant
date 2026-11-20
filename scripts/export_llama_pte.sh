#!/usr/bin/env bash
# Export Llama 3.2 1B Instruct to an ExecuTorch .pte (XNNPACK, 8-bit dynamic activations + 4-bit weights).
# Recipe: configs/llm/llama3_2_1b_instruct_8da4w.yaml.  Needs ~12 GB RAM (+swap) and Python 3.10-3.12, so run it
# on an x86-64 Linux laptop or Colab, not on the 8 GB Jetson.
#
# Prereqs: Hugging Face access to meta-llama/Llama-3.2-1B-Instruct approved and `hf auth login` done
# (or HF_TOKEN exported).
#   PYTHON=/path/to/python scripts/export_llama_pte.sh      # reuse an env that already has executorch
# Output: out_llm/<pte> + tokenizer.model + EXPORT_INFO.txt -> copy to the Jetson's models/llm/.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/versions.env
PY=${PYTHON:-python3}
OUT=$(realpath -m "${OUT:-out_llm}")
CKPT="$OUT/Llama-3.2-1B-Instruct"
PTE="$OUT/$LLAMA_PTE_NAME"
mkdir -p "$OUT"

if ! "$PY" -c "import executorch, sys; sys.exit(0 if executorch.version.__version__.startswith('$ET_VERSION') else 1)" 2>/dev/null; then
  "$PY" -m pip install -q "executorch==$ET_VERSION"
fi
# exporter dependencies that the executorch wheel does not pull in
"$PY" -m pip install -q "huggingface_hub[cli]" pytorch-tokenizers hydra-core omegaconf tiktoken sentencepiece blobfile

"$PY" - "$CKPT" "$LLAMA_HF_REPO" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(repo_id=sys.argv[2], allow_patterns=["original/*"], local_dir=sys.argv[1])
PY

CFG="$OUT/export_config.yaml"
sed -e "s#@CKPT@#$CKPT#g" -e "s#@OUT@#$PTE#g" configs/llm/llama3_2_1b_instruct_8da4w.yaml > "$CFG"
/usr/bin/time -v "$PY" -m executorch.extension.llm.export.export_llm --config "$CFG" 2>&1 | tee "$OUT/export.log"
[ -s "$PTE" ] || { echo "export failed: $PTE not written (see $OUT/export.log)" >&2; exit 1; }

cp "$CKPT/original/tokenizer.model" "$OUT/tokenizer.model"
cat > "$OUT/EXPORT_INFO.txt" <<EOF
model=$LLAMA_HF_REPO  executorch==$("$PY" -c 'import executorch.version as v; print(v.__version__)')
torch==$("$PY" -c 'import torch; print(torch.__version__)')  torchao==$("$PY" -c 'import torchao; print(torchao.__version__)')
recipe=configs/llm/llama3_2_1b_instruct_8da4w.yaml (8da4w, group 32, 4-bit embeddings, XNNPACK, 2048 ctx)
exported=$(date -Iseconds) host=$(uname -m) sha256=$(sha256sum "$PTE" | cut -d' ' -f1)
EOF
ls -lh "$PTE" "$OUT/tokenizer.model"
echo "copy to the Jetson:  scp $PTE $OUT/tokenizer.model $OUT/EXPORT_INFO.txt akshay@192.168.55.1:~/ps5-qc-inspector/models/llm/"
