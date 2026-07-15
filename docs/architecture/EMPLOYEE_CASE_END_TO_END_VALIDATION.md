# Validation de bout en bout du dossier salarié — LOT 5F

## Périmètre

Cette validation démontre l'intégration des composants existants sans ajouter de fonction métier :

1. pipeline LOT 5A ;
2. rapport LOT 5B ;
3. Cockpit LOT 5C ;
4. comparateur LOT 5D ;
5. export LOT 5E.

La suite utilise uniquement les fixtures synthétiques versionnées. Elle ne modifie ni le pipeline, ni le rapport, ni le Cockpit, ni le comparateur, ni l'exporteur.

## Scénarios exécutés

- heures supplémentaires avec dossier complet ;
- astreinte incomplète ;
- maladie avec contradiction documentaire ;
- classification sans fiche de poste ;
- congés payés avec dossier complet.

Pour chaque scénario, les douze étapes du pipeline terminent, le rapport et ses deux vues sont présents, les données exposées au Cockpit sont cohérentes et les exports JSON, Markdown et texte sont produits sans écriture disque. Les thèmes incomplets restent bloqués localement et la contradiction de période d'absence reste visible.

## Cockpit

La validation démarre le serveur local sur une adresse de boucle et un port éphémère. Elle vérifie la liste des cinq scénarios, charge chaque dossier via l'endpoint réel, contrôle les deux vues, les thèmes bloqués et les contradictions, puis confirme qu'un scénario inconnu produit une erreur HTTP explicite.

Les tests frontend et HTTP historiques du Cockpit restent également inclus dans la campagne complète.

## Comparateur

Trois configurations sont contrôlées :

- rapport comparé à lui-même : aucune dimension de fond modifiée ;
- état avant/après : période classée `modified` ;
- rapport complet contre rapport incomplet : thèmes et documents manquants différenciés.

Les catégories `new`, `removed`, `modified` et `unchanged` restent stables. Des copies profondes vérifient l'immutabilité des deux entrées.

## Export et confidentialité

Les rapports simples et comparatifs sont exportés en JSON, Markdown et texte. Les indicateurs confirment l'absence de calcul, d'appel expert et d'écriture disque.

Chaque objet généré est soumis au scanner LOT 4F. Aucun export ne doit produire de donnée interdite. La sixième fixture, exclue du Cockpit public, conserve une sonde construite en mémoire : le pipeline doit la bloquer à l'étape dédiée `check_confidentiality`.

## Performances indicatives

Mesures locales sur 20 itérations du scénario complet, Python standard, Windows, le 15 juillet 2026 :

| Composant | Temps moyen observé |
|---|---:|
| Pipeline | 0,730 ms |
| Rapport | 0,183 ms |
| Comparateur | 0,915 ms |
| Export JSON | 0,931 ms |

Ces mesures ne sont pas des seuils d'acceptation et varient selon la machine. Les lectures de fixture sont incluses uniquement avant le chronométrage du pipeline. Aucune optimisation n'est réalisée dans ce lot.

## Résultats et limites

Les 13 contrôles dédiés de bout en bout réussissent. Ils couvrent cinq scénarios, les endpoints locaux, trois configurations de comparaison, les trois formats d'export, la confidentialité et les quatre mesures de performance. La campagne complète des LOTS 1 à 5F est exécutée séparément avant validation du lot.

Limites :

- données exclusivement synthétiques ;
- aucun document réel, OCR ou PDF ;
- aucune persistance ;
- aucun calcul de paie ;
- aucune conclusion juridique ;
- performances locales non représentatives d'une charge de production concurrente.

## Recommandations avant fusion

- conserver les contrôles de confidentialité et les tests de non-calcul comme conditions de fusion ;
- vérifier que seuls ce test d'intégration et cette documentation ont changé ;
- réexécuter la campagne complète et les référentiels sur le commit destiné à la fusion ;
- traiter séparément toute future persistance, gestion d'accès ou génération PDF.
