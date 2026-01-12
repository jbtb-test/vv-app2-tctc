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
    python tools/env_check.py --print
    deactivate

Usage (Git Bash) :
    source venv/Scripts/activate
    python tools/env_check.py --out docs/env_report.md --json-out docs/env_report.json
    python tools/env_check.py --print
    deactivate

Notes :
    - Pas de dépendance externe.
    - Conçu pour être testable (collect_env_info / write_*).
============================================================
"""

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
    Marqueurs courants : pyproject.toml, pytest.ini, requirements.txt, .git
    """
    cur = start.resolve()
    markers = ("pyproject.toml", "pytest.ini", "requirements.txt", ".git")
    for _ in range(15):
        if any((cur / m).exists() for m in markers):
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
        return "unknown"


def collect_env_info(cwd: Optional[Path] = None) -> EnvInfo:
    cwd_path = (cwd or Path.cwd()).resolve()
    project_root = _detect_project_root(cwd_path)

    is_venv = (sys.prefix != sys.base_prefix) or bool(os.environ.get("VIRTUAL_ENV"))
    venv_prefix = os.environ.get("VIRTUAL_ENV") or sys.prefix

    return EnvInfo(
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


# ============================================================
# ✅ Health / Render
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


def _redact_path(p: str) -> str:
    """
    Masque les chemins personnels pour une démo (ex: C:\\Users\\<user>\\...).
    """
    try:
        path = Path(p)
        parts = list(path.parts)
        # Windows: ("C:\\", "Users", "<name>", ...)
        if len(parts) >= 3 and parts[1].lower() == "users":
            parts[2] = "<user>"
            return str(Path(*parts))
        return p
    except Exception:
        return p


def render_markdown(info: EnvInfo, *, redact_paths: bool = False) -> str:
    cwd = _redact_path(info.cwd) if redact_paths else info.cwd
    root = _redact_path(info.project_root) if redact_paths else info.project_root
    exe = _redact_path(info.python_executable) if redact_paths else info.python_executable
    venvp = _redact_path(info.venv_prefix) if redact_paths else info.venv_prefix

    venv_ok = info.is_venv
    pip_ok = info.pip_version != "unknown"
    root_ok = bool(info.project_root)

    checks = [
        ("Virtualenv détecté", venv_ok, f"prefix={venvp}"),
        ("pip visible", pip_ok, f"pip={info.pip_version}"),
        ("project root détecté", root_ok, f"root={root}"),
    ]
    healthy = all(ok for _, ok, _ in checks)
    verdict = "✅ HEALTHY" if healthy else "⚠️ CHECK"

    lines = [
        "# Environment Healthcheck Report",
        "",
        f"- Generated (UTC): **{info.timestamp_utc}**",
        f"- Verdict: **{verdict}**",
        "",
        "## Checks",
    ]
    for label, ok, detail in checks:
        icon = "✅" if ok else "❌"
        lines.append(f"- {icon} **{label}** — {detail}")

    lines += [
        "",
        "## Runtime",
        f"- Python version: **{info.python_version}**",
        f"- Python executable: `{exe}`",
        f"- Pip version: **{info.pip_version}**",
        "",
        "## System",
        f"- OS: **{info.os_name} {info.os_release}**",
        f"- Platform: `{info.platform}`",
        "",
        "## Project",
        f"- CWD: `{cwd}`",
        f"- Project root (detected): `{root}`",
        "",
        "## Notes",
        "- En entretien : lancer avec `--redact-paths` pour masquer les chemins utilisateur.",
        "- Exit code: `0` si HEALTHY, `2` si venv non détecté.",
        "",
    ]
    return "\n".join(lines)


def is_healthy_minimal(info: EnvInfo) -> bool:
    """
    Critère minimal : venv détecté.
    (On garde ce critère simple pour éviter faux négatifs.)
    """
    return bool(info.is_venv)


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
    p.add_argument("--quiet", action="store_true", help="No stdout (useful in CI)")
    p.add_argument("--redact-paths", action="store_true", help="Mask personal paths for interview/demo")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    info = collect_env_info()
    md = render_markdown(info, redact_paths=args.redact_paths)
    payload = env_info_to_dict(info)

    if args.out:
        write_text(Path(args.out), md)
    if args.json_out:
        write_json(Path(args.json_out), payload)

    # stdout : explicit --print OR no outputs specified (default behavior),
    # unless --quiet.
    if not args.quiet and (args.print or (not args.out and not args.json_out)):
        try:
            print(md)
        except UnicodeEncodeError:
            # Windows consoles (cp1252) peuvent casser sur les emojis (✅).
            # Fallback : remplace les chars non encodables.
            print(md.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))

    return 0 if is_healthy_minimal(info) else 2

if __name__ == "__main__":
    raise SystemExit(main())
