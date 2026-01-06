import json
from pathlib import Path

import pytest

from tools.env_check import collect_env_info, env_info_to_dict, render_markdown, write_json, write_text


def test_collect_env_info_has_expected_fields():
    info = collect_env_info()
    data = env_info_to_dict(info)

    # Champs contractuels
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


def test_render_markdown_contains_sections():
    info = collect_env_info()
    md = render_markdown(info)
    assert "# Environment Healthcheck Report" in md
    assert "## Runtime" in md
    assert "## System" in md
    assert "## Project" in md


def test_write_text_creates_file(tmp_path: Path):
    out = tmp_path / "env_report.md"
    write_text(out, "hello")
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "hello"


def test_write_json_creates_valid_json(tmp_path: Path):
    out = tmp_path / "env_report.json"
    payload = {"a": 1, "b": "x"}
    write_json(out, payload)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == payload
