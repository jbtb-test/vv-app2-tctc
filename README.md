# APP2 — TCTC  
**Traceability & Test Coverage Tool (V&V Demonstrator)**

## 🎯 Objectif

APP2 démontre une maîtrise industrielle de la **traçabilité Exigences ↔ Cas de test** et du **pilotage de la couverture de tests**, au cœur du **V-cycle V&V**.

L’application permet de :

- Construire automatiquement une **matrice de traçabilité**
- Calculer des **KPI de couverture fiables**
- Détecter les anomalies de traçabilité :
  - exigences non couvertes
  - cas de test orphelins
- Proposer (optionnellement) des **suggestions de liens via IA**, sans jamais décider à la place de l’ingénieur

> Positionnement : **outil d’analyse V&V**, pas un générateur automatique de vérité.

## 🧠 Principes de conception (V&V first)

- ✅ **Moteur déterministe prioritaire**
- 🤖 **IA optionnelle**
  - désactivée par défaut
  - non bloquante
  - non décisionnelle
- 📊 **Résultats explicables**
- 🧪 **Tests unitaires systématiques**
- 📁 Séparation stricte :
  - `data/outputs/` → runtime (gitignore)
  - `docs/outputs_demo/` → résultats figés pour revue recruteur

## 📥 Entrées

### Dataset Exigences (CSV)

Exemple :

```csv
requirement_id,title,criticality
REQ-001,Authentification utilisateur,HIGH
REQ-002,Gestion des sessions,MEDIUM
```

### Dataset Cas de test (CSV)

```csv
test_id,title,linked_requirements
TC-01,Test login valide,REQ-001
TC-02,Test expiration session,REQ-002
```

## Traitements principaux

1. Validation des datasets
- unicité des IDs
- existence des liens
- rejet contrôlé des données invalides

2. Construction de la matrice de traçabilité
- exigences ↔ tests
- vue bidirectionnelle

3. Calcul des KPI
- taux de couverture des exigences
- taux de tests liés
- exigences critiques non couvertes

4. Analyse des écarts
- exigences sans tests
- tests sans exigences

5. IA optionnelle (désactivée par défaut)
- suggestion de liens potentiels
- basée sur similarité sémantique
- aucune création automatique ou modification de lien

## KPI produits (exemples)

- Coverage exigences : 85 %
- Exigences critiques non couvertes : 1
- Tests orphelins : 2
- Taux de traçabilité bidirectionnelle : 100 %

> Tous les KPI sont recalculables, traçables, auditables.

## Sorties

1. Formats
- CSV (matrice, KPI)
- HTML (rapport lisible en 2 minutes)

2. Emplacements
- data/outputs/ : exécution locale
- docs/outputs_demo/ : snapshots commités pour démonstration GitHub

## Qualité & tests

1. Tests unitaires couvrant :
- validation des données
- calcul des KPI
- détection des écarts

2. Aucun effet de bord

3. Reproductibilité garantie