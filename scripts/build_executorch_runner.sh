#!/usr/bin/env bash
# Build ExecuTorch (pinned release) natively on the Jetson's Arm Cortex-A78AE CPU with XNNPACK (+KleidiAI),
# then two Llama runners from the same build:
#   llama_main     - ExecuTorch's reference one-shot runner (gate G1, debugging)
#   qc_llm_server  - our persistent worker (native/qc_llm_server): model loaded once, prompts over stdin/stdout
# Takes ~30-60 min on an Orin Nano. Uses its own venv (third_party/.venv-et) with the matching executorch
# wheel, so codegen sees the torch version this release expects and the CUDA torch in .venv is untouched.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/versions.env
ROOT=$(pwd)
ET_DIR="$ROOT/third_party/executorch"
VENV="$ROOT/third_party/.venv-et"
JOBS=${JOBS:-4}   # 8 GB shared RAM: more parallel jobs can OOM while vision is running

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -U pip
  "$VENV/bin/pip" install -q "executorch==$ET_VERSION" "cmake>=3.29,<4" ninja pyyaml ruamel.yaml tomli zstd
fi
export PATH="$VENV/bin:$PATH"
PY="$VENV/bin/python"

if [ ! -d "$ET_DIR/.git" ]; then
  git clone --branch "v$ET_VERSION" --depth 1 https://github.com/pytorch/executorch.git "$ET_DIR"
fi
cd "$ET_DIR"
git submodule sync -q
git submodule update -q --init --recursive --depth 1

python3 "$ROOT/native/patch_prefix_cache.py" . # reuse the unchanged start of each prompt

echo "== [1/3] ExecuTorch core + XNNPACK + LLM extensions (preset 'llm') =="
cmake --preset llm -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=cmake-out \
  -DPYTHON_EXECUTABLE="$PY" -DSUPPORT_REGEX_LOOKAHEAD=ON
cmake --build cmake-out -j"$JOBS" --target install --config Release

echo "== [2/3] register qc_llm_server next to llama_main (same link line) =="
LLAMA_CMAKE=examples/models/llama/CMakeLists.txt
if ! grep -q "qc_llm_server" "$LLAMA_CMAKE"; then
  cat >> "$LLAMA_CMAKE" <<'EOF'

# --- added by ps5-qc-inspector/scripts/build_executorch_runner.sh ---
if(QC_LLM_SERVER_SRC)
  add_executable(qc_llm_server ${QC_LLM_SERVER_SRC})
  target_include_directories(qc_llm_server PUBLIC ${_common_include_directories})
  target_link_libraries(qc_llm_server PUBLIC llama_runner ${link_libraries})
  target_compile_options(qc_llm_server PUBLIC ${_common_compile_options})
  if(UNIX AND NOT APPLE)
    set_target_properties(qc_llm_server PROPERTIES LINK_FLAGS "-Wl,-rpath='$ORIGIN'")
  endif()
endif()
EOF
fi

echo "== [3/3] llama_main + qc_llm_server =="
cmake -DCMAKE_INSTALL_PREFIX=cmake-out -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release \
  -DPYTHON_EXECUTABLE="$PY" -DSUPPORT_REGEX_LOOKAHEAD=ON \
  -DQC_LLM_SERVER_SRC="$ROOT/native/qc_llm_server/qc_llm_server.cpp" \
  -Bcmake-out/examples/models/llama examples/models/llama
cmake --build cmake-out/examples/models/llama -j"$JOBS" --config Release --target llama_main qc_llm_server

OUT="$ET_DIR/cmake-out/examples/models/llama"
ls -la "$OUT/llama_main" "$OUT/qc_llm_server"
cat > "$ROOT/third_party/RUNNER_INFO.txt" <<EOF
executorch v$ET_VERSION ($(git rev-parse --short HEAD))  built $(date -Iseconds) on $(uname -m)
compiler: $(c++ --version | head -1)
cmake: $(cmake --version | head -1)
EOF
echo "runners: $OUT/{llama_main,qc_llm_server}"
