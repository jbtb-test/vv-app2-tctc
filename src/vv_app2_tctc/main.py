#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.main
------------------------------------------------------------
APP2 — TCTC (Traceability & Test Coverage Tool)

Purpose:
    CLI entry point that:
      - Loads requirements and test cases from CSV datasets
      - Validates dataset structure and consistency
      - Builds a traceability matrix (requirements ↔ test cases)
      - Computes coverage KPIs (coverage %, uncovered requirements, orphan tests)
      - Generates a report bundle (HTML + CSV artifacts)

AI assistance (optional, suggestion-only):
    - Enabled only if is_ai_enabled() returns True (env + key)
    - Produces suggestions (no automatic modification of datasets/traceability)
    - Never blocks execution: failures are caught and fallback to []

Inputs (CSV):
    - Requirements: requirement_id, title, description, criticality (tolerant aliases)
    - Tests: test_id, title, description, linked_requirements (tolerant aliases)

Outputs (out-dir):
    - HTML report
    - Traceability CSV
    - KPI CSV
    - AI suggestions CSV (optional)

Exit / failure policy:
    - Missing input files or decoding issues raise ModuleError
    - If --fail-on-empty is enabled:
        * empty datasets raise an error
        * validation errors raise an error (raise_if_invalid)
    - Otherwise: warnings are logged and outputs may be empty but generated.
