# APP2 — TCTC — Walkthrough de démonstration (2–3 minutes)

## Objectif

Guider une démonstration **claire, reproductible et maîtrisée**
de l’outil **APP2 — TCTC**, en contexte entretien ou audit V&V.

Ce walkthrough permet :
- d’adapter la démo au temps disponible,
- de répondre sereinement aux questions,
- d’éviter toute dérive technique inutile.

---

## Étape 1 — Démo sans exécution (recommandée en entretien)

Cette étape montre la valeur de l’outil **sans dépendre de l’environnement**.  
➡️ Elle s’appuie sur le **pack démo figé** dans `docs/demo/assets/`.

### Action

1) **Sans IA (déterministe)**
- Ouvrir : `docs/demo/assets/outputs_no_ai/rapport.html`
- Ou aperçu PNG : `docs/demo/assets/screenshots/no_ai_report.png`

2) **Avec IA (suggestion-only)**
- Ouvrir : `docs/demo/assets/outputs_ai/rapport.html`
- Ou aperçu PNG : `docs/demo/assets/screenshots/ai_report.png`

### À montrer

- KPI de couverture (taux + compteurs)
- exigences **non couvertes**
- tests **orphelins**
- aperçu de la matrice exigences ↔ tests
- statut IA (*disabled* vs *enabled*)

**Les KPI sont calculés à partir de règles explicites et traçables.**

### À éviter

- expliquer l’implémentation technique
- commenter le code
- justifier chaque lien individuellement

---

## Étape 2 — Exécution locale (optionnelle)

À utiliser uniquement si l’interlocuteur souhaite voir
le fonctionnement réel du pipeline.

### Commande (sans IA — référence V&V)

```powershell
$env:ENABLE_AI="0"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

Résultats générés (runtime) :
- matrice de traçabilité (CSV)
- résumé KPI (CSV)
- rapport HTML

À montrer
- rapidité d’exécution
- cohérence entre outputs runtime et démo

À éviter
- lire les logs
- expliquer chaque module

---

## Étape 3 — Exécution locale (optionnelle)

```powershell
. .\tools\load_env_secret.ps1
$env:ENABLE_AI="1"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

À montrer
- suggestions IA clairement identifiées
- KPI et matrice inchangés

 > L’IA ne modifie jamais la traçabilité. Elle suggère, l’humain décide.

---

## Conclusion

APP2 — TCTC est un outil :
- déterministe par conception,
- traçable et audit-ready,
- avec une IA maîtrisée et non décisionnelle.

👉 L’ingénieur V&V reste responsable de la décision.
👉 L’outil apporte objectivité, visibilité et démonstrabilité.