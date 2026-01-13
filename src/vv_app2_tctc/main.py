#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.main
------------------------------------------------------------
Description :
    APP2 — TCTC (Traceability & Test Coverage Tool)
    Étape 2.7 — CLI main

Rôle :
    - Fournir une CLI robuste (MVP) :
        * lecture CSV exigences + CSV cas de test
        * validation minimale des entrées (présence + headers)
        * orchestration (préparation des données)
        * génération d’outputs démontrables (CSV + HTML "snapshot")
    - Aucune dépendance aux modules futurs (models/validators/traceability/kpi/ia/report),
      ceux-ci arriveront aux étapes 2.8+.

Architecture (repo) :
    - Code : src/vv_app2_tctc/
    - Tests : tests/
    - Données : data/
    - Docs : docs/
    - Templates : templates/

Usage CLI :
    python -m vv_app2_tctc.main
    python -m vv_app2_tctc.main --requirements data/inputs/requirements.csv --tests data/inputs/tests.csv
    python -m vv_app2_tctc.main --out-dir data/outputs --verbose
    python -m vv_app2_tctc.main --fail-on-empty

Notes :
    - L’IA est volontairement ABSENTE en 2.7 (ENABLE_AI ignoré ici).
    - Les KPI et la matrice complète arrivent en 2.9 / 2.10.
    - Le HTML généré ici est un rendu standalone minimal (ouvrable localement).
============================================================
"""

from __future__ import annotations

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
    - Génère outputs snapshot (CSV + HTML)
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

        log.info("Démarrage APP2 TCTC — CLI (2.7)")
        log.info(f"Requirements : {req_path}")
        log.info(f"Tests        : {tests_path}")
        log.info(f"Out dir      : {out_dir}")

        # IA volontairement ignorée à ce stade (2.7)
        enable_ai_env = str(os.getenv("ENABLE_AI", "0"))
        has_key = bool((os.getenv("OPENAI_API_KEY") or "").strip())
        log.info(
            f"AI      : {'enabled' if enable_ai_env.strip() in {'1','true','yes','on'} else 'disabled'} "
            f"(ignored in 2.7, ENABLE_AI={enable_ai_env}, key={'yes' if has_key else 'no'})"
        )

        requirements = load_requirements(req_path)
        tests = load_tests(tests_path)

        if fail_on_empty and (not requirements or not tests):
            raise ModuleError("Empty dataset (requirements or tests is empty).")

        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

        out_csv = out_dir / f"tctc_snapshot_{stamp}.csv"
        out_html = out_dir / f"tctc_snapshot_{stamp}.html"

        write_snapshot_csv(out_csv, requirements, tests)
        write_snapshot_html(out_html, requirements, tests)

        payload = {
            "requirements_count": len(requirements),
            "tests_count": len(tests),
            "requirements_input": str(req_path),
            "tests_input": str(tests_path),
            "out_dir": str(out_dir),
            "output_csv": str(out_csv),
            "output_html": str(out_html),
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
            "APP2 TCTC — CLI: read requirements/tests CSV, validate minimal schema, "
            "and generate snapshot outputs (CSV + HTML). "
            "Traceability matrix and KPI are implemented in later steps."
        ),
    )

    p.add_argument(
        "--requirements",
        default="data/inputs/requirements.csv",
        help="Path to requirements CSV (default: data/inputs/requirements.csv)",
    )
    p.add_argument(
        "--tests",
        default="data/inputs/tests.csv",
        help="Path to tests CSV (default: data/inputs/tests.csv)",
    )
    p.add_argument(
        "--out-dir",
        default=os.getenv("OUTPUT_DIR", "data/outputs"),
        help="Output directory (default: OUTPUT_DIR or data/outputs)",
    )
    p.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Fail (non-zero) if requirements or tests dataset is empty.",
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
