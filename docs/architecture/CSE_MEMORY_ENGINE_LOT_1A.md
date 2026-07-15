# CSE Memory Engine — LOT 1A

## Objectif

Le LOT 1A importe localement les documents CSE dans un format JSON normalisé. Il extrait le texte et des métadonnées techniques sans modifier les originaux, sans OCR, sans réseau et sans intelligence artificielle externe.

## Architecture

- `document_models.py` définit l'enregistrement normalisé et les statuts d'extraction.
- `document_importer.py` découvre les fichiers sans suivre les liens, applique un extracteur par format, isole les erreurs et écrit les résultats locaux.
- Chaque identifiant documentaire est déterministe et fondé sur le chemin relatif à la source.
- L'empreinte SHA-256 permet de détecter un fichier inchangé lors d'une reprise.

## Formats

| Format | Prise en charge LOT 1A | Méthode |
|---|---|---|
| PDF | Directe si `pypdf` est disponible | Texte page par page, sans OCR |
| DOCX | Directe si `python-docx` est disponible | Paragraphes et tableaux |
| PPTX | Directe si `python-pptx` est disponible | Formes textuelles et tableaux |
| XLSX | Directe si `openpyxl` est disponible | Valeurs en lecture seule, sans macros |
| TXT | Directe | Encodages locaux limités |
| DOC, PPT, XLS, RTF, MSG | Convertisseur requis | Aucun convertisseur automatique dans ce lot |
| ZIP | Non pris en charge | Archive non ouverte ni extraite |
| Images | Non pris en charge | OCR interdit |
| DB, LNK, PARTIAL, suffixes atypiques | Non pris en charge | Fichiers non ouverts |

Les classeurs XLSX sont limités à 100 000 cellules examinées par document. Un avertissement explicite signale la troncature ou une feuille protégée. Les macros ne sont ni chargées ni évaluées.

## Sorties locales

Les sorties sont placées sous `CCSEMEMORYENGINE/PROCESSED/LOT_1A`, dossier ignoré par Git :

- `documents/<document_id>.json` : un enregistrement normalisé par document ;
- `manifests/import_manifest.json` : manifeste global sans chemin absolu ;
- `manifests/import_summary.md` : synthèse agrégée ;
- `logs/import_errors.json` : erreurs structurées et chemins relatifs.

Les originaux ne sont jamais copiés dans le dossier traité.

## Exécution

Audit sans écriture :

```powershell
python -m automation.cse_memory.document_importer --source CCSEMEMORYENGINE/RAW_DOCUMENTS --output CCSEMEMORYENGINE/PROCESSED/LOT_1A --mode dry-run
```

Import local :

```powershell
python -m automation.cse_memory.document_importer --source CCSEMEMORYENGINE/RAW_DOCUMENTS --output CCSEMEMORYENGINE/PROCESSED/LOT_1A --mode import
```

Les options `--extension`, `--subfolder`, `--limit`, `--limit-per-extension EXT=COUNT` et `--force` permettent respectivement de filtrer, cibler un sous-dossier, limiter un essai, équilibrer un échantillon par format et forcer un réimport. Sans `--force`, un JSON existant dont le SHA-256 source est inchangé est repris sans nouvelle extraction.

## Confidentialité et limites

Le pipeline refuse toute sortie située dans la source, ne suit aucun lien symbolique, n'ouvre pas les raccourcis Windows et n'extrait pas les ZIP. Les chemins absolus éventuellement présents dans le texte, les métadonnées ou les erreurs sont neutralisés dans les sorties dérivées et signalés par un avertissement. Les erreurs d'un fichier n'interrompent pas le lot.

Le LOT 1A ne réalise aucun découpage en chunks, aucune indexation sémantique, aucune analyse métier et aucun traitement CSSCT particulier. Il ne garantit pas l'extraction des PDF composés uniquement d'images.

## Préparation du LOT 1B

Le LOT 1B pourra valider et nettoyer le texte extrait, définir des règles de segmentation et préparer une indexation locale. Les convertisseurs de formats anciens devront faire l'objet d'une décision séparée avant toute installation ou activation.
