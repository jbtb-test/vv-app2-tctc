# Architecture — APP2 TCTC (Traceability & Test Coverage Tool)

> Démo recruteur (sans exécuter le code) : voir `docs/demo/README.md`

## 1. Objectif

APP2 TCTC est une application de **traçabilité Exigences ↔ Cas de test**
(ex. exports DOORS / Polarion), basée sur un **pipeline déterministe**
avec **assistance IA optionnelle et non décisionnelle**.

L’objectif est de :

- construire automatiquement une **matrice de traçabilité**
- calculer des **KPI de couverture fiables**
- détecter les écarts (exigences non couvertes, tests orphelins)
- produire des **preuves auditables** (CSV, HTML)
- garantir une **maîtrise humaine totale** des décisions

APP2 TCTC est conçu comme un **outil d’aide au pilotage de la couverture**,
et non comme un moteur de décision automatisé.

---

## 2. Principes d’architecture

Principes directeurs :

- **Déterminisme prioritaire**
- **Traçabilité complète** (datasets → règles → KPI → rapports)
- **Lisibilité audit / entretien**
- **Aucune dépendance IA par défaut**
- **Exécution locale reproductible**

L’architecture privilégie la robustesse, l’auditabilité et la démonstrabilité.

---

## 3. Vue d’ensemble du pipeline

L’application suit un **pipeline linéaire**, exécutable en ligne de commande,
inspiré d’une logique V-cycle (outillage, règles testées, résultats vérifiables).

```text
CSV exigences        CSV cas de test
     |                     |
     v                     v
[ Parser CSV ]     [ Parser CSV ]
          |         |
          +----+----+
               |
               v
        [ Modèles métier ]
               |
               v
     [ Validation des datasets ]
               |
               v
   [ Matrice de traçabilité ]
               |
               +----------------------+
               |                      |
               v                      v
        [ KPI couverture ]     [ IA (optionnelle) ]
               |                      |
               +----------+-----------+
                          |
                          v
                   [ Agrégation ]
                          |
                          v
                  [ Rapport CSV ]
                          |
                          v
                  [ Rapport HTML ]
                          |
                          v
                   Revue humaine
```

---

## 4. Description des composants

### 4.1 Entrée — CSV exigences

- Fichier CSV standardisé (data/inputs/requirements.csv, tests.csv)
- Colonnes attendues documentées
- Aucune dépendance à un outil propriétaire

### 4.2 Parser CSV

- Implémenté dans main.py
- Rôle :
	- lire le CSV
	- valider la structure minimale
	- transformer chaque ligne en objet métier
Aucune logique métier n’est appliquée à ce stade.

### 4.3 Modèles métier

- Implémentés dans models.py
- Responsabilités :
	- représenter une exigence
	- représenter un cas de test
	- représenter un lien de traçabilité
Les modèles sont simples, explicites et testables.

###  4.4 Validation des datasets

- Implémentée dans validators.py
- Vérifie notamment :
	- unicité des IDs
	- existence des références
	- cohérence des liens

Les données invalides sont rejetées avant toute analyse.

###  4.5 Matrice de traçabilité

- Implémentée dans traceability.py
- Construit la relation Requirement ↔ TestCase
- Base unique pour tous les KPI et rapports

C’est le cœur déterministe de l’application.

###  4.6 Calcul des KPI de couverture

- Implémenté dans kpi.py
- Exemples :
	- % d’exigences couvertes
	- nombre d’exigences non couvertes
	- nombre de tests orphelins

Les KPI sont purement déterministes et auditables.

###  4.7 Assistance IA (optionnelle)

- Implémentée dans ia_assistant.py
- Désactivée par défaut
- Rôle strictement limité à :
	- suggérer des liens potentiels manquants

Contraintes fortes :
- aucune création automatique de lien
- aucune modification de la matrice
- aucun impact sur les KPI

L’IA est un outil d’aide, jamais une autorité.

###  4.8 Agrégation des résultats

- Centralisation de :
	- la matrice
	- les KPI
	- les suggestions IA (si activée)

Préparation des données pour export

###  4.9 Rapports

CSV
- Matrice de traçabilité
- KPI de couverture
- Exploitables par Excel, ALM, outils QA

HTML
- Généré via report.py
- Lisible localement (sans serveur)
- Support principal de démonstration en entretien

---

## 5. Exécution

Commande principale :
```bash
python -m vv_app2_tctc.main --verbose
```

Résultats :
- Matrice CSV
- KPI CSV
- Rapport HTML
- Logs explicites

---

## 6. Non-objectifs (assumés)

APP2 TCTC ne vise pas à :
- remplacer un ingénieur V&V
- certifier automatiquement une couverture
- créer ou modifier des liens sans validation humaine
- dépendre d’une IA pour fonctionner

Ces choix sont volontaires et alignés avec un usage industriel maîtrisé.

---

## 7. Positionnement entretien / audit

APP2 TCTC démontre :
- une approche traçabilité & couverture outillée
- une maîtrise du déterminisme
- une intégration raisonnée de l’IA
- une capacité à produire des preuves concrètes

L’outil est conçu pour être compris en quelques minutes, sans prérequis techniques.