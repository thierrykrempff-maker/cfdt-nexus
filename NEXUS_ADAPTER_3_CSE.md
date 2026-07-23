# NEXUS ADAPTER 3 — CSE Memory

## Architecture

L'adaptateur CSE est une couche indépendante dépendant uniquement des modèles
publics de `automation.cse_memory` et de `NEXUS_CORE`. Le moteur CSE et le Core ne
dépendent jamais de l'adaptateur.

Le moteur CSE actuel expose des documents, métadonnées, documents normalisés et
chunks, mais aucun modèle public Meeting, Decision ou Vote. L'adaptateur définit
donc des snapshots immuables injectés explicitement : `CSEMeetingSnapshot`,
`CSEDecisionSnapshot` et `CSEVoteSnapshot`. Il ne modifie pas le moteur et
n'invente aucune extraction.

## Composants

- `CSEAdapter` : façade de traduction et intégration orchestration ;
- `CSEEvidenceMapper` : PV et snapshots vers preuves Core ;
- `CSEMeetingMapper` : réunion, instance, ordre du jour et relations entre PV ;
- `CSEDecisionMapper` : rôle de traduction déclaré vers constat/recommandation ;
- `CSEVoteMapper` : résultat et décompte vers preuve et constat ;
- `CSEFindingMapper` et `CSERecommendationMapper` : agrégation déterministe ;
- `CSEMetadataMapper` : confiance, qualité, validation et redaction ;
- `CSEAdapterInput`, `CSEAdapterResult`, `CSEAdapterDiagnostics` : contrats immuables.

## Mappings explicites

| Entrée | Sortie Core | Conservation |
|---|---|---|
| `DocumentRecord` | `DocumentReference`, `Evidence`, `Provenance` | Identifiant pseudonymisé, date source, version, famille, source |
| `CSEMeetingSnapshot` | `Evidence` | Date, instance, agenda, participants pseudonymisés, documents et liens PV |
| `CSEDecisionSnapshot` | `Finding`, `Recommendation` ou les deux | Rôle fourni explicitement, jamais inféré |
| `CSEVoteSnapshot` | `Evidence`, `Finding` | Résultat et nombres pour/contre/abstention |
| Conflit `MetadataRecord` | `ReasoningConflict` | Conflit non arbitré et références techniques |
| Confiances de métadonnées | `ConfidenceAssessment` | Moyenne technique bornée, sans portée juridique |

`EmploymentPeriod` reste vide : aucun objet CSE présent ne décrit une période
d'emploi applicable. Aucune période n'est inventée.

## Protocols

`CSEAdapter` satisfait `ExecutableEngine`, `EvidenceProducer`, `FindingProducer`,
`RecommendationProducer` et `FactProducer`. Les preuves produites sont compatibles
avec Evidence Graph, Generic Reasoning Pipeline, Conflict Resolution et Orchestration.

## Confidentialité

Les chemins, noms de fichiers, identifiants source et participants ne sont jamais
placés dans les diagnostics. Les participants sont pseudonymisés. Les agendas,
décisions et résultats sont des métadonnées sensibles marquées redacted. Les
diagnostics contiennent uniquement des codes, catégories, gravités et références
techniques pseudonymisées.

Le champ `text_content` des PV n'est jamais copié dans le Core. L'adaptateur ne
charge aucun document, n'importe pas le transport ou l'importeur CSE et n'effectue
aucun accès réseau.

## Limites

Cette couche ne réalise ni classification CSE, ni extraction de réunion, ni analyse
de décision, ni interprétation de vote. Le choix Finding/Recommendation est fourni
par `CSEDecisionRole`. Les pièces jointes sont représentées comme références
documentaires lorsque le moteur les fournit comme `DocumentRecord`.

## Tests

Les tests couvrent PV, réunions, décisions, votes, confiance, conflits, Evidence
Graph, Reasoning, Conflict Resolution, Orchestration, Protocols, déterminisme,
immutabilité, confidentialité et isolement de l'importeur CSE.
