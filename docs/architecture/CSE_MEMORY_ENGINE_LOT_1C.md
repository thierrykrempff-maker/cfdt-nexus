# CSE Memory Engine — LOT 1C

Le LOT 1C extrait localement une carte d'identité documentaire traçable depuis les JSON normalisés du LOT 1B. Il ne réalise ni OCR, ni réseau, ni IA externe, ni analyse des sujets CSE.

Les sources sont pondérées dans cet ordre : premiers blocs (0,90), titre interne (0,85), nom de fichier (0,72), corps normalisé (0,45), dossiers parents (0,35), métadonnées techniques (0,15). Un accord indépendant renforce la confiance; un conflit conserve les alternatives et réduit la qualité globale. Les niveaux sont `very_high`, `high`, `medium`, `low` et `very_low`.

Les dates françaises textuelles, numériques et ISO sont validées calendrièrement. Le jour ou le mois manquant n'est jamais inventé. Les années hors de la plage raisonnable sont conservées seulement comme indices suspects. L'année, le mois et le trimestre sont dérivés uniquement d'une date complète retenue.

Le moteur reconnaît CSE, CE, CCE, CHSCT, CSSCT, NAO et commission comme métadonnées documentaires, sans traitement métier CSSCT. Il détecte les réunions explicites, les principales natures documentaires, les statuts prouvés, un titre structuré et les numéros explicitement précédés de PV ou réunion.

Les sorties locales ignorées sont écrites sous `CCSEMEMORYENGINE/PROCESSED/LOT_1C` : un JSON par document, manifeste, synthèse, rapport qualité, journal d'erreurs et rapport de conflits. Elles ne contiennent aucun chemin absolu ni extrait complet dans les rapports.

```powershell
python -m automation.cse_memory.metadata_extractor --source CCSEMEMORYENGINE/PROCESSED/LOT_1B/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1C --mode dry-run
python -m automation.cse_memory.metadata_extractor --source CCSEMEMORYENGINE/PROCESSED/LOT_1B/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1C --mode extract
```

La reprise compare l'empreinte source et la version d'extraction; `--force` réexécute. Les heuristiques restent prudentes : aucune valeur absente n'est inventée, et les ambiguïtés demeurent visibles. Le LOT 1D pourra exploiter ces cartes d'identité sans être commencé ici.
