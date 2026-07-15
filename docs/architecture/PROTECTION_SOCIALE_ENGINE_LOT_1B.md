# Protection sociale — LOT 1B

## Objectif et architecture

Le LOT 1B normalise localement les textes JSON produits par le LOT 1A et leur attribue une qualité technique déterministe. Il est indépendant du CSE Memory Engine et ne modifie ni les originaux ni les JSON sources.

Le pipeline lit chaque enregistrement séparément, produit un JSON normalisé et isole les erreurs. Une version de normalisation et un UUID v5 stable permettent la reprise sans retraitement ; `--force` autorise uniquement la réécriture des sorties LOT 1B.

## Règles de normalisation

Les fins de ligne sont homogénéisées, les caractères de contrôle inutiles supprimés, les espaces horizontaux multiples réduits et les suites excessives de lignes vides compactées. Les séparateurs techniques `PAGE`, `PARAGRAPH` et `TABLE` sont conservés explicitement.

Aucun texte n’est traduit, résumé, reformulé ou interprété. Les motifs de chemins absolus sont remplacés par une marque neutre dans les sorties locales.

## Qualité

Le score explicable de 0 à 100 détecte texte vide ou court, volume anormal, caractères suspects, répétitions, fragmentation, pages sans texte et extraction signalée comme partielle. Les niveaux sont `excellent`, `good`, `acceptable`, `poor` et `unusable`. Aucun document n’est supprimé selon son score.

## Sorties et commandes

Les sorties restent sous `PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B/` : JSON documentaires, `normalization_manifest.json`, `normalization_summary.md`, `quality_report.json` et `normalization_errors.json`.

```powershell
python -m automation.protection_sociale.text_normalizer --source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A/documents --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B --mode dry-run
python -m automation.protection_sociale.text_normalizer --source PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1A/documents --output PROTECTION_SOCIALE_ENGINE/PROCESSED/LOT_1B --mode normalize
```

Une limite et le réimport forcé sont disponibles. Les rapports ne contiennent aucun chemin absolu et restent ignorés par Git.

## Confidentialité et limites

Le pipeline n’utilise ni OCR, ni réseau, ni IA externe, ni modèle. Il ne qualifie aucune garantie, prestation, clause ou contrat. La normalisation demeure technique ; le LOT 1C pourra ajouter ultérieurement des métadonnées métier traçables, sans être commencé ici.
