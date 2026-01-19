# APP2 — TCTC — FAQ Recruteur

---

## À quoi sert APP2 — TCTC ?

À **automatiser et objectiver** la traçabilité entre :
- exigences
- cas de test

et à produire des **KPI de couverture exploitables**.

---

## Dois-je exécuter le code pour comprendre la démo ?

Non.

Un **pack démo figé** est fourni dans `docs/demo/` :
- HTML
- PNG
- CSV

Il est **consultable directement sur GitHub**.

---

## L’outil dépend-il d’une IA ?

Non.

- Le mode par défaut est **sans IA**
- Les résultats sont **déterministes et reproductibles**
- L’IA est **optionnelle**

---

## Que fait exactement l’IA ?

Uniquement des **suggestions de liens manquants**.

- Aucune création automatique
- Aucune modification de la matrice
- Aucune décision prise par l’IA

➡️ *Suggestion-only, jamais décisionnelle.*

---

## Que se passe-t-il si l’IA est absente ou mal configurée ?

Fallback strict :
- pas d’erreur bloquante
- mêmes résultats qu’en mode sans IA
- pipeline entièrement fonctionnel

---

## Quels livrables sont produits ?

- Rapport HTML de synthèse
- Matrice de traçabilité (CSV)
- KPI de couverture (CSV)
- (optionnel) Suggestions IA (CSV)

---

## Pourquoi c’est pertinent en V&V ?

- Détection immédiate des trous de couverture
- Support aux revues et audits
- KPI objectifs pour le pilotage test
- Traçabilité exploitable hors outil (Excel, Jira, etc.)

---

## Est-ce un produit industriel ?

Non.

C’est un **démonstrateur V&V** destiné à illustrer :
- une architecture propre
- une démarche outillée
- une gouvernance IA maîtrisée
