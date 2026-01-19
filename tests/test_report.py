#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_report.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests unitaires de génération de rapport (CSV + HTML).

Objectifs :
    - Vérifier génération des fichiers attendus dans tmp_path
    - Vérifier en-têtes CSV + contenu minimal
    - Vérifier comportement AI (csv optionnel + badge)

Usage :
    pytest -q tests/test_report.py
============================================================
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict

import pytest

from vv_app2_tctc.models import Requirement, TestCase
from vv_app2_tctc.kpi import compute_coverage_kpis
from vv_app2_tctc.report import generate_report_bundle
from vv_app2_tctc.traceability import build_matrix_from_testcases


# ============================================================
# 🔧 Fixtures / Helpers
# ============================================================

@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _req(req_id: str, title: str = "t") -> Requirement:
    return Requirement.from_dict(
        {"requirement_id": req_id, "title": title, "description": "d", "criticality": "HIGH"}
    )


def _tc(tc_id: str, title: str, links_raw: str) -> TestCase:
    return TestCase.from_dict(
        {"test_id": tc_id, "title": title, "description": "d", "linked_requirements_raw": links_raw}
    )


def _read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        return next(r)


# ============================================================
# 🧪 Tests
# ============================================================

def test_generate_report_bundle_no_ai_writes_html_and_csv(tmp_path: Path, repo_root: Path) -> None:
    # Dataset minimal (1 covered, 1 uncovered + 1 orphan) pour alimenter toutes sections
    reqs = [_req("REQ-001", "Req 1"), _req("REQ-002", "Req 2")]
    tcs = [_tc("TC-001", "TC 1", "REQ-001"), _tc("TC-002", "TC 2", "")]

    matrix = build_matrix_from_testcases(reqs, tcs)
    kpi = compute_coverage_kpis(matrix)

    paths = generate_report_bundle(
        reqs,
        tcs,
        matrix,
        kpi,
        ai_suggestions=None,
        out_dir=tmp_path,
        templates_dir=repo_root / "templates" / "tctc",
        template_name="tctc_report.html",
    )

    # --- Files exist ---
    assert paths.report_html.exists()
    assert paths.traceability_csv.exists()
    assert paths.kpi_csv.exists()
    assert paths.ai_suggestions_csv is None

    # --- CSV headers ---
    assert _read_csv_header(paths.traceability_csv) == ["requirement_id", "covered", "linked_test_ids"]
    assert _read_csv_header(paths.kpi_csv) == ["metric", "value"]

    # --- HTML minimal content ---
    html = paths.report_html.read_text(encoding="utf-8", errors="replace")
    assert "APP2" in html
    assert "TCTC" in html
    assert "DETERMINISTIC" in html  # badge

    # 2.12.D lists should be rendered (IDs at least present somewhere)
    assert "REQ-001" in html
    assert "TC-001" in html


def test_generate_report_bundle_with_ai_writes_ai_csv_and_badge(tmp_path: Path, repo_root: Path) -> None:
    reqs = [_req("REQ-001", "Req 1")]
    tcs = [_tc("TC-001", "TC 1", "")]

    matrix = build_matrix_from_testcases(reqs, tcs)
    kpi = compute_coverage_kpis(matrix)

    # AI suggestions structure expected by report.py: LinkSuggestion-like object
    # We use a minimal duck-typed object with required attrs.
    class _S:
        def __init__(self, requirement_id: str, test_id: str, confidence: float | None, rationale: str) -> None:
            self.requirement_id = requirement_id
            self.test_id = test_id
            self.confidence = confidence
            self.rationale = rationale

    suggestions = [_S("REQ-001", "TC-001", 0.9, "suggestion")]

    paths = generate_report_bundle(
        reqs,
        tcs,
        matrix,
        kpi,
        ai_suggestions=suggestions,
        out_dir=tmp_path,
        templates_dir=repo_root / "templates" / "tctc",
        template_name="tctc_report.html",
    )

    assert paths.report_html.exists()
    assert paths.traceability_csv.exists()
    assert paths.kpi_csv.exists()

    # AI csv now present
    assert paths.ai_suggestions_csv is not None
    assert paths.ai_suggestions_csv.exists()
    assert _read_csv_header(paths.ai_suggestions_csv) == ["requirement_id", "test_id", "confidence", "rationale"]

    html = paths.report_html.read_text(encoding="utf-8", errors="replace")
    assert "AI ENABLED" in html
    assert "REQ-001" in html
    assert "TC-001" in html


def test_generate_report_bundle_bad_templates_dir_falls_back_to_html(tmp_path: Path, caplog) -> None:
    reqs = [_req("REQ-001")]
    tcs = [_tc("TC-001", "TC 1", "REQ-001")]
    matrix = build_matrix_from_testcases(reqs, tcs)
    kpi = compute_coverage_kpis(matrix)

    bad_tpl_dir = tmp_path / "does_not_exist"

    with caplog.at_level("WARNING"):
        paths = generate_report_bundle(
            reqs,
            tcs,
            matrix,
            kpi,
            out_dir=tmp_path,
            templates_dir=bad_tpl_dir,
            template_name="tctc_report.html",
        )

    # CSV must exist
    assert paths.traceability_csv.exists()
    assert paths.kpi_csv.exists()

    # HTML must exist (fallback)
    assert paths.report_html.exists()
    html = paths.report_html.read_text(encoding="utf-8", errors="replace")
    assert "fallback" in html.lower()

    # Warning must be explicit
    assert any("templates_dir not found" in r.message for r in caplog.records)

