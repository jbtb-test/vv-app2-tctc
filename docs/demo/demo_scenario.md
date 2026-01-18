# Scénario de démonstration — APP2 TCTC (2–3 minutes)

Ce scénario est conçu pour une **démonstration courte en entretien ou audit**.  
Il montre la valeur de l’outil pour le **pilotage de la traçabilité et de la couverture de tests**,
**sans dépendance à l’IA** (mode par défaut).

---

## Objectif de la démo

- Illustrer la **construction automatique de la matrice de traçabilité**
- Montrer des **KPI de couverture objectifs**
- Montrer des **outputs concrets** (CSV + HTML)
- Insister sur la **maîtrise humaine** et la **non-décision IA**

---

## Pré-requis (avant entretien)

- Repository cloné
- Environnement Python prêt
- Fichiers :
  - `data/inputs/requirements.csv`
  - `data/inputs/tests.csv`
- IA désactivée (`ENABLE_AI=0`)

---

## Script chronométré

### ⏱️ 0:00 – 0:30 — Contexte

> « Je pars d’un petit export d’exigences et de cas de test,
> typiquement issu de DOORS ou Polarion.
> La couverture et la traçabilité sont souvent maintenues manuellement,
> ce qui est coûteux et peu fiable.
> L’objectif ici est de **les objectiver et les démontrer**. »

*(Aucune manipulation à l’écran)*

---

### ⏱️ 0:30 – 1:00 — Lancement du pipeline

Commande exécutée :

```bash
python -m vv_app2_tctc.main --verbose
```

**Le pipeline est entièrement déterministe. Aucune IA n’est utilisée pour détecter ou scorer les défauts.**

### ⏱️ 1:00 – 1:45 — Résultats CSV

Ouvrir les fichiers CSV générés :
- Matrice de traçabilité
- KPI de couverture

**Chaque exigence et chaque test est traçable.Les exigences non couvertes et les tests orphelins sont visibles immédiatement.**

C’est un support orienté audit et pilotage V&V.

### ⏱️ 1:45 – 2:30 — Rapport HTML

Ouvrir le rapport HTML localement.

**Ce rapport est lisible sans outil spécifique.Il synthétise la matrice et les KPI pour une revue rapide.**

Points à montrer :
- taux de couverture
- exigences non couvertes
- clarté de la matrice

### ⏱️ 2:30 – 3:00 — Conclusion

**L’outil ne prend aucune décision.Il mesure, structure et met en évidence les écarts.**
**La décision reste entièrement humaine.**

Optionnel :

**L’IA peut être activée uniquement pour suggérer des liens manquants,sans impact sur la matrice ni les KPI.**

APP2 TCTC est un outil de pilotage de la traçabilité :
- déterministe
- mesurable
- démontrable
- défendable en audit

**L’ingénieur V&V reste au centre de la décision.**