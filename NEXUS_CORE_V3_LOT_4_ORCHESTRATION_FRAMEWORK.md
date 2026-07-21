# Nexus Core V3 — LOT 4 — Orchestration Framework

## Statut

Le LOT 4 fournit un framework d'orchestration générique. Il ne connaît aucun domaine, moteur concret, connecteur ou règle métier. Il coordonne uniquement des composants conformes aux Protocols publics de `NEXUS_CORE.orchestration`.

## Architecture

Le paquet est organisé en couches techniques :

- `models.py` définit les objets immuables et versionnés ;
- `contracts.py` définit les Protocols publics ;
- `registry.py` enregistre les descripteurs et implémentations compatibles ;
- `planner.py` construit un plan selon les capacités déclarées ;
- `executor.py` exécute séquentiellement les étapes ;
- `report.py` agrège les statuts techniques et sérialise le rapport ;
- `_identity.py` génère des identifiants techniques déterministes.

Le paquet dépend exclusivement de Nexus Core et de la bibliothèque standard Python.

## Cycle d'exécution

1. Un moteur conforme à `ExecutableEngine` est enregistré avec son `EngineDescriptor`.
2. L'appelant demande des `EngineCapability` techniques.
3. `ExecutionPlanner` sélectionne les moteurs activés qui déclarent ces capacités.
4. Le plan est ordonné par identifiant technique, sans priorité métier ou documentaire.
5. `PipelineExecutor` exécute les étapes séquentiellement.
6. Les erreurs sont converties en diagnostics neutres sans message d'exception.
7. `ExecutionReportBuilder` agrège moteurs exécutés ou ignorés, capacités, erreurs et durées.
8. `JsonExecutionReporter` produit un JSON déterministe.

## Registry

`EngineRegistry` propose `register()`, `unregister()`, `get()`, `list()` et `supports()`. Il accepte uniquement les objets compatibles avec le Protocol `ExecutableEngine`. Il ne conserve aucune connaissance d'un domaine.

## Planner

`ExecutionPlanner` construit des `ExecutionStage` uniquement à partir des capacités demandées et déclarées. L'ordre lexicographique des identifiants techniques garantit la reproductibilité sans créer de hiérarchie métier.

## Executor

`PipelineExecutor` préserve le contexte technique, l'ordre des étapes, les références de sortie, les diagnostics et les durées déclarées. Un échec est fermé pour l'étape concernée et n'empêche pas l'exécution des étapes suivantes.

## Reporting

Le rapport contient uniquement :

- identifiants des moteurs exécutés et ignorés ;
- capacités utilisées ;
- statuts techniques ;
- références techniques de sortie ;
- codes de diagnostic ;
- durées ;
- résumé agrégé.

Il ne contient aucun résultat métier, décision juridique, recommandation ou contenu documentaire.

## Confidentialité

Les contextes et rapports utilisent uniquement des identifiants pseudonymes, des codes techniques, des dates et des durées. Les messages et valeurs d'exception ne sont jamais reproduits. Tous les modèles utilisent `schema_version = "1.0"`.

## Tests

Les tests couvrent l'enregistrement, la suppression, la détection de capacités, la planification déterministe, l'exécution séquentielle, l'agrégation, la poursuite après erreur, la confidentialité, la sérialisation, les Protocols, les frontières d'import, l'absence de cycle et Python 3.10.

## Extensions futures

CORE 5 intégrera progressivement les moteurs réels au moyen d'adaptateurs dédiés. Ces adaptateurs traduiront les contrats des moteurs sans introduire de dépendance de domaine dans le framework. Le Registry, le Planner, l'Executor et les rapports resteront indépendants des domaines métiers.
