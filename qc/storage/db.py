"""Local inspection log (SQLite). Thread-safe: inspection loop, advisory worker and UI share one connection."""
from __future__ import annotations

import csv
import json
import sqlite3
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import IO, Optional

from qc.schema import SEVERITIES, AdviceResult, InspectionRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspections(
  unit_id TEXT PRIMARY KEY, ts TEXT, profile TEXT, source TEXT, image_ref TEXT, frame_path TEXT,
  result TEXT, n_defects INTEGER, max_severity TEXT,
  pre_ms REAL, infer_ms REAL, post_ms REAL, vision_ms REAL, rules_ms REAL, e2e_ms REAL, record_json TEXT);
CREATE TABLE IF NOT EXISTS detections(
  id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id TEXT REFERENCES inspections(unit_id), defect TEXT, conf REAL,
  x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER, size REAL, size_unit TEXT, zone TEXT, severity TEXT,
  needs_review INTEGER);
CREATE TABLE IF NOT EXISTS advice(
  unit_id TEXT PRIMARY KEY REFERENCES inspections(unit_id), ts TEXT, backend TEXT, json TEXT, valid INTEGER,
  fallback INTEGER, attempts INTEGER, errors TEXT, ttft_ms REAL, tok_s REAL, total_ms REAL, load_ms REAL,
  prompt_tokens INTEGER, generated_tokens INTEGER, queue_ms REAL, e2e_ms REAL, repaired INTEGER, loop_stop INTEGER);
CREATE TABLE IF NOT EXISTS system_metrics(
  ts TEXT, cpu_pct REAL, ram_used_mb REAL, gpu_pct REAL, temp_c REAL, power_mw REAL, proc_rss_mb REAL,
  llm_rss_mb REAL);
CREATE INDEX IF NOT EXISTS idx_det_unit ON detections(unit_id);
"""

# columns added after the first release; older databases are migrated in place
MIGRATIONS = {"advice": {"queue_ms": "REAL", "e2e_ms": "REAL", "repaired": "INTEGER", "loop_stop": "INTEGER"}, "system_metrics": {"llm_rss_mb": "REAL"}}

EXPORT_COLS = ["unit_id", "ts", "profile", "result", "n_defects", "max_severity", "defects", "vision_ms",
               "e2e_ms", "advice_backend", "advice_summary", "advice_valid", "advice_fallback", "ttft_ms", "tok_s",
               "llm_total_ms", "advice_e2e_ms", "image_ref", "frame_path"]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class InspectionDB:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.lock:
            self.conn.executescript(SCHEMA)
            self.conn.execute("PRAGMA journal_mode=WAL")
            for table, cols in MIGRATIONS.items():
                have = {r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")}
                for col, typ in cols.items():
                    if col not in have:
                        self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

    def log_inspection(self, rec: InspectionRecord, profile: str, frame_path: Optional[str] = None) -> None:
        sevs = [d.severity for d in rec.detections if d.severity]
        max_sev = max(sevs, key=SEVERITIES.index) if sevs else None
        t = rec.timings_ms
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec.unit_id, rec.timestamp, profile, rec.source, rec.image_ref, frame_path, rec.inspection_result,
                 len(rec.detections), max_sev, t.get("pre"), t.get("infer"), t.get("post"), t.get("vision"),
                 t.get("rules"), t.get("e2e"), json.dumps(rec.to_dict())),
            )
            self.conn.executemany(
                "INSERT INTO detections(unit_id, defect, conf, x1, y1, x2, y2, size, size_unit, zone, severity, "
                "needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [(rec.unit_id, d.defect, d.confidence, *d.bbox, d.size, d.size_unit, d.zone, d.severity,
                  int(d.needs_review)) for d in rec.detections],
            )

    def log_advice(self, r: AdviceResult) -> None:
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO advice(unit_id, ts, backend, json, valid, fallback, attempts, errors, ttft_ms, "
                "tok_s, total_ms, load_ms, prompt_tokens, generated_tokens, queue_ms, e2e_ms, repaired, loop_stop) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r.unit_id, _now(), r.backend, json.dumps(r.advice), int(r.valid), int(r.fallback), r.attempts,
                 json.dumps(r.errors), r.ttft_ms, r.tok_s, r.total_ms, r.load_ms, r.prompt_tokens,
                 r.generated_tokens, r.queue_ms, r.e2e_ms, int(r.repaired), int(r.loop_stop)),
            )

    def log_metrics(self, m: dict) -> None:
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO system_metrics(ts, cpu_pct, ram_used_mb, gpu_pct, temp_c, power_mw, proc_rss_mb, "
                "llm_rss_mb) VALUES (?,?,?,?,?,?,?,?)",
                (_now(), m.get("cpu_pct"), m.get("ram_used_mb"), m.get("gpu_pct"), m.get("temp_c"),
                 m.get("power_mw"), m.get("proc_rss_mb"), m.get("llm_rss_mb")))

    def recent(self, limit: int = 50) -> list[dict]:
        q = """
        SELECT i.unit_id, i.ts, i.profile, i.result, i.n_defects, i.max_severity, i.vision_ms, i.e2e_ms,
               i.image_ref, i.frame_path,
               (SELECT group_concat(defect || ':' || severity, ' ') FROM detections d WHERE d.unit_id = i.unit_id)
                 AS defects,
               a.backend AS advice_backend, a.json AS advice_json, a.valid AS advice_valid,
               a.fallback AS advice_fallback, a.ttft_ms, a.tok_s, a.total_ms AS llm_total_ms,
               a.e2e_ms AS advice_e2e_ms
        FROM inspections i LEFT JOIN advice a ON a.unit_id = i.unit_id
        ORDER BY i.rowid DESC LIMIT ?"""
        with self.lock:
            rows = [dict(r) for r in self.conn.execute(q, (limit,))]
        for r in rows:
            adv = json.loads(r.pop("advice_json") or "{}")
            r["advice_summary"] = adv.get("summary", "")
        return rows

    def stats(self, last_n: int = 200) -> dict:
        with self.lock:
            units = [dict(r) for r in self.conn.execute(
                "SELECT unit_id, result FROM inspections ORDER BY rowid DESC LIMIT ?", (last_n,))]
            ids = [u["unit_id"] for u in units]
            dets = []
            if ids:
                marks = ",".join("?" * len(ids))
                dets = [dict(r) for r in self.conn.execute(
                    f"SELECT defect, severity, zone FROM detections WHERE unit_id IN ({marks})", ids)]
        return {
            "units": len(units),
            "results": dict(Counter(u["result"] for u in units)),
            "defects": dict(Counter(d["defect"] for d in dets).most_common()),
            "severity": dict(Counter(d["severity"] for d in dets)),
            "zones": dict(Counter(d["zone"] for d in dets).most_common(5)),
        }

    def export_csv(self, fh: IO[str], limit: int = 100000) -> None:
        w = csv.DictWriter(fh, fieldnames=EXPORT_COLS, extrasaction="ignore")
        w.writeheader()
        for row in reversed(self.recent(limit)):
            w.writerow(row)
