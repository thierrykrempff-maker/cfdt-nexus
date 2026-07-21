# A3 — Pipeline d'import de carrière obligatoire

## Anomalie corrigée

Avant A3, chacun des cinq connecteurs convertissait ses métadonnées en
`ImportBatch`, puis appelait directement `CareerReconstructionEngine` par la
fondation commune. La validation structurelle du Career Import pouvait donc
être contournée.

## Architecture après A3

Le flux architectural est désormais unique :

`Connecteur → Career Import → Career Reconstruction → Timeline → Evidence → Potential Rights`

`CareerImportPipeline` est l'unique passerelle entre les connecteurs et la
reconstruction. Il vérifie le type exact `ImportBatch`, son caractère
synthétique, la provenance de chaque document et enregistrement, puis exécute
la validation publique de `CareerImportEngine`. Il produit ensuite un batch
immuable portant le statut `VALIDATED`.

`CareerReconstructionEngine` refuse tout objet autre qu'un `ImportBatch`, tout
batch qui n'a pas le statut `VALIDATED` et toute donnée non synthétique. Les
étapes Timeline, Evidence et Potential Rights restent leurs couches publiques
existantes ; A3 ne modifie ni leurs responsabilités ni leur logique métier.

## Voies supprimées

- import direct de `CareerReconstructionEngine` par Career Statement ;
- import direct de `CareerReconstructionEngine` par Payslip ;
- import direct de `CareerReconstructionEngine` par Employment Contract ;
- import direct de `CareerReconstructionEngine` par Kelio ;
- import direct de `CareerReconstructionEngine` par Nibelis ;
- acceptation d'un batch créé mais non validé par la reconstruction ;
- acceptation implicite d'une liste, d'un tuple, d'un dictionnaire ou d'un
  modèle métier à la place d'un `ImportBatch`.

## Compatibilité

Les méthodes publiques historiques des cinq connecteurs sont conservées. Leur
paramètre d'injection technique devient `import_pipeline`; l'ancien paramètre
`reconstruction_engine`, qui autorisait le contournement, est supprimé. Les
convertisseurs, rapports, validateurs spécialisés, règles Kelio et validation
fail-closed Nibelis restent inchangés.

## Garde-fous

- métadonnées synthétiques uniquement ;
- provenance obligatoire ;
- validation Career Import terminée avant reconstruction ;
- aucune lecture de document réel ;
- aucun OCR, scraping, appel réseau, CNAV ou CARSAT ;
- aucune conversion implicite et aucune correction automatique.
