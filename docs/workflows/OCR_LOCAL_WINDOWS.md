# OCR local Windows - Bible Accords Sarralbe V1

## Objectif

Cette procédure permet de traiter localement les PDF classés `OCR_REQUIRED` dans la Bible Accords Sarralbe.

Aucun document réel, aucun PDF OCRisé, aucun texte extrait et aucun rapport privé ne doit être committé dans GitHub.

## Principe

Le pipeline OCR travaille uniquement dans :

```text
local-index/agreements/ocr/
```

Le PDF original du corpus privé n'est jamais modifié.

Pour chaque document, le moteur crée une copie de travail locale, puis produit :

- soit un PDF OCRisé ;
- soit des pages texte OCR structurées par numéro de page.

## Dépendances locales

Solution recommandée :

- Tesseract OCR Windows 64-bit avec la langue `fra` ;
- Ghostscript 64-bit ;
- OCRmyPDF installé dans un environnement Python local.

Solution de repli :

- Tesseract OCR Windows 64-bit avec `fra` ;
- `pdftoppm` local ;
- extraction texte structurée page par page.

Références officielles :

- OCRmyPDF : https://ocrmypdf.readthedocs.io/en/latest/installation.html
- Tesseract : https://tesseract-ocr.github.io/tessdoc/Installation.html

## Diagnostic

Depuis la racine du dépôt :

```powershell
python automation/scripts/agreements_bible.py ocr-diagnose
```

Le diagnostic vérifie :

- `ocrmypdf` ;
- `tesseract` ;
- `ghostscript` ;
- `pdftoppm` ;
- présence de la langue française `fra` ;
- nombre de documents détectés ;
- nombre de documents indexables ;
- nombre de documents encore en `OCR_REQUIRED` ;
- couverture documentaire.

## Installation locale

Ne jamais installer silencieusement.

Si le diagnostic indique des dépendances manquantes, installer manuellement :

```powershell
python -m pip install ocrmypdf
tesseract --list-langs
ocrmypdf --version
gswin64c --version
```

La commande `tesseract --list-langs` doit afficher au minimum :

```text
fra
```

`eng` est utile si l'on souhaite utiliser `fra+eng`.

## Test prudent

Ne pas lancer immédiatement tous les documents.

Commencer par :

```powershell
python automation/scripts/agreements_bible.py ocr-run --limit 3
```

Ou sur un document précis :

```powershell
python automation/scripts/agreements_bible.py ocr-run --document-id doc_xxxxxxxxxxxxxxxx
```

Après OCR réussi, le pipeline relance automatiquement :

```text
OCR -> extraction -> chunks -> index lexical
```

## Reprise après interruption

Chaque document OCRisé possède un statut privé local dans :

```text
local-index/agreements/ocr/<document_id>/ocr-status.private.json
```

Lors d'une nouvelle exécution, les documents déjà traités avec succès sont ignorés.

Pour forcer un retraitement :

```powershell
python automation/scripts/agreements_bible.py ocr-run --document-id doc_xxxxxxxxxxxxxxxx --force-ocr
```

## Qualité OCR

Le moteur conserve la pagination autant que possible.

Si la confiance OCR est faible, le document est marqué `OCR_LOW_CONFIDENCE`.

Dans ce cas :

- les citations restent possibles ;
- un avertissement accompagne la source ;
- une validation humaine est obligatoire avant usage en CSE, CSSCT, négociation ou défense.

## Sécurité

Interdit :

- API OCR cloud ;
- envoi vers OpenAI, Google, Microsoft, AWS ou autre service externe ;
- commit d'un PDF réel ;
- commit d'un PDF OCRisé ;
- commit d'un texte extrait réel ;
- commit d'un rapport privé ;
- publication automatique d'un contenu issu des accords.

En cas de doute, arrêter le traitement et vérifier la politique documentaire.
