# Résultats de baseline

Ce dossier contient les réponses brutes anonymisées et les évaluations des six
cas métier réels.

- `raw/` : enveloppes de réponses publiques Nexus, sans attentes d'évaluation
  ni issues connues, réduites aux éléments visibles et utiles à l'évaluation ;
- `baseline-assessment.json` : évaluation sémantique motivée ;
- `baseline-results.json` : scores calculés et verdicts ;
- `BASELINE.md` : rapport lisible.

Les fichiers bruts sont régénérés avec :

```text
python tools/run_real_business_cases_baseline.py run
```

Le rapport est ensuite régénéré avec :

```text
python tools/run_real_business_cases_baseline.py evaluate
```

Si d'anciennes réponses contiennent encore les payloads runtime complets, leur
projection fidèle peut être réduite avec :

```text
python tools/run_real_business_cases_baseline.py compact
```
