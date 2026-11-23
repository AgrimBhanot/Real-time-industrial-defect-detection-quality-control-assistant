# PS5 QC Inspector: on-device industrial defect detection + Llama QC assistant

Bharat AI-SoC Challenge 2026-27, PS5. Runs fully offline on one **NVIDIA Jetson Orin Nano Super (Arm Cortex-A78AE)**:

```
frame source ──► vision (runtime A) ──► rule engine ──► SQLite log ──► operator UI (Flask, :8000)
 folder/video/    YOLO on the Orin GPU    severity +        │               ▲
 USB/CSI camera   TensorRT | ONNX RT      PASS/FAIL/REVIEW  ▼               │
                                                  async queue ──► advisory (runtime B) ──► validator
                                                                  qc_llm_server process:     JSON + grounding,
                                                                  Llama 3.2 1B Instruct .pte retry, then SOP
                                                                  ExecuTorch, XNNPACK, CPU   template fallback
```

- **Rules decide, Llama explains.** PASS/FAIL never depends on the LLM. Severity comes from type, size and location, never confidence. Low-confidence detections are routed to human REVIEW.
- **Two runtimes, two processes.** Vision runs in the Python process on the GPU (TensorRT). Llama runs in `qc_llm_server`, a small C++ program linked against ExecuTorch (`native/qc_llm_server/`). It loads the `.pte` once and then serves prompts over stdin/stdout, so no unit pays the model load. ExecuTorch's own `llama_main` is built alongside it for one-shot checks. The two runtimes are benchmarked separately and together.
- **Domain = profile.** `configs/profiles/pcb.yaml` (DeepPCB, 6 classes) and `configs/profiles/fasteners.yaml` (bolts, Phase 2, no model yet) hold the classes, severity policy, decision rules and SOP notes. Switch with `--set profile=fasteners`.

## Layout

| Path | What |
|---|---|
| `configs/app.yaml` | runtime config (source, backends, paths, server); override any key with `--set a.b=c` |
| `configs/profiles/*.yaml` | per-domain classes, severity policy, SOP table used to ground Llama |
| `qc/` | the application: `sources`, `vision/`, `rules/`, `advisory/`, `storage/`, `pipeline`, `app/` (UI), `telemetry` |
| `training/` | `prepare_deeppcb.py`, `train.py`, `calibrate_severity.py`, `evaluate.py`, `export.py`, `capture_images.py`, `colab_train.ipynb` |
| `bench/` | `bench_vision.py` (FPS/latency/power, `--with-llm` for concurrency), `bench_llm.py` (TTFT, tok/s, validity), `soak.py`, `run_summary.py` |
| `native/qc_llm_server/` | persistent ExecuTorch Llama worker (C++, built by `build_executorch_runner.sh`) |
| `configs/llm/` | Llama export recipe (ExecuTorch `export_llm` config) |
| `scripts/` | `setup_jetson.sh`, `build_executorch_runner.sh`, `export_llama_pte.sh`, `offline_check.sh`, `run_demo.sh` |
| `tests/` | rule engine, validator/prompt, LLM-server protocol (fake server), end-to-end pipeline + UI (no model needed) |
| `data/`, `models/`, `runs/`, `third_party/` | generated / downloaded, git-ignored |

## Workflow

### 0. Jetson environment (once, needs internet)
```bash
cd ~/ps5-qc-inspector
scripts/setup_jetson.sh          # apt TensorRT bindings, .venv, Jetson PyTorch, ultralytics, flask, onnxruntime-gpu
source .venv/bin/activate
python -m qc check               # shows what is present / missing
python -m pytest -q tests
```

### 1. Vision model
- **PCB:** open `training/colab_train.ipynb` in Colab (T4). It downloads DeepPCB, converts it, calibrates severity thresholds, trains YOLO11n, evaluates and exports ONNX. Download `artifacts_pcb.zip`.
- **Fasteners (live camera, Phase 2):** bolts; capture, per-part split, training and live scoring are described in `docs/fasteners_live.md`. No trained model yet.

Then, on the Jetson:
```bash
unzip -o artifacts_pcb.zip                              # models/vision/pcb/best.pt (+ .onnx, thresholds)
python training/export.py --profile pcb --to engine      # TensorRT FP16 engine, built on this GPU
python training/evaluate.py --profile pcb --backend tensorrt   # numbers for the report
```
Data can also be prepared on the Jetson itself: `python training/prepare_deeppcb.py --download --templates`.

### 2. Llama via ExecuTorch (mandatory)
1. Hugging Face access to `meta-llama/Llama-3.2-1B-Instruct`, then `hf auth login`.
2. **Export** on an x86-64 Linux machine with Python 3.10-3.12 and about 12 GB RAM (laptop or Colab):
   `PYTHON=/path/to/python scripts/export_llama_pte.sh`. The recipe is `configs/llm/llama3_2_1b_instruct_8da4w.yaml` (8da4w, group 32, 4-bit embeddings, XNNPACK, 2k context). The script writes the `.pte`, `tokenizer.model` and `EXPORT_INFO.txt` (versions and sha256); copy all three to `models/llm/`.
