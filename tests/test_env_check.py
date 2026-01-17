#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_env_check.py — Tools
------------------------------------------------------------
Description :
    Tests unitaires du healthcheck environnement (tools/env_check.py).

Objectifs :
    - Vérifier présence des champs contractuels
    - Vérifier rendu markdown (sections)
    - Vérifier IO (write_text / write_json)

Usage :
    pytest -q tests/test_env_check.py
============================================================
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.env_check import collect_env_info, env_info_to_dict, render_markdown, write_json, write_text


# ============================================================
# 🧪 Tests
# ============================================================

def test_collect_env_info_has_expected_fields() -> None:
    info = collect_env_info()
    data = env_info_to_dict(info)

    expected_keys = {
        "timestamp_utc",
        "cwd",
        "project_root",
        "python_version",
        "python_executable",
        "pip_version",
        "is_venv",
        "venv_prefix",
        "os_name",
        "os_release",
        "platform",
    }
    assert expected_keys.issubset(set(data.keys()))
    assert isinstance(data["python_version"], str)
    assert isinstance(data["is_venv"], bool)


def test_render_markdown_contains_sections() -> None:
    info = collect_env_info()
    md = render_markdown(info)
    assert "# Environment Healthcheck Report" in md
    assert "## Runtime" in md
    assert "## System" in md
    assert "## Project" in md


def test_write_text_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "env_report.md"
    write_text(out, "hello")
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "hello"


def test_write_json_creates_valid_json(tmp_path: Path) -> None:
    out = tmp_path / "env_report.json"
    payload = {"a": 1, "b": "x"}
    write_json(out, payload)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == payload
