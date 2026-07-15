# CSE Memory Engine — LOT 1D

## Objectif et périmètre

Le LOT 1D transforme localement les blocs normalisés du LOT 1B en chunks techniques déterministes et traçables, enrichis d’un instantané limité des métadonnées du LOT 1C. Il ne résume, ne reformule et n’interprète aucun contenu métier.

Il n’utilise ni réseau, ni OCR, ni IA externe, ni modèle, ni embedding, ni base vectorielle. Il prépare une indexation ultérieure sans la réaliser.

## Modèle et stratégie hybride

Chaque chunk porte ses identifiants documentaires, son rang (commençant à 0), son texte, ses tailles, ses blocs et localisateurs sources, ses liens précédent/suivant, ses chevauchements, ses qualités, sa version et son instantané de métadonnées. L’identifiant UUID v5 dépend du document, du rang, du texte unique et de la version : une même entrée produit le même identifiant.

Les séparateurs techniques LOT 1B sont explicitement exclus. Les autres blocs sont conservés dans l’ordre, regroupés jusqu’à la taille cible, et séparés de préférence lors d’un changement de page, slide ou feuille. Les gros blocs sont coupés, dans l’ordre, sur double saut de ligne, fin de phrase, ponctuation forte, saut de ligne, espace, puis strictement. Une coupure stricte est signalée.

Configuration par défaut : cible 1 600 caractères, maximum strict 2 500, minimum souhaité 300 et chevauchement 200. L’estimation locale des tokens est `ceil(nombre de caractères / 4)` ; ce n’est pas une tokenisation.

## Chevauchement, types et qualité

Le contexte terminal réel du chunk précédent préfixe le suivant, dans la limite configurée et de la taille maximale. Les nombres de caractères dupliqués sont enregistrés dans les deux chunks. Le texte unique demeure reconstructible en retirant les préfixes de chevauchement.

Les types techniques prévus sont `text`, `page`, `slide`, `sheet`, `table`, `list`, `mixed`, `empty_placeholder` et `unsupported_source`. Un document sans bloc exploitable reste dans le manifeste via un placeholder vide non indexable.

Le score déterministe de 0 à 100 signale notamment le vide, la brièveté, le dépassement, la coupure stricte, le chevauchement excessif, les caractères suspects, la faible qualité source, l’absence de localisateur et de métadonnées minimales. Les niveaux sont `excellent`, `good`, `acceptable`, `poor` et `unusable`. Aucun chunk n’est supprimé en fonction de ce score.

## Couverture et sorties

Le contrôle compare exactement le flux exploitable des blocs et la concaténation des parties uniques. Il fournit caractères sources, caractères uniques couverts, pertes, chevauchement, taux et avertissements. L’objectif est 100 %, hors séparateurs documentés.

Toutes les sorties sont locales sous `CCSEMEMORYENGINE/PROCESSED/LOT_1D/` : synthèses par document dans `documents/`, JSONL par document dans `chunks/`, manifeste, synthèse Markdown, rapports qualité/couverture dans `manifests/`, erreurs isolées dans `logs/`. Une ligne JSONL représente un chunk, ce qui permet une lecture progressive.

## Commandes

```powershell
python -m automation.cse_memory.chunk_builder --normalized-source CCSEMEMORYENGINE/PROCESSED/LOT_1B/documents --metadata-source CCSEMEMORYENGINE/PROCESSED/LOT_1C/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1D --mode dry-run --limit 14
python -m automation.cse_memory.chunk_builder --normalized-source CCSEMEMORYENGINE/PROCESSED/LOT_1B/documents --metadata-source CCSEMEMORYENGINE/PROCESSED/LOT_1C/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1D --mode build --limit 14
```

Les filtres disponibles portent sur extension, instance, type documentaire, qualités LOT 1B/1C et sous-dossier. Les tailles sont configurables. Sans `--force`, des sorties documentaires déjà présentes ne sont pas réécrites ; `--force` autorise leur seule réécriture. Les erreurs sont isolées document par document. `--statistics-only` garantit une sortie console statistique, déjà dépourvue de texte documentaire.

## Confidentialité, garde-fous et limites

Le moteur refuse une source `RAW_DOCUMENTS` et une sortie dans `RAW_DOCUMENTS`, LOT 1A, LOT 1B ou LOT 1C. Il ignore les liens symboliques et fichiers LNK, ne modifie ni source ni original, ne supprime aucune sortie et ne journalise aucun texte complet. Les chemins stockés sont relatifs.

La segmentation reste purement technique. Les tableaux sont seulement reconnus lorsque les blocs sources les déclarent. L’estimation de tokens est approximative. Le LOT 2 pourra consommer ces sorties validées pour une indexation, sans que le LOT 1D ne présume de sa technologie.
