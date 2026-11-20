"""Jetson system telemetry from `tegrastats` (RAM, CPU, GPU load, temperature, VDD_IN board power)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from typing import Optional

import psutil

RE_RAM = re.compile(r"RAM (\d+)/(\d+)MB")
RE_CPU = re.compile(r"CPU \[([^\]]+)\]")
RE_GPU = re.compile(r"GR3D_FREQ (\d+)%")
RE_TEMP = re.compile(r"(\w+)@(-?[\d.]+)C")
RE_VDD_IN = re.compile(r"VDD_IN (\d+)mW(?:/(\d+)mW)?")


def parse_tegrastats(line: str) -> dict:
    out: dict = {}
    if m := RE_RAM.search(line):
        out["ram_used_mb"], out["ram_total_mb"] = float(m.group(1)), float(m.group(2))
    if m := RE_CPU.search(line):
        loads = [float(x.split("%")[0]) for x in m.group(1).split(",") if "%" in x]
        out["cpu_pct"] = sum(loads) / len(loads) if loads else None
    if m := RE_GPU.search(line):
        out["gpu_pct"] = float(m.group(1))
    temps = {k.lower(): float(v) for k, v in RE_TEMP.findall(line)}
    if temps:
        out["temps_c"] = temps
        out["temp_c"] = temps.get("tj") or max(temps.values())
    if m := RE_VDD_IN.search(line):
        out["power_mw"] = float(m.group(1))
    return out


class Telemetry(threading.Thread):
    def __init__(self, interval_ms: int = 1000, llm_pid=None):
        """llm_pid: callable returning the PID of the Llama server process (separate runtime), or None."""
        super().__init__(daemon=True, name="telemetry")
        self.interval_ms = interval_ms
        self.llm_pid = llm_pid
        self.latest: dict = {}
        self.proc: Optional[subprocess.Popen] = None
        self.me = psutil.Process(os.getpid())

    @property
    def available(self) -> bool:
        return shutil.which("tegrastats") is not None

    def snapshot(self) -> dict:
        snap = dict(self.latest)
        snap["proc_rss_mb"] = self.me.memory_info().rss / 2**20
        pid = self.llm_pid() if self.llm_pid else None
        if pid:
            try:
                snap["llm_rss_mb"] = psutil.Process(pid).memory_info().rss / 2**20
            except psutil.Error:
                pass
        if "cpu_pct" not in snap:
            snap["cpu_pct"] = psutil.cpu_percent()
            vm = psutil.virtual_memory()
            snap["ram_used_mb"], snap["ram_total_mb"] = (vm.total - vm.available) / 2**20, vm.total / 2**20
        return snap

    def run(self) -> None:
        if not self.available:
            return
        self.proc = subprocess.Popen(["tegrastats", "--interval", str(self.interval_ms)],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for line in self.proc.stdout:
            self.latest = parse_tegrastats(line)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
