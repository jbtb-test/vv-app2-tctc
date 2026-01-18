# APP2 — TCTC — Walkthrough de démonstration (2–3 minutes)

Ce walkthrough est conçu pour une **présentation courte en entretien**
ou lors d’une revue V&V / audit.

Il permet de démontrer la valeur de l’outil **sans exécuter le code**.

---

## Objectif de la démo

- Illustrer la **traçabilité exigences ↔ tests**
- Montrer des **KPI de couverture mesurables**
- Démontrer une **IA maîtrisée, non décisionnelle**
- Mettre en avant une approche **V&V rigoureuse et auditable**

---

## Étape 1 — Démo sans exécution (recommandée)

Ouvrir directement les artefacts figés :

### Mode sans IA (déterministe)
- HTML : `docs/demo/assets/outputs_no_ai/rapport.html`
- PNG : `docs/demo/assets/screenshots/no_ai_report.png`

### Mode avec IA (suggestion-only)
- HTML : `docs/demo/assets/outputs_ai/rapport.html`
- PNG : `docs/demo/assets/screenshots/ai_report.png`

### Points à commenter (1–2 minutes)
- KPI couverture (taux + compteurs)
- Exigences **non couvertes**
- Tests **orphelins**
- Aperçu de la matrice Req ↔ TC
- Statut IA : *disabled* vs *enabled*

---

## Étape 2 — Exécution locale (optionnelle)

À faire uniquement si l’interlocuteur le demande.

### Sans IA (référence V&V)
```powershell
$env:ENABLE_AI="0"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

###  Avec IA (optionnel)
```powershell
. .\tools\load_env_secret.ps1
$env:ENABLE_AI="1"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

---

## Message clé à faire passer

- Les résultats sont déterministes par défaut
- Les KPI sont calculés, pas estimés
- L’IA ne modifie jamais la traçabilité : elle propose, l’humain décide

> 👉 L’ingénieur V&V reste responsable.