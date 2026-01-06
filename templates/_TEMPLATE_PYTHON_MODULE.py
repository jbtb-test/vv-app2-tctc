#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
_TEMPLATE_PYTHON_MODULE.py
------------------------------------------------------------
Description :
    Template standard de module Python pour les repos APP
    du projet "V&V IA" (APP1_QRA / APP2_TCTC / APP3_AITA).

Rôle :
    - Fournir une structure de code homogène (docstring, exceptions, logs,
      fonctions, point d’entrée CLI) conforme à la méthode V&V.
    - Le code métier sera implémenté dans les phases applicatives.

Architecture :
    - Emplacement cible des modules : src/<package_name>/
    - Tests unitaires : tests/
    - Données : data/
    - Docs : docs/
    - Outils : tools/

Usage CLI (exemple) :
    python -m <package_name>.<module>

Usage test (exemple) :
    pytest -q

Notes :
    - Aucun import projet "dur" ici (pour éviter erreurs avant implémentation).
    - Le logger est local et autonome à ce template.
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional


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
# 🧩 Modèle de données (optionnel)
# ============================================================
@dataclass
class ProcessResult:
    """
    Exemple de structure de sortie standardisée.
    À adapter selon les besoins de l’app.
    """
    ok: bool
    payload: Dict[str, Any]
    message: Optional[str] = None


# ============================================================
# 🔧 Fonctions principales
# ============================================================
def process(data: Dict[str, Any]) -> ProcessResult:
    """
    Fonction principale du module.

    Args:
        data: dictionnaire de données en entrée (à définir par app).
    Returns:
        ProcessResult: résultat standardisé.
    Raises:
        ModuleError: en cas d’erreur (validation entrée, logique, etc.)
    """
    try:
        if not isinstance(data, dict):
            raise ModuleError("Invalid input: 'data' must be a dict.")

        log.info("Démarrage traitement module (template)...")

        # TODO: implémenter la logique métier dans les phases APP
        result_payload = dict(data)

        return ProcessResult(ok=True, payload=result_payload, message="OK")

    except ModuleError:
        # Erreurs métier déjà typées → on relance
        raise
    except Exception as e:
        log.exception("Erreur inattendue dans process()")
        raise ModuleError(str(e)) from e


# ============================================================
# ▶️ Main (debug seulement)
# ============================================================
def main() -> None:
    """
    Point d’entrée CLI pour debug local.

    Exemple :
        python src/<package_name>/<module>.py
    """
    log.info("=== Exécution directe du module (template) ===")
    sample = {"test": True}
    out = process(sample)
    log.info(f"Résultat : ok={out.ok}, message={out.message}, payload={out.payload}")


if __name__ == "__main__":
    main()
