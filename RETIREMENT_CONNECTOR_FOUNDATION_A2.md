# A2 — Fondation commune des connecteurs Retraite & Pénibilité

## Objet

A2 réduit la duplication technique des cinq connecteurs sans fusionner leurs
modèles, leurs validations métier, leurs extractions ou leurs rapports.

Connecteurs audités :

- Career Statement Connector ;
- Payslip Connector ;
- Employment Contract Connector ;
- Kelio Connector ;
- Nibelis Connector.

## Cartographie initiale

| Connecteur | Création | Validation | Conversion | Extraction | Reconstruction | Rapport |
|---|---|---|---|---|---|---|
| Career Statement | `create_empty_statement` | `validate_statement` | `convert_to_import_batch` | `extract_metadata` | `prepare_reconstruction` | `generate_import_report` |
| Payslip | `create_empty_payslip` | `validate_payslip` | `convert_to_import_batch` | `extract_payroll_information` | `prepare_reconstruction` | `generate_import_report` |
| Employment Contract | `create_empty_contract` | `validate_contract` | `convert_to_import_batch` | `extract_contract_information` | `prepare_reconstruction` | `generate_import_report` |
| Kelio | `create_empty_export` | `validate_export` | `convert_to_import_batch` | `extract_working_time` | `prepare_reconstruction` | `generate_import_report` |
| Nibelis | `create_empty_export` | `validate_export` | `convert_to_import_batch` | `extract_payroll_data` | `prepare_reconstruction` | `generate_import_report` |

Chaque connecteur répétait le câblage du validateur, du convertisseur et du
moteur de reconstruction, la délégation de validation, la conversion après
validation et la construction d'un contexte de reconstruction. Quatre rapports
partageaient une forme voisine, mais leurs entrées et modèles de sortie restent
spécifiques.

## Comportements mutualisés

`ConnectorFoundation` mutualise uniquement :

1. la composition d'un validateur, d'un convertisseur et d'un coordinateur de
   reconstruction injectables ;
2. la délégation de validation ;
3. la conversion brute nécessaire aux rapports ;
4. la conversion fail-closed après validation ;
5. la création déterministe du contexte et de la requête de reconstruction ;
6. l'ajout de l'`ImportBatch` et la production de la proposition.

`ConnectorReconstructionSpec` porte seulement les préfixes techniques et le
libellé déjà présents dans chaque connecteur.

## Comportements non mutualisés

Restent volontairement propres à chaque source :

- création des objets vides et métadonnées propres au domaine ;
- extraction de paie, temps de travail, contrat ou relevé de carrière ;
- modèles, statuts, erreurs et avertissements ;
- règles de validation et messages associés ;
- vérification d'anonymisation Kelio ;
- lookup référentiel et mode fail-closed Nibelis ;
- convertisseurs et règles de projection vers Career Import ;
- construction des rapports Employee View et Expert View ;
- wrappers de résultat de reconstruction.

Les dix contrôles techniques de provenance et de caractère synthétique restent
dans les cinq validateurs. Leur résultat métier, leurs codes et leurs messages
ne sont pas assez homogènes pour justifier une abstraction dans A2.

## Fichiers créés

- `RETIREMENT_PENIBILITY_ENGINE/connector_contract.py` ;
- `RETIREMENT_PENIBILITY_ENGINE/connector_base.py` ;
- `tests/test_retirement_connector_foundation.py` ;
- `RETIREMENT_CONNECTOR_FOUNDATION_A2.md`.

## Contrat commun

`RetirementSourceConnector` décrit le noyau public réellement partagé :

- `convert_to_import_batch()` ;
- `prepare_reconstruction()` ;
- `generate_import_report()`.

Il n'impose pas de noms génériques artificiels pour la création, la validation
ou l'extraction. Les méthodes historiques restent donc les interfaces lisibles
et publiques de chaque connecteur.

Les protocols techniques `ConnectorValidator`, `ConnectorConverter` et
`ReconstructionCoordinator` permettent à la fondation de rester indépendante
des cinq implémentations concrètes et d'éviter `Any`.

## Architecture finale

```text
modèles et contrats spécifiques
              ↓
connector_contract (protocols neutres)
              ↓
connector_base (composition technique)
              ↓
cinq connecteurs concrets
```

La fondation n'importe aucun connecteur. Les contrats n'importent aucune
implémentation. Aucun import dynamique ou différé n'est utilisé.

## Compatibilité

- Toutes les méthodes publiques historiques sont conservées.
- Les signatures d'appel et les types de résultats sont inchangés.
- Les objets vides, validations, `ImportBatch`, propositions et rapports sont
  identiques selon les suites historiques.
- Les composants restent injectables dans les constructeurs.
- Le fail-closed Nibelis et l'anonymisation Kelio sont inchangés.
- Aucune conversion, règle métier, règle juridique ou politique documentaire
  n'a été modifiée.

## Métriques avant/après

| Mesure | Avant A2 | Après A2 |
|---|---:|---:|
| Familles techniques équivalentes examinées | 5 | 5 |
| Occurrences de méthodes techniquement équivalentes | 24 | 24 signatures publiques conservées |
| Blocs d'implémentation redondants au-delà du premier | 19 | 3 |
| Blocs techniques centralisés | 0 | 4 familles / 16 duplications supprimées |
| Validations techniques provenance/synthétique répétées | 10 | 10, volontairement spécifiques |
| Constructions de rapport voisines | 4 | 4, volontairement spécifiques |
| Lignes physiques des cinq connecteurs | 452 | 472 |
| Lignes non vides des cinq connecteurs | 391 | 406 |
| Lignes physiques ajoutées à la fondation commune | 0 | 161 |
| Lignes non vides de la fondation commune | 0 | 115 |
| Lignes supprimées des cinq connecteurs | 0 | 110 |
| Lignes ajoutées aux cinq connecteurs | 0 | 130 |
| Lignes opérationnelles mutualisées dans `ConnectorFoundation` | 0 | 24 |

La réduction porte sur le nombre d'implémentations de comportement, pas sur le
volume brut. Le typage des protocols, les configurations explicites et les
délégations augmentent volontairement le nombre de lignes tout en établissant
un seul point de maintenance pour les quatre mécanismes identiques. Les blocs
métier majoritaires n'ont pas été déplacés dans une classe de base.

## Risques évités

- aucune classe de base métier massive ;
- aucune fusion de modèles homonymes ;
- aucun report builder générique à signature variable ;
- aucun contournement des validateurs propres aux sources ;
- aucune dépendance de la fondation vers les connecteurs ;
- aucun affaiblissement du fail-closed Nibelis ou de l'anonymisation Kelio.

## Hors périmètre

A2 ne traite pas le pipeline Career Import → Reconstruction, le matching selon
le type métier, l'intégration réelle Kelio, la confidentialité active globale,
la normalisation complète des rapports, la façade publique, les anomalies P2,
les données réelles, PDF, OCR, API ou réseau.
