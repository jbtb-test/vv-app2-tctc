#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_kpi.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests unitaires (pytest) pour le calcul KPI de couverture.

Objectifs :
    - Comportement nominal (couverture partielle)
    - Cas limite (0 exigences)
    - Cas limite (liens vides)
    - Cas nominal (100% couvert)
    - Cas nominal (tests sans liens -> uncovered + orphans)

Usage :
    pytest -q tests/test_kpi.py
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
import pytest

from vv_app2_tctc import models
from vv_app2_tctc.kpi import compute_coverage_kpis
from vv_app2_tctc.traceability import build_matrix_from_testcases


# ============================================================
# 🔧 Fixtures
# ============================================================
@pytest.fixture
def req_001() -> models.Requirement:
    return models.Requirement.from_dict(
        {"requirement_id": "REQ-001", "title": "t", "description": "d", "criticality": "HIGH"}
    )


@pytest.fixture
def req_002() -> models.Requirement:
    return models.Requirement.from_dict(
        {"requirement_id": "REQ-002", "title": "t", "description": "d", "criticality": "HIGH"}
    )


# ============================================================
# 🧪 Tests
# ============================================================
def test_kpi_nominal_one_covered_one_uncovered(req_001: models.Requirement, req_002: models.Requirement) -> None:
    tcs = [
        models.TestCase.from_dict(
            {"test_id": "TC-001", "title": "t", "description": "d", "linked_requirements_raw": "REQ-001"}
        )
    ]
    matrix = build_matrix_from_testcases([req_001, req_002], tcs)
    kpi = compute_coverage_kpis(matrix)

    assert kpi.total_requirements == 2
    assert kpi.coverage_percent == 50.0
    assert kpi.covered_requirements == ["REQ-001"]
    assert kpi.uncovered_requirements == ["REQ-002"]
    assert kpi.orphan_tests == []


def test_kpi_no_requirements() -> None:
    tcs = [
        models.TestCase.from_dict(
            {"test_id": "TC-001", "title": "t", "description": "d", "linked_requirements_raw": "REQ-001"}
        )
    ]
    matrix = build_matrix_from_testcases([], tcs)
    kpi = compute_coverage_kpis(matrix)

    assert kpi.total_requirements == 0
    assert kpi.coverage_percent == 0.0


def test_kpi_empty_links_handled(req_001: models.Requirement) -> None:
    tcs = [
        models.TestCase.from_dict(
            {"test_id": "TC-001", "title": "t", "description": "d", "linked_requirements_raw": ""}
        )
    ]
    matrix = build_matrix_from_testcases([req_001], tcs)
    kpi = compute_coverage_kpis(matrix)

    assert kpi.covered_requirements == []
    assert kpi.uncovered_requirements == ["REQ-001"]
    assert kpi.coverage_percent == 0.0


def test_kpi_all_covered_no_orphans() -> None:
    reqs = [
        models.Requirement.from_dict(
            {"requirement_id": "REQ-001", "title": "t", "description": "d", "criticality": "HIGH"}
        ),
        models.Requirement.from_dict(
            {"requirement_id": "REQ-002", "title": "t", "description": "d", "criticality": "LOW"}
        ),
    ]
    tcs = [
        models.TestCase.from_dict(
            {"test_id": "TC-001", "title": "t", "description": "d", "linked_requirements_raw": "REQ-001"}
        ),
        models.TestCase.from_dict(
            {"test_id": "TC-002", "title": "t", "description": "d", "linked_requirements_raw": "REQ-002"}
        ),
    ]

    m = build_matrix_from_testcases(reqs, tcs)
    kpi = compute_coverage_kpis(m)

    assert kpi.coverage_percent == 100.0
    assert list(kpi.uncovered_requirements) == []
    assert list(kpi.orphan_tests) == []
    assert kpi.total_links == 2


def test_kpi_tests_present_but_no_links_all_uncovered_all_orphans() -> None:
    reqs = [
        models.Requirement.from_dict(
            {"requirement_id": "REQ-001", "title": "t", "description": "d", "criticality": "HIGH"}
        ),
        models.Requirement.from_dict(
            {"requirement_id": "REQ-002", "title": "t", "description": "d", "criticality": "LOW"}
        ),
    ]
    tcs = [
        models.TestCase.from_dict(
            {"test_id": "TC-001", "title": "t", "description": "d", "linked_requirements_raw": ""}
        ),
        models.TestCase.from_dict(
            {"test_id": "TC-002", "title": "t", "description": "d", "linked_requirements_raw": ""}
        ),
    ]

    m = build_matrix_from_testcases(reqs, tcs)
    kpi = compute_coverage_kpis(m)

    assert kpi.coverage_percent == 0.0
    assert set(kpi.uncovered_requirements) == {"REQ-001", "REQ-002"}
    assert set(kpi.orphan_tests) == {"TC-001", "TC-002"}
    assert kpi.total_links == 0
