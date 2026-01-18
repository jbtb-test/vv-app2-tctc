# APP2 — TCTC — Pitch entretien (2–3 minutes)

## Contexte

Dans les projets de validation et vérification,
la gestion de la **traçabilité exigences ↔ tests**
et de la **couverture de tests** est souvent :

- manuelle (Excel, exports hétérogènes),
- fragile (liens incomplets ou obsolètes),
- difficile à objectiver en audit.

Cela entraîne :
- des exigences non couvertes,
- des cas de test orphelins,
- une vision floue de la couverture réelle.

APP2 — TCTC est un **outil de démonstration**
qui outille cette problématique de manière pragmatique.

---

## Objectif de l’outil

L’objectif est de **construire automatiquement**
une matrice de traçabilité exigences ↔ cas de test
et d’en dériver des **KPI de couverture objectifs**, afin de :

- détecter immédiatement les trous de couverture,
- identifier les tests orphelins,
- objectiver l’état de la traçabilité.

Les données d’entrée sont des exports simples
issus d’outils comme DOORS, Polarion ou Jira (CSV).

---

## Principe clé

Le cœur de l’outil est **entièrement déterministe**.

- La matrice de traçabilité est calculée explicitement
- Les KPI sont reproductibles
- Les résultats sont auditables

L’IA est :
- **désactivée par défaut**
- **strictement non décisionnelle**
- utilisée uniquement pour proposer des **suggestions de liens manquants**

L’outil fonctionne **intégralement sans IA**.

---

## Démonstration

À partir de deux fichiers CSV simples :
- exigences
- cas de test

APP2 — TCTC génère automatiquement :

- une matrice de traçabilité (CSV),
- un résumé KPI de couverture (CSV),
- un rapport HTML lisible immédiatement.

Un rapport HTML de démonstration est fourni dans  
`docs/demo/assets/outputs_no_ai/rapport.html`  
(voir `docs/demo/README.md`).

---

## Valeur ajoutée

APP2 — TCTC permet :

- une vision immédiate de la couverture réelle,
- une détection automatique des incohérences de traçabilité,
- des indicateurs objectifs utilisables en revue et audit,
- une intégration IA maîtrisée, optionnelle et défendable.

---

## Conclusion

APP2 — TCTC ne remplace pas
la stratégie de test ni le jugement de l’ingénieur V&V.

Il **structure**, **objectivise** et **sécurise**
la gestion de la traçabilité et de la couverture.

👉 Je peux vous montrer soit le **rapport HTML de démonstration**,  
👉 soit l’**exécution locale du pipeline**, en quelques secondes.
