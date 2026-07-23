# Nexus Core V3 — LOT 3 — Conflict Resolution Engine

## Statut

Le LOT 3 fournit un moteur générique de classification des situations documentaires déjà détectées. Il n'est ni un moteur métier ni un moteur juridique. Il ne choisit aucune preuve, n'applique aucune priorité documentaire et ne produit aucune décision.

## Architecture

Le paquet `NEXUS_CORE.conflict_resolution` dépend exclusivement des API publiques de `NEXUS_CORE`, notamment du Reasoning Engine et de l'Evidence Graph.

Le pipeline est déterministe :

1. consommation d'un `ReasoningReport` et, facultativement, d'un `EvidenceGraph`, d'`Evidence`, de `Finding`, d'`EvidenceConflict` et de `Fact` ;
2. classification structurelle des situations ;
3. création de candidats descriptifs sans sélection ;
4. évaluation de la cohérence documentaire ;
5. génération de diagnostics techniques ;
6. construction d'un rapport immuable ;
7. sérialisation JSON déterministe.

## Modèles publics

- `ResolutionCandidate` décrit une situation possible sans lui attribuer de priorité.
- `ResolutionClassification` associe une catégorie et une explication technique.
- `ResolutionDiagnostic` expose uniquement des codes et références techniques.
- `CoherenceAssessment` contient cinq dimensions documentaires et un score agrégé.
- `ResolutionSummary` agrège les comptes et catégories.
- `ResolutionReport` constitue la sortie versionnée du moteur.

Tous les modèles sont immuables et utilisent `schema_version = "1.0"`.

## Catégories

Les catégories supportées sont : `NO_CONFLICT`, `DOCUMENT_CONFLICT`, `TEMPORAL_CONFLICT`, `SOURCE_CONFLICT`, `MISSING_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, `PARTIAL_CORROBORATION`, `STRONG_CORROBORATION`, `MULTIPLE_HYPOTHESES` et `UNRESOLVED`.

Plusieurs catégories peuvent décrire simultanément un même rapport. Elles ne constituent jamais un classement de preuves.

## Cohérence documentaire

`CoherenceEvaluator` calcule cinq scores techniques bornés entre zéro et un :

- cohérence temporelle ;
- cohérence documentaire ;
- couverture par corroboration ;
- diversité de provenance ;
- complétude des preuves attendues.

Le score global est la moyenne arithmétique de ces dimensions. Il ne représente ni une probabilité juridique, ni la crédibilité d'une personne, ni la validité d'un droit.

## Preuves manquantes

Les diagnostics reprennent uniquement le type technique de fait explicitement déclaré comme attendu et un code indiquant son utilité structurelle. Aucun contenu absent n'est inventé.

## Confidentialité

Les rapports ne copient aucune valeur de preuve. Les diagnostics sont limités aux codes, catégories, niveaux de gravité et identifiants techniques pseudonymes. Les identifiants générés sont déterministes et segmentés pour rester compatibles avec les contrôles de données personnelles de Nexus Core.

## Garanties

Le moteur ne contient aucune dépendance vers un expert, un connecteur, l'automation, une API, le réseau ou une base de données. Il ne contient aucune règle métier, règle juridique, priorité documentaire, recommandation ou décision automatique.

## Tests

Les tests couvrent toutes les catégories, les explications, les diagnostics de preuves manquantes, la cohérence, l'absence d'arbitrage, la sérialisation déterministe, la confidentialité, les Protocols publics, les frontières d'import, l'absence de cycle et Python 3.10.

## Évolutions futures

Les futurs moteurs pourront enrichir les entrées au moyen des contrats publics de Nexus Core. Toute interprétation métier ou juridique devra rester dans une couche spécialisée distincte et ne devra pas modifier la neutralité du Conflict Resolution Engine.
