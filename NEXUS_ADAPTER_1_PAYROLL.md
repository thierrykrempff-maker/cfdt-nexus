# Nexus Adapter 1 — Expert Paie

## Objectif

`NEXUS_ADAPTERS.payroll` est la couche officielle de traduction entre les rapports normalisés d'Expert Paie et Nexus Core. Elle ne déplace, ne reproduit et n'exécute aucune règle de paie.

L'adaptateur reçoit un `ExpertReport` déjà produit, un sujet pseudonyme, une date technique et, facultativement, une période. Toutes les conversions sont ensuite réalisées en mémoire.

## Architecture

- `adapter.py` expose `PayrollAdapter` et coordonne les mappers.
- `metadata.py` centralise toutes les tables de correspondance.
- `evidence.py` produit les `Evidence`, `DocumentReference` et `Provenance`.
- `findings.py` produit les `Finding` neutres.
- `recommendations.py` traduit uniquement les recommandations déjà présentes.
- `models.py` définit `PayrollAdapterResult` et `PayrollAdapterDiagnostics`.
- `_identity.py` génère des identifiants techniques déterministes et pseudonymes.

Le paquet dépend des contrats Expert Paie existants et des API publiques de `NEXUS_CORE`. Nexus Core ne dépend jamais de `NEXUS_ADAPTERS`.

## Mappings explicites

| Source Expert Paie | Sortie Nexus Core | Règle de conversion |
|---|---|---|
| `findings` | `Evidence` + `Finding.OBSERVATION` | texte conservé dans une valeur sensible, code neutre |
| `contradictions` | `Evidence` + `Finding.CONFLICT` | aucune résolution ni priorité |
| `missing_information` | `Evidence` + `Finding.MISSING_INFORMATION` | criticité convertie par table explicite |
| `risks` | `Evidence` + `Finding.RISK` | criticité convertie sans recalcul |
| `recommendations` | `Recommendation.VERIFY_INFORMATION` | priorité `NORMAL`, texte sensible |
| `proposed_actions` | `Recommendation.MANUAL_REVIEW` | priorité `NORMAL`, texte sensible |
| `KnowledgeSource` | `DocumentReference` + `SourceReference` | type documentaire et provenance par tables explicites |
| `SourceEvidence` | `Evidence` de consultation | statut technique uniquement |
| `confidence_assessments` | `ConfidenceScore` | premier niveau déclaré, échelle convertie explicitement |
| `ReportStatus` | qualité et validation | table fermée et documentée dans le code |

La période est fournie explicitement à l'adaptateur et conservée sans transformation.

## Protocols

`PayrollAdapter` implémente structurellement :

- `ExecutableEngine` ;
- `FactProducer` ;
- `EvidenceProducer` ;
- `FindingProducer` ;
- `RecommendationProducer`.

L'exécution par CORE 4 ne transporte que les références techniques des objets produits. L'extraction de faits réutilise le `FactExtractor` public de CORE 2.

## Diagnostics

Les situations suivantes produisent un diagnostic sans interrompre l'adaptation :

- données absentes ;
- rapport incomplet ;
- version de schéma incompatible ;
- diagnostics présents dans le rapport source.

Les diagnostics contiennent uniquement des codes, catégories, niveaux de gravité et références techniques pseudonymes. Aucun message source n'est reproduit.

## Confidentialité

Les textes provenant d'Expert Paie sont placés dans des `EvidenceValue` ou `MetadataEntry` marqués sensibles. La sérialisation Nexus Core les remplace par `<redacted>`. Les identifiants source sont hachés et segmentés. Aucun nom, matricule, NIR, IBAN, courriel ou téléphone ne doit apparaître dans un diagnostic.

## Limites

L'adaptateur :

- n'appelle pas Expert Paie ;
- ne réalise aucun calcul ;
- ne vérifie aucune règle de paie ;
- ne crée aucune recommandation absente du rapport source ;
- ne résout aucune contradiction ;
- ne persiste aucune donnée ;
- n'effectue aucun accès réseau.

## Tests

Les tests couvrent les conversions, les correspondances explicites, la période, la confiance, la provenance, les documents, les diagnostics, la confidentialité, les identifiants stables et les compatibilités Evidence Graph, Reasoning Engine et Orchestration Framework.
