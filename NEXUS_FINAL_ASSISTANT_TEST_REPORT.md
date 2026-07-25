# Rapport de tests — Assistant final CFDT Nexus

## Couverture prévue

- contrats immuables et API publique ;
- normalisation et détection des dix domaines ;
- planification, limites et flags ;
- orchestration, isolation d’erreur et absence de contamination ;
- adaptation des sorties ;
- contradictions et sources ;
- questions dédupliquées ;
- modes rapide, dossier et expert ;
- synthèse et brouillons ;
- contradicteur ;
- confidentialité, anonymisation et blocage ;
- Runtime actif, inactif et fallback ;
- vingt scénarios d’intégration ;
- non-régression du routeur, des moteurs, du Runtime et de l’interface.

## Politique

Fixtures exclusivement synthétiques. Aucun réseau, document réel ou donnée personnelle réelle. Les trois anomalies historiques ne sont acceptables que strictement inchangées. Aucun nouvel échec n’est accepté.

## Résultats

- Assistant Final : 62 réussites.
- Routeur historique : 13 réussites.
- Orchestrateur commun : 14 réussites.
- Syndical Reasoning R0–R2C : 362 réussites.
- Expert Paie V2 : 46 réussites.
- CSE Memory : 78 réussites.
- Runtime : 186 réussites.
- Répertoire `tests/` : 1 469 réussites.
- Suite complète : 2 946 réussites et 128 sous-tests réussis.
- Syntaxe de l’intégration JavaScript : valide.
- Syntaxe Python 3.10 des fichiers du lot : valide.
- Nouvel échec : aucun.

Les trois anomalies historiques reproduites sont :

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Le script HTTP autonome de l’interface atteint le serveur avec un statut 200, puis s’arrête sur sa précondition historique `answer["sources"]` : le corpus local de classification est absent ou non indexé dans cet environnement. Cette précondition se situe avant l’intégration Assistant Final et le flag est désactivé ; les 186 tests Runtime, dont les tests serveur, confirment l’absence de régression de l’interface.