3. **Build** on the Jetson: `scripts/build_executorch_runner.sh` builds `llama_main` and `qc_llm_server` from the same ExecuTorch release (pinned in `scripts/versions.env`), using its own venv `third_party/.venv-et`.
4. `python -m qc advise-sample --set advisory.backend=executorch` runs one grounded advisory call (gate G1).

   **Version note (Phase 1):** the `.pte` in use was exported on Colab, which had ExecuTorch 1.6.0 (Colab's Python has no 1.0.0 wheel). The Jetson runtime is 1.0.0. That combination is tested and working (gate G1 passed on 20 Nov 2026), but the release notes promise no compatibility across versions, so Phase 2 should align both to one release. Re-export with 1.0.0 using Python 3.10-3.12 (`scripts/export_llama_pte.sh`, 12+ GB free RAM), or rebuild the runners from a newer tag. `--set advisory.executorch.mode=oneshot` uses `llama_main` instead.

### 3. Run
```bash
python -m qc run --max-frames 50 --set vision.backend=groundtruth   # whole pipeline before a model exists
scripts/run_demo.sh                                                  # UI: http://192.168.55.1:8000 from the laptop
scripts/run_demo.sh --set source.type=camera --set profile=fasteners
```

### 4. Benchmarks (on the Jetson, network off: `scripts/offline_check.sh --go-offline`)
```bash
python bench/bench_vision.py --backend tensorrt --frames 300                     # pre/infer/post, FPS, power
python bench/bench_vision.py --backend onnxruntime --frames 300
python bench/bench_llm.py --n 30 --set advisory.backend=executorch               # TTFT, tok/s, validity (+ review sheet)
python bench/bench_vision.py --backend tensorrt --with-llm --set advisory.backend=executorch   # concurrency
python bench/soak.py --units 1000 --set advisory.backend=executorch              # reliability + log integrity
python bench/run_summary.py runs/inspections.db                                  # frame->verdict / ->advice latency
```
Results land in `bench/results/*.json`. `bench_llm` also writes a `*.review.md` sheet for scoring advice by hand. Power is the board's `VDD_IN` rail from `tegrastats`. Use `sudo nvpmodel -q` to record the power mode (15 W for our runs).

## Results so far (Jetson Orin Nano Super 8 GB, JetPack 6.2 / L4T R36.5, nvpmodel 25 W, Wi-Fi on)

Raw files: `bench/results/`. Re-run with `scripts/run_benchmarks.sh`. Final report numbers should come from a run with the network off.

**Vision: YOLO11n 640, trained on the Jetson (60 epochs), TensorRT FP16.** DeepPCB test split (500 boards) plus 500 defect-free templates, IoU 0.5, conf 0.25.

| metric | value |
|---|---|
| mAP@0.5 / mAP@0.5:0.95 | 0.970 / 0.746 |
| macro P / R / F1 | 0.862 / 0.963 / 0.906 |
| weakest classes | open P 0.68 (false alarms), pin-hole P 0.77, short R 0.91 |
| unit escape rate (defective passed) | 0.6% (3/500) |
| unit false-reject rate (clean failed) | 8.4% (42/500) |
| TensorRT: FPS, pre / infer / post ms | 35.4 FPS, 3.6 / 11.9 / 5.5 ms (22.7 ms total, p95 23.9) |
| ONNX Runtime GPU: FPS, total ms | 26.1 FPS, 34.7 ms |
| frame -> verdict logged (end to end) | 22.5 ms mean, 24.9 ms p95 |

**Llama 3.2 1B Instruct, ExecuTorch 8da4w, XNNPACK, 4 Cortex-A78AE threads, persistent `qc_llm_server`.** 30 realistic records.

| metric | value |
|---|---|
| model load (once) | 3.6-3.9 s; process RSS 1.25 GB |
| prompt / generated tokens | 1105 / 152 mean |
| TTFT | 15.5 s mean (17.9 p95), dominated by prefill of the ~1.1k-token prompt |
| decode speed | 15.0 tok/s mean |
| total per advice | 25.5 s mean (30.6 p95) |
| valid advice / clean first try / repaired / template fallback | 100% / 67% / 30% / 0% |
| faithfulness failures (defect not in record) | 0 |
| running together with vision | vision 38 FPS (no loss); Llama 13.3 tok/s (about -9%) |

**Reliability:** 1,000-unit soak with Llama advice passed: no crashes, every unit logged, SQLite integrity ok, app RSS +3 MB. Board power during the soak was 8.4 W mean and 9.0 W max; temperature stayed at or below 55 C.

**Known limits / Phase 2 work:**
- Llama latency is mostly prompt prefill. Shorten the worked example, and cache the KV of the fixed system prompt.
- Llama advises roughly 2 units per minute. Faster conveyors get advice on the most recent units only (oldest dropped by design).
- Add per-class confidence thresholds for `open` and `pin-hole`, which drive the 8.4% false rejects.
- The 1B model's causes are sometimes generic or list defect names. Score this with the `*.review.md` sheet.
- The `.pte` was exported with ExecuTorch 1.6.0 but runs on the 1.0.0 runtime (see section 2).

## Status (Phase 1 checklist)

| Item | State |
|---|---|
| Application, dataset, classes | `pcb` profile (DeepPCB, 6 classes) done; `fasteners` profile drafted |
| Detector with P/R | done: YOLO11n, TensorRT FP16 on the Orin GPU, results above |
| Llama via ExecuTorch on device | done: Llama 3.2 1B 8da4w, persistent `qc_llm_server` on the Arm CPU |
| Vision -> Llama hand-off + local log | done: JSON record, async queue, validator with repair, SQLite log |
| Offline end-to-end run | runs end to end; repeat with Wi-Fi off for the record (`scripts/offline_check.sh --go-offline`) |
| FPS / latency / memory / power | measured, see above |
| GitHub repo, demo video, report | repo initialised locally; video and report to do |

## Notes
- DeepPCB: research use; many defects are artificially added to real board scans. Disclose this in the report.
- Ultralytics YOLO is AGPL-3.0, which is satisfied by publishing this repository's source.
- Llama 3.2 is under the Llama 3.2 Community License. Model weights are not committed.