============================================================
"""


from __future__ import annotations

from vv_app2_tctc.models import Requirement, TestCase
from vv_app2_tctc.validators import validate_datasets, raise_if_invalid

from vv_app2_tctc.traceability import build_matrix_from_testcases
from vv_app2_tctc.kpi import compute_coverage_kpis
from vv_app2_tctc.ia_assistant import is_ai_enabled, suggest_missing_links
from vv_app2_tctc.report import generate_report_bundle

# ============================================================
# 📦 Imports
# ============================================================
import argparse
import csv
import datetime as dt
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
class ModuleError(Exception):
    """Erreur spécifique au module (erreur métier ou technique encapsulée)."""


# ============================================================
# 🧩 Modèle de données (standard V&V)
# ============================================================
@dataclass
class ProcessResult:
    """
    Structure de sortie standardisée pour le run CLI.
    """
    ok: bool
    payload: Dict[str, Any]
    message: Optional[str] = None


# ============================================================
# 🔧 Helpers CSV
# ============================================================
def _normalize_header(s: str) -> str:
    return (s or "").strip().lower()


def _detect_delimiter(sample: str) -> str:
    """
    Détecte un séparateur probable entre ';' et ','.
    (Tolérant Excel vs CSV standard)
    """
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","

def _read_text_with_fallback_encodings(path: Path, encodings: List[str]) -> Tuple[str, str]:
    """
    Read file content trying multiple encodings.
    Returns (text, encoding_used).
    """
    last_err: Optional[Exception] = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc), enc
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise ModuleError(f"Unable to decode file {path} with encodings {encodings}: {last_err}")  # noqa: TRY003

def _read_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Lit un CSV avec:
      - détection simple du séparateur (';' vs ',')
      - fallback d'encodages (Windows / Excel)
    Retourne (fieldnames_normalized, rows_normalized).

    Encodages tentés (ordre) :
      - utf-8-sig (UTF-8 BOM)
      - utf-8
      - cp1252 (Windows-1252)
      - latin-1 (fallback permissif)
    """
    if not path.exists():
        raise ModuleError(f"Input file not found: {path}")

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    raw_text, used_enc = _read_text_with_fallback_encodings(path, encodings)

    lines = raw_text.splitlines()
    first_line = lines[0] if lines else ""
    delim = _detect_delimiter(first_line)

    # Re-open with the same encoding to feed csv module consistently
    with path.open("r", encoding=used_enc, newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        if not reader.fieldnames:
            raise ModuleError(f"CSV has no header row: {path}")

        fieldnames = [_normalize_header(x) for x in reader.fieldnames]
        rows: List[Dict[str, str]] = []

        for raw in reader:
            norm = {
                _normalize_header(k): (v or "").strip()
                for k, v in raw.items()
                if k is not None
            }
            rows.append(norm)

    log.debug(f"CSV read OK: path={path}, encoding={used_enc}, delimiter='{delim}', rows={len(rows)}")
    return fieldnames, rows

def _pick(row: Dict[str, str], keys: List[str], default: str = "") -> str:
    for k in keys:
        v = (row.get(k) or "").strip()
        if v:
            return v
    return default


# ============================================================
# 📥 Loaders (MVP 2.7)
# ============================================================
def load_requirements(path: Path) -> List[Dict[str, str]]:
    """
    Charge les exigences depuis requirements.csv (MVP 2.5).
    Schéma attendu (tolérant) :
      - requirement_id
      - title
      - description
      - criticality
    """
    _, rows = _read_csv_rows(path)
    out: List[Dict[str, str]] = []
    for idx, r in enumerate(rows, start=1):
        req_id = _pick(r, ["requirement_id", "req_id", "id"], default=f"REQ-{idx:03d}")
        title = _pick(r, ["title", "summary"], default="")
        desc = _pick(r, ["description", "text", "requirement_text"], default="")
        crit = _pick(r, ["criticality", "priority"], default="")
        if not (req_id and (title or desc)):
            log.warning(f"Requirement row {idx}: empty -> skipped")
            continue
        out.append(
            {
                "requirement_id": req_id,
                "title": title,
                "description": desc,
                "criticality": crit,
            }
        )
    return out


def load_tests(path: Path) -> List[Dict[str, str]]:
    """
    Charge les cas de test depuis tests.csv (MVP 2.6).
    Schéma attendu (tolérant) :
      - test_id
      - title
      - description
      - linked_requirements  (ex: "REQ-001|REQ-002" ou "REQ-001,REQ-002" ou vide)
    """
    _, rows = _read_csv_rows(path)
    out: List[Dict[str, str]] = []
    for idx, r in enumerate(rows, start=1):
        tc_id = _pick(r, ["test_id", "tc_id", "id"], default=f"TC-{idx:03d}")
        title = _pick(r, ["title", "summary"], default="")
        desc = _pick(r, ["description", "text"], default="")
        links = _pick(r, ["linked_requirements", "links", "requirements"], default="")
        if not (tc_id and (title or desc)):
            log.warning(f"Test row {idx}: empty -> skipped")
            continue
        out.append(
            {
                "test_id": tc_id,
                "title": title,
                "description": desc,
                "linked_requirements": links,
            }
        )
    return out


# ============================================================
# 🧾 Outputs (MVP 2.7)
# ============================================================
def _html_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_snapshot_csv(out_path: Path, requirements: List[Dict[str, str]], tests: List[Dict[str, str]]) -> None:
    """
    CSV snapshot minimal : récap exigences + tests (sans matrice).
    Sert de preuve d’exécution MVP 2.7.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["type", "id", "title", "details"])
        for r in requirements:
            w.writerow(["REQ", r["requirement_id"], r["title"], r["criticality"]])
        for t in tests:
            w.writerow(["TC", t["test_id"], t["title"], t["linked_requirements"]])


def write_snapshot_html(out_path: Path, requirements: List[Dict[str, str]], tests: List[Dict[str, str]]) -> None:
    """
    HTML snapshot minimal : liste des exigences + tests.
    (La matrice et les KPI viendront en 2.9/2.10/2.12)
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    req_rows = "\n".join(
        f"<tr><td>{_html_escape(r['requirement_id'])}</td>"
        f"<td>{_html_escape(r['title'])}</td>"
        f"<td style='white-space:pre-wrap'>{_html_escape(r['description'])}</td>"
        f"<td>{_html_escape(r['criticality'])}</td></tr>"
        for r in requirements
    )

    tc_rows = "\n".join(
        f"<tr><td>{_html_escape(t['test_id'])}</td>"
        f"<td>{_html_escape(t['title'])}</td>"
        f"<td style='white-space:pre-wrap'>{_html_escape(t['description'])}</td>"
        f"<td>{_html_escape(t['linked_requirements'])}</td></tr>"
        for t in tests
    )

    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>APP2 TCTC — Snapshot</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f5f7fa; color: #333; }}
    header {{ font-size: 24px; font-weight: bold; padding-bottom: 10px; margin-bottom: 20px; border-bottom: 2px solid #888; }}
    .badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:12px; background:#e9eef6; border:1px solid #c9d6ea; color:#234; margin-left: 8px; }}
    h2 {{ margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f0f0f0; text-align: left; }}
    .meta {{ color:#555; margin: 10px 0 18px 0; }}
  </style>
</head>
<body>
  <header>
    APP2 — TCTC (Traceability & Test Coverage Tool)
    <span class="badge">MVP CLI 2.7</span>
  </header>

  <div class="meta">
    Généré le {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    — Exigences : {len(requirements)} — Tests : {len(tests)}
  </div>

  <h2>Exigences</h2>
  <table>
    <thead><tr><th>ID</th><th>Titre</th><th>Description</th><th>Criticité</th></tr></thead>
    <tbody>
      {req_rows}
    </tbody>
  </table>

  <h2>Cas de test</h2>
  <table>
    <thead><tr><th>ID</th><th>Titre</th><th>Description</th><th>Liens (brut)</th></tr></thead>
    <tbody>
      {tc_rows}
    </tbody>
  </table>

  <p class="meta">
    Note : la matrice de traçabilité et les KPI seront produits dans les étapes 2.9 / 2.10 / 2.12.
  </p>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


# ============================================================
# 🔧 Fonction principale
# ============================================================
def process(data: Dict[str, Any]) -> ProcessResult:
    """
    - Charge requirements.csv + tests.csv
    - Applique validations minimales (présence, non-vide si fail_on_empty)
    - Valide la cohérence datasets (2.8.1)
    - Construit matrice (2.9) + KPI (2.10)
    - (Optionnel) Génère suggestions IA (2.11)
    - Génère rapport HTML + CSV (2.12)
    """
    try:
        if not isinstance(data, dict):
            raise ModuleError("Invalid input: 'data' must be a dict.")

        req_path = Path(str(data.get("requirements_path", "data/inputs/requirements.csv")))
        tests_path = Path(str(data.get("tests_path", "data/inputs/tests.csv")))
        out_dir = Path(str(data.get("out_dir", os.getenv("OUTPUT_DIR", "data/outputs"))))
        fail_on_empty = bool(data.get("fail_on_empty", False))
        verbose = bool(data.get("verbose", False))

        if verbose:
            log.setLevel(logging.DEBUG)

        log.info("Démarrage APP2 TCTC — CLI (2.12)")
        log.info("Requirements : %s", req_path)
        log.info("Tests        : %s", tests_path)
        log.info("Out dir      : %s", out_dir)

        enable_ai_env = str(os.getenv("ENABLE_AI", "0")).strip().lower()
        has_key = bool((os.getenv("OPENAI_API_KEY") or "").strip())

        ai_effective = is_ai_enabled()
        log.info(
            "AI      : %s (ENABLE_AI=%s, key=%s)",
            "enabled" if ai_effective else "disabled",
            enable_ai_env,
            "yes" if has_key else "no",
        )

        # ============================================================
        # 📥 Load datasets (dicts)
        # ============================================================
        requirements = load_requirements(req_path)
        tests = load_tests(tests_path)

        if fail_on_empty and (not requirements or not tests):
            raise ModuleError("Empty dataset (requirements or tests is empty).")

        # ============================================================
        # ✅ Validation datasets (2.8.1) + mapping models
        # ============================================================
        requirements_m = [Requirement.from_dict(r) for r in requirements]
        tests_m = [
            TestCase.from_dict(
                {
                    "test_id": t.get("test_id", ""),
                    "title": t.get("title", ""),
                    "description": t.get("description", ""),
                    "linked_requirements_raw": t.get("linked_requirements", ""),
                }
            )
            for t in tests
        ]

        validation_report = validate_datasets(requirements_m, tests_m)

        # Logs audit-friendly
        log.info(
            "Validation datasets: ok=%s, errors=%d, warnings=%d",
            validation_report.ok,
            len(validation_report.errors),
            len(validation_report.warnings),
        )

        if validation_report.errors:
            for e in validation_report.errors:
                log.error("VAL_ERROR %s: %s | %s", e.code, e.message, e.context)

        if validation_report.warnings:
            for w in validation_report.warnings:
                log.warning("VAL_WARN  %s: %s | %s", w.code, w.message, w.context)

        # Mode bloquant : on bloque sur erreurs si --fail-on-empty est activé
        if fail_on_empty:
            raise_if_invalid(validation_report)

        # ============================================================
        # 🔗 Matrice + KPI (2.9 / 2.10)
        # ============================================================
        matrix = build_matrix_from_testcases(requirements_m, tests_m)
        kpi = compute_coverage_kpis(matrix)

        # ============================================================
        # 🤖 Suggestions IA (optionnel) (2.11) — never blocking
        # ============================================================
        ai_suggestions = []
        if is_ai_enabled():
            try:
                ai_suggestions = (
                    suggest_missing_links(
                        requirements=requirements_m,
                        testcases=tests_m,
                        matrix=matrix,
                        verbose=verbose,
                    )
                    or []
                )
            except Exception as e:
                log.warning("AI suggestion step failed -> fallback [] (%s)", e)
                ai_suggestions = []


        # ============================================================
        # 📄 Report bundle (HTML + CSV) (2.12)
        # ============================================================
        out_dir.mkdir(parents=True, exist_ok=True)

        bundle = generate_report_bundle(
            requirements=requirements_m,
            testcases=tests_m,
            matrix=matrix,
            kpi=kpi,
            ai_suggestions=ai_suggestions,
            out_dir=out_dir,
            templates_dir="templates/tctc",
            template_name="tctc_report.html",
            title="APP2 TCTC — Traceability Report",
        )

        payload = {
            "requirements_count": len(requirements),
            "tests_count": len(tests),
            "requirements_input": str(req_path),
            "tests_input": str(tests_path),
            "out_dir": str(out_dir),

            # 2.12 outputs
            "report_html": str(bundle.report_html),
            "traceability_csv": str(bundle.traceability_csv),
            "kpi_csv": str(bundle.kpi_csv),
            "ai_suggestions_csv": str(bundle.ai_suggestions_csv) if bundle.ai_suggestions_csv else None,

            # KPI useful fields
            "coverage_percent": kpi.coverage_percent,
            "uncovered_requirements": list(kpi.uncovered_requirements),
            "orphan_tests": list(kpi.orphan_tests),
            "ai_suggestions_count": len(ai_suggestions),

            # Validation report
            "validation": validation_report.to_dict(),
        }

        return ProcessResult(ok=True, payload=payload, message="OK")

    except ModuleError:
        raise
    except Exception as e:
        log.exception("Erreur inattendue dans process()")
        raise ModuleError(str(e)) from e


# ============================================================
# ▶️ Main (CLI)
# ============================================================
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vv-app2-tctc",
        description=(
            "APP2 TCTC — Traceability & Test Coverage Tool.\n\n"
            "Reads requirements/tests CSV datasets, validates consistency, builds a traceability matrix,\n"
            "computes coverage KPIs, and generates a report bundle (HTML + CSV artifacts).\n\n"
            "AI assistance is optional, suggestion-only, and never blocks execution."
        ),
        epilog=(
            "Notes:\n"
            "- Outputs are generated in --out-dir (HTML + CSV).\n"
            "- AI is enabled only when is_ai_enabled() is True; failures fallback to [].\n"
            "- --fail-on-empty enforces stricter behavior (empty datasets and validation errors become fatal)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    p.add_argument(
        "--requirements",
        default="data/inputs/requirements.csv",
        help="Path to requirements CSV (default: data/inputs/requirements.csv).",
    )
    p.add_argument(
        "--tests",
        default="data/inputs/tests.csv",
        help="Path to tests CSV (default: data/inputs/tests.csv).",
    )
    p.add_argument(
        "--out-dir",
        default=os.getenv("OUTPUT_DIR", "data/outputs"),
        help="Output directory (default: OUTPUT_DIR or data/outputs).",
    )
    p.add_argument(
        "--fail-on-empty",
        action="store_true",
        help=(
            "Fail (non-zero) if datasets are empty.\n"
            "When enabled, validation errors are also fatal."
        ),
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logs.",
    )

    return p



def main() -> None:
    args = _build_parser().parse_args()
    out = process(
        {
            "requirements_path": args.requirements,
            "tests_path": args.tests,
            "out_dir": args.out_dir,
            "fail_on_empty": args.fail_on_empty,
            "verbose": args.verbose,
        }
    )
    log.info(f"Résultat : ok={out.ok}, message={out.message}")
    log.info(f"Payload  : {out.payload}")


if __name__ == "__main__":
    main()
