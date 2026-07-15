# Protection sociale — LOT 1A

## Objectif et architecture

Le LOT 1A importe localement les PDF et DOCX du corpus confidentiel. Il produit un enregistrement JSON traçable par source, un manifeste, une synthèse, un rapport de doublons et un journal d’erreurs. Le module reste indépendant du CSE Memory Engine et ne modifie aucun autre moteur.

L’importeur parcourt les fichiers sans suivre les liens symboliques ni ouvrir les raccourcis LNK. Les erreurs sont isolées fichier par fichier. Les identifiants UUID v5 sont déterministes à partir du chemin relatif et de la version d’import.

## Extraction

Les PDF sont lus page par page avec `pypdf`. Chaque page reçoit un séparateur explicite ; les pages sans texte et PDF probablement constitués d’images sont signalés, sans OCR ni extraction d’image.

Les DOCX sont lus avec `python-docx`. Paragraphes et tableaux sont séparés explicitement, avec leurs compteurs. Les tableaux restent du texte technique sans interprétation de garanties, prestations ou clauses.

Les fichiers vides produisent le statut `empty` et un texte vide. Les erreurs ou formats non pris en charge conservent également une trace sans contenu inventé.

## Doublons et classification

Chaque copie exacte conserve son propre identifiant documentaire. Les membres partagent un `duplicate_group_id` stable dérivé du SHA-256 et portent `is_exact_duplicate=true`. Aucune copie n’est supprimée ou ignorée.

Les hints de domaine, catégorie et sous-catégorie proviennent exclusivement des règles de chemins du LOT 0. Ils ne constituent pas une qualification métier.

## Sorties et commandes

Toutes les sorties restent sous `PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A/`, ignoré par Git : JSON documentaires, `import_manifest.json`, `import_summary.md`, `duplicate_report.json` et `import_errors.json`.

```powershell
python -m automation.protection_sociale.document_importer --source PROTECTION_SOCIALE_ENGINE/RAW_DOCUMENTS --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A --mode dry-run
python -m automation.protection_sociale.document_importer --source PROTECTION_SOCIALE_ENGINE/RAW_DOCUMENTS --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A --mode import --balanced-sample
python -m automation.protection_sociale.document_importer --source PROTECTION_SOCIALE_ENGINE/RAW_DOCUMENTS --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A --mode import --force
```

Les filtres portent sur extension, domaine probable, catégorie probable et sous-dossier. Une limite globale est disponible. Sans `--force`, un JSON dont l’empreinte correspond est repris sans retraitement ; `--force` autorise sa réécriture, jamais celle de la source.

## Confidentialité et limites

Aucun chemin absolu n’est stocké. Aucun texte complet n’est journalisé. L’importeur refuse une sortie sous RAW_DOCUMENTS, ne modifie, déplace, renomme ou supprime aucun original et ne copie pas les binaires.

Le lot ne fait aucun OCR, appel réseau, appel à une IA, chargement de modèle ou analyse métier. La qualité et la normalisation du texte seront traitées dans le LOT 1B, qui n’est pas commencé ici.
