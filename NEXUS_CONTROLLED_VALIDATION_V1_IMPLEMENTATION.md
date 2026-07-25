# Implémentation — Validation contrôlée CFDT Nexus V1

## Corrections minimales

- Isolation reproductible des deux contrôles d’import dans des sous-processus Python neufs.
- Chemin canonique unique pour l’intégration référentielle Paie.
- Exports paresseux des moteurs Runtime optionnels.
- Chargement conditionnel de l’Assistant Final par le serveur.
- Chargement d’Expert Paie V2 uniquement lors de l’exécution explicite de son runner.
- Valeurs de production des deux feature flags inchangées et désactivées.

## Harness

`tools/run_nexus_controlled_validation.py` :

- charge exclusivement `NEXUS_CONTROLLED_VALIDATION_V1_CASES.json` ;
- refuse un corpus non marqué `synthetic_only` ou inférieur à 30 cas ;
- accepte une activation explicite séparée des deux flags ;
- exécute l’Assistant Final hors ligne ;
- simule des moteurs déterministes et une défaillance contrôlée ;
- applique dix critères totalisant 100 points ;
- rend non acceptable tout incident dur ;
- ne conserve pas les questions ni les payloads complets dans la matrice publique ;
- produit un rapport JSON et Markdown ;
- n’écrit dans aucun stockage métier.

## Corpus

34 dossiers synthétiques :

- R1A : 3 ;
- R1B : 3 ;
- R1C : 4 ;
- R1D : 4 ;
- R1E : 4 ;
- R2A : 3 ;
- R2B : 3 ;
- R2C : 3 ;
- Expert Paie V2 : 3 ;
- transversal : 4.

Les pièges couvrent notamment la non-surqualification, une régularisation déjà faite, `to_verify`, `calculation_allowed = false`, une décision CPAM en attente, l’absence de preuve, une contradiction et un moteur indisponible.

## Confidentialité

Les cas ne contiennent ni identité, ni document, ni donnée réelle. Les valeurs ressemblant à des identifiants sensibles sont limitées aux tests dédiés, marquées synthétiques et absentes des rapports générés. Aucun réseau, OCR, PDF ou service externe n’est utilisé.

## Matrice des flags

| Configuration | Assistant Final | Expert Paie V2 | Réponse |
|---|---:|---:|---|
| A | non | non | Runtime historique |
| B | oui | non | Assistant Final sans Paie V2 |
| C | oui | oui | Assistant Final, Paie V2 autorisée si pertinente |
| D | non | oui | Runtime historique ; Paie V2 non chargée par l’Assistant |

Les moteurs non autorisés ne sont ni chargés ni exécutés par le harness.
