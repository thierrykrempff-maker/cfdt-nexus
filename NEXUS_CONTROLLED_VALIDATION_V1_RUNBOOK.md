# Runbook — Validation contrôlée CFDT Nexus V1

## Restrictions

Utiliser uniquement des fixtures fictives explicitement marquées synthétiques. Aucun dossier, document, nom, identifiant ou secret réel n’est autorisé.

## Lancement standard

Depuis la racine, avec Python 3.10 :

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python tools/run_nexus_controlled_validation.py `
  --final-assistant-enabled true `
  --expert-paie-v2-enabled true
```

Les rapports sont écrits dans :

- `NEXUS_CONTROLLED_VALIDATION_V1_MATRIX.json`
- `NEXUS_CONTROLLED_VALIDATION_V1_RESULTS.md`

## Matrice des configurations

```powershell
# A — historique seul
python tools/run_nexus_controlled_validation.py --final-assistant-enabled false --expert-paie-v2-enabled false

# B — Assistant Final sans Paie V2
python tools/run_nexus_controlled_validation.py --final-assistant-enabled true --expert-paie-v2-enabled false

# C — Assistant Final et Paie V2 explicitement autorisés
python tools/run_nexus_controlled_validation.py --final-assistant-enabled true --expert-paie-v2-enabled true

# D — historique ; flag Paie V2 seul
python tools/run_nexus_controlled_validation.py --final-assistant-enabled false --expert-paie-v2-enabled true
```

Ces options appartiennent au harness. Elles ne changent jamais les valeurs par défaut du Runtime.

## Lecture des scores

- 90–100 : excellent ;
- 80–89 : utilisable ;
- 70–79 : à revoir ;
- moins de 70 : non acceptable.

Un incident dur de confidentialité, calcul interdit, diagnostic, qualification automatique sensible ou crash global rend le cas non acceptable indépendamment du score.

## Ajouter un cas

Ajouter un objet à `NEXUS_CONTROLLED_VALIDATION_V1_CASES.json`, avec un identifiant unique et tous les champs contrôlés par `test_nexus_controlled_validation_cases.py`. Ne jamais copier un dossier réel.

## Retour au comportement historique

Ne définir ni `NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED` ni `NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED`, ou leur donner la valeur `false`. Le serveur conserve alors le rapport historique.

## Tests

```powershell
python -m pytest -q tests/test_nexus_controlled_validation_*.py tests/test_nexus_historical_anomalies_fixed.py
```

La validation finale exige ensuite toutes les suites moteurs, Runtime, interface, `tests/` et la suite complète.
