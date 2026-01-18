# APP2 TCTC — Demo Pack (Recruteur)

Ce dossier contient une **démonstration complète consultable sans exécuter le code**.

Il permet de comparer :
- le mode **déterministe** (référence V&V)
- et le mode **assisté par IA** (suggestion-only, gouverné)

---

## 1) Inputs (datasets)

Exports représentatifs DOORS / Polarion :

- Exigences : `assets/inputs/requirements.csv`
- Cas de test : `assets/inputs/tests.csv`

---

## 2) Mode **Sans IA** — matrice + KPI (déterministe)

Traçabilité et KPI calculés **sans IA**.

- Rapport HTML : `assets/outputs_no_ai/rapport.html`
- Matrice CSV : `assets/outputs_no_ai/traceability_matrix.csv`
- KPI CSV : `assets/outputs_no_ai/kpi_summary.csv`

➡️ Référence V&V : **reproductible, auditable, défendable en audit**.

---

## 3) Mode **Avec IA** — suggestions gouvernées (optionnel)

Même pipeline, avec en plus des **suggestions IA** (aucune décision automatique).

- Rapport HTML : `assets/outputs_ai/raport.html`
- Matrice CSV : `assets/outputs_ai/traceability_matrix.csv`
- KPI CSV : `assets/outputs_ai/kpi_summary.csv`
- (optionnel) Suggestions IA : `assets/outputs_ai/ai_suggestions.csv`

➡️ L’IA **n’altère pas** la matrice ni les KPI : elle **propose uniquement**.

---

## 4) Screenshots (PNG)

Captures prêtes pour aperçu GitHub :

- Sans IA : `assets/screenshots/no_ai_report.png`
- Avec IA : `assets/screenshots/ai_report.png`

---

## 5) Exécution locale (optionnelle) — génération runtime

### Sans IA (déterministe)
```powershell
$env:ENABLE_AI="0"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

### Avec IA (optionnel, avancé)
```powershell
. .\tools\load_env_secret.ps1
$env:ENABLE_AI="1"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

> ➡️ Scénario 2–3 min : docs/demo_scenario.md