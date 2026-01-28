#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.ia_assistant
------------------------------------------------------------
Description :
    Module IA (OpenAI) encapsulé pour suggestions de liens manquants
    (APP2 — TCTC) — IA "suggestion-only" et non bloquante.

Objectifs :
    - Aucune dépendance IA obligatoire pour faire tourner l’app
    - IA désactivable via ENABLE_AI (env var) + fallback contrôlé
    - API OpenAI appelée uniquement si ENABLE_AI=1 ET OPENAI_API_KEY présent
    - "Suggestion-only" : ne modifie jamais la matrice / datasets

Variables d'environnement :
    - ENABLE_AI         : 0/1 (default: 0)
    - OPENAI_API_KEY    : clé API (si absent -> IA désactivée)
    - OPENAI_MODEL      : modèle (default: gpt-4.1-mini) [modifiable]

API utilisée :
    - OpenAI Responses API via openai-python (si installé)

Notes :
    - Sortie attendue STRICTEMENT JSON.
    - Toute erreur -> log explicite + fallback [] (NEVER RAISE).
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from vv_app2_tctc import models

# ============================================================
# 🔎 Public exports
# ============================================================
__all__ = [
    "ModuleError",
    "LinkSuggestion",
    "is_ai_enabled",
    "suggest_missing_links",
]

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
# ⚠️ Exceptions
# ============================================================
class ModuleError(Exception):
    """Erreur spécifique au module ia_assistant (APP2)."""


# ============================================================
# 🧩 Modèles de données
# ============================================================
@dataclass(frozen=True)
class LinkSuggestion:
    """
    Suggestion de lien : relier requirement_id -> test_id.

    Attributes:
        requirement_id: ID exigence (ex: REQ-001)
        test_id: ID test (ex: TC-010)
        rationale: justification courte
        confidence: confiance [0..1] optionnelle
    """
    requirement_id: str
    test_id: str
    rationale: str = ""
    confidence: Optional[float] = None


# ============================================================
# 🔧 Config / Helpers (aligné APP1)
# ============================================================
def _truthy(value: str | None) -> bool:
    v = (value or "").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def is_ai_enabled() -> bool:
    """
    IA activée seulement si ENABLE_AI est truthy ET OPENAI_API_KEY présent.
    """
    if not _truthy(os.getenv("ENABLE_AI", "0")):
        return False
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return False
    return True


def _get_model() -> str:
    """
    Modèle par défaut. Ajustable via OPENAI_MODEL.
    """
    return (os.getenv("OPENAI_MODEL") or "gpt-4.1-mini").strip()


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON robuste : NEVER RAISE.
    Retourne {} si invalide (fallback contrôlé).
    """
    try:
        return json.loads(text)
    except Exception as e:
        log.warning("AI JSON parse failed -> fallback {} (%s)", e)
        return {}


def _build_prompt(
    *,
    req: models.Requirement,
    candidate_tests: Sequence[models.TestCase],
    max_suggestions: int,
) -> str:
    """
    Prompt orienté traçabilité : proposer des couples (REQ -> TC).
    Réponse attendue STRICTEMENT en JSON.
    """
    tests_lines = "\n".join(
        f"- {tc.test_id}: {tc.title} | {tc.description}"
        for tc in candidate_tests
    ) or "- (none)"

    return f"""
You are a senior V&V / Test & Requirements Traceability assistant.

TASK:
Given ONE uncovered requirement and a list of candidate test cases, propose up to {max_suggestions} test cases
that should link to this requirement.

RULES:
- Suggestion-only: do NOT claim you changed anything.
- Use only the provided candidate test IDs (do not invent IDs).
- Keep rationales short and testable.
- Output MUST be valid JSON ONLY (no markdown, no prose).

INPUT REQUIREMENT:
requirement_id: {req.requirement_id}
title: {req.title}
description: {req.description}
criticality: {req.criticality}

CANDIDATE TEST CASES:
{tests_lines}

