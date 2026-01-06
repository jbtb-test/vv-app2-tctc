"""
============================================================
_TEMPLATE_PYTHON_TEST.py
------------------------------------------------------------
Description :
    Template standard de tests unitaires (pytest) pour les modules
    des repos APP du projet "V&V IA".

Objectifs :
    - Vérifier comportement nominal
    - Vérifier validation des entrées
    - Vérifier encapsulation des erreurs (ModuleError)

Usage :
    pytest -q
============================================================
"""

import pytest


# TODO: activer ces imports quand un vrai module existe
# from <package_name>.<module> import process, ModuleError


class ModuleError(Exception):
    """
    Stub local de ModuleError uniquement pour rendre le template exécutable
    même avant implémentation du code réel.
    À supprimer dès que l'import réel est activé.
    """


def process(_data):
    """
    Stub local uniquement pour template.
    À supprimer dès que l'import réel est activé.
    """
    raise ModuleError("Template stub: replace with real implementation.")


# ============================================================
# 🔧 Fixtures
# ============================================================
@pytest.fixture
def sample_input():
    return {"key": "value"}


@pytest.fixture
def invalid_input():
    return None


# ============================================================
# 🧪 Tests
# ============================================================
def test_process_nominal(sample_input):
    """
    À adapter quand process() réel sera implémenté.
    """
    with pytest.raises(ModuleError):
        process(sample_input)


def test_process_error(invalid_input):
    """
    Vérifie qu’une entrée invalide remonte une ModuleError.
    """
    with pytest.raises(ModuleError):
        process(invalid_input)
