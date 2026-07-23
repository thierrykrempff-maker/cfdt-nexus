# Nexus Runtime Integration — LOT 1

## Objet

Ce lot raccorde progressivement le parcours utilisateur local existant à Nexus Core V3 pour les domaines Juriste Travail et Expert Paie. Il conserve le rapport historique comme référence et comme solution de repli. Le raccordement est désactivé par défaut.

## Runtime avant le lot

Le point d'entrée réel est `apps/nexus-local-interface/server.py::analyze_question`. Il appelle `assistant_ds_router.py` par le module `experts/orchestrator.py`, exécute les experts historiques Juriste Travail et Paie, puis transmet leurs résultats à `experts/report_generator.py`. Le Core V3, le Payroll Adapter et le `CommonExpertOrchestrator` ne participaient pas à ce chemin utilisateur.

## Runtime après le lot

Le parcours historique reste exécuté en premier et sans modification de ses experts :

`question -> serveur local -> assistant_ds_router -> Juriste/Paie -> orchestration historique -> rapport historique`

Lorsque `NEXUS_CORE_RUNTIME_ENABLED=true`, une couche post-traitement ajoute le parcours suivant :

`sorties Juriste/Paie -> RuntimeExpertPayloadMapper -> PayrollAdapter + mapper Juriste minimal -> EngineRegistry/ExecutionPlanner/PipelineExecutor -> CommonExpertOrchestrator -> section Core délimitée dans le rapport existant`

Le serveur, le routeur et les experts ne sont ni dupliqués ni remplacés. Le Core reste indépendant de l'interface.

## Activation et repli

- Variable : `NEXUS_CORE_RUNTIME_ENABLED`.
- Valeur par défaut, valeur inconnue ou valeur fausse : `runtime_mode=legacy`.
- Exécution Core réussie : `runtime_mode=core_v3`.
- Payload incompatible ou erreur Core : `runtime_mode=core_v3_fallback`.

En mode legacy ou fallback, le mapper rend exactement l'objet rapport historique. Aucune exception, stack trace ou valeur utilisateur n'est placée dans les diagnostics. Les causes de repli sont des codes techniques stables.

## Mappings

### Juriste Travail

Le mapper local convertit uniquement les champs déjà présents : constats, risques, conclusions, recommandations, questions, limites et références documentaires. Il produit des `Evidence`, `Finding`, `Recommendation` et `DocumentReference` Core avec provenance. Il ne constitue pas un SDK juridique général et n'invente aucune donnée manquante.

### Expert Paie

Le mapper réutilise `legacy_payroll_report_to_expert_report`, puis instancie le véritable `NEXUS_ADAPTERS.payroll.PayrollAdapter`. Le résultat de l'adaptateur est comptabilisé dans les artefacts Core. Les absences, échecs et payloads mal formés provoquent soit une exécution partielle valide, soit un repli sûr selon le cas.

## Orchestration réelle

`RuntimeCoreIntegration` enregistre les moteurs d'adaptation disponibles dans le véritable `EngineRegistry`, produit un plan avec `ExecutionPlanner` et l'exécute avec `PipelineExecutor`. Il enregistre ensuite des façades immuables pour les rapports déjà calculés et appelle le véritable `automation.orchestrator_common.CommonExpertOrchestrator`.

## Rapport et compatibilité

Le rapport historique est toujours construit par le générateur existant. En succès Core uniquement, `RuntimeCoreReportMapper` ajoute une section `core_v3_runtime` et des marqueurs internes `generated_from`. Les sections, sources, accords INEOS, références Légifrance/JUDILIBRE/CDTN et conclusions historiques sont conservés.

## Diagnostics et confidentialité

Les diagnostics exposent exclusivement des booléens, des compteurs et un code de fallback : activation, experts exécutés, appels Adapter/Core/Common Orchestrator, nombres de preuves/constats/recommandations et état du repli. Ils ne contiennent ni question, ni payload, ni valeur salariale, ni identité, ni secret, ni contenu documentaire.

Les tests emploient seulement des données synthétiques et vérifient notamment le masquage des noms, adresses, matricules, NIR, IBAN, courriels, téléphones et valeurs de rémunération.

## Fichiers

Créés :

- `NEXUS_RUNTIME_INTEGRATION/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/config.py`
- `NEXUS_RUNTIME_INTEGRATION/models.py`
- `NEXUS_RUNTIME_INTEGRATION/mappers.py`
- `NEXUS_RUNTIME_INTEGRATION/integration.py`
- `NEXUS_RUNTIME_INTEGRATION/report_mapper.py`
- `tests/test_runtime_core_integration.py`
- `tests/test_runtime_core_mappers.py`
- `tests/test_runtime_core_report_and_confidentiality.py`
- `tests/test_runtime_core_server_integration.py`
- `NEXUS_RUNTIME_INTEGRATION_LOT_1.md`
- `NEXUS_RUNTIME_INTEGRATION_LOT_1_MATRIX.json`

Modifié :

- `apps/nexus-local-interface/server.py`

## Tests couverts

Configuration active/inactive, mappings Juriste et Paie, appel réel du Payroll Adapter, pipeline Core, appel réel du Common Orchestrator, rapport enrichi, compatibilité legacy, fallback Core, payload Paie mal formé, experts absents, scénarios juridique/paie/mixte/classification/heures supplémentaires/prime et confidentialité des diagnostics.

## Limites et prochaines étapes

Ce lot ne raccorde pas Retraite, CSE Memory, Protection Sociale ni les connecteurs officiels. Le mapper Juriste est volontairement minimal. Le marquage runtime reste interne au payload. Les prochains lots pourront raccorder les autres adaptateurs et sources à partir de ce point d'intégration, sans modifier les contrats fondamentaux du Core.
