#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.validators
------------------------------------------------------------
Description :
    Validation de cohérence des datasets APP2 — TCTC.

Rôle :
    - Valider les exigences et cas de test avant toute analyse :
        * IDs non vides
        * unicité des IDs (requirements / tests)
        * liens TestCase → Requirement existants
    - Produire un rapport structuré (erreurs / warnings / stats)
    - Fournir une exception dédiée pour rejeter proprement les datasets invalides

Notes :
    - Les KPI (couverture %) sont calculés dans kpi.py.
    - Ici, on se limite à la cohérence des données et à des indicateurs de base.
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set, Tuple

from vv_app2_tctc.models import Requirement, TestCase, TraceLink, build_links_from_testcases

# ============================================================
# 🔎 Public exports
# ============================================================
__all__ = [
    "DatasetValidationError",
    "ValidationIssue",
    "ValidationReport",
    "validate_datasets",
    "raise_if_invalid",
]


# ============================================================
# ⚠️ Exceptions / Issues
# ============================================================
class DatasetValidationError(Exception):
    """Erreur levée lorsque le dataset est invalide (bloquant)."""


@dataclass(frozen=True)
class ValidationIssue:
    """Une anomalie de validation (erreur ou warning)."""
    code: str
    message: str
    context: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "context": dict(self.context)}


# ============================================================
# 🧾 Rapport de validation (audit-friendly)
# ============================================================
@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    # stats utiles pour pipeline / audit
    requirements_total: int = 0
    tests_total: int = 0
    links_total: int = 0

    requirement_ids: List[str] = field(default_factory=list)
    test_ids: List[str] = field(default_factory=list)

    requirements_uncovered: List[str] = field(default_factory=list)  # req sans aucun test
    tests_orphan: List[str] = field(default_factory=list)  # test sans lien

    unknown_requirement_links: List[Tuple[str, str]] = field(default_factory=list)  # (test_id, req_id)
    duplicate_requirement_ids: List[str] = field(default_factory=list)
    duplicate_test_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "requirements_total": self.requirements_total,
            "tests_total": self.tests_total,
            "links_total": self.links_total,
            "requirement_ids": list(self.requirement_ids),
            "test_ids": list(self.test_ids),
            "requirements_uncovered": list(self.requirements_uncovered),
            "tests_orphan": list(self.tests_orphan),
            "unknown_requirement_links": [list(x) for x in self.unknown_requirement_links],
            "duplicate_requirement_ids": list(self.duplicate_requirement_ids),
            "duplicate_test_ids": list(self.duplicate_test_ids),
        }


# ============================================================
# 🔧 Internals (helpers privés)
# ============================================================
def _find_duplicates(ids: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    dup: Set[str] = set()
    for x in ids:
        if x in seen:
            dup.add(x)
        else:
            seen.add(x)
    return sorted(dup)


def _index_requirements(requirements: Iterable[Requirement]) -> Dict[str, Requirement]:
    index: Dict[str, Requirement] = {}
    for r in requirements:
        index[r.requirement_id] = r
    return index


# ============================================================
# ✅ Validation principale
# ============================================================
def validate_datasets(
    requirements: List[Requirement],
    tests: List[TestCase],
) -> ValidationReport:
    """
    Valide la cohérence des datasets.
    Ne lève pas d'exception : retourne un ValidationReport.

    Erreurs (bloquantes) :
      - doublons d'IDs (REQ/TC)
      - lien vers exigence inexistante

    Warnings (non bloquants) :
      - exigences non couvertes
      - tests orphelins (sans liens)

    Retourne aussi un comptage des liens issus du dataset.
    """
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    req_ids = [r.requirement_id for r in requirements]
    tc_ids = [t.test_id for t in tests]

    dup_reqs = _find_duplicates(req_ids)
    dup_tcs = _find_duplicates(tc_ids)

    if dup_reqs:
        errors.append(
            ValidationIssue(
                code="DUPLICATE_REQUIREMENT_ID",
                message="Duplicate requirement_id detected.",
                context={"ids": ",".join(dup_reqs)},
            )
        )

    if dup_tcs:
        errors.append(
            ValidationIssue(
                code="DUPLICATE_TEST_ID",
                message="Duplicate test_id detected.",
                context={"ids": ",".join(dup_tcs)},
            )
        )

    req_index = _index_requirements(requirements)

    # Liens issus du dataset (via TestCase.linked_requirements)
    links: List[TraceLink] = build_links_from_testcases(tests)
    unknown_links: List[Tuple[str, str]] = []
    for link in links:
        if link.requirement_id not in req_index:
            unknown_links.append((link.test_id, link.requirement_id))

    if unknown_links:
        preview = "; ".join([f"{tc}->{req}" for tc, req in unknown_links[:10]])
        errors.append(
            ValidationIssue(
                code="UNKNOWN_REQUIREMENT_LINK",
                message="One or more tests reference unknown requirement_id(s).",
                context={
                    "count": str(len(unknown_links)),
                    "preview": preview,
                },
            )
        )

    # Warnings : orphelins / non couverts
    orphan_tests = sorted([t.test_id for t in tests if len(t.linked_requirements) == 0])
    if orphan_tests:
        warnings.append(
            ValidationIssue(
                code="ORPHAN_TEST",
                message="One or more test cases have no linked requirements (orphan tests).",
                context={"count": str(len(orphan_tests)), "ids": ",".join(orphan_tests)},
            )
        )

    covered_req_ids: Set[str] = set()
    for t in tests:
        for rid in t.linked_requirements:
            covered_req_ids.add(rid)

    uncovered_reqs = sorted([r.requirement_id for r in requirements if r.requirement_id not in covered_req_ids])
    if uncovered_reqs:
        warnings.append(
            ValidationIssue(
                code="UNCOVERED_REQUIREMENT",
                message="One or more requirements are not covered by any test case.",
                context={"count": str(len(uncovered_reqs)), "ids": ",".join(uncovered_reqs)},
            )
        )

    ok = len(errors) == 0

    return ValidationReport(
        ok=ok,
        errors=errors,
        warnings=warnings,
        requirements_total=len(requirements),
        tests_total=len(tests),
        links_total=len(links),
        requirement_ids=sorted(req_ids),
        test_ids=sorted(tc_ids),
        requirements_uncovered=uncovered_reqs,
        tests_orphan=orphan_tests,
        unknown_requirement_links=unknown_links,
        duplicate_requirement_ids=dup_reqs,
        duplicate_test_ids=dup_tcs,
    )


def raise_if_invalid(report: ValidationReport) -> None:
    """
    Lève DatasetValidationError si report.ok == False.
    Message synthétique, mais exploitable (liste codes).
    """
    if report.ok:
        return
    codes = sorted({e.code for e in report.errors})
    raise DatasetValidationError(f"Dataset validation failed: {', '.join(codes)}")
