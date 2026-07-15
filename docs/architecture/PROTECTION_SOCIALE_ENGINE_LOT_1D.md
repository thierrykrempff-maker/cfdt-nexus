# Protection sociale — LOT 1D — chunks techniques traçables

## Objectif et périmètre

Le LOT 1D transforme localement les textes normalisés du LOT 1B en chunks techniques, enrichis par un instantané limité des métadonnées explicites du LOT 1C. Le texte est conservé sans reformulation. Chaque chunk est rattaché à la version exacte de sa source par identifiants, empreinte SHA-256 et offsets.

Ce lot ne produit ni embedding, ni index vectoriel, ni recherche sémantique. Il n'utilise aucun OCR, réseau, modèle externe ou IA et ne réalise aucune interprétation juridique, extraction de montant ou normalisation de garantie.

## Modèle de chunk

Le modèle contient les identifiants du chunk, du document, de la source et de la carte de métadonnées, le chemin relatif, l'empreinte, l'index et le nombre de chunks, le type technique, le texte, les tailles et l'estimation locale des tokens. Il conserve aussi les offsets, pages, paragraphes, tables, liens précédent/suivant, chevauchements, qualités, avertissements et décisions d'indexabilité.

`chunk_id` est un UUID v5 stable calculé à partir du document, de son empreinte, de l'index, des offsets et de la version de découpage. `created_at` est informatif et n'entre pas dans cet identifiant.

## Stratégie hybride

La configuration par défaut vise 1 600 caractères, impose 2 500 caractères au maximum, souhaite au moins 300 caractères et autorise jusqu'à 200 caractères de chevauchement. Ces valeurs sont configurables sans tokeniseur externe.

Les coupures cherchent successivement une page, une table, un double saut de ligne, un paragraphe balisé, une fin de phrase, un point-virgule ou deux-points, un saut de ligne puis un espace. Une coupure stricte Unicode-safe n'intervient qu'en dernier recours et produit le drapeau `strict_cut`.

Les petits paragraphes restent regroupés. Les pages, paragraphes et tableaux sont localisés à partir des séparateurs techniques disponibles. Un tableau déjà aplati n'est jamais reconstruit : il reste inchangé et reçoit `flattened_table`. Les lignes, colonnes, taux et garanties ne sont ni interprétés ni recalculés.

## Chevauchement et couverture

Le chevauchement reprend uniquement du texte source réel, privilégie une limite de ligne ou de phrase et ne peut faire dépasser la taille maximale. Les nombres de caractères dupliqués sont inscrits sur les deux chunks adjacents.

La couverture est contrôlée avec les plages uniques `[source_start_offset, source_end_offset)`. Pour chaque document, le rapport expose caractères source, caractères uniques couverts, caractères dupliqués, taux de couverture, pertes et avertissements de reconstruction. La cible est 100 % du texte normalisé exploitable, dans son ordre exact.

## Métadonnées attachées

L'instantané limité contient domaine principal, sous-domaine, type, organisme émetteur, assureur, contrat, référence, dates d'effet et de fin, public et thème, accompagnés de leur confiance. `topic_tags` reprend seulement un champ explicite du LOT 1C ou, à défaut, la valeur explicite de `thème_principal`; aucun tag nouveau n'est inféré. La preuve complète et les conflits détaillés restent dans la carte LOT 1C, retrouvable par `metadata_record_id`.

## Qualité, doublons et documents vides

Le score déterministe de 0 à 100 classe les chunks en `excellent`, `good`, `acceptable`, `poor` ou `unusable`. Il signale notamment vide, taille atypique, coupure stricte, chevauchement excessif, caractères suspects, source faible, localisateur absent, métadonnées essentielles absentes et table aplatie. Aucun chunk n'est supprimé en raison de son score.

Un document vide produit un `empty_placeholder`, non indexable et conservé dans le manifeste. Les copies exactes restent séparées par provenance; `duplicate_group_id` et `content_id` sont propagés lorsqu'ils existent afin de permettre une future déduplication logique.

## Sorties locales

Toutes les sorties sont sous `PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1D/` et restent ignorées par Git :

- `documents/<document_id>.json` : synthèse et couverture du document ;
- `chunks/<document_id>.jsonl` : un chunk par ligne ;
- `manifests/chunk_manifest.json` ;
- `manifests/chunk_summary.md` ;
- `manifests/chunk_quality_report.json` ;
- `manifests/chunk_coverage_report.json` ;
- `logs/chunk_errors.json`.

Les originaux et les JSON LOT 1B/1C ne sont jamais modifiés ni recopiés.

## Commandes

Dry-run statistique :

```powershell
python -m automation.protection_sociale.chunk_builder `
  --normalized-source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B/documents `
  --metadata-source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1C/documents `
  --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1D `
  --mode dry-run --statistics-only
```

Construction locale :

```powershell
python -m automation.protection_sociale.chunk_builder `
  --normalized-source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B/documents `
  --metadata-source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1C/documents `
  --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1D `
  --mode build --statistics-only
```

Les filtres disponibles portent sur domaine, sous-domaine, type, `topic_tag`, qualités LOT 1B/1C et sous-dossier. `--limit` limite le nombre de documents. Une sortie complète est reprise sans retraitement; `--force` permet sa réexécution explicite. Chaque erreur de fichier est isolée.

## Garde-fous et confidentialité

Les sources dans `RAW_DOCUMENTS`, les liens symboliques, les fichiers LNK et les sorties dans `RAW_DOCUMENTS` ou LOT 1A à LOT 1C sont refusés. Aucun chemin absolu ni contenu documentaire complet n'est journalisé dans les erreurs ou rapports statistiques. Les tests utilisent uniquement des textes synthétiques.

## Limites et suite

Les localisateurs dépendent des séparateurs conservés par le LOT 1B. Une table aplatie ne peut pas retrouver une structure absente. L'estimation de tokens (`ceil(caractères / 4)`) est volontairement approximative. Le moteur prépare un futur moteur de recherche local, mais le LOT 2, l'indexation et toute réponse utilisateur restent hors périmètre.
