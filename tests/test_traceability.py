#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_traceability.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests unitaires du moteur de matrice de traçabilité.

Objectifs :
    - Construction matrice via build_matrix_from_testcases()
    - uncovered_requirements() + orphan_tests()
    - utilitaire matrix_cell()
    - Déterminisme (tri IDs + dédup links)

Usage :
    pytest -q tests/test_traceability.py
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
from vv_app2_tctc.models import LinkSource, Requirement, TestCase, TraceLink
from vv_app2_tctc.traceability import build_matrix_from_testcases, build_traceability_matrix, matrix_cell


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
def test_build_matrix_from_testcases_nominal_uncovered_and_orphan() -> None:
    reqs = [_req("REQ-001"), _req("REQ-002")]
    tcs = [_tc("TC-001", "REQ-001"), _tc("TC-002", "")]

    m = build_matrix_from_testcases(reqs, tcs)

    assert m.requirement_ids == ["REQ-001", "REQ-002"]
    assert m.test_ids == ["TC-001", "TC-002"]

    assert m.req_to_tests["REQ-001"] == {"TC-001"}
    assert m.req_to_tests["REQ-002"] == set()
    assert m.test_to_reqs["TC-001"] == {"REQ-001"}
    assert m.test_to_reqs["TC-002"] == set()

    assert m.uncovered_requirements() == ["REQ-002"]
    assert m.orphan_tests() == ["TC-002"]

    assert matrix_cell(m, "REQ-001", "TC-001") is True
    assert matrix_cell(m, "REQ-001", "TC-002") is False


def test_build_matrix_from_testcases_parsing_dedup_links_in_testcase() -> None:
    reqs = [_req("REQ-001")]
    tcs = [_tc("TC-001", "REQ-001, REQ-001 | REQ-001")]

    m = build_matrix_from_testcases(reqs, tcs)

    assert m.req_to_tests["REQ-001"] == {"TC-001"}
    assert m.test_to_reqs["TC-001"] == {"REQ-001"}
    assert m.uncovered_requirements() == []
    assert m.orphan_tests() == []


def test_build_traceability_matrix_dedups_and_sorts_links_by_key() -> None:
    reqs = [_req("REQ-001"), _req("REQ-002")]
    tcs = [_tc("TC-001", ""), _tc("TC-002", "")]

    links = [
        TraceLink(requirement_id="REQ-002", test_id="TC-002", source=LinkSource.DATASET),
        TraceLink(requirement_id="REQ-002", test_id="TC-002", source=LinkSource.DATASET),
        TraceLink(requirement_id="REQ-001", test_id="TC-001", source=LinkSource.AI),
        TraceLink(requirement_id="REQ-001", test_id="TC-001", source=LinkSource.AI),
        TraceLink(requirement_id="REQ-001", test_id="TC-001", source=LinkSource.HUMAN),
    ]

    m = build_traceability_matrix(reqs, tcs, links=links)

    assert len(m.links) == 3
    assert [(l.requirement_id, l.test_id, l.source.value) for l in m.links] == [
        ("REQ-001", "TC-001", "AI"),
        ("REQ-001", "TC-001", "HUMAN"),
        ("REQ-002", "TC-002", "DATASET"),
    ]

    assert m.req_to_tests["REQ-001"] == {"TC-001"}
    assert m.req_to_tests["REQ-002"] == {"TC-002"}
    assert m.orphan_tests() == []
    assert m.uncovered_requirements() == []
