# CI — GitHub Actions désactivées (blocage facturation)

## Contexte

Les GitHub Actions ne s’exécutent pas actuellement sur ce dépôt car le compte GitHub est **verrouillé suite à un problème de facturation**.

Message observé dans les Checks :
> "The job was not started because your account is locked due to a billing issue."

## Décision (temporaire)

Afin d’éviter des ❌ trompeurs (non liés à la qualité du code), le workflow CI a été **désactivé** :

- `.github/workflows/pytest.yml` → `.github/workflows/pytest.yml.disabled`

## Référence CI locale (pendant le blocage)

La validation “CI” est réalisée localement via :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
pytest -q
python -m vv_app2_tctc.main --out-dir data\outputs --verbose
```

## Réactiver la CI (quand la facturation est résolue)

Renommer le fichier pour réactiver GitHub Actions :

- `.github/workflows/pytest.yml.disabled` → `.github/workflows/pytest.yml`

## Statut

- Le workflow GitHub Actions est volontairement désactivé tant que le compte est verrouillé.
- La validation CI est assurée localement via la procédure ci-dessus.
- Le problème est externe au code (plateforme GitHub / facturation) et ne reflète pas l’état de la base de code.

