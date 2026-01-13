#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
kpi.py — APP2 TCTC
------------------------------------------------------------
Description :
    Calcul des KPI de couverture (Requirements ↔ TestCases) à partir
    d'une TraceabilityMatrix.

Rôle :
    - Produire des métriques exactes et déterministes :
        * coverage % (exigences couvertes / total)
        * liste exigences couvertes / non couvertes
        * tests orphelins (non liés à une exigence)
        * métriques dérivées (comptages, densité moyenne de liens, etc.)

Architecture :
    - Entrée : TraceabilityMatrix (construite par traceability.build_matrix_from_testcases)
    - Sortie : CoverageKPI (dataclass) + fonctions utilitaires

Usage (exemples) :
    from vv_app2_tctc.kpi import compute_coverage_kpis
    kpis = compute_coverage_kpis(matrix)
    print(kpis.coverage_percent)

Tests :
    pytest -q

Notes :
    - Déterministe (aucune IA ici).
    - Robuste aux cas limites (0 exigences, liens vides, etc.).
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

# Import "soft" : on ne dépend que de l'interface runtime de TraceabilityMatrix
# (pas besoin d'importer Requirement/TestCase ici)


# ============================================================
# 🧾 Logging (local, autonome)
# ============================================================
def get_logger(name: str) -> logging.Logger:
    """
    Crée un logger simple et stable (stdout), sans dépendance externe.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


log = get_logger(__name__)


# ============================================================
# ⚠️ Exceptions spécifiques au module
# ============================================================
class KPIError(Exception):
    """Erreur spécifique KPI (validation d'entrée, incohérences, etc.)."""


# ============================================================
# 🧩 Modèles de données
# ============================================================
@dataclass(frozen=True)
class CoverageKPI:
    """
    KPI de couverture Requirements ↔ Tests.

    Attributs principaux :
        - coverage_percent : % d'exigences couvertes (0..100)
        - covered_requirements / uncovered_requirements : listes d'IDs
        - orphan_tests : liste d'IDs de tests non liés à une exigence

    Attributs dérivés :
        - total_requirements / total_tests
        - total_links : somme des liens req->tests
        - avg_tests_per_requirement : densité moyenne (si total_requirements>0)
    """
    total_requirements: int
    total_tests: int

    covered_requirements: List[str]
    uncovered_requirements: List[str]
    orphan_tests: List[str]

    coverage_percent: float

    total_links: int
    avg_tests_per_requirement: float

    # Extra (utile pour report / debug)
    req_to_tests_count: Dict[str, int]


# ============================================================
# 🔧 Helpers
# ============================================================
def _safe_sorted(values: Sequence[str]) -> List[str]:
    """
    Tri stable des IDs (déterministe).
    """
    return sorted(set(values))


def _round_pct(value: float) -> float:
    """
    Arrondi stable pour affichage KPI (2 décimales).
    """
    return round(value, 2)


# ============================================================
# 🔧 Fonction principale
# ============================================================
def compute_coverage_kpis(matrix: Any) -> CoverageKPI:
    """
    Calcule les KPI de couverture à partir d'une TraceabilityMatrix.

    Args:
        matrix: objet TraceabilityMatrix (duck-typing accepté).
            Doit exposer au minimum :
                - req_to_tests: dict[str, set[str]]
                - uncovered_requirements(): list[str] (ou équivalent)
                - orphan_tests(): list[str] (ou équivalent)

    Returns:
        CoverageKPI: structure KPI complète et déterministe.

    Raises:
        KPIError: si l'entrée ne respecte pas le contrat minimal.
    """
    if matrix is None:
        raise KPIError("Invalid input: 'matrix' is None.")

    if not hasattr(matrix, "req_to_tests"):
        raise KPIError("Invalid input: 'matrix' must expose attribute 'req_to_tests'.")

    req_to_tests = getattr(matrix, "req_to_tests")
    if not isinstance(req_to_tests, dict):
        raise KPIError("Invalid input: 'matrix.req_to_tests' must be a dict.")

    req_ids = _safe_sorted([str(k) for k in req_to_tests.keys()])
    total_requirements = len(req_ids)

    # covered requirements = celles qui ont >=1 test lié
    covered_req_ids: List[str] = []
    uncovered_req_ids: List[str] = []

    req_to_tests_count: Dict[str, int] = {}
    total_links = 0

    for req_id in req_ids:
        tests = req_to_tests.get(req_id, set())
        if tests is None:
            tests = set()
        if not isinstance(tests, (set, list, tuple)):
            raise KPIError(
                f"Invalid input: req_to_tests['{req_id}'] must be a set/list/tuple of test IDs."
            )
        test_ids = [str(t) for t in tests if str(t).strip() != ""]
        count = len(set(test_ids))
        req_to_tests_count[req_id] = count
        total_links += count

        if count > 0:
            covered_req_ids.append(req_id)
        else:
            uncovered_req_ids.append(req_id)

    # Certains projets préfèrent s'aligner sur matrix.uncovered_requirements()
    # -> on l'utilise si disponible, mais on garde le calcul ci-dessus comme baseline.
    if hasattr(matrix, "uncovered_requirements") and callable(getattr(matrix, "uncovered_requirements")):
        try:
            external_uncovered = [str(x) for x in matrix.uncovered_requirements()]
            external_uncovered = _safe_sorted(external_uncovered)
            # On ne force pas si incohérence majeure, mais on log.
            if set(external_uncovered) != set(uncovered_req_ids):
                log.warning(
                    "KPI uncovered mismatch (computed=%s, matrix=%s). Keeping computed baseline.",
                    uncovered_req_ids,
                    external_uncovered,
                )
        except Exception as e:
            log.warning("matrix.uncovered_requirements() failed (%s). Keeping computed baseline.", e)

    orphan_tests: List[str] = []
    if hasattr(matrix, "orphan_tests") and callable(getattr(matrix, "orphan_tests")):
        try:
            orphan_tests = _safe_sorted([str(x) for x in matrix.orphan_tests()])
        except Exception as e:
            raise KPIError(f"matrix.orphan_tests() failed: {e}") from e
    else:
        # fallback : si matrix expose test_to_reqs, on peut inférer
        if hasattr(matrix, "test_to_reqs"):
            test_to_reqs = getattr(matrix, "test_to_reqs")
            if isinstance(test_to_reqs, dict):
                orphan_tests = _safe_sorted([str(t) for t, reqs in test_to_reqs.items() if not reqs])

    # total tests : on estime à partir de l'union des tests liés + orphelins
    linked_tests_union = set()
    for tests in req_to_tests.values():
        if isinstance(tests, (set, list, tuple)):
            linked_tests_union.update([str(t) for t in tests if str(t).strip() != ""])

    all_tests_union = set(linked_tests_union).union(set(orphan_tests))
    total_tests = len(all_tests_union)

    # coverage %
    if total_requirements == 0:
        coverage_percent = 0.0
        avg_tests_per_requirement = 0.0
    else:
        coverage_percent = (len(covered_req_ids) / total_requirements) * 100.0
        avg_tests_per_requirement = total_links / total_requirements

    kpi = CoverageKPI(
        total_requirements=total_requirements,
        total_tests=total_tests,
        covered_requirements=_safe_sorted(covered_req_ids),
        uncovered_requirements=_safe_sorted(uncovered_req_ids),
        orphan_tests=_safe_sorted(orphan_tests),
        coverage_percent=_round_pct(coverage_percent),
        total_links=total_links,
        avg_tests_per_requirement=round(avg_tests_per_requirement, 2),
        req_to_tests_count=dict(req_to_tests_count),
    )

    log.info(
        "KPI computed: req=%s covered=%s uncovered=%s coverage=%s%% tests=%s orphans=%s links=%s",
        kpi.total_requirements,
        len(kpi.covered_requirements),
        len(kpi.uncovered_requirements),
        kpi.coverage_percent,
        kpi.total_tests,
        len(kpi.orphan_tests),
        kpi.total_links,
    )

    return kpi


# ============================================================
# ▶️ Main (debug seulement)
# ============================================================
def main() -> None:
    """
    Point d’entrée CLI pour debug local (non utilisé par la CLI app2).
    """
    log.info("=== Debug kpi.py ===")

    class _DummyMatrix:
        req_to_tests = {"REQ-001": {"TC-001"}, "REQ-002": set()}

        def uncovered_requirements(self) -> List[str]:
            return ["REQ-002"]

        def orphan_tests(self) -> List[str]:
            return []

    kpis = compute_coverage_kpis(_DummyMatrix())
    log.info("coverage_percent=%s uncovered=%s", kpis.coverage_percent, kpis.uncovered_requirements)


if __name__ == "__main__":
    main()
