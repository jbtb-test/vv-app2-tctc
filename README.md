# APP2 — TCTC (Traceability & Test Coverage Tool)

## TL;DR — Démo en 1 phrase
Outil de **traçabilité Exigences ↔ Cas de test** (type DOORS / Polarion) qui construit automatiquement une **matrice de traçabilité**,
calcule des **KPI de couverture** (exigences non couvertes, tests orphelins) et génère un **rapport HTML démontrable**,
avec **IA optionnelle et non décisionnelle** pour suggérer des liens manquants.

**But :** fiabiliser et démontrer la couverture de tests grâce à un **pipeline outillé** :
- construction de la traçabilité via **moteur déterministe**
- calcul automatique des **KPI de couverture**
- suggestions **optionnelles** via IA
- génération d’outputs démontrables (**CSV + HTML**)

> IA = **suggestion only** (jamais décisionnelle).  
> L’application fonctionne **sans IA** par défaut.

---

## Problème métier
La traçabilité et la couverture de tests sont souvent :
- dispersées (Excel, ALM, liens manuels)
- fragiles (exigences non couvertes, tests orphelins)
- difficiles à auditer rapidement
- peu démontrables en entretien sans **matrice claire ni KPI synthétiques**

---

## Valeur apportée
- **Couverture mesurée** : KPI calculés automatiquement et auditables
- **Détection des écarts** : exigences non couvertes, tests orphelins
- **Traçabilité V&V** : règles explicites, validation des datasets, tests unitaires
- **Démo portfolio** : rapport HTML consultable + CSV exploitables sans exécuter le code

---

## Fonctionnement (pipeline résumé)

1) **Entrées**  
   CSV d’exigences + CSV de cas de test  
   (format proche DOORS / Polarion)

2) **Analyse déterministe**  
   Validation des datasets, construction de la matrice, calcul des KPI

3) **IA (optionnelle)**  
   Suggestions de **liens manquants**  
   (non décisionnelles, aucune création ou modification automatique)

4) **Sorties**
   - Matrice de traçabilité (CSV)
   - KPI de couverture (CSV)
   - Rapport HTML (consultable)

> L’IA est **optionnelle**, **non bloquante**, et **n’influence jamais les KPI**.

---

## Installation (local)

```powershell
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
# option IA
pip install -e ".[dev,ai]"
```

## Tests (CI-friendly)
```bash
pytest -vv
```

---

## Quickstart

### Option A — Démo sans exécution (recommandée pour recruteur)

Cette application fournit un **pack de démonstration figé**, consultable directement sur GitHub,
sans installer ni exécuter Python.

Démonstration **clé en main pour recruteur**, sans installer ni exécuter Python.

Ouvrir :
- `docs/demo/README.md`

Accès direct :
- **Sans IA (moteur déterministe)**  
  `docs/demo/assets/outputs_no_ai/rapport.html`
- **Avec IA (suggestions gouvernées)**  
  `docs/demo/assets/outputs_ai/rapport.html`

Des captures d’écran sont disponibles dans :
`docs/demo/assets/screenshots/`

👉 Point d’entrée unique :
- `docs/demo/README.md`

---

### Option B — Reproduire localement (sans IA, recommandé)

Cette option correspond au mode nominal de l’outil (100 % déterministe).

```bash
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

Génère automatiquement :
- `data/outputs/tctc_matrix_<timestamp>.csv`
- `data/outputs/tctc_kpi_<timestamp>.csv`
- `data/outputs/tctc_report_<timestamp>.html`

Ouvrir le fichier HTML généré dans un navigateur.

### Option C — Mode IA (optionnel, avancé)

Copier `.env.example` en `.env` et renseigner les valeurs localement.  
⚠️ Ne jamais committer `.env` / `.env.*` (seul `.env.example` est versionné).

```powershell
. .\tools\load_env_secret.ps1
$env:ENABLE_AI="1"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

> L’IA fournit uniquement des suggestions de liens.
> Elle ne crée ni ne modifie automatiquement la traçabilité.

## Structure du projet

```text
vv-app2-tctc/
├─ src/
│  └─ vv_app2_tctc/
├─ tests/
├─ data/
│  └─ inputs/
├─ docs/
│  └─ demo/
└─ README.md
```

---

### Installation

> Les dépendances et environnements sont gérés via `pyproject.toml`.
> Les fichiers `requirements*.txt` sont fournis à titre informatif et de traçabilité.


