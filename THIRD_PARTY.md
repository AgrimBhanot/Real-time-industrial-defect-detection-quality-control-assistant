# Third-party components, data and models

| Component | Use here | License / terms | Source |
|---|---|---|---|
| ExecuTorch v1.0.0 | Llama runtime (runtime B), `llama_main`, links into `qc_llm_server` | BSD-3-Clause | github.com/pytorch/executorch |
| XNNPACK, KleidiAI | CPU kernels used by ExecuTorch on the Arm Cortex-A78AE | BSD-3-Clause / Apache-2.0 | bundled with ExecuTorch |
| Llama 3.2 1B Instruct | advisory model, exported to `.pte` (weights not in this repo) | Llama 3.2 Community License; "Built with Llama" | huggingface.co/meta-llama/Llama-3.2-1B-Instruct |
| Ultralytics YOLO11 | detector training, export, inference wrapper | AGPL-3.0 (satisfied by publishing this repository's source) | github.com/ultralytics/ultralytics |
| PyTorch / torchvision | training, torch backend | BSD-3-Clause | pytorch.org (Jetson builds: pypi.jetson-ai-lab.io) |
| TensorRT 10.3, CUDA 12.6 | vision runtime A on the Orin GPU | NVIDIA SDK license (JetPack) | developer.nvidia.com/embedded/jetpack |
| ONNX Runtime GPU | alternative vision backend | MIT | onnxruntime.ai |
| OpenCV 4.5 (JetPack) | capture, GStreamer/CSI camera, drawing | Apache-2.0 | opencv.org |
| Flask | local operator UI | BSD-3-Clause | flask.palletsprojects.com |

## Dataset

**DeepPCB** (Tang et al., "Online PCB Defect Detector On A New PCB Defect Dataset", arXiv:1902.06197),
github.com/tangsanli5201/DeepPCB. 1,500 aligned template/test pairs, 640x640, ~48 px/mm, 6 classes.
The repository states the data is for research use. Many defects were added artificially to real board scans
by the authors; results on DeepPCB are therefore an optimistic proxy for a real AOI line. The data is downloaded
by `training/prepare_deeppcb.py` and is not redistributed in this repository.

## Citation

```
@article{tang2019online,
  title={Online PCB Defect Detector On A New PCB Defect Dataset},
  author={Tang, Sanli and He, Fan and Huang, Xiaolin and Yang, Jie},
  journal={arXiv preprint arXiv:1902.06197},
  year={2019}
}
```
