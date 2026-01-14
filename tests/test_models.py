"""
============================================================
tests.test_models
------------------------------------------------------------
Description :
    Tests unitaires des modèles de domaine APP2 — TCTC.

Objectifs :
    - Cas nominaux (from_dict / to_dict / parsing)
    - Cas d'erreurs (validation stricte, champs requis)
    - Robustesse parsing des liens (multi-séparateurs, dedup, trim)

Usage :
    pytest -q
============================================================
"""

import pytest

from vv_app2_tctc.models import (
    CoverageKpi,
    Criticality,
    LinkSource,
    Requirement,
    TestCase,
    TraceLink,
    parse_requirement_ids,
)


# ============================================================
# 🧪 Helpers
# ============================================================

def test_parse_requirement_ids_nominal_and_dedup_ordered():
    raw = " REQ-001 | REQ-002 ; REQ-002,REQ-003  ,, "
    out = parse_requirement_ids(raw)
    assert out == ["REQ-001", "REQ-002", "REQ-003"]


def test_parse_requirement_ids_empty():
    assert parse_requirement_ids("") == []
    assert parse_requirement_ids(None) == []


# ============================================================
# 🧪 Requirement
# ============================================================

def test_requirement_from_dict_nominal_and_aliases():
    d = {
        "req_id": "REQ-001",
        "title": "Title",
        "text": "Desc via alias",
        "criticality": "HIGH",
        "source": "demo",
    }
    r = Requirement.from_dict(d)

    assert r.requirement_id == "REQ-001"
    assert r.title == "Title"
    assert r.description == "Desc via alias"
    assert r.criticality == Criticality.HIGH
    assert r.source == "demo"

    # to_dict stability
    dd = r.to_dict()
    assert dd["requirement_id"] == "REQ-001"
    assert dd["criticality"] == "HIGH"


def test_requirement_validation_missing_id():
    with pytest.raises(ValueError):
        Requirement.from_dict({"title": "t", "description": "d"})


def test_requirement_validation_missing_title_and_description():
    with pytest.raises(ValueError):
        Requirement.from_dict({"requirement_id": "REQ-001", "title": "", "description": ""})


def test_requirement_invalid_criticality():
    with pytest.raises(ValueError):
        Requirement.from_dict({"requirement_id": "REQ-001", "title": "t", "description": "d", "criticality": "NOPE"})


# ============================================================
# 🧪 TestCase
# ============================================================

def test_testcase_from_dict_parses_raw_links():
    d = {
        "test_id": "TC-001",
        "title": "t",
        "description": "d",
        "linked_requirements_raw": "REQ-001, REQ-002|REQ-002",
    }
    tc = TestCase.from_dict(d)
    assert tc.test_id == "TC-001"
    assert tc.linked_requirements_raw == "REQ-001, REQ-002|REQ-002"
    assert tc.linked_requirements == ["REQ-001", "REQ-002"]


def test_testcase_from_dict_links_as_list():
    d = {
        "test_id": "TC-002",
        "title": "t",
        "description": "d",
        "linked_requirements": ["REQ-001", " ", None, "REQ-002"],
    }
    tc = TestCase.from_dict(d)
    assert tc.linked_requirements == ["REQ-001", "REQ-002"]


def test_testcase_validation_missing_id():
    with pytest.raises(ValueError):
        TestCase.from_dict({"title": "t", "description": "d"})


def test_testcase_validation_missing_title_and_description():
    with pytest.raises(ValueError):
        TestCase.from_dict({"test_id": "TC-001", "title": "", "description": ""})


def test_testcase_from_dict_expects_dict():
    with pytest.raises(ValueError):
        TestCase.from_dict("not-a-dict")  # type: ignore[arg-type]


# ============================================================
# 🧪 TraceLink
# ============================================================

def test_tracelink_from_dict_nominal_and_source_enum():
    d = {
        "requirement_id": "REQ-001",
        "test_id": "TC-001",
        "source": "AI",
        "confidence": 0.8,
        "rationale": "suggestion",
    }
    link = TraceLink.from_dict(d)
    assert link.source == LinkSource.AI
    assert link.confidence == 0.8

    dd = link.to_dict()
    assert dd["source"] == "AI"


def test_tracelink_validation_confidence_range():
    with pytest.raises(ValueError):
        TraceLink.from_dict({"requirement_id": "REQ-001", "test_id": "TC-001", "confidence": 1.5})


def test_tracelink_validation_missing_ids():
    with pytest.raises(ValueError):
        TraceLink.from_dict({"test_id": "TC-001"})
    with pytest.raises(ValueError):
        TraceLink.from_dict({"requirement_id": "REQ-001"})


# ============================================================
# 🧪 CoverageKpi
# ============================================================

def test_coveragekpi_nominal():
    k = CoverageKpi(
        requirements_total=10,
        requirements_covered=7,
        requirements_uncovered=3,
        tests_total=5,
        tests_orphan=1,
        coverage_percent=70.0,
    )
    d = k.to_dict()
    assert d["coverage_percent"] == 70.0


def test_coveragekpi_invalid_percent():
    with pytest.raises(ValueError):
        CoverageKpi(
            requirements_total=1,
            requirements_covered=1,
            requirements_uncovered=0,
            tests_total=1,
            tests_orphan=0,
            coverage_percent=120.0,
        )


def test_coveragekpi_invalid_negative_int():
    with pytest.raises(ValueError):
        CoverageKpi(
            requirements_total=-1,
            requirements_covered=0,
            requirements_uncovered=0,
            tests_total=0,
            tests_orphan=0,
            coverage_percent=0.0,
        )
