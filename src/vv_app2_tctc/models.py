#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
vv_app2_tctc.models
------------------------------------------------------------
Description :
    Modèles de domaine pour APP2 — TCTC (Traceability & Test Coverage Tool).

Rôle :
    - Définir les structures de données stables utilisées par :
        * validators.py : validation de cohérence datasets / liens
        * traceability.py : construction matrice Requirement ↔ TestCase
        * kpi.py : calcul KPI de couverture
        * ia_assistant.py : suggestions de liens (source=AI)
        * report.py : rendu HTML/CSV

    - Fournir une sérialisation simple (to_dict / from_dict) pour :
        * outputs
        * logs
        * tests

Contraintes :
    - stdlib only
    - modèles "data-only" (pas de logique KPI/matrice ici)
============================================================
"""

from __future__ import annotations

# ============================================================
# 📦 Imports
# ============================================================
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

# ============================================================
# 🔎 Public exports
# ============================================================
__all__ = [
    "Criticality",
    "LinkSource",
    "Requirement",
    "TestCase",
    "TraceLink",
    "CoverageKpi",
]

# ============================================================
# 🧱 Enums
# ============================================================
class Criticality(str, Enum):
    """Criticité (V&V/QA) d'une exigence."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LinkSource(str, Enum):
    """
    Origine d’un lien de traçabilité.
    - DATASET : lien explicitement présent dans tests.csv
    - AI : suggestion non décisionnelle
    - HUMAN : validation / ajout manuel (hors scope code, mais utile pour audit)
    """
    DATASET = "DATASET"
    AI = "AI"
    HUMAN = "HUMAN"


# ============================================================
# 🔧 Helpers (validation / mapping)
# ============================================================
def _s(v: Any) -> str:
    """Convertit en str et trim (robuste pour None)."""
    return ("" if v is None else str(v)).strip()


def _enum_from_str(enum_cls: type[Enum], raw: Any, field_name: str) -> Enum:
    """
    Convertit un champ texte en Enum (strict).

    Accepte :
      - instance Enum
      - chaîne égalant une valeur (ex: "HIGH")
      - chaîne égalant le nom (ex: "HIGH")
    """
    if isinstance(raw, enum_cls):
        return raw

    s = _s(raw)
    if not s:
        raise ValueError(f"{field_name} is required (got empty).")

    # match valeur
    try:
        return enum_cls(s)  # type: ignore[misc]
    except Exception:
        pass

    # match nom
    try:
        return enum_cls[s]  # type: ignore[index]
    except Exception as e:
        allowed = ", ".join([m.value for m in enum_cls])  # type: ignore[attr-defined]
        raise ValueError(f"Invalid {field_name}='{s}'. Allowed: {allowed}") from e


def parse_requirement_ids(raw: Any) -> List[str]:
    """
    Parse un champ de liens (linked_requirements) provenant du dataset.

    Accepte des séparateurs fréquents :
      - "REQ-001"
      - "REQ-001,REQ-002"
      - "REQ-001;REQ-002"
      - "REQ-001|REQ-002"
      - " REQ-001  |  REQ-002 "
    Retourne une liste ordonnée, dédupliquée, sans vides.
    """
    s = _s(raw)
    if not s:
        return []

    # Normalisation multi-séparateurs → ','
    for sep in ["|", ";"]:
        s = s.replace(sep, ",")
    parts = [_s(p) for p in s.split(",")]
    out: List[str] = []
    seen: Set[str] = set()
    for p in parts:
        if not p:
            continue
        if p in seen:
            continue
        out.append(p)
        seen.add(p)
    return out


