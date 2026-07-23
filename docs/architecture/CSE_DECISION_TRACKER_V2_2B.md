# CSE Decision & Action Tracker — V2-2B

## Objet

Le CSE Decision & Action Tracker suit les décisions, engagements de la
Direction et actions confiées aux élus à partir des seules métadonnées et
relations explicites du Document Intelligence Center.

Il complète le CSE Knowledge Engine sans le modifier et ne dépend d'aucun
Runtime, expert existant, connecteur ou corpus.

## Architecture

```text
Document Intelligence Center
        |
        | DocumentNavigationService
        v
CSE Knowledge Engine
        |
        | décisions et engagements explicites
        v
CSE Decision & Action Tracker
        |
        | tableau, ordre du jour et indicateurs metadata-only
        v
Futurs consommateurs CSE
```

Le tracker reçoit explicitement :

- un `CSEKnowledgeEngine`, pour les décisions et engagements déjà qualifiés ;
- un `DocumentNavigationService`, pour les actions des élus, les échéances et
  les liens de suivi.

Le paquet contient :

- `contracts.py` : protocole public stable ;
- `models.py` : requêtes, éléments suivis, récurrences, indicateurs et rapport
  immuables ;
- `policy.py` : normalisation explicite des statuts, dates et clés de
  récurrence ;
- `tracker.py` : agrégation déterministe en lecture seule.

## Relations et catégories explicites

Le tracker ne lit aucun PV. Un fait existe uniquement s'il est représenté par
des métadonnées sûres :

- décision : relation `DECIDES_ON` vers un nœud `DECISION` ;
- engagement de la Direction : nœud `MANAGEMENT_COMMITMENT` relié
  explicitement au PV ;
- action d'élu : nœud `ELECTED_ACTION` relié explicitement au PV ;
- suivi d'une décision : relation `APPLIES_TO`, `IMPLEMENTS` ou `RELATED_TO`
  vers un engagement ou une action.

Une décision sans une telle relation est signalée comme sans suivi.

## Cycle de vie

Les statuts documentaires sont ramenés sans inférence vers :

- `OPEN` ;
- `IN_PROGRESS` ;
- `CLOSED` ;
- `CANCELLED` ;
- `UNKNOWN`.

Une valeur non reconnue reste `UNKNOWN`. Le tracker ne corrige et ne complète
jamais automatiquement un statut.

## Échéances et déterminisme

L'échéance utilise exclusivement `effective_to` dans la projection publique de
navigation. Une action est en retard uniquement si :

- son échéance est antérieure à `as_of_date` ;
- son statut n'est ni clôturé ni annulé.

`as_of_date` est fourni par l'appelant. En son absence, aucun retard n'est
déduit. Le moteur ne consulte donc jamais l'horloge système.

Tous les résultats sont dédupliqués et triés par des clés stables. Deux appels
sur le même graphe avec la même requête produisent le même rapport JSON.

## Tableau de suivi et ordre du jour

Le rapport contient :

- décisions ;
- engagements de la Direction ;
- actions des élus ;
- décisions sans suivi ;
- groupes de décisions récurrentes ;
- point « Suivi des décisions précédentes » ;
- statistiques.

Le point d'ordre du jour exclut les éléments clôturés ou annulés et place les
actions en retard en premier. Il reste une liste de métadonnées explicables,
pas un texte généré.

## Indicateurs

Les statistiques comprennent :

- nombre de décisions, engagements et actions ;
- répartition par statut ;
- taux de clôture des décisions ;
- nombre d'actions d'élus en retard ;
- décisions sans suivi ;
- groupes de décisions récurrentes.

Le taux de clôture porte uniquement sur les décisions.

## Confidentialité

Les sorties sont limitées aux identifiants pseudonymisés et métadonnées sûres
de l'API de navigation. Elles n'exposent jamais :

- contenu de PV, extrait ou chunk ;
- PDF ou HTML ;
- URL et chemin local ;
- identifiant de stockage ;
- donnée personnelle ou secret.

## Limites

Le lot n'utilise ni LLM, ni IA générative, ni recherche sémantique, ni OCR, ni
embedding, ni base vectorielle, ni réseau. Il ne déduit pas une responsabilité
depuis un texte et ne juge pas la portée juridique d'une décision.
