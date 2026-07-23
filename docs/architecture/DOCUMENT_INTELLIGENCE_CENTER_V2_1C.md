# Document Intelligence Center — V2 LOT 1C

## Objet

Le LOT V2-1C fournit une API interne, locale et en lecture seule pour explorer
le graphe documentaire. Cette façade est indépendante des experts, du Runtime,
de Nexus Core et des producteurs de métadonnées.

Elle servira de fondation aux futurs Expert CSE V2, Expert Accords V2 et Expert
CSSCT sans leur imposer une dépendance aux structures internes du graphe.

## Architecture

Deux modules sont ajoutés :

- `navigation_models.py` définit les contrats immuables et sérialisables ;
- `navigation_service.py` implémente les parcours et statistiques déterministes.

Le service dépend uniquement de `DocumentGraph`, `MetadataIndex` et
`AgreementVersionManager`. Il ne modifie jamais le graphe et n'appelle aucun
expert, connecteur, corpus ou service distant.

## Contrats publics

### NavigationQuery

Décrit des filtres exacts :

- identifiant pseudonymisé ;
- type documentaire ;
- période ;
- instance ;
- statut ;
- famille d'accord ;
- types de relations ;
- direction entrante, sortante ou bidirectionnelle ;
- profondeur maximale.

Les types de relations sont dédupliqués et triés lors de la construction.

### NavigationResult

Retourne :

- la requête normalisée ;
- des projections `NavigationDocument` ;
- les `DocumentRelation` déjà présentes dans le graphe.

La projection documentaire exclut volontairement URL canonique, contenu,
chunks, chemins, données binaires et identifiants de stockage.

### DocumentRelation

Le contrat immuable créé par le LOT V2-1A est réutilisé. Aucun second modèle
concurrent n'est introduit. La sérialisation publique expose uniquement ses
extrémités pseudonymisées, son type, sa provenance logique et sa confiance.

### GraphPath

Décrit le plus court chemin avec :

- la suite des identifiants documentaires pseudonymisés ;
- les identifiants déterministes des relations ;
- la longueur ;
- l'indication qu'un chemin a été trouvé.

### GraphStatistics

Expose uniquement des agrégats et identifiants pseudonymisés.

## API de navigation

`DocumentNavigationService` permet :

- `get_document()` : récupérer une projection sûre ;
- `related_documents()` : parcourir un voisinage à profondeur contrôlée ;
- `incoming()` et `outgoing()` : parcourir les relations dirigées ;
- `search()` : filtrer par métadonnées exactes ;
- `agreement_versions()` : obtenir l'historique ordonné d'une famille ;
- `replaced_or_modified()` : suivre `SUPERSEDES` et `AMENDS` ;
- `minutes_for_agreement()` : retrouver les PV explicitement liés ;
- `agreements_for_minutes()` : retrouver les accords explicitement cités ;
- `shortest_path()` : calculer un chemin non pondéré déterministe ;
- `orphan_document_ids()` : détecter les nœuds sans relation ;
- `connected_components()` : détecter les sous-graphes isolés ;
- `statistics()` : produire les indicateurs globaux.

Tous les parcours visitent les voisins dans un ordre stable fondé sur les
identifiants documentaires et relationnels.

## Recherche

La recherche réutilise exclusivement l'index metadata-only du LOT V2-1B. Elle
supporte les types, dates, instances, statuts et familles. Elle n'analyse aucun
texte et n'effectue aucune recherche approximative ou sémantique.

## Versions et relations documentaires

Les versions d'accords utilisent les relations explicites `SUPERSEDES` et
`AMENDS`. Les PV et accords sont rapprochés uniquement par les relations
`REFERENCES`, `DISCUSSES` et `DECIDES_ON` déjà validées lors de l'ingestion.

L'API ne déduit aucune relation nouvelle.

## Statistiques

Les statistiques disponibles sont :

- nombre de nœuds ;
- nombre de relations ;
- densité dirigée `relations / (nœuds × (nœuds - 1))` ;
- identifiants pseudonymisés des documents orphelins ;
- composantes connexes non orientées ;
- familles d'accords ;
- nombre de documents d'accord versionnés ;
- répartition par type documentaire.

## Confidentialité

Avant exposition, chaque identifiant doit respecter le format pseudonymisé et
chaque métadonnée textuelle traverse les garde-fous du LOT V2-1B. Une valeur
contenant un chemin local, HTML, secret, adresse électronique, NIR, IBAN ou
identifiant technique interdit provoque un refus explicite.

Les URL canoniques ne font pas partie de la projection publique afin d'éviter
la propagation accidentelle d'une URI privée.

## Limites

Cette API :

- ne persiste pas le graphe ;
- ne crée ni ne modifie de relation ;
- ne classe pas juridiquement les documents ;
- n'implémente ni LLM, ni embeddings, ni OCR, ni base vectorielle ;
- n'effectue aucun accès réseau ;
- n'est raccordée à aucun expert ou Runtime dans ce lot.
