# LOT A — Rapport de tests

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Environnement : Python fourni par Codex, syntaxe validée pour Python 3.10
- Réseau : interdit et neutralisé dans les tests

## Résultats

### Tests ciblés

- Connecteurs CARSAT, France Chimie, ANACT et Droit local
- Connector Platform
- Document Registry
- alimentation metadata-only
- Runtime des connecteurs officiels
- Connector Adapter et Core
- confidentialité et absence de réseau

Résultat : **495 réussites et 37 sous-tests réussis**, aucun échec.

Les 7 tests Runtime propres aux quatre nouveaux raccordements réussissent également lorsqu'ils sont exécutés isolément.

### Scénarios LOT A

Résultat : **4/4 scénarios réussis**.

- CARSAT activé avec citations ;
- France Chimie activé avec citations ;
- ANACT activé avec citations ;
- Droit local activé avec citations ;
- aucune activation injustifiée sur le scénario témoin ;
- aucun fallback `OFFICIAL_CONNECTORS_NO_RESULT` sur les quatre scénarios pertinents.

### Tests du répertoire `tests`

Résultat : **983 réussites**, aucun échec.

### Suite complète

Résultat : **2 449 réussites, 128 sous-tests réussis et 3 échecs historiques qualifiés** en 28,97 secondes.

Échecs historiques inchangés :

- `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
- `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
- `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Aucun nouvel échec n'est introduit par le LOT A.

## Contrôles

- persistance JSON déterministe : réussie ;
- synchronisation initiale et incrémentale : réussie ;
- idempotence : réussie ;
- mises à jour et suppressions logiques : réussies ;
- domaines et HTTPS : conformes ;
- identifiants stables et absence de doublons : conformes ;
- citations métier : 10/10 exploitables ;
- contenu intégral, HTML, PDF et chunks : absents ;
- données confidentielles : absentes ;
- appels réseau dans les tests : absents ;
- passage Connector Adapter / Core / orchestrateur : réussi ;
- `git diff --check` : réussi ;
- syntaxe Python 3.10 : conforme.

## Fallbacks et anomalies restantes

- Fallbacks supprimés : 4 chemins `OFFICIAL_CONNECTORS_NO_RESULT`, un par scénario/connecteur pertinent.
- Fallbacks propres au LOT A restants : 0 lorsque les métadonnées pertinentes sont présentes.
- Anomalies nouvelles : 0.
- Anomalies historiques : 3, inchangées et hors périmètre.

## Verdict

**LOT A VALIDÉ**
