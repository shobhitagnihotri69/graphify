"""Tests for PYTHONHASHSEED pinning (#3641)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from graphify.__main__ import _pin_pythonhashseed


def test_pin_pythonhashseed_no_op_for_other_subcommands(monkeypatch):
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)
    _pin_pythonhashseed("help")
    assert "PYTHONHASHSEED" not in os.environ

    _pin_pythonhashseed("version")
    assert "PYTHONHASHSEED" not in os.environ

    _pin_pythonhashseed("query")
    assert "PYTHONHASHSEED" not in os.environ


def test_pin_pythonhashseed_preserves_existing_env(monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "42")
    _pin_pythonhashseed("update")
    assert os.environ.get("PYTHONHASHSEED") == "42"

    _pin_pythonhashseed("extract")
    assert os.environ.get("PYTHONHASHSEED") == "42"

    _pin_pythonhashseed("cluster-only")
    assert os.environ.get("PYTHONHASHSEED") == "42"


def test_pin_pythonhashseed_sets_zero_for_target_subcommands(monkeypatch):
    for subcmd in ("update", "extract", "cluster-only", "label"):
        monkeypatch.delenv("PYTHONHASHSEED", raising=False)
        _pin_pythonhashseed(subcmd)
        assert os.environ.get("PYTHONHASHSEED") == "0"


def test_out_of_process_update_inherits_seed(tmp_path):
    """Running graphify update out-of-process without PYTHONHASHSEED sets it."""
    code = (
        "import os, sys\n"
        "from graphify.__main__ import _pin_pythonhashseed\n"
        "_pin_pythonhashseed(sys.argv[1])\n"
        "print(os.environ.get('PYTHONHASHSEED'))\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}
    for cmd in ("update", "extract", "cluster-only", "label"):
        proc = subprocess.run(
            [sys.executable, "-c", code, cmd],
            capture_output=True,
            text=True,
            env=env,
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == "0"
