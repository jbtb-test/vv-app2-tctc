#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
============================================================
env_check.py
------------------------------------------------------------
Description :
    Vérification d'environnement pour une APP du projet "V&V IA"
    (QRA / TCTC / AITA).

Rôle :
    - Collecter des informations de santé environnement (Python, pip,
      venv, OS, chemins projet)
    - Produire une preuve exploitable (Markdown) pour validation Rx-V (R5)
    - Optionnel : produire un JSON pour exploitation automatisée

Usage (PowerShell) :
    .\venv\Scripts\Activate.ps1
    python tools/env_check.py --out docs/env_report.md --json-out docs/env_report.json
    deactivate

Usage (Git Bash) :
    source venv/Scripts/activate
    python tools/env_check.py --out docs/env_report.md --json-out docs/env_report.json
    deactivate

Notes :
    - Pas de dépendance externe.
    - Conçu pour être testable (collect_env_info / write_*).
============================================================
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# 🧩 Data model
# ============================================================
@dataclass(frozen=True)
class EnvInfo:
    """Structure stable d'info environnement."""
    timestamp_utc: str
    cwd: str
    project_root: str
    python_version: str
    python_executable: str
    pip_version: str
    is_venv: bool
    venv_prefix: str
    os_name: str
    os_release: str
    platform: str


# ============================================================
# 🔧 Collect
# ============================================================
def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _detect_project_root(start: Path) -> Path:
    """
    Détecte la racine projet (repo app) en cherchant un marqueur.
    Ici : requirements.txt (créé en 0.7) ou pytest.ini.
    """
    cur = start.resolve()
    for _ in range(10):
        if (cur / "requirements.txt").exists() or (cur / "pytest.ini").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def _safe_run_pip_version() -> str:
    """
    Récupère la version pip sans subprocess (robuste).
    """
    try:
        import pip  # type: ignore
        return getattr(pip, "__version__", "unknown")
    except Exception:
        # Fallback : pip peut ne pas être importable selon environnement
        return "unknown"


def collect_env_info(cwd: Optional[Path] = None) -> EnvInfo:
    cwd_path = (cwd or Path.cwd()).resolve()
    project_root = _detect_project_root(cwd_path)

    is_venv = (sys.prefix != sys.base_prefix) or bool(os.environ.get("VIRTUAL_ENV"))
    venv_prefix = os.environ.get("VIRTUAL_ENV") or sys.prefix

    info = EnvInfo(
        timestamp_utc=_now_utc_iso(),
        cwd=str(cwd_path),
        project_root=str(project_root),
        python_version=sys.version.split()[0],
        python_executable=sys.executable,
        pip_version=_safe_run_pip_version(),
        is_venv=is_venv,
        venv_prefix=str(venv_prefix),
        os_name=platform.system(),
        os_release=platform.release(),
        platform=platform.platform(),
    )
    return info


# ============================================================
# 🧾 Render / Write
# ============================================================
def env_info_to_dict(info: EnvInfo) -> Dict[str, Any]:
    return {
        "timestamp_utc": info.timestamp_utc,
        "cwd": info.cwd,
        "project_root": info.project_root,
        "python_version": info.python_version,
        "python_executable": info.python_executable,
        "pip_version": info.pip_version,
        "is_venv": info.is_venv,
        "venv_prefix": info.venv_prefix,
        "os_name": info.os_name,
        "os_release": info.os_release,
        "platform": info.platform,
    }


def render_markdown(info: EnvInfo) -> str:
    ok_venv = "OK" if info.is_venv else "KO (venv non détecté)"
    lines = [
        "# Environment Healthcheck Report",
        "",
        f"- Generated (UTC): **{info.timestamp_utc}**",
        "",
        "## Runtime",
        f"- Python version: **{info.python_version}**",
        f"- Python executable: `{info.python_executable}`",
        f"- Pip version: **{info.pip_version}**",
        f"- Virtualenv detected: **{ok_venv}**",
        f"- Venv prefix: `{info.venv_prefix}`",
        "",
        "## System",
        f"- OS: **{info.os_name} {info.os_release}**",
        f"- Platform: `{info.platform}`",
        "",
        "## Project",
        f"- CWD: `{info.cwd}`",
        f"- Project root (detected): `{info.project_root}`",
        "",
        "## Verdict",
        "- ✅ If venv is detected and python/pip are visible, environment is considered **HEALTHY** for Phase 0.",
        "",
    ]
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================================================
# ▶️ CLI
# ============================================================
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="V&V IA - Environment healthcheck")
    p.add_argument("--out", type=str, default="", help="Output Markdown report path (e.g. docs/env_report.md)")
    p.add_argument("--json-out", type=str, default="", help="Output JSON report path (e.g. docs/env_report.json)")
    p.add_argument("--print", action="store_true", help="Print report to stdout")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    info = collect_env_info()
    md = render_markdown(info)
    payload = env_info_to_dict(info)

    if args.out:
        write_text(Path(args.out), md)
    if args.json_out:
        write_json(Path(args.json_out), payload)
    if args.print or (not args.out and not args.json_out):
        print(md)

    # Exit code : 0 si healthy minimal (venv détecté)
    return 0 if info.is_venv else 2


if __name__ == "__main__":
    raise SystemExit(main())
