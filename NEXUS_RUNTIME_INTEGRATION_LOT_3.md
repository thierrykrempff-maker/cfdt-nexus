# Nexus Runtime Integration — LOT 3

## Objet

Ce lot raccorde le Runtime local aux artefacts existants de CSE Memory pour les questions documentaires CSE. Il ne modifie ni le corpus, ni les documents, ni les chunks, ni les extracteurs, ni les pipelines d'import.

## Architecture avant le lot

CSE Memory fournissait :

- l'audit du corpus ;
- l'import documentaire local ;
- la normalisation ;
- l'extraction de métadonnées ;
- le chunking déterministe LOT 1D ;
- un `CSEAdapter` officiel vers Nexus Core V3.

Le Runtime utilisateur n'appelait aucun de ces composants. Le dépôt ne contient pas d'API publique de recherche CSE ni d'index sémantique/vectoriel. La documentation LOT 1D précise que les chunks préparent une indexation ultérieure sans la réaliser.

## Architecture après le lot

Avec `NEXUS_CSE_MEMORY_RUNTIME_ENABLED=true` :

`question -> route existante -> détection documentaire CSE -> accès local LOT 1D en lecture seule -> CSEAdapter -> Core V3 -> CommonExpertOrchestrator -> section documentaire bornée`

Le Runtime historique Juriste/Paie/Connecteurs reste exécuté normalement. La section CSE est ajoutée seulement après succès complet du chemin CSE.

## Détection

La détection réutilise en priorité les domaines et intentions du routeur. Pour les requêtes non classées, une liste fermée de marqueurs documentaires couvre notamment `PV CSE`, `ancien PV`, `décision CSE` et `ordre du jour`. Il n'existe aucun nouveau modèle ou moteur NLP.

## Recherche locale

`RuntimeCSEMemoryGateway` parcourt uniquement les JSONL déjà préparés sous `CCSEMEMORYENGINE/PROCESSED/LOT_1D/chunks`. La recherche est lexicale, déterministe, bornée et hors ligne. Elle ignore les chunks non indexables, les liens symboliques et les fichiers hors du répertoire `chunks`.

Le gateway ne renvoie jamais le texte des chunks au rapport. Il prépare des `DocumentRecord` à contenu vide pour le `CSEAdapter`, en conservant uniquement les éléments techniques nécessaires à la provenance interne. Aucun fichier du corpus n'est écrit, déplacé ou supprimé.

## Passage par l'adaptateur et le Core

Le véritable `NEXUS_ADAPTERS.cse.CSEAdapter` reçoit les documents rapprochés. Il produit des `DocumentReference`, `Evidence` et `Provenance` confidentiels et pseudonymisés. Le véritable `PipelineExecutor` exécute ensuite la capacité `CSE_MEMORY_RESULT_ADAPTATION`.

Un rapport technique minimal `cse_memory` est transmis au véritable `CommonExpertOrchestrator`. Il contient uniquement des codes et compteurs documentaires, jamais le texte, le chemin ou les identifiants internes.

## Feature flag et fallback

Le flag `NEXUS_CSE_MEMORY_RUNTIME_ENABLED` est désactivé par défaut. Le répertoire peut être configuré par `NEXUS_CSE_MEMORY_PROCESSED_ROOT`; sinon le serveur utilise le LOT 1D local standard.

Fallbacks possibles :

- `CSE_MEMORY_UNAVAILABLE` ;
- `CSE_MEMORY_NO_MATCH` ;
- `CSE_MEMORY_SEARCH_FAILED` ;
- `CSE_MEMORY_ADAPTER_FAILED` ;
- `CSE_MEMORY_CORE_FAILED` ;
- `CSE_MEMORY_ORCHESTRATION_FAILED`.

En fallback ou lorsque CSE Memory n'est pas requis, le mapper retourne exactement le rapport produit par le Runtime antérieur.

## Diagnostics et confidentialité

Les diagnostics contiennent uniquement : activation, appel, nombre de documents, nombre de chunks, durée en millisecondes, étapes Adapter/Core/Common Orchestrator et code de fallback.

Ils ne contiennent jamais : texte de chunk, chemin disque, nom de fichier, identifiant de document ou chunk, question utilisateur, exception, stack trace ou donnée personnelle.

La section de rapport CSE expose seulement des nombres de documents, chunks et preuves. Aucun document brut ou extrait n'est copié.

## Fichiers

Créés :

- `NEXUS_RUNTIME_INTEGRATION/cse_memory_search.py`
- `NEXUS_RUNTIME_INTEGRATION/cse_memory_runtime.py`
- `tests/test_runtime_cse_memory_search.py`
- `tests/test_runtime_cse_memory_integration.py`
- `tests/test_runtime_cse_memory_server_and_confidentiality.py`
- `NEXUS_RUNTIME_INTEGRATION_LOT_3.md`
- `NEXUS_RUNTIME_INTEGRATION_LOT_3_MATRIX.json`

Modifiés :

- `NEXUS_RUNTIME_INTEGRATION/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/config.py`
- `NEXUS_RUNTIME_INTEGRATION/report_mapper.py`
- `apps/nexus-local-interface/server.py`

## Limites

Ce lot n'ajoute aucune interprétation métier des PV, aucune extraction de décision ou de vote et aucune recherche sémantique. La qualité du rapprochement dépend des chunks LOT 1D existants et d'une correspondance lexicale. Un futur lot explicitement autorisé pourrait fournir une véritable API d'indexation/recherche, mais elle n'est pas créée ici.

Retraite, Protection Sociale, CSSCT, nouveaux experts, connecteurs ou corpus restent hors périmètre.
