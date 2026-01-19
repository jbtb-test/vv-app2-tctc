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
        * tctc_report.html
    - Rapport ouvrable localement (standalone)

Notes :
    - Aucune dépendance IA ici (on reçoit déjà les suggestions).
    - 2.12.D : ajout des listes complètes exigences & tests (ID + titre) au rapport.
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

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except Exception:  # pragma: no cover (dépend de l'environnement)
    Environment = None  # type: ignore[assignment]
    FileSystemLoader = None  # type: ignore[assignment]
    select_autoescape = None  # type: ignore[assignment]


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
    Construit les lignes CSV/HTML de la matrice (req -> tests).
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
# 2.12.D — Helpers pour listes complètes
# ============================================================
def _requirements_list(requirements: Sequence[models.Requirement]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for r in requirements:
        out.append(
            {
                "id": str(getattr(r, "requirement_id", "")),
                "title": (getattr(r, "title", "") or "").strip(),
            }
        )
    out.sort(key=lambda x: x["id"])
    return out


def _tests_list(testcases: Sequence[models.TestCase]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for t in testcases:
        out.append(
            {
                "id": str(getattr(t, "test_id", "")),
                "title": (getattr(t, "title", "") or "").strip(),
            }
        )
    out.sort(key=lambda x: x["id"])
    return out


# ============================================================
# 🔧 HTML rendering
# ============================================================
def _render_fallback_html(context: Dict[str, Any], reason: str) -> str:
    """
    Fallback HTML minimal (sans Jinja2), pour garantir un artefact ouvrable localement.
    """
    title = str(context.get("title", "APP2 TCTC — Report"))
    badge = str(context.get("badge", "FALLBACK"))
    counts = context.get("counts", {}) or {}
    req_n = counts.get("requirements", 0)
    tc_n = counts.get("testcases", 0)
    ai_n = int(context.get("ai_suggestions_count", 0) or 0)

    # KPI: on évite d'afficher un objet brut; on met quelques champs clés si présents
    kpi = context.get("kpi", None)
    kpi_lines: List[str] = []
    for key in ["total_requirements", "total_tests", "coverage_percent", "total_links", "avg_tests_per_requirement"]:
        if kpi is not None and hasattr(kpi, key):
            kpi_lines.append(f"<li><b>{key}</b>: {getattr(kpi, key)}</li>")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; background: #333; color: #fff; }}
    .warn {{ background: #b00020; }}
    code {{ background: #f2f2f2; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="badge warn">{badge} (fallback)</p>

  <h2>Summary</h2>
  <ul>
    <li><b>requirements</b>: {req_n}</li>
    <li><b>testcases</b>: {tc_n}</li>
    <li><b>ai_suggestions_count</b>: {ai_n}</li>
  </ul>

  <h2>KPI (partial)</h2>
  <ul>
    {''.join(kpi_lines) if kpi_lines else '<li>No KPI fields available</li>'}
  </ul>

  <h2>Reason</h2>
  <p><code>{reason}</code></p>

  <p>Note: Full HTML rendering was not available. CSV exports were still generated.</p>
</body>
</html>
"""


def _render_html(
    templates_dir: Path,
    template_name: str,
    context: Dict[str, Any],
) -> str:
    """
    Render HTML via Jinja2 if available and template exists.
    Fallback to a minimal standalone HTML otherwise.
    """
    # Jinja2 optional
    if Environment is None or FileSystemLoader is None or select_autoescape is None:
        reason = "Jinja2 not available"
        log.warning("%s -> using fallback HTML", reason)
        return _render_fallback_html(context, reason=reason)

    # Templates dir / file checks
    if not templates_dir.exists() or not templates_dir.is_dir():
        reason = f"templates_dir not found: {templates_dir}"
        log.warning("%s -> using fallback HTML", reason)
        return _render_fallback_html(context, reason=reason)

    tpl_path = templates_dir / template_name
    if not tpl_path.exists() or not tpl_path.is_file():
        reason = f"template not found: {tpl_path}"
        log.warning("%s -> using fallback HTML", reason)
        return _render_fallback_html(context, reason=reason)

    try:
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        tpl = env.get_template(template_name)
        return tpl.render(**context)
    except Exception as e:
        reason = f"Jinja2 render failed: {e}"
        log.warning("%s -> using fallback HTML", reason)
        return _render_fallback_html(context, reason=reason)



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
    template_name: str = "tctc_report.html",
    title: str = "APP2 TCTC — Traceability Report",
) -> ReportPaths:
    """
    Génère exports CSV + rapport HTML.

    Durcissement 5.3:
      - out_dir créé tôt
      - CSV toujours générés (matrix + KPI, AI optionnel)
      - HTML toujours généré : rendu Jinja2 si possible, sinon fallback HTML minimal
      - Logging explicite (machine vierge : templates/jinja2 absents)

    Returns:
        ReportPaths: chemins des fichiers générés.
    """
    try:
        out_path = Path(out_dir)
        tpl_dir = Path(templates_dir)

        # Always create output dir early
        out_path.mkdir(parents=True, exist_ok=True)

        # Stabiliser les séquences (évite len(list(...)) multiples)
        req_list = list(requirements)
        tc_list = list(testcases)
        ai_list = list(ai_suggestions or [])

        # Pré-calculs déterministes (évite double appel)
        matrix_rows = _matrix_rows(matrix)

        # ============================================================
        # CSV exports (must succeed)
        # ============================================================

        # CSV: matrix
        trace_csv = out_path / "traceability_matrix.csv"
        _write_csv(
            trace_csv,
            header=["requirement_id", "covered", "linked_test_ids"],
            rows=matrix_rows,
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
        if ai_list:
            ai_csv = out_path / "ai_suggestions.csv"
            _write_csv(
                ai_csv,
                header=["requirement_id", "test_id", "confidence", "rationale"],
                rows=_ai_rows(ai_list),
            )

        # ============================================================
        # 2.12.D — Full lists (deterministic)
        # ============================================================
        requirements_list = _requirements_list(req_list)
        tests_list = _tests_list(tc_list)

        # ============================================================
        # HTML report (never missing: Jinja2 if possible else fallback)
        # ============================================================
        ai_enabled = bool(ai_list)
        badge = "AI ENABLED" if ai_enabled else "DETERMINISTIC"

        context: Dict[str, Any] = {
            "title": title,
            "header": title,
            "badge": badge,
            "ai_enabled": ai_enabled,
            "ai_suggestions_count": len(ai_list),
            "kpi": kpi,
            "matrix_rows": matrix_rows,
            "uncovered": list(getattr(kpi, "uncovered_requirements", [])),
            "orphans": list(getattr(kpi, "orphan_tests", [])),
            # 2.12.D
            "requirements_list": requirements_list,
            "tests_list": tests_list,
            # keep existing AI rendering format used by template
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
                "requirements": len(req_list),
                "testcases": len(tc_list),
            },
        }

        # _render_html() must be hardened to fallback to minimal HTML when needed
        html = _render_html(tpl_dir, template_name, context)

        report_html = out_path / "tctc_report.html"
        report_html.write_text(html, encoding="utf-8")

        log.info(
            "Report bundle generated: html=%s trace=%s kpi=%s ai=%s",
            report_html.name,
            trace_csv.name,
            kpi_csv.name,
            ai_csv.name if ai_csv else "none",
        )
        log.info("Report bundle output dir: %s", out_path.resolve())

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
