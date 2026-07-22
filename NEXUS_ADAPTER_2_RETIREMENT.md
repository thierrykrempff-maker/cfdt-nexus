# NEXUS ADAPTER 2 — Expert Retraite & Pénibilité

## Statut

Adaptateur indépendant entre les sorties immuables de `RETIREMENT_PENIBILITY_ENGINE`
et les modèles publics de `NEXUS_CORE`. Il ne déplace, ne réexécute et ne complète
aucune règle métier.

## Architecture

`RetirementAdapterInput` reçoit explicitement un `RetirementReport`, un `ExpertReport`
optionnel déjà produit par la façade experte, un sujet
technique, une date de production et, lorsque disponibles, une proposition de
reconstruction, un graphe de preuves et un résultat de raisonnement. L'absence de
ces sorties produit des diagnostics non bloquants.

Les conversions sont réparties entre des composants spécialisés :

- `RetirementEvidenceMapper` : preuves, références documentaires et provenance ;
- `RetirementFindingMapper` : informations manquantes, écarts et conflits ;
- `RetirementRecommendationMapper` : actions déjà présentes dans le rapport ;
- `RetirementMetadataMapper` : tables de correspondance fermées ;
- `RetirementCareerMapper` : périodes reconstruites vers `EmploymentPeriod` ;
- `RetirementConflictMapper` : conflits et candidats, sans arbitrage.

`RetirementAdapterResult` rassemble les objets Core sans modifier les objets source.

## Mappings explicites

| Source Retraite | Destination Nexus Core | Règle |
|---|---|---|
| `CareerEvidenceItem` | `Evidence`, `DocumentReference`, `Provenance` | Référence et métadonnées uniquement |
| `ExpertReport` | `Evidence`, `Finding`, `Recommendation` | Sorties existantes uniquement |
| `EvidenceItem` | `Evidence` | Grade, statut officiel et validation conservés |
| `ReconstructedCareerPeriod` | `EmploymentPeriod` | Période exacte uniquement, employeur pseudonymisé |
| `MissingInformation` | `Finding` | Code stable `RETIREMENT_INFORMATION_MISSING` |
| `ReasoningFinding` | `Finding` | Observation neutre |
| Action recommandée | `Recommendation` | Texte marqué sensible et redacted |
| Conflit de reconstruction | `ReasoningConflict`, `ResolutionCandidate` | Type conservé, aucune sélection |
| Conflit de règle | `ReasoningConflict`, `ResolutionCandidate` | Références techniques, aucune conclusion |

Une date absente ou invalide n'est jamais inventée. Une période sans date de début
n'est pas convertie et déclenche un diagnostic technique.

## Protocols

`RetirementAdapter` satisfait structurellement `ExecutableEngine`,
`EvidenceProducer`, `FindingProducer`, `RecommendationProducer` et `FactProducer`.
L'extraction de faits délègue à l'API publique `FactExtractor` de Nexus Core.

## Confidentialité

Les identifiants Core sont des empreintes techniques déterministes. Les valeurs
Retraite placées en métadonnées sont marquées sensibles et redacted. Les titres,
références documentaires, noms d'employeur et descriptions de diagnostic ne sont
jamais recopiés dans les diagnostics. Ceux-ci contiennent uniquement code,
catégorie, gravité et référence pseudonymisée.

## Limites

L'adaptateur ne calcule aucun droit, date, durée, point, pension ou éligibilité. Il
ne télécharge aucun document, n'appelle aucun connecteur et n'arbitre aucun conflit.
Il ne remplace ni le raisonnement Retraite ni les moteurs génériques du Core.

## Tests

Les tests vérifient les conversions, la provenance, les périodes, la confiance,
les conflits, les Protocols, l'orchestration, la déterminisme, l'immutabilité et
l'absence de fuite dans les diagnostics.
