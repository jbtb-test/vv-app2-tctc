# APP2 — Validation intégration IA (2.11.R1)

## Objectif

Ce document interne décrit et valide l’intégration de l’IA dans l’application **APP2 – TCTC (Test-Case Traceability Checker)**.

Il est destiné :
- à moi-même (mémoire projet),
- à la préparation d’entretien technique,
- à justifier une intégration IA **maîtrisée, non bloquante et auditable**.

⚠️ Ce document n’est **pas destiné au recruteur** (le recruteur voit le README et les outputs).

Objectif de la version **2.11** :
- intégrer des **suggestions IA optionnelles** pour proposer des liens manquants (REQ ↔ TC),
- sans jamais remettre en cause le calcul déterministe (matrice + KPI),
- sans dépendance forte à la disponibilité de l’IA.

---

## Architecture

### Vue globale du repo
```text
vv-app2-tctc/
├─ src/
│ └─ vv_app2_tctc/
│    ├─ main.py           # CLI
│    ├─ models.py         # Requirement, TestCase, TraceLink
│    ├─ traceability.py   # Matrice Req ↔ Test (déterministe)
│    ├─ kpi.py            # KPI couverture (déterministe)
│    ├─ ia_assistant.py   # Suggestions IA (optionnelles)
│    └─ report.py         # (à venir 2.12) exports HTML/CSV
│
├─ data/
│ ├─ inputs/
│ │  ├─ requirements.csv
│ │  └─ tests.csv
│ └─ outputs/
│    └─ (snapshots générés par la CLI)
│
├─ tests/
│ ├─ test_env_check.py
│ ├─ test_kpi.py
│ └─ test_ia_assistant.py
│
├─ .env.secret            # Clé OpenAI (non committée)
└─ README.md
```

### Principe architectural clé

- **Le moteur principal est déterministe (matrix + KPI).**
- L’IA est un module optionnel, appelé uniquement si explicitement activé.
- Aucune logique critique ne dépend de l’IA.
- L’IA ne modifie jamais la matrice ni les KPI : elle propose uniquement.

---

## Description pipeline

### Pipeline logique (ordre strict)
```text
CSV inputs (requirements.csv + tests.csv)
↓
Parsing / validation
↓
Construction matrice (déterministe)
↓
Calcul KPI couverture (déterministe)
↓
[Optionnel] IA – suggest_missing_links() -> suggestions de liens
↓
Rapport / exports (HTML/CSV) (à venir 2.12)
```

### Point clé

- **Les KPI de couverture sont calculés avant toute IA et restent la référence.**.

---

## Détail des CAS (0 → 4)

### CAS 0 — Baseline tests

**Objectif**  
Valider la stabilité du socle sans exécution CLI.

**Commande**
```bash
pytest -q
```

Résultat attendu
- Tous les tests passent
- Aucun accès IA
- Environnement stable

Résultat obtenu
- Tests OK (APP2)

### CAS 1 — CLI sans IA (mode déterministe)

**Variables**
- ENABLE_AI=0
- OPENAI_API_KEY non définie

**Commande**
```powershell
$env:ENABLE_AI="0"
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

Attendu :
- log AI : disabled
- pas de ai_suggestions.csv
- report OK, matrice/KPI OK

Comportement
- Aucune tentative IA
- L’assistant retourne []
- Aucun impact sur matrice/KPI

Résultat
- Suggestions IA : vide
- Déterminisme garanti

###  CAS 2 — IA demandée sans clé

**Variables**
- ENABLE_AI=1
- OPENAI_API_KEY absente

**Commandes (PowerShell)**
```powershell
$env:ENABLE_AI="1"
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

Attendu :
- log warning “AI requested … missing key -> fallback []”
- ai_suggestions_count = 0
- ai_suggestions_csv = None
- report/matrice/KPI générés identiques

Comportement
- IA demandée mais clé absente
- Log warning explicite
- Fallback propre []
- Aucun crash

Résultat attendu (R1)
- Résultats identiques au mode IA off (pas de suggestions AI)
- CI reste verte

###  CAS 3 — IA réelle (clé valide)

**Variables**
- ENABLE_AI=1
- OPENAI_API_KEY valide
- OPENAI_MODEL configuré

**Commandes (PowerShell)**
```powershell
# Activer l'environnement Python
.\venv\Scripts\activate.ps1

. .\tools\load_env_secret.ps1
$env:ENABLE_AI="1"
python -m vv_app2_tctc.main --out-dir data/outputs --verbose
```

Attendu :
- ai_suggestions.csv présent
- ai_suggestions_count > 0 (si dataset déclenche suggestion)
- report OK

Comportement
- Matrice + KPI calculés (déterministes)
- Appel IA uniquement ensuite
- Suggestions ajoutées comme "propositions" (pas d’auto-modif)

Résultat attendu
- Suggestions possibles pour exigences non couvertes
- Aucune modification des KPI/matrice

🔒 Sécurité :
- La clé OpenAI n’est jamais écrite dans la documentation ni dans le code.
- Elle est uniquement chargée dynamiquement via le fichier `.env.secret`,
- protégé par `.gitignore` et non versionné.

###  CAS 4 — IA invalide (clé erronée)

**Objectif**
Garantir que l’app et la CI ne dépendent pas de l’IA.

Cas possibles :
- openai-python non installé
- clé invalide (401)
- erreur réseau

Comportement
- Exception catchée
- fallback []
- pipeline continue

---

## Variables d’environnement

| Variable | Rôle |
|--------|------|
| ENABLE_AI | Active / désactive l’IA |
| OPENAI_API_KEY | Clé API OpenAI |
| OPENAI_MODEL | Modèle utilisé (si IA active) |


Règles
- ENABLE_AI=0 → IA ignorée
- ENABLE_AI=1 + clé absente → fallback
- ENABLE_AI=1 + SDK absent → fallback
- La clé n’est jamais committée

---

## Règles de sécurité IA

Principes appliqués :

1. **IA non bloquante**
- Toute erreur IA est catchée
- Fallback systématique

2. **IA non décisionnelle**
- Le score est calculé uniquement par les règles
- IA n’altère jamais statut / KPI / matrice

3. **IA auditable**
- Suggestions structurées (requirement_id, test_id, rationale, confidence optionnelle)
- Traçable dans les exports/rapport (2.12)

4. **IA optionnelle**
- Désactivable par variable d’environnement
- Aucun impact sur la CI

---

## Conclusion

L’intégration IA APP2 TCTC respecte les objectifs suivants :
- ✅ Robustesse (CAS 0 → CAS 4)
- ✅ Séparation claire déterministe / IA
- ✅ IA non critique et non bloquante
- ✅ Résultats auditables
- ✅ Architecture défendable en contexte V&V / QA

>  L’IA agit comme un assistant de traçabilité, jamais comme un décideur.

