# Document Intelligence Center — V2 LOT 1A

## Objet

Le Document Intelligence Center est une nouvelle couche documentaire commune.
Il indexe les métadonnées et les relations entre documents sans lire, copier,
télécharger ni indexer leur contenu. Il ne modifie ni le Runtime V1, ni les
connecteurs, ni les experts, ni le Document Registry, ni Nexus Core.

## Responsabilités

- décrire un document par un identifiant stable et des métadonnées publiques ;
- représenter des relations dirigées entre documents ;
- construire un graphe documentaire déterministe ;
- gérer les chaînes explicites de versions d'accords ;
- relier un PV CSE ou CSSCT à un accord explicitement référencé ;
- produire une projection metadata-only pour de futurs moteurs de recherche.

## Frontières

Le Document Registry reste responsable du cycle de vie des métadonnées des
connecteurs. L'Evidence Graph de Nexus Core reste responsable des preuves et
constats métier. Le Document Intelligence Center ne dépend d'aucun expert et
n'est appelé par aucun parcours Runtime dans ce lot.

Les contenus, chunks, chemins locaux, PDF, HTML, OCR et embeddings sont hors
périmètre. Les références à un accord depuis un PV proviennent exclusivement de
métadonnées explicites. Aucun rapprochement lexical implicite n'est effectué.

## Schéma des relations

| Relation | Source | Cible | Sens |
|---|---|---|---|
| `REFERENCES` | document citant | document cité | référence explicite |
| `SUPERSEDES` | nouvelle version | ancienne version | remplacement |
| `AMENDS` | document modificateur | document modifié | modification |
| `IMPLEMENTS` | document d'application | norme ou accord | mise en œuvre |
| `DISCUSSES` | PV | objet discuté | discussion |
| `DECIDES_ON` | PV | objet décidé | décision |
| `APPLIES_TO` | document | périmètre documentaire | application |
| `RELATED_TO` | document | document | relation générique explicite |

Chaque relation possède un identifiant SHA-256 déterministe calculé à partir de
la source, du type et de la cible. Les extrémités doivent exister dans le graphe.

## Versions des accords

Une version plus récente pointe vers la version antérieure avec `SUPERSEDES` ou
`AMENDS`. Le gestionnaire :

- limite la résolution à une même famille d'accords ;
- ordonne les versions par métadonnées de date et de version ;
- signale plusieurs versions courantes comme une ambiguïté ;
- refuse les cycles de version.

Il ne décide jamais de la validité juridique d'un accord.

## Rapprochement PV–accords

Le rapprochement accepte uniquement les identifiants documentaires ou URL
canoniques explicitement portés par les métadonnées du PV. Une correspondance de
titre ou de texte ne suffit pas. Cette règle fournit un comportement explicable,
déterministe et sans extraction de contenu.

## Recherche future

`DocumentSearchBackend` définit un contrat remplaçable. Les projections
contiennent seulement l'identifiant, le titre, le type, la provenance, la date,
les thèmes et les identifiants liés. Aucun moteur sémantique, embedding, stockage
vectoriel ou appel réseau n'est implémenté dans ce lot.

## Évolutions prévues

Ce socle pourra être consommé ultérieurement par Expert CSE V2, Expert Accords
V2 et Expert CSSCT. Leur intégration nécessitera des lots séparés, des règles
d'accès explicites et des tests de confidentialité dédiés.
