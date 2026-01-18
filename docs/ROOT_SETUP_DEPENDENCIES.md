# Setup & Dependencies — Notes internes

## Principes clés

- `pyproject.toml` = **source de vérité**
- runtime minimal (IA optionnelle)
- extras : `dev`, `ai`
- layout `src/`
- installation éditable (`pip install -e`)
- aucun secret versionné

---

## Installation standard (machine vierge)

```powershell
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
# option IA
pip install -e ".[dev,ai]"
python -m vv_app2-tctc.main --out-dir data\outputs --verbose
pytest -vv
```

---

## Environnement & secrets

- .env.example versionné
- .env / .env.secret locaux uniquement
- .gitignore protège tous les secrets