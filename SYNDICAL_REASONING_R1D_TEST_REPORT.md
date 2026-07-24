# Rapport de tests R1D

## Périmètre

- Modèles immuables et API publique.
- Douze scénarios synthétiques obligatoires.
- Chronologie et séparation faits/interprétations/ressentis/hypothèses.
- Critères protégés, mesures défavorables et comparateurs.
- Questions, preuves, urgences, stratégies et argumentation contradictoire.
- Articulation R1A/R1B/R1C/R1D.
- Runtime activé, désactivé et fail-safe.
- Confidentialité, absence de diagnostic médical et déterminisme.

## Exigences

Les tests doivent réussir sous une syntaxe compatible Python 3.10. La suite complète ne peut conserver que les trois anomalies historiques déjà qualifiées, strictement inchangées.

## Résultats

- R1D : 56 réussites.
- R0 : 15 réussites.
- R1A : 13 réussites.
- R1B : 30 réussites.
- R1C : 40 réussites.
- Runtime syndical R0 à R1D : 32 réussites.
- Orchestrateur commun : 14 réussites.
- Répertoire `tests/` : 1 177 réussites.
- Suite complète : 2 654 réussites et 128 sous-tests réussis.
- Nouveaux échecs : aucun.

Les trois échecs historiques restent strictement identiques :

- `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
- `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
- `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

`git diff --check`, l'import de l'API publique et la validation syntaxique Python 3.10 réussissent.
