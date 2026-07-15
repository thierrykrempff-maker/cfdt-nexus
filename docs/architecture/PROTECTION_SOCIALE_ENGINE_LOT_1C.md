# Protection sociale — LOT 1C

## Architecture et modèle

Le LOT 1C enrichit localement les JSON normalisés du LOT 1B avec des métadonnées métier traçables. Chaque champ contient une valeur éventuelle, une source de détection et un niveau de confiance. Une valeur non démontrée reste `null`.

Le moteur est indépendant du CSE Memory Engine. Ses règles explicites analysent les chemins, titres, en-têtes et fréquences de mots sans modèle externe. Les identifiants UUID v5 sont stables et la reprise vérifie l’empreinte source et la version d’extraction.

## Règles et thèmes

Les règles couvrent domaines mutuelle, prévoyance et autres thèmes techniques : garanties, remboursement, optique, dentaire, hospitalisation, pharmacie, médecine douce, audioprothèse, incapacité, invalidité, décès, rente, capital, maintien de salaire, portabilité, cotisations, affiliation, dispense et bénéficiaires.

Les champs émetteur, assureur, contrat, référence, version et dates ne sont retenus que lorsqu’un libellé explicite est présent. Les publics sont signalés uniquement par présence explicite. Aucun montant n’est extrait et aucune clause n’est interprétée juridiquement.

## Confiance et conflits

Les niveaux sont `very_high`, `high`, `medium`, `low` et `very_low`. Un libellé d’en-tête pèse davantage qu’un titre, un nom de fichier, un chemin ou une fréquence. La répétition cohérente renforce modérément la confiance ; plusieurs candidats la réduisent et créent un conflit explicite. Aucune alternative n’est inventée pour résoudre un conflit.

## Sorties et commandes

Les sorties locales ignorées sont sous `PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1C/` : JSON documentaires, manifeste, synthèse, rapport qualité, conflits et erreurs.

```powershell
python -m automation.protection_sociale.metadata_extractor --source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B/documents --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1C --mode dry-run
python -m automation.protection_sociale.metadata_extractor --source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B/documents --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1C --mode extract
```

## Confidentialité et limites

Le moteur ne fait aucun OCR, réseau, appel IA, résumé ou interprétation juridique. Il ne modifie aucune entrée et ne journalise aucun contenu complet. Les règles lexicales peuvent manquer des formulations non prévues ; ces absences restent explicites. Le LOT 1D pourra préparer des chunks techniques sans être commencé dans ce lot.
