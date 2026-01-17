#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_main.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests d'intégration légers pour vv_app2_tctc.main :
    - process() génère le bundle (HTML + CSV) dans tmp_path
    - exécution module -m (CLI-like) génère les fichiers dans tmp_path

Objectifs :
    - Prouver la génération d'artefacts (HTML/CSV) sans IA
    - Vérifier le contrat minimal du payload (clés, types, chemins)
    - Rester stable / reproductible (datasets repo + tmp_path)

Usage :
    pytest -q tests/test_main.py
============================================================
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest


def _repo_root() -> Path:
    # tests/ est au niveau repo_app2
    return Path(__file__).resolve().parents[1]


def _env_no_ai() -> Dict[str, str]:
    env = dict(os.environ)
    env["ENABLE_AI"] = "0"
    # même si OPENAI_API_KEY existe, ENABLE_AI=0 force le fallback
    return env


def test_process_generates_report_bundle_in_tmp_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    process() doit :
      - retourner ok=True
      - retourner un payload dict avec chemins des artefacts
      - générer les fichiers dans tmp_path
    """
    monkeypatch.setenv("ENABLE_AI", "0")

    from vv_app2_tctc.main import process  # import après env patch

    root = _repo_root()
    req_csv = root / "data" / "inputs" / "requirements.csv"
    tc_csv = root / "data" / "inputs" / "tests.csv"
    assert req_csv.exists(), f"Missing requirements dataset: {req_csv}"
    assert tc_csv.exists(), f"Missing tests dataset: {tc_csv}"

    out = process(
        {
            "requirements_path": str(req_csv),
            "tests_path": str(tc_csv),
            "out_dir": str(tmp_path),
            "fail_on_empty": False,
            "verbose": True,
        }
    )

    assert out.ok is True
    assert out.message == "OK"
    assert isinstance(out.payload, dict)

    payload = out.payload

    # --- Payload contract (essentiel) ---
    for k in (
        "requirements_count",
        "tests_count",
        "report_html",
        "traceability_csv",
        "kpi_csv",
        "ai_suggestions_csv",
        "coverage_percent",
        "validation",
    ):
        assert k in payload, f"Missing payload key: {k}"

    # --- Files exist ---
    report_html = Path(payload["report_html"])
    trace_csv = Path(payload["traceability_csv"])
    kpi_csv = Path(payload["kpi_csv"])

    assert report_html.exists(), f"Missing report HTML: {report_html}"
    assert trace_csv.exists(), f"Missing traceability CSV: {trace_csv}"
    assert kpi_csv.exists(), f"Missing KPI CSV: {kpi_csv}"

    # --- No AI ---
    assert payload["ai_suggestions_csv"] in (None, "", "None")
    assert payload.get("ai_suggestions_count", 0) == 0

    # --- Minimal sanity content ---
    html_text = report_html.read_text(encoding="utf-8", errors="replace")
    assert "APP2" in html_text
    assert "TCTC" in html_text
    assert "Traceability" in html_text or "traç" in html_text.lower()


def test_cli_like_module_execution_generates_files(tmp_path: Path) -> None:
    """
    CLI-like : python -m vv_app2_tctc.main --out-dir <tmp> --verbose
    Vérifie returncode=0 + artefacts générés.
    """
    root = _repo_root()
    cmd = [
        sys.executable,
        "-m",
        "vv_app2_tctc.main",
        "--out-dir",
        str(tmp_path),
        "--verbose",
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        env=_env_no_ai(),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Artefacts attendus (conforme aux logs et au bundle)
    assert (tmp_path / "tctc_report.html").exists()
    assert (tmp_path / "traceability_matrix.csv").exists()
    assert (tmp_path / "kpi_summary.csv").exists()
