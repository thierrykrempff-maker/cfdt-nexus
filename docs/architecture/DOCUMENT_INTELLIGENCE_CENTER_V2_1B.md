# Document Intelligence Center — V2 LOT 1B

## Objet

Le LOT V2-1B ajoute une alimentation contrôlée du graphe documentaire créé par
le LOT V2-1A. La couche reçoit uniquement des métadonnées déjà produites et
normalisées dans Nexus. Elle ne lit aucun corpus, document, PDF, HTML, chunk ou
chemin local.

Le Runtime, Nexus Core, les experts, les connecteurs, CSE Memory et les moteurs
juridiques restent inchangés.

## Architecture

Le flux est strictement descendant :

1. un producteur existant fournit un objet de métadonnées ;
2. un adaptateur structurel ignore les champs de stockage et pseudonymise
   l'identité ;
3. un contrat d'ingestion valide les champs et la confidentialité ;
4. le service contrôle les conflits et la déduplication ;
5. le graphe reçoit les nœuds et relations explicitement acceptés ;
6. l'index local expose des recherches exactes par métadonnées ;
7. l'export d'audit restitue uniquement des compteurs et codes.

Les modules sont :

- `ingestion_models.py` : contrats immuables, sérialisation et garde-fous ;
- `cse_memory_adapter.py` : projection metadata-only des PV CSE/CSSCT ;
- `agreements_adapter.py` : projection déclarative des accords INEOS ;
- `ingestion_service.py` : ingestion unitaire et par lot ;
- `metadata_index.py` : index exact, déterministe et local ;
- `ingestion_audit.py` : statistiques sans contenu documentaire.

## Contrats

`DocumentMetadataInput` est le contrat générique. Les contrats spécialisés
`AgreementMetadataInput` et `MeetingMinutesMetadataInput` sont convertis
explicitement vers ce contrat.

Une entrée ne peut contenir que :

- un identifiant pseudonymisé ;
- un type, un titre normalisé et une provenance logique ;
- des dates et un statut ;
- une instance et une nature ;
- une référence, une famille et une version d'accord ;
- des thèmes courts ;
- des liens documentaires explicites ;
- un niveau de confiance.

La sérialisation JSON trie les clés et les collections afin d'être
reproductible.

## Adaptateur CSE Memory

L'adaptateur accepte la structure de métadonnées existante sans importer le
module CSE Memory. Il :

- ignore les statuts non indexables ;
- exige un identifiant source, un titre et une instance ;
- pseudonymise l'identifiant par SHA-256 avec un espace de noms CSE Memory ;
- conserve la date et le type CSE/CSSCT lorsqu'ils sont disponibles ;
- ignore explicitement les chemins, empreintes de stockage et contenus ;
- ne crée que les relations d'accord déjà déclarées dans les métadonnées.

## Adaptateur accords INEOS

L'adaptateur représente les accords, avenants, protocoles, décisions
unilatérales, règlements intérieurs et autres documents conventionnels. Il
calcule une identité stable à partir de la référence, de la famille et de la
version.

Les liens parent autorisés sont :

- `SUPERSEDES` pour « remplace » ;
- `AMENDS` pour « modifie » ;
- `IMPLEMENTS` pour « complète » ;
- `RELATED_TO` pour « annexe ».

Les chemins relatifs, noms de fichiers et hash de stockage éventuellement
présents dans la source ne sont jamais copiés.

## Déduplication

Deux niveaux déterministes sont appliqués :

1. l'identifiant pseudonymisé stable ;
2. une clé contrôlée composée du type documentaire, de la référence d'accord,
   de la date, de l'instance, de la famille et de la version.

La deuxième clé n'est utilisée que lorsqu'au moins une métadonnée discriminante
est disponible. Une réingestion identique retourne `DUPLICATE` et ne crée ni
nœud ni relation supplémentaire. Aucune similarité sémantique ou textuelle
n'intervient.

## Mises à jour et conflits

Un même identifiant peut mettre à jour les métadonnées d'un nœud lorsque son
type reste stable. Les conflits suivants sont explicites :

| Code | Cas | Décision |
|---|---|---|
| `DOCUMENT_TYPE_CONFLICT` | même identité, types différents | rejet |
| `AGREEMENT_VERSION_DATE_CONFLICT` | même famille/version, dates contradictoires | rejet |
| `AGREEMENT_STATUS_CONFLICT` | même version active et remplacée | rejet |
| `RELATION_TARGET_MISSING` | cible explicite absente | nœud conservé, relation refusée |
| `RELATION_INCOMPATIBLE` | relation non compatible avec les types | relation refusée |
| `AGREEMENT_PARENT_INCONSISTENT` | familles parent/enfant différentes | relation refusée |
| `AGREEMENT_VERSION_CYCLE` | cycle `SUPERSEDES` ou `AMENDS` | relation refusée |

Chaque issue contient un code stable, une criticité, l'identifiant pseudonymisé
concerné, la décision et l'état final du graphe. Les descriptions ne
reproduisent jamais la valeur en cause.

## Index metadata-only

`MetadataIndex` recherche par :

- identifiant ;
- type documentaire ;
- date ou intervalle ISO ;
- instance ;
- nature ;
- référence d'accord ;
- famille ;
- statut ;
- version.

Il n'implémente ni recherche plein texte, ni embeddings, ni base vectorielle.

## Audit

L'export fournit :

- documents présentés au service ;
- nœuds créés et mis à jour ;
- relations créées ;
- doublons, conflits, rejets et avertissements ;
- statistiques par type documentaire.

Il ne restitue ni titres, ni chemins, ni contenus, ni métadonnées sources
brutes.

## Confidentialité

Les contrats refusent explicitement :

- chemins Windows, Linux et répertoires temporaires ;
- HTML et valeurs longues assimilables à du contenu ;
- identifiants de chunks ou de stockage ;
- adresses électroniques personnelles ;
- NIR et IBAN ;
- secrets, tokens et clés d'API ;
- identifiants non pseudonymisés.

Ces contrôles complètent la frontière documentaire sans modifier ni affaiblir
le Privacy Gate existant.

## Limites

Ce lot ne décide pas de la validité juridique d'un accord, ne déduit aucune
relation depuis le texte, ne persiste pas le graphe et ne fournit pas de moteur
sémantique. Ces capacités nécessiteraient des lots indépendants et une
validation dédiée.
