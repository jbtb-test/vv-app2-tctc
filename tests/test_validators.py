#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_validators.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests unitaires pour vv_app2_tctc.validators :
    - validate_datasets() : erreurs bloquantes + warnings
    - raise_if_invalid()  : exception DatasetValidationError

Objectifs :
    - Vérifier cohérence des datasets (unicité IDs, liens existants)
    - Vérifier indicateurs non bloquants (orphelins / non couverts)
    - Vérifier rapport audit-friendly (to_dict + stats)

Usage :
    pytest -q tests/test_validators.py
============================================================
"""

from __future__ import annotations

import pytest

from vv_app2_tctc.models import Requirement, TestCase
from vv_app2_tctc.validators import (
    DatasetValidationError,
    validate_datasets,
    raise_if_invalid,
)


# ============================================================
# 🔧 Helpers
# ============================================================
def _req(req_id: str) -> Requirement:
    return Requirement.from_dict(
        {"requirement_id": req_id, "title": "t", "description": "d", "criticality": "HIGH"}
    )


def _tc(tc_id: str, links_raw: str) -> TestCase:
    return TestCase.from_dict(
        {"test_id": tc_id, "title": "t", "description": "d", "linked_requirements_raw": links_raw}
    )


# ============================================================
# 🧪 Tests
# ============================================================
def test_validate_datasets_nominal_with_warnings_orphan_and_uncovered() -> None:
    # REQ-002 uncovered (no test linked), TC-002 orphan (no links)
    reqs = [_req("REQ-001"), _req("REQ-002")]
    tcs = [_tc("TC-001", "REQ-001"), _tc("TC-002", "")]

    report = validate_datasets(reqs, tcs)

    # No blocking errors expected
    assert report.ok is True
    assert report.errors == []

    # Warnings expected
    warn_codes = {w.code for w in report.warnings}
    assert "ORPHAN_TEST" in warn_codes
    assert "UNCOVERED_REQUIREMENT" in warn_codes

    assert report.tests_orphan == ["TC-002"]
    assert report.requirements_uncovered == ["REQ-002"]

    # Stats
    assert report.requirements_total == 2
    assert report.tests_total == 2
    assert report.links_total == 1  # only TC-001 -> REQ-001

    # Audit-friendly dict
    d = report.to_dict()
    assert d["ok"] is True
    assert d["requirements_total"] == 2
    assert d["tests_total"] == 2
    assert isinstance(d["warnings"], list)


def test_validate_datasets_duplicate_requirement_ids_is_blocking_error() -> None:
    reqs = [_req("REQ-001"), _req("REQ-001")]  # duplicate
    tcs = [_tc("TC-001", "REQ-001")]

    report = validate_datasets(reqs, tcs)

    assert report.ok is False
    err_codes = {e.code for e in report.errors}
    assert "DUPLICATE_REQUIREMENT_ID" in err_codes
    assert report.duplicate_requirement_ids == ["REQ-001"]

    with pytest.raises(DatasetValidationError):
        raise_if_invalid(report)


def test_validate_datasets_duplicate_test_ids_is_blocking_error() -> None:
    reqs = [_req("REQ-001")]
    tcs = [_tc("TC-001", "REQ-001"), _tc("TC-001", "REQ-001")]  # duplicate

    report = validate_datasets(reqs, tcs)

    assert report.ok is False
    err_codes = {e.code for e in report.errors}
    assert "DUPLICATE_TEST_ID" in err_codes
    assert report.duplicate_test_ids == ["TC-001"]

    with pytest.raises(DatasetValidationError):
        raise_if_invalid(report)


def test_validate_datasets_unknown_requirement_link_is_blocking_error() -> None:
    reqs = [_req("REQ-001")]
    tcs = [_tc("TC-001", "REQ-999")]  # unknown req link

    report = validate_datasets(reqs, tcs)

    assert report.ok is False
    err_codes = {e.code for e in report.errors}
    assert "UNKNOWN_REQUIREMENT_LINK" in err_codes

    # unknown_requirement_links contains (test_id, req_id)
    assert ("TC-001", "REQ-999") in report.unknown_requirement_links

    with pytest.raises(DatasetValidationError):
        raise_if_invalid(report)


def test_raise_if_invalid_ok_does_nothing() -> None:
    reqs = [_req("REQ-001")]
    tcs = [_tc("TC-001", "REQ-001")]

    report = validate_datasets(reqs, tcs)
    assert report.ok is True

    # Must not raise
    raise_if_invalid(report)