OUTPUT JSON SCHEMA:
{{
  "links": [
    {{
      "requirement_id": "REQ-xxx",
      "test_id": "TC-yyy",
      "rationale": "string",
      "confidence": 0.0
    }}
  ]
}}
""".strip()


def _extract_candidate_tests(
    testcases: Sequence[models.TestCase],
    matrix: Any,
    *,
    prefer_orphans: bool,
    max_candidates: int,
) -> List[models.TestCase]:
    """
    Sélection déterministe des tests candidats :
    - Priorité aux tests orphelins si demandée et disponible via matrix.orphan_tests()
    - Sinon fallback : premiers tests de la liste (tri par test_id)
    """
    tcs_sorted = sorted(testcases, key=lambda x: str(x.test_id))

    if prefer_orphans and hasattr(matrix, "orphan_tests") and callable(getattr(matrix, "orphan_tests")):
        try:
            orphan_ids = set(str(x) for x in matrix.orphan_tests())
            orphans = [tc for tc in tcs_sorted if str(tc.test_id) in orphan_ids]
            if orphans:
                return orphans[:max_candidates]
        except Exception:
            # Ne pas casser l'app, fallback déterministe
            pass

    return tcs_sorted[:max_candidates]


# ============================================================
# 🤖 API principale (APP2)
# ============================================================
def suggest_missing_links(
    requirements: Sequence[models.Requirement],
    testcases: Sequence[models.TestCase],
    matrix: Any,
    *,
    max_suggestions_per_req: int = 2,
    max_candidate_tests: int = 25,
    prefer_orphan_tests: bool = True,
    model: Optional[str] = None,
    verbose: bool = False,
) -> List[LinkSuggestion]:
    """
    Propose des liens manquants pour les exigences non couvertes.

    Contrat (hardening):
    - is_ai_enabled() est l'unique source de vérité pour activer l'IA
    - NEVER RAISE : toute erreur => log explicite + fallback []
    - Suggestion-only : ne modifie jamais datasets/matrice

    Returns:
        Liste de LinkSuggestion (peut être vide).
    """
    try:
        if verbose:
            log.setLevel(logging.DEBUG)

        # ------------------------------------------------------------
        # Guard rails: invalid inputs -> fallback []
        # ------------------------------------------------------------
        if matrix is None:
            log.warning("AI disabled: invalid input (matrix is None) -> fallback []")
            return []

        if not hasattr(matrix, "uncovered_requirements") or not callable(getattr(matrix, "uncovered_requirements")):
            log.warning("AI disabled: invalid input (matrix has no uncovered_requirements()) -> fallback []")
            return []

        # ------------------------------------------------------------
        # Single source of truth for AI enablement
        # ------------------------------------------------------------
        if not is_ai_enabled():
            enable_ai_env = (os.getenv("ENABLE_AI", "0") or "").strip().lower()
            has_key = bool((os.getenv("OPENAI_API_KEY") or "").strip())
            if enable_ai_env in {"1", "true", "yes", "on"} and not has_key:
                log.warning("AI requested (ENABLE_AI=1) but OPENAI_API_KEY missing -> fallback []")
            else:
                log.debug("AI disabled -> fallback []")
            return []

        # ------------------------------------------------------------
        # Optional dependency
        # ------------------------------------------------------------
        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            log.warning("openai-python not installed -> fallback []")
            return []

        # Uncovered req IDs (deterministic)
        try:
            uncovered_ids = sorted(str(x) for x in matrix.uncovered_requirements())
        except Exception as e:
            log.warning("AI disabled: matrix.uncovered_requirements() failed -> fallback [] (%s)", e)
            return []

        if not uncovered_ids:
            log.debug("No uncovered requirements -> no AI suggestions")
            return []

        # Index req_id -> Requirement
        req_by_id: Dict[str, models.Requirement] = {str(r.requirement_id): r for r in requirements}

        used_model = (model or _get_model()).strip()
        client = OpenAI()

        suggestions: List[LinkSuggestion] = []

        # Candidates tests (stable selection)
        candidates = _extract_candidate_tests(
            testcases,
            matrix,
            prefer_orphans=prefer_orphan_tests,
            max_candidates=max_candidate_tests,
        )
        candidate_ids = {str(tc.test_id) for tc in candidates}

        for req_id in uncovered_ids:
            req = req_by_id.get(req_id)
            if req is None:
                log.debug("Uncovered requirement id not found in dataset: %s", req_id)
                continue

            prompt = _build_prompt(req=req, candidate_tests=candidates, max_suggestions=max_suggestions_per_req)

            try:
                resp = client.responses.create(model=used_model, input=prompt)

                output_text = (getattr(resp, "output_text", None) or "").strip()
                if not output_text:
                    output_text = str(resp).strip()

                data = _safe_parse_json(output_text)
                raw = data.get("links", [])

                if not isinstance(raw, list):
                    log.warning("AI JSON invalid: 'links' is not a list -> skip")
                    continue

                for item in raw[:max_suggestions_per_req]:
                    if not isinstance(item, dict):
                        continue

                    rid = (item.get("requirement_id") or "").strip() or req_id
                    tid = (item.get("test_id") or "").strip()
                    if not tid:
                        continue

                    # Safety: accept only known candidate IDs
                    if tid not in candidate_ids:
                        continue

                    rationale = (item.get("rationale") or "").strip()
                    conf = item.get("confidence", None)

                    suggestions.append(
                        LinkSuggestion(
                            requirement_id=rid,
                            test_id=tid,
                            rationale=rationale,
                            confidence=conf if isinstance(conf, (int, float)) else None,
                        )
                    )

            except Exception as e:
                log.warning("AI call failed -> skip (%s)", e)
                continue

        return suggestions

    except Exception as e:
        log.exception("AI assistant unexpected failure -> fallback [] (%s)", e)
        return []


# ============================================================
# ▶️ Main (debug seulement)
# ============================================================
def main() -> None:
    """
    Point d’entrée debug local.
    """
    log.info("=== Debug ia_assistant.py (APP2) ===")
    log.info("AI enabled? %s", is_ai_enabled())


if __name__ == "__main__":
    main()
