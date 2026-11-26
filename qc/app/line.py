"""The running inspection line, and switching between lines (tray, metal parts, steel sheet, PCB ...) without a restart.

One Llama server process and one inspection log are shared by all lines, so a switch only reloads the vision model.
"""
from __future__ import annotations

import gc
import logging
import threading
from typing import Optional

from qc.advisory.llm import LLMServerClient, server_client
from qc.config import Config, load_config
from qc.pipeline import Pipeline
from qc.storage import InspectionDB
from qc.vision.detector import WEIGHT_FILES

log = logging.getLogger(__name__)


class Line:
    def __init__(self, cfg: Config, overrides: list[str] | None = None, config_path=None):
        self.overrides = [o for o in overrides or [] if not o.startswith("profile=")]
        self.config_path = config_path
        self.lock = threading.Lock()
        self.cfg = cfg
        self.db = InspectionDB(cfg.path(cfg.section("logging").get("db", "runs/inspections.db")))
        self.llm: Optional[LLMServerClient] = None
        if cfg.section("advisory").get("enabled", True) and cfg.section("advisory").get("backend") == "executorch":
            self.llm = server_client(cfg)
        self.pipe: Optional[Pipeline] = None
        self.thread: Optional[threading.Thread] = None
        self.switching: Optional[str] = None
        self.error: Optional[str] = None

    def start(self) -> None:
        self._launch(self.cfg)

    def _launch(self, cfg: Config) -> None:
        pipe = Pipeline(cfg, db=self.db, llm_server=self.llm)
        pipe.keep_alive = True
        self.cfg, self.pipe = cfg, pipe
        self.thread = threading.Thread(target=self._run, args=(pipe,), name="inspection", daemon=True)
        self.thread.start()

    def _run(self, pipe: Pipeline) -> None:
        try:
            pipe.run()
        except Exception:
            log.exception("inspection loop stopped")  # shown on the site through state.error

    def stop(self) -> None:
        pipe, thread = self.pipe, self.thread
        if pipe:
            pipe.stop()
            if thread:
                thread.join(timeout=20)
            pipe.close()

    def config_for(self, profile: str) -> Config:
        return load_config(self.config_path, [f"profile={profile}", *self.overrides])

    def switch(self, profile: str) -> None:
        """Runs in the background; the previous line is restored if the new one cannot start."""
        with self.lock:
            if self.switching:
                raise RuntimeError(f"already switching to {self.switching}")
            self.switching = profile
        threading.Thread(target=self._switch, args=(profile,), daemon=True).start()

    def _switch(self, profile: str) -> None:
        before = self.cfg
        self.error = None
        try:
            cfg = self.config_for(profile)
            self.stop()
            self.pipe.detector = None  # free GPU memory before the next model loads
            _free_gpu()
            try:
                self._launch(cfg)
            except Exception as exc:
                log.exception("cannot start %s", profile)
                self.error = f"cannot start {profile}: {exc}"
                self._launch(before)
        except Exception as exc:
            log.exception("switch to %s failed", profile)
            self.error = str(exc)
        finally:
            self.switching = None

    def available(self) -> list[dict]:
        out = []
        for name in self.cfg.app.get("lines") or [self.cfg.profile_name]:
            try:
                cfg = self.config_for(name)
            except Exception as exc:
                out.append({"name": name, "label": name, "ready": False, "why": str(exc), "camera": False})
                continue
            v, s = cfg.section("vision"), cfg.section("source")
            why, f = "", WEIGHT_FILES.get(v.get("backend", "tensorrt"))
            if f and not (cfg.path(v.get("weights_dir", "models/vision/{profile}")) / f).exists():
                why = "model not built yet"
            elif s.get("type") == "folder" and not cfg.path(s["path"]).exists():
                why = "no images"
            out.append({"name": name, "label": cfg.profile.get("label") or cfg.profile.get("title", name),
                        "ready": not why, "why": why, "camera": s.get("type") == "camera"})
        return out

    def close(self) -> None:
        self.stop()
        if self.llm:
            self.llm.close()


def _free_gpu() -> None:
    gc.collect()
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:
        pass
