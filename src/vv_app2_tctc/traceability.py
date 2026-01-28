#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.traceability
------------------------------------------------------------
Description :
    Construction de la matrice de traçabilité Requirement ↔ TestCase (APP2 TCTC).

Rôle :
    - Construire des structures déterministes et auditables :
        * mapping Requirement -> set(TestCase)
        * mapping TestCase -> set(Requirement)
        * liste normalisée des TraceLink (source DATASET/AI/HUMAN)
    - Fournir une vue "matrice" exploitable (exports CSV / HTML).

Notes :
    - La validation de cohérence (IDs uniques, liens existants) est gérée dans validators.py.
    - Ici, on suppose des datasets déjà validés si l'appelant veut du "strict".
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

from vv_app2_tctc.models import (
    Requirement,
    TestCase,
    TraceLink,
    LinkSource,
    build_links_from_testcases,
)

# ============================================================
# 🔎 Public exports
# ============================================================
__all__ = [
    "TraceabilityMatrix",
    "build_traceability_matrix",
    "build_matrix_from_testcases",
    "matrix_cell",
]


# ============================================================
# 🧩 Modèle de matrice
# ============================================================
@dataclass(frozen=True)
class TraceabilityMatrix:
    """
    Matrice de traçabilité déterministe.

    Contenu :
      - requirements_by_id / tests_by_id : index stables
      - req_to_tests : mapping req_id -> set(test_id)
      - test_to_reqs : mapping test_id -> set(req_id)
      - links : liste de TraceLink normalisée (triée)
      - requirement_ids / test_ids : ordres déterministes (tri alpha)
    """
    requirements_by_id: Dict[str, Requirement]
    tests_by_id: Dict[str, TestCase]

    req_to_tests: Dict[str, Set[str]] = field(default_factory=dict)
    test_to_reqs: Dict[str, Set[str]] = field(default_factory=dict)

    links: List[TraceLink] = field(default_factory=list)

    requirement_ids: List[str] = field(default_factory=list)
    test_ids: List[str] = field(default_factory=list)

    # ----------------------------
    # Vues dérivées (deterministic)
    # ----------------------------
    def covered_requirements(self) -> Set[str]:
        """Ensemble des exigences couvertes (au moins 1 test)."""
        return {rid for rid, tcs in self.req_to_tests.items() if tcs}

    def uncovered_requirements(self) -> List[str]:
        """Liste triée des exigences non couvertes."""
        covered = self.covered_requirements()
        return [rid for rid in self.requirement_ids if rid not in covered]

    def orphan_tests(self) -> List[str]:
        """Liste triée des tests orphelins (aucune exigence liée)."""
        return [tid for tid in self.test_ids if not self.test_to_reqs.get(tid)]


# ============================================================
# 🔧 Internals (helpers privés)
# ============================================================
def _index_requirements(requirements: Iterable[Requirement]) -> Dict[str, Requirement]:
    return {r.requirement_id: r for r in requirements}


def _index_tests(tests: Iterable[TestCase]) -> Dict[str, TestCase]:
    return {t.test_id: t for t in tests}


def _dedup_links(links: Iterable[TraceLink]) -> List[TraceLink]:
    """
    Déduplication déterministe :
      - clé = (requirement_id, test_id, source)
      - on conserve le premier (ordre d'entrée)
      - tri final stable pour audit / tests
    """
    seen: Set[Tuple[str, str, str]] = set()
    out: List[TraceLink] = []

    for l in links:
        key = (l.requirement_id, l.test_id, l.source.value)
        if key in seen:
            continue
        seen.add(key)
        out.append(l)

    out.sort(key=lambda x: (x.requirement_id, x.test_id, x.source.value))
    return out


# ============================================================
# ✅ API principale
# ============================================================
def build_traceability_matrix(
    requirements: List[Requirement],
    tests: List[TestCase],
    links: Optional[List[TraceLink]] = None,
) -> TraceabilityMatrix:
    """
    Construit la matrice Req ↔ Test.

    Hypothèse :
        - la cohérence est validée en amont (validators.py)
        - les liens invalides doivent être bloqués avant cet appel
    """
    req_index = _index_requirements(requirements)
    test_index = _index_tests(tests)

    requirement_ids = sorted(req_index.keys())
    test_ids = sorted(test_index.keys())

    if links is None:
        links = build_links_from_testcases(tests)

    norm_links = _dedup_links(links)

    req_to_tests: Dict[str, Set[str]] = {rid: set() for rid in requirement_ids}
    test_to_reqs: Dict[str, Set[str]] = {tid: set() for tid in test_ids}

    for l in norm_links:
        if l.requirement_id in req_to_tests and l.test_id in test_to_reqs:
            req_to_tests[l.requirement_id].add(l.test_id)
            test_to_reqs[l.test_id].add(l.requirement_id)

    return TraceabilityMatrix(
        requirements_by_id=req_index,
        tests_by_id=test_index,
        req_to_tests=req_to_tests,
        test_to_reqs=test_to_reqs,
        links=norm_links,
        requirement_ids=requirement_ids,
        test_ids=test_ids,
    )


def build_matrix_from_testcases(
    requirements: List[Requirement],
    tests: List[TestCase],
) -> TraceabilityMatrix:
    """
    Raccourci : construit la matrice uniquement depuis les liens DATASET
    présents dans TestCase.linked_requirements.
    """
    return build_traceability_matrix(requirements=requirements, tests=tests, links=None)


# ============================================================
# 🧱 Utilitaire cellule (export / report)
# ============================================================
def matrix_cell(matrix: TraceabilityMatrix, requirement_id: str, test_id: str) -> bool:
    """Retourne True si (requirement_id ↔ test_id) est lié dans la matrice."""
    return test_id in matrix.req_to_tests.get(requirement_id, set())
