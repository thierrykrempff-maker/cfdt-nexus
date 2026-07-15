# CSE Memory Engine — LOT 1B

## Objectif

Le LOT 1B transforme localement les JSON documentaires du LOT 1A en textes normalisés, blocs techniques et indicateurs de qualité. Il ne modifie ni les documents originaux ni les JSON LOT 1A.

Il ne réalise aucun OCR, appel réseau, recours à une IA externe, résumé, reformulation, analyse juridique ou indexation sémantique.

## Transformations appliquées

Les transformations sont prudentes, déterministes et consignées dans `transformations_applied` :

- homogénéisation des fins de ligne ;
- retrait des caractères de contrôle non imprimables, hors tabulations et retours utiles ;
- homogénéisation des espaces horizontaux et réduction des lignes vides excessives ;
- correction des espaces non ambigus autour des virgules, points, pourcentages et apostrophes ;
- conversion documentée des apostrophes, guillemets et tirets typographiques vers des formes stables ;
- recollement limité d'une césure de fin de ligne lorsqu'elle sépare deux fragments alphabétiques suffisamment longs et que le second commence par une minuscule ;
- neutralisation des chemins absolus éventuellement présents dans le texte dérivé.

Les séparateurs `PAGE`, `SLIDE` et `SHEET`, les accents, majuscules, nombres, dates, pourcentages, sigles, références et mots composés sur une même ligne sont préservés. Le pipeline ne corrige jamais le fond et n'invente aucun mot.

## Blocs techniques

Le texte normalisé est représenté par des blocs déterministes : séparateur, paragraphe, candidat titre, élément de liste, ligne de tableau ou bloc textuel. Chaque bloc possède un identifiant, un type, un ordinal, un localisateur de page/diapositive/feuille, un texte et une longueur.

Ces blocs préparent un futur découpage sans constituer des chunks sémantiques.

## Score qualité

Le score commence à 100 et applique des pénalités explicites :

- texte vide : score 0 ;
- texte très court : −35, texte court : −15 ;
- caractères non alphanumériques excessifs : −20 ;
- répétitions anormales : −15 ;
- lignes fragmentées ou mots isolés excessifs : −10 chacun ;
- pages sans texte : pénalité progressive, jusqu'à −25 ;
- PDF probablement composé d'images : −20 supplémentaire, sans OCR ;
- corruption ou encodage suspect : jusqu'à −30 ;
- volume supérieur à cinq millions de caractères : −10 ;
- extraction assortie d'avertissements : −8 ;
- faible rapport texte/taille source : −15 ;
- tableau fortement aplati : −10.

Les niveaux sont : `excellent` (90–100), `good` (75–89), `acceptable` (55–74), `poor` (25–54) et `unusable` (0–24). Aucun document n'est rejeté silencieusement.

## En-têtes et pieds répétés

Seules la première et la dernière ligne courte de chaque section paginée sont candidates. Une ligne doit apparaître sur au moins trois sections et 70 % des sections. Les seuils sont configurables dans l'API. Par défaut, les candidats sont signalés mais conservés. L'option explicite de suppression ne retire que les candidats à haute confiance et conserve localement la liste des suppressions.

## Sorties locales

Les résultats sont écrits uniquement sous `CCSEMEMORYENGINE/PROCESSED/LOT_1B`, déjà protégé par l'exclusion Git de `PROCESSED` :

- `documents/<document_id>.json` ;
- `manifests/normalization_manifest.json` ;
- `manifests/normalization_summary.md` ;
- `manifests/quality_report.json` ;
- `logs/normalization_errors.json`.

Aucun chemin absolu n'est conservé et aucun contenu complet n'est écrit dans les manifestes ou journaux.

## Exécution

```powershell
python -m automation.cse_memory.text_normalizer --source CCSEMEMORYENGINE/PROCESSED/LOT_1A/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1B --mode dry-run
```

```powershell
python -m automation.cse_memory.text_normalizer --source CCSEMEMORYENGINE/PROCESSED/LOT_1A/documents --output CCSEMEMORYENGINE/PROCESSED/LOT_1B --mode normalize
```

Les options permettent de filtrer par statut, extension ou sous-dossier, de limiter le nombre de fichiers, de reprendre sans retraitement, de forcer une réexécution et d'activer explicitement la suppression des en-têtes/pieds à haute confiance.

## Confidentialité, limites et LOT 1C

Le pipeline refuse une source `RAW_DOCUMENTS` et une sortie dans `RAW_DOCUMENTS` ou `LOT_1A`. Il ignore les liens symboliques, ne charge aucun modèle et ne lance aucun traitement externe.

La détection linguistique est un indice local rudimentaire (`fr`, `en`, `undetermined`) et non une classification. Le score qualité est heuristique. La césure et les en-têtes répétitifs privilégient la conservation en cas de doute.

Le LOT 1C pourra utiliser les blocs validés pour définir un découpage local et traçable, sans être commencé dans ce lot.
