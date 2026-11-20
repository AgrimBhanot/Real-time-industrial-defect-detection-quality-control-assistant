"""PS5 on-device visual QC inspector: vision -> rules -> Llama (ExecuTorch) advisory -> log/UI."""
import os

# The Jetson venv deliberately uses JetPack's OpenCV (GStreamer/CSI) instead of the pip wheel; stop Ultralytics
# from "fixing" that by pip-installing packages at runtime (the demo must also work offline).
os.environ.setdefault("YOLO_AUTOINSTALL", "false")

__version__ = "0.2.0"
