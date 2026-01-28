#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
APP2 — TCTC (Traceability & Test Coverage Tool)
------------------------------------------------------------
Public package exports for stable imports.

This module defines the official public API of APP2:
- Domain models (Requirement, TestCase, TraceLink, enums)
- Traceability matrix builders
- Coverage KPI computation

Design principles:
- Stable, explicit exports (portfolio-grade)
- Clear separation between internal helpers and public API
- KPI acronyms kept in uppercase for consistency (KPI)
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports — domain models
# ============================================================
from vv_app2_tctc.models import (
    Criticality,
    LinkSource,
    Requirement,
    TestCase,
    TraceLink,
    build_links_from_testcases,
)

# ============================================================
# 🔗 Imports — traceability
# ============================================================
from vv_app2_tctc.traceability import (
    TraceabilityMatrix,
    build_matrix_from_testcases,
    build_traceability_matrix,
    matrix_cell,
)

# ============================================================
# 📊 Imports — KPI
# ============================================================
from vv_app2_tctc.kpi import CoverageKPI, compute_coverage_kpis

# ============================================================
# 🔎 Public API
# ============================================================
__all__ = [
    # models
    "Criticality",
    "LinkSource",
    "Requirement",
    "TestCase",
    "TraceLink",
    "build_links_from_testcases",
    # traceability
    "TraceabilityMatrix",
    "build_traceability_matrix",
    "build_matrix_from_testcases",
    "matrix_cell",
    # kpi
    "CoverageKPI",
    "compute_coverage_kpis",
]
