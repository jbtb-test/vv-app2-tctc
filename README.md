# APP2 — TCTC (Traceability & Test Coverage Tool)
## Traceability & Coverage Assistant — Requirements ↔ Tests

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

## Quickstart

### Option A — Démo sans exécution (portfolio)

Démonstration **clé en main pour recruteur**, sans installer ni exécuter Python.

Ouvrir :
- `docs/demo/README.md`

Accès direct :
- **Rapport HTML**  
  `docs/demo/assets/tctc_report.html`
- **Matrice CSV**  
  `docs/demo/assets/tctc_matrix.csv`
- **KPI CSV**  
  `docs/demo/assets/tctc_kpi.csv`

(Des captures d’écran sont fournies dans `docs/demo/assets/screenshots/`.)

---

### Option B — Reproduire localement (sans IA, recommandé)

Mode nominal, 100 % déterministe.

```bash
python -m vv_app2_tctc.main --verbose
```

Génère automatiquement :
- `data/outputs/tctc_matrix_<timestamp>.csv'
- `data/outputs/tctc_kpi_<timestamp>.csv`
- `data/outputs/tctc_report_<timestamp>.html`

Ouvrir le fichier HTML généré dans un navigateur.

### Option C — Mode IA (optionnel, avancé)

fichier .env.secret présent (non committé)

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

