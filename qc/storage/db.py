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
CREATE TABLE IF NOT EXISTS decisions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id TEXT REFERENCES inspections(unit_id), ts TEXT, decision TEXT,
  operator TEXT, note TEXT);
CREATE INDEX IF NOT EXISTS idx_det_unit ON detections(unit_id);
CREATE INDEX IF NOT EXISTS idx_dec_unit ON decisions(unit_id);
"""

# what an operator can record about a unit; every entry is kept (decisions is append-only), the newest one counts
DECISIONS = ("confirmed", "false_alarm", "missed_defect", "rework", "scrap")

# columns added after the first release; older databases are migrated in place
MIGRATIONS = {"advice": {"queue_ms": "REAL", "e2e_ms": "REAL", "repaired": "INTEGER", "loop_stop": "INTEGER",
                         "cached_tokens": "INTEGER"},
              "system_metrics": {"llm_rss_mb": "REAL"},
              "inspections": {"session": "TEXT", "gt_result": "TEXT", "gt_outcome": "TEXT", "n_parts": "INTEGER"}}

EXPORT_COLS = ["unit_id", "ts", "session", "profile", "result", "n_defects", "max_severity", "defects", "n_parts",
               "gt_result", "gt_outcome", "decision", "decision_operator", "decision_note", "decision_ts", "vision_ms",
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

    def log_inspection(self, rec: InspectionRecord, profile: str, frame_path: Optional[str] = None,
                       session: Optional[str] = None) -> None:
        sevs = [d.severity for d in rec.detections if d.severity]
        max_sev = max(sevs, key=SEVERITIES.index) if sevs else None
        t = rec.timings_ms
        row = {"unit_id": rec.unit_id, "ts": rec.timestamp, "profile": profile, "source": rec.source,
               "image_ref": rec.image_ref, "frame_path": frame_path, "result": rec.inspection_result,
               "n_defects": len(rec.detections), "max_severity": max_sev, "pre_ms": t.get("pre"),
               "infer_ms": t.get("infer"), "post_ms": t.get("post"), "vision_ms": t.get("vision"),
               "rules_ms": t.get("rules"), "e2e_ms": t.get("e2e"), "record_json": json.dumps(rec.to_dict()),
               "session": session, "gt_result": rec.gt_result, "gt_outcome": rec.gt_outcome,
               "n_parts": len(rec.parts) or None}
        with self.lock, self.conn:
            self.conn.execute(f"INSERT OR REPLACE INTO inspections({', '.join(row)}) "
                              f"VALUES ({', '.join('?' * len(row))})", list(row.values()))
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
                "tok_s, total_ms, load_ms, prompt_tokens, generated_tokens, queue_ms, e2e_ms, repaired, loop_stop, "
                "cached_tokens) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r.unit_id, _now(), r.backend, json.dumps(r.advice), int(r.valid), int(r.fallback), r.attempts,
                 json.dumps(r.errors), r.ttft_ms, r.tok_s, r.total_ms, r.load_ms, r.prompt_tokens,
                 r.generated_tokens, r.queue_ms, r.e2e_ms, int(r.repaired), int(r.loop_stop),
                 r.cached_tokens),
            )

    def log_metrics(self, m: dict) -> None:
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO system_metrics(ts, cpu_pct, ram_used_mb, gpu_pct, temp_c, power_mw, proc_rss_mb, "
                "llm_rss_mb) VALUES (?,?,?,?,?,?,?,?)",
                (_now(), m.get("cpu_pct"), m.get("ram_used_mb"), m.get("gpu_pct"), m.get("temp_c"),
                 m.get("power_mw"), m.get("proc_rss_mb"), m.get("llm_rss_mb")))

    _LIST = """
        SELECT i.rowid AS row, i.unit_id, i.ts, i.session, i.profile, i.result, i.n_defects, i.n_parts, i.max_severity,
               i.vision_ms, i.e2e_ms, i.image_ref, i.frame_path, i.gt_result, i.gt_outcome,
               (SELECT group_concat(defect || ':' || severity, ' ') FROM detections d WHERE d.unit_id = i.unit_id)
                 AS defects,
               a.backend AS advice_backend, a.json AS advice_json, a.valid AS advice_valid,
               a.fallback AS advice_fallback, a.repaired AS advice_repaired, a.ttft_ms, a.tok_s,
               a.total_ms AS llm_total_ms, a.e2e_ms AS advice_e2e_ms,
               c.decision, c.operator AS decision_operator, c.note AS decision_note, c.ts AS decision_ts
        FROM inspections i LEFT JOIN advice a ON a.unit_id = i.unit_id
        LEFT JOIN decisions c ON c.id = (SELECT max(id) FROM decisions x WHERE x.unit_id = i.unit_id)"""

    @staticmethod
    def _where(f: dict) -> tuple[str, list]:
        """Filters of the log page -> SQL. Unknown keys are ignored; values are always bound parameters."""
        w, p = [], []
        if f.get("results"):
            w.append(f"i.result IN ({','.join('?' * len(f['results']))})")
            p += list(f["results"])
        for key, col in (("profile", "i.profile"), ("session", "i.session"), ("gt_outcome", "i.gt_outcome")):
            if f.get(key):
                w.append(f"{col} = ?")
                p.append(f[key])
        if f.get("defect"):
            w.append("EXISTS (SELECT 1 FROM detections d WHERE d.unit_id = i.unit_id AND d.defect = ?)")
            p.append(f["defect"])
        if f.get("decision") == "open":   # stopped units nobody has decided about yet
            w.append("c.id IS NULL AND i.result IN ('FAIL', 'REVIEW')")
        elif f.get("decision"):
            w.append("c.decision = ?")
            p.append(f["decision"])
        if f.get("since"):
            w.append("i.ts >= ?")
            p.append(f["since"])
        if f.get("until"):
            w.append("i.ts < ?")
            p.append(f["until"])
        if f.get("q"):
            like = "%" + str(f["q"]).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            w.append("(i.unit_id LIKE ? ESCAPE '\\' OR i.image_ref LIKE ? ESCAPE '\\' OR a.json LIKE ? ESCAPE '\\' "
                     "OR c.note LIKE ? ESCAPE '\\')")
            p += [like] * 4
        return (" WHERE " + " AND ".join(w)) if w else "", p

    def search(self, filters: Optional[dict] = None, limit: int = 50, offset: int = 0) -> dict:
        where, p = self._where(filters or {})
        join = " FROM inspections i LEFT JOIN advice a ON a.unit_id = i.unit_id LEFT JOIN decisions c ON c.id = " \
               "(SELECT max(id) FROM decisions x WHERE x.unit_id = i.unit_id)"
        with self.lock:
            total = self.conn.execute(f"SELECT count(*){join}{where}", p).fetchone()[0]
            by = dict(self.conn.execute(f"SELECT i.result, count(*){join}{where} GROUP BY 1", p).fetchall())
            rows = [dict(r) for r in self.conn.execute(
                f"{self._LIST}{where} ORDER BY i.rowid DESC LIMIT ? OFFSET ?", [*p, limit, offset])]
        for r in rows:
            adv = json.loads(r.pop("advice_json") or "{}")
            r["advice_summary"] = adv.get("summary", "")
        return {"total": total, "by_result": by, "rows": rows}

    def recent(self, limit: int = 50) -> list[dict]:
        return self.search(limit=limit)["rows"]

    def unit(self, unit_id: str) -> Optional[dict]:
        """Everything known about one unit: record, advice and every operator decision."""
        with self.lock:
            r = self.conn.execute(f"{self._LIST} WHERE i.unit_id = ?", (unit_id,)).fetchone()
            if r is None:
                return None
            out = dict(r)
            rec = self.conn.execute("SELECT record_json FROM inspections WHERE unit_id = ?", (unit_id,)).fetchone()[0]
            adv = self.conn.execute("SELECT * FROM advice WHERE unit_id = ?", (unit_id,)).fetchone()
            out["decisions"] = [dict(x) for x in self.conn.execute(
                "SELECT ts, decision, operator, note FROM decisions WHERE unit_id = ? ORDER BY id DESC", (unit_id,))]
            out["older"] = self._one("SELECT unit_id FROM inspections WHERE rowid < ? ORDER BY rowid DESC LIMIT 1", out["row"])
            out["newer"] = self._one("SELECT unit_id FROM inspections WHERE rowid > ? ORDER BY rowid LIMIT 1", out["row"])
        out.pop("advice_json", None)
        out["record"] = json.loads(rec or "{}")
        out["advice"] = None
        if adv is not None:
            a = dict(adv)
            a["advice"] = json.loads(a.pop("json") or "{}")
            a["errors"] = json.loads(a["errors"] or "[]")
            out["advice"] = a
        return out

    def _one(self, sql: str, *p):
        r = self.conn.execute(sql, p).fetchone()
        return r[0] if r else None

    def decide(self, unit_id: str, decision: str, operator: str = "", note: str = "") -> None:
        if decision not in DECISIONS:
            raise ValueError(f"decision must be one of {DECISIONS}")
        with self.lock, self.conn:
            if self._one("SELECT 1 FROM inspections WHERE unit_id = ?", unit_id) is None:
                raise KeyError(unit_id)
            self.conn.execute("INSERT INTO decisions(unit_id, ts, decision, operator, note) VALUES (?,?,?,?,?)",
                              (unit_id, _now(), decision, operator[:60], note[:500]))

    def facets(self) -> dict:
        """Values offered in the log's filter bar."""
        with self.lock:
            col = lambda q: [r[0] for r in self.conn.execute(q)]  # noqa: E731
            return {
                "profiles": col("SELECT DISTINCT profile FROM inspections WHERE profile IS NOT NULL ORDER BY 1"),
                "sessions": col("SELECT session FROM inspections WHERE session IS NOT NULL GROUP BY 1 ORDER BY max(rowid) DESC LIMIT 30"),
                "defects": col("SELECT DISTINCT defect FROM detections ORDER BY 1"),
                "decisions": list(DECISIONS),
            }

    def analytics(self, filters: Optional[dict] = None, buckets: int = 24) -> dict:
        """Numbers for the analytics page, over the units the filters select."""
        where, p = self._where(filters or {})
        src = "FROM inspections i LEFT JOIN advice a ON a.unit_id = i.unit_id LEFT JOIN decisions c ON c.id = " \
              f"(SELECT max(id) FROM decisions x WHERE x.unit_id = i.unit_id){where}"
        with self.lock:
            units = [dict(r) for r in self.conn.execute(
                "SELECT i.unit_id, i.ts, i.result, i.vision_ms, i.e2e_ms, i.gt_outcome, i.gt_result, c.decision, "
                f"a.backend, a.valid, a.fallback, a.repaired, a.total_ms, a.ttft_ms, a.tok_s {src} ORDER BY i.rowid", p)]
            dets = self.conn.execute(
                "SELECT d.defect, d.severity, d.zone, count(*) FROM detections d JOIN (SELECT i.unit_id "
                f"{src}) u ON u.unit_id = d.unit_id GROUP BY 1, 2, 3", p).fetchall()
        defects, zones = {}, Counter()
        for name, sev, zone, n in dets:
            e = defects.setdefault(name, {"low": 0, "medium": 0, "high": 0, "total": 0})
            e[sev or "low"] += n
            e["total"] += n
            zones[zone] += n
        buckets = min(buckets, max(4, len(units) // 6))   # at least about six units per point, so a share means something
        k = max(1, -(-len(units) // buckets))
        trend = []
        for i in range(0, len(units), k):
            part = units[i:i + k]
            trend.append({"from": part[0]["ts"], "to": part[-1]["ts"], "n": len(part),
                          **{r: sum(u["result"] == r for u in part) for r in ("PASS", "PASS_WITH_NOTE", "REVIEW", "FAIL")}})
        # a fallback is stored with the template as its backend, but it was a Llama attempt
        adv = [u for u in units if u["valid"] is not None and (u["backend"] != "template" or u["fallback"])]
        n_template = sum(u["valid"] is not None for u in units) - len(adv)
        mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
        p95 = lambda xs: sorted(xs)[min(len(xs) - 1, int(0.95 * len(xs)))] if xs else None  # noqa: E731
        vis = [u["vision_ms"] for u in units if u["vision_ms"] is not None]
        labelled = [u for u in units if u["gt_outcome"]]
        ok = ("PASS", "PASS_WITH_NOTE")
        return {
            "units": len(units), "results": dict(Counter(u["result"] for u in units)),
            "defects": dict(sorted(defects.items(), key=lambda kv: -kv[1]["total"])), "zones": dict(zones), "trend": trend,
            "latency": {"vision_mean": mean(vis), "vision_p95": p95(vis),
                        "e2e_mean": mean([u["e2e_ms"] for u in units if u["e2e_ms"] is not None])},
            "advice": {"n": len(adv), "template": n_template, "valid": sum(u["valid"] for u in adv), "fallback": sum(u["fallback"] or 0 for u in adv),
                       "repaired": sum(u["repaired"] or 0 for u in adv),
                       "total_mean_ms": mean([u["total_ms"] for u in adv if u["total_ms"]]),
                       "ttft_mean_ms": mean([u["ttft_ms"] for u in adv if u["ttft_ms"]]),
                       "tok_s_mean": mean([u["tok_s"] for u in adv if u["tok_s"]])},
            "labels": {"n": len(labelled), "outcomes": dict(Counter(u["gt_outcome"] for u in labelled)),
                       "defective": sum(u["gt_result"] not in ok for u in labelled),
                       "acceptable": sum(u["gt_result"] in ok for u in labelled)},
            "decisions": dict(Counter(u["decision"] for u in units if u["decision"])),
            "open": sum(u["decision"] is None and u["result"] in ("FAIL", "REVIEW") for u in units),
        }

    def metrics(self, limit: int = 240) -> list[dict]:
        with self.lock:
            rows = [dict(r) for r in self.conn.execute(
                "SELECT * FROM system_metrics ORDER BY rowid DESC LIMIT ?", (limit,))]
        return rows[::-1]

    def stats(self, last_n: int = 200, profile: Optional[str] = None) -> dict:
        with self.lock:
            units = [dict(r) for r in self.conn.execute(
                "SELECT unit_id, result FROM inspections WHERE ? IS NULL OR profile = ? ORDER BY rowid DESC LIMIT ?",
                (profile, profile, last_n))]
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

    def export_csv(self, fh: IO[str], limit: int = 100000, filters: Optional[dict] = None) -> None:
        w = csv.DictWriter(fh, fieldnames=EXPORT_COLS, extrasaction="ignore")
        w.writeheader()
        for row in reversed(self.search(filters, limit)["rows"]):
            # a leading = + - @ would run as a formula when the file is opened in a spreadsheet
            w.writerow({k: "'" + v if isinstance(v, str) and v[:1] in "=+-@" else v for k, v in row.items()})
