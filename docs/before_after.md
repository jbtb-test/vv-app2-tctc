# Avant / Après — Traçabilité & Couverture de tests

Ce document compare une **gestion manuelle de la traçabilité et de la couverture**
avec une **traçabilité outillée via APP2 TCTC**.

L’objectif est d’illustrer :
- les **gains concrets**
- les **limites assumées**
- la **maîtrise humaine conservée**

> Démo consultable : voir `docs/demo/README.md`

---

## Avant — Traçabilité manuelle classique

### Processus typique

1. Exigences gérées dans DOORS, Polarion ou Excel
2. Cas de test dans un outil séparé
3. Liens de traçabilité ajoutés manuellement
4. Calcul de la couverture via Excel ou requêtes ALM
5. Mise à jour manuelle avant chaque audit

### Avantages

- Expertise humaine complète
- Connaissance fine du système
- Arbitrage possible sur les cas ambigus

### Limites observées

- ⏱️ Mise à jour longue et coûteuse
- ❌ Risque élevé d’oubli de liens
- ❌ Exigences non couvertes non détectées à temps
- ❌ Tests orphelins fréquents
- ❌ KPI peu fiables ou obsolètes
- ❌ Démonstration difficile en audit ou entretien

---

## Après — Traçabilité outillée avec APP2 TCTC

### Processus outillé

1. Export CSV des exigences et des cas de test
2. Exécution locale du pipeline APP2 TCTC
3. Validation des datasets
4. Construction automatique de la matrice de traçabilité
5. Calcul des KPI de couverture
6. (Optionnel) Suggestions IA de liens manquants
7. Génération d’outputs structurés (CSV + HTML)
8. Revue humaine et décision

---

### Avantages concrets

- ⚡ Mise à jour immédiate de la couverture
- ✔️ Détection automatique des exigences non couvertes
- ✔️ Détection des tests orphelins
- ✔️ KPI de couverture fiables et reproductibles
- ✔️ Matrice de traçabilité claire
- ✔️ Support direct pour audit, revue et entretien

---

### Limites maîtrisées

- Ne remplace pas la stratégie de test
- Ne remplace pas l’analyse métier
- Ne décide jamais de la couverture acceptable

---

## Rôle de l’IA (optionnelle)

- Désactivée par défaut
- Fournit uniquement :
  - des suggestions de **liens potentiels** entre exigences et tests

L’IA :
- n’ajoute pas de lien automatiquement
- ne modifie pas la matrice
- n’influence pas les KPI

👉 Elle agit comme **assistant**, jamais comme arbitre.

---

## Comparatif synthétique

| Critère | Traçabilité manuelle | APP2 TCTC |
|------|--------------------|----------|
| Temps de mise à jour | Élevé | Faible |
| Couverture mesurée | Approximative | Exacte |
| Détection des écarts | Manuelle | Automatique |
| Traçabilité | Fragile | Forte |
| Reproductibilité | Faible | Élevée |
| KPI | Peu fiables | Calculés automatiquement |
| Décision humaine | Oui | Oui |
| IA décisionnelle | N/A | Non |

---

## Conclusion

APP2 TCTC ne remplace pas l’ingénieur V&V.  
Il **structure**, **sécurise** et **objectivise** la traçabilité et la couverture de tests.

👉 L’ingénieur reste **responsable de la décision**  
👉 L’outil apporte **cohérence, KPI et démonstrabilité**
