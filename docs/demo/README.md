# APP1 QRA — Demo Pack (Recruteur)

Ce dossier contient une **démonstration complète consultable sans exécuter le code**.

Il permet de comparer :
- le moteur **déterministe** de qualité des exigences
- et la version **assistée par IA** (suggestion-only)

---

## 1) Input

Fichier d’entrée commun aux deux modes :

- `assets/inputs/demo_input.csv`

Il représente un export typique DOORS / Polarion (exigences système).

---

## 2) Mode **Sans IA** — moteur déterministe

Analyse basée **uniquement sur les règles métier QRA** (pas d’IA).

- Rapport HTML :  
  `assets/outputs_no_ai/rapport.html`

- Export CSV :  
  `assets/outputs_no_ai/results.csv`

Contenu :
- scores de qualité
- statuts OK / À risque
- défauts détectés (ambiguïté, testabilité, critères d’acceptation…)

➡️ C’est la **référence V&V** (reproductible, auditée, traçable).

---

## 3) Mode **Avec IA** — suggestions gouvernées

Même moteur déterministe, avec en plus des **suggestions IA non décisionnelles**.

- Rapport HTML :  
  `assets/outputs_ai/rapport.html`

- Export CSV :  
  `assets/outputs_ai/results.csv`

Contenu supplémentaire :
- reformulations proposées
- exemples de critères d’acceptation
- compléments de vérifiabilité

➡️ L’IA **n’altère jamais les scores** ni les statuts, elle **propose uniquement**.

---

## 4) Gouvernance IA (résumé)

- IA **désactivée par défaut**
- Activation contrôlée via variable d’environnement `ENABLE_AI`
- Clé absente ou invalide → **fallback strict**
- Le moteur QRA reste **100 % déterministe**

➡️ L’IA est un **assistant**, jamais un décideur.

---

## 5) Lecture rapide

Pour une revue rapide en entretien :

- Sans IA → `assets/outputs_no_ai/rapport.html`
- Avec IA → `assets/outputs_ai/rapport.html`

Des captures PNG sont fournies dans :
`assets/screenshots/`

---

## 6) Exécution locale (optionnelle) — outputs runtime

Si l’on exécute l’outil localement (`python -m vv_app1_qra.main`), il peut générer :
- des **outputs runtime legacy timestampés** (ex: `qra_output_*.html` / `*.csv`) dans `data/outputs/`
- et/ou un **rapport stable** (`rapport.html` + `results.csv`) selon le mode de génération.

➡️ Pour un recruteur, la référence “sans exécuter” reste :
- `assets/outputs_no_ai/rapport.html`
- `assets/outputs_ai/rapport.html`
