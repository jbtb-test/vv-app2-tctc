# APP2 — TCTC (Traceability & Test Coverage Tool) — Traceability & Coverage Assistant

## TL;DR — Démo en 1 phrase
Outil de traçabilité Exigences ↔ Cas de test qui construit automatiquement une matrice de traçabilité,
calcule des KPI de couverture (exigences non couvertes, tests orphelins) et génère un rapport HTML démontrable,
avec IA optionnelle et non décisionnelle pour suggérer des liens manquants.

**But :** fiabiliser et démontrer la couverture de tests grâce à un **pipeline outillé** :
- construction de la traçabilité via **moteur déterministe**
- détection automatique des écarts de couverture
- suggestions **optionnelles** via IA
- génération d’outputs démontrables (CSV + HTML)

> IA = **suggestion only** (jamais décisionnelle).  
> L’application fonctionne **sans IA** par défaut.

## Problème métier
La traçabilité et la couverture de tests sont souvent :
- dispersées (Excel, ALM, liens manuels)
- fragiles (exigences non couvertes, tests orphelins)
- difficiles à auditer rapidement
- peu démontrables en entretien sans matrice claire ni KPI synthétiques

## Valeur apportée
- **Couverture fiable** : KPI calculés automatiquement et auditables
- **Détection des écarts** : exigences non couvertes, tests orphelins
- **Traçabilité** : règles explicites, tests unitaires, outputs reproductibles
- **Démo immédiate** : rapport HTML consultable (sans exécution)

## Fonctionnement (pipeline résumé)

1) **Entrées**  
   CSV d’exigences + CSV de cas de test  
   (format proche DOORS / Polarion)

2) **Analyse déterministe**  
   Validation des datasets, construction de la matrice, calcul des KPI

3) **IA (optionnelle)**  
   Suggestions de liens potentiels manquants  
   (non décisionnelles, aucune création ou modification automatique)

4) **Sorties**
   - Matrice de traçabilité CSV
   - KPI de couverture CSV
   - Rapport HTML (consultable)

> L’IA est **optionnelle**, **non bloquante**, et **n’influence jamais les KPI**.

## Quickstart

### Option A — Démo immédiate (sans exécution)
Ouvrir directement le rapport HTML de démonstration :

- `docs/outputs_demo/tctc_output_demo.html`

Note GitHub :  
GitHub affiche le code HTML.  
Pour voir le rapport, téléchargez le fichier ou le dépôt, puis ouvrez
`docs/outputs_demo/tctc_output_demo.html` dans votre navigateur.

### Option B — Reproduire localement (sans IA, recommandé)

```bash
python -m vv_app2_tctc.main --verbose
```

Génère automatiquement :
- `data/outputs/tctc_matrix_<timestamp>.csv'
- `data/outputs/tctc_kpi_<timestamp>.csv`
- `data/outputs/tctc_report_<timestamp>.html`

Ouvrir le fichier HTML généré dans un navigateur.

### Option C — Mode IA (optionnel, avancé)

```powershell
$env:ENABLE_AI="1"
$env:OPENAI_API_KEY="your_key_here"
python -m vv_app2_tctc.main --verbose
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
│  └─ outputs_demo/
└─ README.md
```

