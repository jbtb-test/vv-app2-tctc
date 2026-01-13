#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
test_ia_assistant.py — APP2 TCTC
------------------------------------------------------------
Description :
    Tests unitaires pour l'assistant IA (suggestion-only).
    On teste principalement le fallback déterministe (R1).

Usage :
    pytest -q
============================================================
"""

from __future__ import annotations

import os
from typing import List

import pytest

from vv_app2_tctc import models
from vv_app2_tctc.ia_assistant import suggest_missing_links
from vv_app2_tctc.traceability import build_matrix_from_testcases


def _mk_req(req_id: str) -> models.Requirement:
    return models.Requirement.from_dict(
        {"requirement_id": req_id, "title": "t", "description": "d", "criticality": "HIGH"}
    )


def _mk_tc(tc_id: str, links_raw: str) -> models.TestCase:
    return models.TestCase.from_dict(
        {"test_id": tc_id, "title": "t", "description": "d", "linked_requirements_raw": links_raw}
    )


def test_ai_disabled_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_AI", "0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    reqs = [_mk_req("REQ-001")]
    tcs = [_mk_tc("TC-001", "REQ-001")]
    matrix = build_matrix_from_testcases(reqs, tcs)

    out = suggest_missing_links(reqs, tcs, matrix)
    assert out == []


def test_ai_requested_but_missing_key_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_AI", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # uncovered req => devrait tenter IA, mais clé absente => fallback []
    reqs = [_mk_req("REQ-001")]
    tcs = [_mk_tc("TC-001", "")]
    matrix = build_matrix_from_testcases(reqs, tcs)

    out = suggest_missing_links(reqs, tcs, matrix)
    assert out == []


def test_ai_enabled_but_openai_missing_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_AI", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    # On simule l'absence de openai-python via import failure
    # -> on force sys.modules clean en supprimant 'openai' si présent
    import sys
    sys.modules.pop("openai", None)

    reqs = [_mk_req("REQ-001")]
    tcs = [_mk_tc("TC-001", "")]
    matrix = build_matrix_from_testcases(reqs, tcs)

    out = suggest_missing_links(reqs, tcs, matrix)
    assert out == []
