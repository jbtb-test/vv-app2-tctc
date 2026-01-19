"""
APP2 — TCTC (Traceability & Test Coverage Tool)

Public package exports for stable imports:
- Domain models (Requirement, TestCase, TraceLink, enums)
- Traceability matrix builders
- KPI computation
"""

from __future__ import annotations

from vv_app2_tctc.models import (
    Criticality,
    LinkSource,
    Requirement,
    TestCase,
    TraceLink,
    CoverageKpi,
    build_links_from_testcases,
)
from vv_app2_tctc.traceability import (
    TraceabilityMatrix,
    build_matrix_from_testcases,
    build_traceability_matrix,
    matrix_cell,
)
from vv_app2_tctc.kpi import CoverageKPI, compute_coverage_kpis

__all__ = [
    # models
    "Criticality",
    "LinkSource",
    "Requirement",
    "TestCase",
    "TraceLink",
    "CoverageKpi",
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
