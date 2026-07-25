# Audit — Validation contrôlée CFDT Nexus V1

SHA audité : `76669f471b1837e32d6320e8676e9455e85b8d06`.

## 1. Isolation de l’adaptateur Paie

- Test : `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`.
- Composant : `automation.adapters.payroll`.
- Attendu : l’import isolé ne charge ni Connector Platform, ni CSE Memory, ni Protection Sociale.
- Observé : la suite complète inspectait l’intégralité de `sys.modules`, déjà alimentée par la collecte d’autres tests.
- Cause : mesure d’un état global antérieur au lieu des effets de l’import audité.
- Caractère historique : dépendant de l’ordre de collecte et reproductible sans violation statique dans l’adaptateur.
- Risque fonctionnel : nul ; risque d’architecture : faux signal masquant une future régression réelle.
- Correction minimale : exécuter l’import et l’assertion inchangée dans un sous-processus Python neuf.
- Risque de régression : faible.
- Tests : test ciblé, ordre inverse, répétition, suite complète.

## 2. Isolation des contrats communs

- Test : `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`.
- Composant : `automation.contracts`.
- Attendu : l’import des contrats ne charge aucun domaine, expert Paie ou Connector Platform.
- Observé : `automation.experts` figurait déjà dans `sys.modules` après la collecte globale.
- Cause : assertion sur l’état partagé du processus pytest, sans isolation temporelle.
- Caractère historique : strictement dépendant de l’ordre ; les imports statiques des contrats respectent déjà ARCH-01.
- Risque fonctionnel : nul ; risque d’architecture : faux positif et résultat non reproductible.
- Correction minimale : conserver la frontière vérifiée dans un sous-processus neuf.
- Risque de régression : faible.
- Tests : test ciblé, répétition, suite complète.

## 3. Fallback du référentiel Paie

- Test : `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`.
- Composants : `automation.experts.paie` et `automation.payroll.payroll_referential_integration`.
- Attendu : l’échec du référentiel facultatif produit `available = false` tout en conservant le payload Paie historique.
- Observé : selon l’ordre des imports, le test modifiait `automation.payroll.payroll_referential_integration` alors que l’expert détenait l’alias distinct `payroll.payroll_referential_integration`.
- Cause : double identité de module créée par un import top-level prioritaire lorsque `automation/` était ajouté à `sys.path`.
- Caractère historique : dépendant du chemin d’import et de l’ordre de chargement.
- Risque fonctionnel : moyen ; un monkeypatch, une injection ou un fallback pouvait viser une autre instance du module.
- Risque d’architecture : moyen ; deux singletons de module incompatibles.
- Correction minimale : importer d’abord le chemin canonique `automation.payroll`, conserver le chemin top-level uniquement en repli.
- Risque de régression : faible, l’API publique ne change pas.
- Tests : échec injecté, payload historique, tests Paie et suite complète.

## Chargement des moteurs optionnels

L’audit a également confirmé que la façade Runtime importait Assistant Final et Expert Paie V2 au chargement, même avec les flags désactivés. Les exports publics sont désormais paresseux, le serveur ne charge l’Assistant Final qu’après lecture d’un flag actif et Expert Paie V2 n’est importé que si son runner est réellement exécuté. Les API publiques restent identiques.

## Précondition HTTP historique

Le script HTTP autonome peut toujours recevoir une réponse sans `answer["sources"]` lorsque le corpus local de classification n’est pas installé. Cette précondition se situe dans le routeur documentaire, avant l’Assistant Final. La campagne HTTP synthétique injecte explicitement une source publique fictive et valide le parcours complet. Une correction du corpus réel élargirait le présent lot.