# ============================================================
# 🧩 Modèles
# ============================================================
@dataclass(frozen=True)
class Requirement:
    """Exigence d'entrée (proche DOORS/Polarion), normalisée."""
    requirement_id: str
    title: str
    description: str
    criticality: Criticality = Criticality.MEDIUM

    source: str = "demo"
    system: str = ""
    component: str = ""
    priority: str = ""

    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirement_id", _s(self.requirement_id))
        object.__setattr__(self, "title", _s(self.title))
        object.__setattr__(self, "description", _s(self.description))
        object.__setattr__(self, "source", _s(self.source) or "demo")
        object.__setattr__(self, "system", _s(self.system))
        object.__setattr__(self, "component", _s(self.component))
        object.__setattr__(self, "priority", _s(self.priority))

        if not self.requirement_id:
            raise ValueError("Requirement.requirement_id must be non-empty.")
        if not (self.title or self.description):
            raise ValueError("Requirement must have at least a title or a description.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "title": self.title,
            "description": self.description,
            "criticality": self.criticality.value,
            "source": self.source,
            "system": self.system,
            "component": self.component,
            "priority": self.priority,
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Requirement":
        if not isinstance(d, dict):
            raise ValueError("Requirement.from_dict expects a dict.")
        crit_raw = d.get("criticality", Criticality.MEDIUM.value)
        crit = _enum_from_str(Criticality, crit_raw, "Requirement.criticality")
        return Requirement(
            requirement_id=d.get("requirement_id", "") or d.get("req_id", "") or d.get("id", ""),
            title=d.get("title", ""),
            description=d.get("description", "") or d.get("text", ""),
            criticality=crit,  # type: ignore[arg-type]
            source=d.get("source", "demo"),
            system=d.get("system", ""),
            component=d.get("component", ""),
            priority=d.get("priority", ""),
            meta=dict(d.get("meta", {}) or {}),
        )


@dataclass(frozen=True)
class TestCase:
    """Cas de test d'entrée, avec liens bruts vers exigences."""

    __test__ = False  # empêche pytest de collecter cette classe métier

    test_id: str
    title: str
    description: str

    linked_requirements_raw: str = ""  # texte tel que dataset (auditabilité)
    linked_requirements: List[str] = field(default_factory=list)  # liste normalisée

    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "test_id", _s(self.test_id))
        object.__setattr__(self, "title", _s(self.title))
        object.__setattr__(self, "description", _s(self.description))
        object.__setattr__(self, "linked_requirements_raw", _s(self.linked_requirements_raw))

        if not self.test_id:
            raise ValueError("TestCase.test_id must be non-empty.")
        if not (self.title or self.description):
            raise ValueError("TestCase must have at least a title or a description.")

        # linked_requirements : si vide, on parse depuis raw
        parsed = self.linked_requirements or parse_requirement_ids(self.linked_requirements_raw)
        object.__setattr__(self, "linked_requirements", parsed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "title": self.title,
            "description": self.description,
            "linked_requirements_raw": self.linked_requirements_raw,
            "linked_requirements": list(self.linked_requirements),
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TestCase":
        if not isinstance(d, dict):
            raise ValueError("TestCase.from_dict expects a dict.")

        raw = d.get("linked_requirements_raw", "")
        if not raw:
            # compat dataset v2.6 / main.py
            raw = d.get("linked_requirements", "") if isinstance(d.get("linked_requirements"), str) else ""

        links = d.get("linked_requirements", [])
        if isinstance(links, str):
            links_list = parse_requirement_ids(links)
        else:
            links_list = [_s(x) for x in (links or []) if _s(x)]

        return TestCase(
            test_id=d.get("test_id", "") or d.get("tc_id", "") or d.get("id", ""),
            title=d.get("title", ""),
            description=d.get("description", "") or d.get("text", ""),
            linked_requirements_raw=raw,
            linked_requirements=links_list,
            meta=dict(d.get("meta", {}) or {}),
        )


    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TestCase":
        if not isinstance(d, dict):
            raise ValueError("TestCase.from_dict expects a dict.")

        raw = d.get("linked_requirements_raw", "")
        if not raw:
            # compat dataset v2.6 / main.py
            raw = d.get("linked_requirements", "") if isinstance(d.get("linked_requirements"), str) else ""

        links = d.get("linked_requirements", [])
        if isinstance(links, str):
            links_list = parse_requirement_ids(links)
        else:
            links_list = [ _s(x) for x in (links or []) if _s(x) ]

        return TestCase(
            test_id=d.get("test_id", "") or d.get("tc_id", "") or d.get("id", ""),
            title=d.get("title", ""),
            description=d.get("description", "") or d.get("text", ""),
            linked_requirements_raw=raw,
            linked_requirements=links_list,
            meta=dict(d.get("meta", {}) or {}),
        )


@dataclass(frozen=True)
class TraceLink:
    """
    Lien de traçabilité entre une exigence et un test.

    - source : DATASET / AI / HUMAN
    - confidence : utile pour AI (0..1), None sinon
    """
    requirement_id: str
    test_id: str
    source: LinkSource = LinkSource.DATASET
    confidence: Optional[float] = None
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirement_id", _s(self.requirement_id))
        object.__setattr__(self, "test_id", _s(self.test_id))
        object.__setattr__(self, "rationale", _s(self.rationale))

        if not self.requirement_id:
            raise ValueError("TraceLink.requirement_id must be non-empty.")
        if not self.test_id:
            raise ValueError("TraceLink.test_id must be non-empty.")

        if self.confidence is not None:
            if not isinstance(self.confidence, (int, float)):
                raise ValueError("TraceLink.confidence must be a number (float) or None.")
            c = float(self.confidence)
            if c < 0.0 or c > 1.0:
                raise ValueError("TraceLink.confidence must be in [0.0, 1.0].")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "test_id": self.test_id,
            "source": self.source.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TraceLink":
        if not isinstance(d, dict):
            raise ValueError("TraceLink.from_dict expects a dict.")
        src = _enum_from_str(LinkSource, d.get("source", LinkSource.DATASET.value), "TraceLink.source")
        return TraceLink(
            requirement_id=d.get("requirement_id", "") or d.get("req_id", ""),
            test_id=d.get("test_id", "") or d.get("tc_id", ""),
            source=src,  # type: ignore[arg-type]
            confidence=d.get("confidence", None),
            rationale=d.get("rationale", ""),
        )


@dataclass(frozen=True)
class CoverageKpi:
    """
    KPI de couverture — modèle data-only (calculé dans kpi.py).

    Ces KPI sont conçus pour :
    - être exportés facilement
    - être affichés dans un rapport
    - être testés unitairement
    """
    requirements_total: int
    requirements_covered: int
    requirements_uncovered: int

    tests_total: int
    tests_orphan: int

    coverage_percent: float  # 0..100

    def __post_init__(self) -> None:
        for name in [
            "requirements_total",
            "requirements_covered",
            "requirements_uncovered",
            "tests_total",
            "tests_orphan",
        ]:
            v = getattr(self, name)
            if not isinstance(v, int) or v < 0:
                raise ValueError(f"CoverageKpi.{name} must be a non-negative int.")

        if not isinstance(self.coverage_percent, (int, float)):
            raise ValueError("CoverageKpi.coverage_percent must be a number.")
        p = float(self.coverage_percent)
        if p < 0.0 or p > 100.0:
            raise ValueError("CoverageKpi.coverage_percent must be in [0.0, 100.0].")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirements_total": self.requirements_total,
            "requirements_covered": self.requirements_covered,
            "requirements_uncovered": self.requirements_uncovered,
            "tests_total": self.tests_total,
            "tests_orphan": self.tests_orphan,
            "coverage_percent": float(self.coverage_percent),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "CoverageKpi":
        if not isinstance(d, dict):
            raise ValueError("CoverageKpi.from_dict expects a dict.")
        return CoverageKpi(
            requirements_total=int(d.get("requirements_total", 0) or 0),
            requirements_covered=int(d.get("requirements_covered", 0) or 0),
            requirements_uncovered=int(d.get("requirements_uncovered", 0) or 0),
            tests_total=int(d.get("tests_total", 0) or 0),
            tests_orphan=int(d.get("tests_orphan", 0) or 0),
            coverage_percent=float(d.get("coverage_percent", 0.0) or 0.0),
        )


# ============================================================
# Convenience constructors (optionnels, utiles pour traceability.py)
# ============================================================
def build_links_from_testcases(testcases: Iterable[TestCase]) -> List[TraceLink]:
    """
    Construit les TraceLink "DATASET" depuis les TestCase.linked_requirements.
    (Pas de validation ici : validators.py s'en charge)
    """
    links: List[TraceLink] = []
    for tc in testcases:
        for req_id in tc.linked_requirements:
            links.append(TraceLink(requirement_id=req_id, test_id=tc.test_id, source=LinkSource.DATASET))
    return links
