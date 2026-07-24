# LOT R0 — Audit préalable du moteur de raisonnement syndical

## Référence

- Branche auditée : `main`
- SHA : `acfb7812d70677a355457a265a144df214f8ca28`
- Working tree initial : propre
- Python cible : 3.10

## Architecture actuelle

Le parcours utilisateur part de `apps/nexus-local-interface/server.py`, appelle
`automation/scripts/assistant_ds_router.py`, puis l'orchestrateur historique
`automation/experts/orchestrator.py`. Les enrichissements optionnels passent
ensuite par `NEXUS_RUNTIME_INTEGRATION`, Nexus Core V3, `PipelineExecutor` et
`CommonExpertOrchestrator`.

Les connaissances officielles sont normalisées par la Connector Platform et le
Document Registry. Les citations disposent de contrats dédiés. La
confidentialité est couverte par les primitives de `NEXUS_CORE/privacy.py`, le
Privacy Gate et le filtrage des payloads publics.

## Composants réutilisables

- `assistant_ds_router.py` : domaines, intentions et plan d'exécution ;
- `automation/experts/juriste_travail.py` : qualification juridique historique ;
- `automation/experts/paie.py` : enrichissement paie historique ;
- `automation/payroll/payroll_reasoning_protocol.py` : exemple de protocole
  explicite et non calculatoire ;
- moteurs CSE et CSE Memory : résultats documentaires déjà structurés ;
- `automation/orchestrator_common/` : isolation et agrégation des experts ;
- `NEXUS_CORE/orchestration/` : exécution technique déterministe ;
- `automation/official_knowledge/document_registry/` : identités et métadonnées ;
- `automation/connector_platform/connector_citation.py` et
  `automation/official_knowledge/citation_policy.py` : traçabilité ;
- `NEXUS_CORE/privacy.py` et
  `NEXUS_RUNTIME_INTEGRATION/public_payload.py` : confidentialité.

## Lacunes

- absence de contrat transversal représentant un dossier syndical ;
- absence de séparation explicite entre faits déclarés, faits établis,
  hypothèses et données manquantes ;
- absence de protocole transversal observable en 18 étapes ;
- absence de politique commune de hiérarchie des sources ;
- absence de modèle partagé d'options d'action graduées ;
- absence d'un rapport syndical court et détaillé ;
- absence de pont Runtime optionnel vers un tel moteur.

## Risques de duplication

1. Refaire le routage juridique ou paie dans le nouveau moteur.
2. Refaire la recherche documentaire ou le Document Registry.
3. Créer un second orchestrateur généraliste.
4. Introduire une hiérarchie rigide sans tenir compte du sujet.
5. Propager des faits, chemins ou identifiants confidentiels dans les
   diagnostics.
6. Présenter une qualification provisoire comme une décision certaine.

## Architecture retenue

Le paquet `SYNDICAL_REASONING_ENGINE` reste indépendant des experts et du
Runtime. Il reçoit uniquement des objets immuables déjà structurés. Il contient :

- modèles et contrats d'entrée/sortie ;
- protocole observable ;
- politique de sources ;
- règles de confiance et de prudence ;
- construction déterministe d'options progressives ;
- moteur d'assemblage non décisionnel ;
- scénario synthétique de référence.

Le pont `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py` détecte le
besoin, adapte le payload historique et appelle le moteur sous feature flag.
Désactivé, ou en cas d'erreur, il restitue strictement le rapport antérieur.

## Fichiers prévus

Créés :

- `SYNDICAL_REASONING_ENGINE/__init__.py`
- `SYNDICAL_REASONING_ENGINE/models.py`
- `SYNDICAL_REASONING_ENGINE/protocol.py`
- `SYNDICAL_REASONING_ENGINE/source_policy.py`
- `SYNDICAL_REASONING_ENGINE/prudence.py`
- `SYNDICAL_REASONING_ENGINE/strategies.py`
- `SYNDICAL_REASONING_ENGINE/engine.py`
- `SYNDICAL_REASONING_ENGINE/reference_scenario.py`
- `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py`
- quatre suites de tests ciblées ;
- les quatre livrables R0.

Modifiés :

- `NEXUS_RUNTIME_INTEGRATION/config.py`
- `NEXUS_RUNTIME_INTEGRATION/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/report_mapper.py`
- `apps/nexus-local-interface/server.py`

Le périmètre exclut tout moteur existant, connecteur, corpus, règle paie,
interface visuelle ou document réel.
