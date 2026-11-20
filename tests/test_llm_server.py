"""Persistent ExecuTorch server client, exercised against a protocol-compatible fake (no model needed)."""
import stat
import sys
from pathlib import Path

import pytest

from qc.advisory import Advisor
from qc.advisory.llm import ExecuTorchLLM, LLMServerClient
from qc.config import load_config

FAKE = Path(__file__).with_name("fake_llm_server.py")


@pytest.fixture
def client(tmp_path):
    c = LLMServerClient([sys.executable, str(FAKE)], tmp_path / "srv.log", start_timeout=10, call_timeout=2)
    yield c
    c.close()


def test_start_generate_stats(client):
    client.start()
    assert client.info["load_ms"] == 12 and client.pid
    text, stats = client.generate("<|begin_of_text|>DEFECT=short", 200, 0.2)
    assert '"short' in text and "ünïcode" in text
    assert stats["generated_tokens"] == 41
    # second call reuses the same process (model stays loaded)
    pid = client.pid
    client.generate("DEFECT=open", 200, 0.2)
    assert client.pid == pid
    assert "noise on stderr" in (client.log_path.read_text())


def test_timeout_then_restart(client):
    client.start()
    with pytest.raises(TimeoutError):
        client.generate("HANG", 10, 0.2)
    assert client.pid is None
    text, _ = client.generate("DEFECT=spur", 10, 0.2)  # restarts lazily
    assert "spur" in text


def test_crash_is_reported(client):
    client.start()
    with pytest.raises(RuntimeError):
        client.generate("CRASH", 10, 0.2)
    assert "open" in client.generate("DEFECT=open", 10, 0.2)[0]


def _executorch_cfg(tmp_path):
    srv = tmp_path / "server.sh"
    srv.write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE} \"$@\"\n")
    srv.chmod(srv.stat().st_mode | stat.S_IEXEC)
    (tmp_path / "m.pte").write_bytes(b"x")
    (tmp_path / "tok.model").write_bytes(b"x")
    return load_config(overrides=[
        "advisory.backend=executorch", f"advisory.executorch.server={srv}", f"advisory.executorch.model={tmp_path / 'm.pte'}",
        f"advisory.executorch.tokenizer={tmp_path / 'tok.model'}", f"advisory.executorch.server_log={tmp_path / 's.log'}",
        "advisory.executorch.timeout_s=3",
    ])


def test_executorch_llm_stats(tmp_path):
    llm = ExecuTorchLLM(_executorch_cfg(tmp_path))
    try:
        assert llm.start()["load_ms"] == 12
        out = llm.complete("DEFECT=open")
        assert out.text.endswith("}")  # <|eot_id|> stripped
        assert out.stats["ttft_ms"] == 400 and out.stats["total_ms"] == 2400 and out.stats["load_ms"] is None
        assert out.stats["tok_s"] == pytest.approx(40 / 2.0)
    finally:
        llm.close()
    assert llm.pid is None


def test_advisor_validates_server_output(tmp_path, record):
    # the fake answers about "open", which is in the sample record -> valid, not a fallback
    advisor = Advisor(_executorch_cfg(tmp_path))
    try:
        res = advisor.advise(record)
    finally:
        advisor.close()
    assert res.backend == "executorch" and res.valid and not res.fallback, res.errors
    assert res.ttft_ms == 400
