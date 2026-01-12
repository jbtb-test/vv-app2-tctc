# Architecture — APP2 TCTC (Traceability & Test Coverage Tool)

## Objectif
APP2 TCTC est une application de **traçabilité Exigences ↔ Cas de test** et de **pilotage de la couverture de tests**
(type DOORS / Polarion), basée sur un pipeline déterministe, avec **assistance IA optionnelle et non décisionnelle**.

L’objectif est de :
- construire automatiquement une matrice de traçabilité
- calculer des KPI de couverture fiables
- détecter les écarts de traçabilité (exigences non couvertes, tests orphelins)
- conserver une **maîtrise humaine totale** des décisions

## Vue d’ensemble

L’application suit un **pipeline linéaire**, exécutable en CLI, conforme à une logique V-cycle
(outillage, règles testées, outputs traçables).

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
