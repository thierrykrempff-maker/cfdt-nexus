# Nexus Core V3 — LOT 1 — Evidence Graph

## Objectif

Le Nexus Evidence Graph fournit une structure commune dans laquelle les
domaines de CFDT Nexus pourront publier des références vers leurs preuves,
constats, conflits et documents. Il ne copie aucune donnée métier et ne
résout aucun conflit.

## Architecture

Le sous-paquet autonome `NEXUS_CORE/evidence_graph/` dépend uniquement des
modèles publics de `NEXUS_CORE` et de la bibliothèque standard Python 3.10.

- `models.py` définit les nœuds, arêtes, relations, liens, clusters et
  statistiques ;
- `graph.py` porte les opérations immuables élémentaires ;
- `contracts.py` expose les Protocols d’extension ;
- `__init__.py` constitue la façade publique explicite.

Chaque opération d’ajout renvoie un nouveau graphe. Les identifiants déjà
présents sont idempotents lorsque leur objet est identique et refusés en cas
de collision incohérente. Un graphe scellé ne peut plus être étendu.

## Modèles

`EvidenceNode` contient exclusivement un identifiant de nœud, un type, une
référence typée et une période facultative. La référence est l’union explicite
de `EvidenceId`, `FindingId`, `ConflictId` et `DocumentId`. Aucune Evidence,
Finding, EvidenceConflict ou DocumentReference complète n’est copiée.

`EvidenceEdge` conserve origine, destination, type de relation, confiance
technique, provenance et période facultative. `EvidenceRelation` permet de
préparer ces attributs indépendamment des extrémités. `EvidenceLink` fournit
une projection minimale d’adjacence.

`EvidenceCluster` regroupe des identifiants techniques existants sans contenu.
`GraphStatistics` expose uniquement des compteurs déterministes.

Les relations disponibles sont génériques : `SUPPORTS`, `CONTRADICTS`,
`DUPLICATES`, `REFERENCES`, `EXTENDS`, `CORROBORATES` et `UNKNOWN`. Elles ne
portent aucune qualification juridique et aucune priorité entre preuves.

## Opérations

Le graphe fournit :

- création vide ;
- ajout idempotent de nœuds, relations et clusters ;
- recherche par identifiant, type et chevauchement de période ;
- liens d’adjacence ;
- parcours dirigé simple à profondeur bornée ;
- statistiques ;
- scellement ;
- export JSON.

Aucun classement, calcul, algorithme de chemin, arbitrage ou inférence n’est
implémenté.

## Protocols

`EvidenceGraphBuilder` prépare l’intégration future de résultats de domaines
sans imposer d’implémentation. `EvidenceGraphExporter` permet de remplacer
l’exporteur tout en conservant une sortie textuelle stable.

## Dépendances

Sont autorisés : imports relatifs `NEXUS_CORE`, `dataclasses`, `enum` et
`typing`.

Sont interdits : moteurs Paie, Retraite, CSE, Protection Sociale ou Juriste,
`automation`, connecteurs, API, réseau, frameworks web, stockage, caches et
bases de données.

## Confidentialité

Le graphe ne reçoit que des identifiants techniques validés par CORE 0. Il ne
possède aucun champ pour un nom, NIR, IBAN, RIB, email, téléphone, adresse ou
contenu documentaire. Provenance et confiance sont conservées par référence
et modèle neutre. Les fixtures de test sont entièrement synthétiques.

## Sérialisation

L’export réutilise `NEXUS_CORE.serialization.to_json()` : ordre stable, enums
explicites, dates ISO 8601, identifiants techniques et `schema_version =
"1.0"`. Aucune représentation mémoire Python n’est produite.

## Tests

`tests/test_nexus_evidence_graph.py` couvre le graphe vide, les quatre types de
nœuds, l’ajout et l’idempotence, les arêtes, recherche, périodes, parcours,
cycles de parcours, clusters, statistiques, immutabilité, JSON déterministe,
Protocols, frontières d’import, absence de réseau, absence de cycles internes
et grammaire Python 3.10.

## Évolutions prévues

Un lot ultérieur pourra créer un Conflict Resolver consommant le graphe, sans
intégrer sa logique dans celui-ci. L’orchestrateur Nexus V3 pourra ensuite
utiliser `EvidenceGraphBuilder` et `EvidenceGraphExporter`. Ces évolutions
restent explicitement hors du LOT CORE 1.
