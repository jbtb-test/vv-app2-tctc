#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
report.py — APP2 TCTC
------------------------------------------------------------
Description :
    Génération des exports (CSV) et du rapport HTML (Jinja2)
    à partir de la TraceabilityMatrix + CoverageKPI + suggestions IA.

Rôle :
    - Exporter :
        * traceability_matrix.csv (Req -> Tests)
        * kpi_summary.csv
        * ai_suggestions.csv (si présent)
        * report.html
    - Rapport ouvrable localement (standalone)

Architecture :
    Entrées:
        - requirements: list[Requirement]
        - testcases: list[TestCase]
        - matrix: TraceabilityMatrix
        - kpi: CoverageKPI
        - ai_suggestions: list[LinkSuggestion] (optionnel)
    Sorties:
        - fichiers dans out_dir

Usage (exemple) :
    from vv_app2_tctc.report import generate_report_bundle
    paths = generate_report_bundle(...)

Notes :
    - Aucune dépendance IA ici (on reçoit déjà les suggestions).
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from jinja2 import Environment, FileSystemLoader, select_autoescape

from vv_app2_tctc import models
from vv_app2_tctc.ia_assistant import LinkSuggestion
from vv_app2_tctc.kpi import CoverageKPI


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
class ReportError(Exception):
    """Erreur spécifique au reporting (I/O, template, données)."""


# ============================================================
# 🧩 Modèle de sortie
# ============================================================
@dataclass(frozen=True)
class ReportPaths:
    """
    Chemins de sortie générés par generate_report_bundle().
    """
    out_dir: Path
    report_html: Path
    traceability_csv: Path
    kpi_csv: Path
    ai_suggestions_csv: Optional[Path] = None


# ============================================================
# 🔧 Helpers CSV
# ============================================================
def _write_csv(path: Path, header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(list(header))
        for r in rows:
            writer.writerow(list(r))


def _matrix_rows(matrix: Any) -> List[List[str]]:
    """
    Construit les lignes CSV de la matrice (req -> tests).
    """
    req_to_tests = getattr(matrix, "req_to_tests", {})
    rows: List[List[str]] = []
    for req_id in sorted(str(k) for k in req_to_tests.keys()):
        tests = req_to_tests.get(req_id, set()) or set()
        test_ids = sorted(str(t) for t in tests)
        covered = "YES" if len(test_ids) > 0 else "NO"
        rows.append([req_id, covered, " ".join(test_ids)])
    return rows


def _kpi_rows(kpi: CoverageKPI) -> List[List[str]]:
    """
    KPI -> format 'metric,value' simple et lisible.
    """
    rows = [
        ["total_requirements", str(kpi.total_requirements)],
        ["total_tests", str(kpi.total_tests)],
        ["coverage_percent", str(kpi.coverage_percent)],
        ["covered_requirements_count", str(len(kpi.covered_requirements))],
        ["uncovered_requirements_count", str(len(kpi.uncovered_requirements))],
        ["orphan_tests_count", str(len(kpi.orphan_tests))],
        ["total_links", str(kpi.total_links)],
        ["avg_tests_per_requirement", str(kpi.avg_tests_per_requirement)],
    ]
    return rows


def _ai_rows(ai_suggestions: Sequence[LinkSuggestion]) -> List[List[str]]:
    rows: List[List[str]] = []
    for s in ai_suggestions:
        rows.append(
            [
                str(s.requirement_id),
                str(s.test_id),
                "" if s.confidence is None else str(s.confidence),
                (s.rationale or "").strip(),
            ]
        )
    return rows


# ============================================================
# 🔧 HTML rendering
# ============================================================
def _render_html(
    templates_dir: Path,
    template_name: str,
    context: Dict[str, Any],
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template(template_name)
    return tpl.render(**context)


# ============================================================
# 🔧 Fonction principale
# ============================================================
def generate_report_bundle(
    requirements: Sequence[models.Requirement],
    testcases: Sequence[models.TestCase],
    matrix: Any,
    kpi: CoverageKPI,
    *,
    ai_suggestions: Optional[Sequence[LinkSuggestion]] = None,
    out_dir: str | Path = "data/outputs",
    templates_dir: str | Path = "templates/tctc",
    template_name: str = "report.html",
    title: str = "APP2 TCTC — Traceability Report",
) -> ReportPaths:
    """
    Génère exports CSV + rapport HTML.

    Returns:
        ReportPaths: chemins des fichiers générés.
    """
    try:
        out_path = Path(out_dir)
        tpl_dir = Path(templates_dir)

        # CSV: matrix
        trace_csv = out_path / "traceability_matrix.csv"
        _write_csv(
            trace_csv,
            header=["requirement_id", "covered", "linked_test_ids"],
            rows=_matrix_rows(matrix),
        )

        # CSV: KPI
        kpi_csv = out_path / "kpi_summary.csv"
        _write_csv(
            kpi_csv,
            header=["metric", "value"],
            rows=_kpi_rows(kpi),
        )

        # CSV: AI (optional)
        ai_csv: Optional[Path] = None
        ai_list = list(ai_suggestions or [])
        if ai_list:
            ai_csv = out_path / "ai_suggestions.csv"
            _write_csv(
                ai_csv,
                header=["requirement_id", "test_id", "confidence", "rationale"],
                rows=_ai_rows(ai_list),
            )

        # HTML report
        badge = "AI ENABLED" if ai_list else "DETERMINISTIC"
        context = {
            "title": title,
            "header": title,
            "badge": badge,
            "kpi": kpi,
            "matrix_rows": _matrix_rows(matrix),
            "uncovered": list(kpi.uncovered_requirements),
            "orphans": list(kpi.orphan_tests),
            "ai_suggestions": [
                {
                    "requirement_id": s.requirement_id,
                    "test_id": s.test_id,
                    "confidence": s.confidence,
                    "rationale": s.rationale,
                }
                for s in ai_list
            ],
            "counts": {
                "requirements": len(list(requirements)),
                "testcases": len(list(testcases)),
            },
        }

        html = _render_html(tpl_dir, template_name, context)
        report_html = out_path / "report.html"
        report_html.parent.mkdir(parents=True, exist_ok=True)
        report_html.write_text(html, encoding="utf-8")

        log.info("Report bundle generated in: %s", out_path.resolve())

        return ReportPaths(
            out_dir=out_path,
            report_html=report_html,
            traceability_csv=trace_csv,
            kpi_csv=kpi_csv,
            ai_suggestions_csv=ai_csv,
        )

    except Exception as e:
        log.exception("Report generation failed")
        raise ReportError(str(e)) from e


# ============================================================
# ▶️ Main (debug seulement)
# ============================================================
def main() -> None:
    """
    Debug local (non utilisé par la CLI).
    """
    log.info("report.py loaded (debug).")


if __name__ == "__main__":
    main()
