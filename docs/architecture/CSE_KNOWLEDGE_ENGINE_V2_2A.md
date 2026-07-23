# CSE Knowledge Engine — V2-2A

## Objet

Le CSE Knowledge Engine est le premier moteur consommateur du Document
Intelligence Center. Il transforme exclusivement des métadonnées documentaires
déjà présentes dans le graphe en vues déterministes utiles à la préparation et
au suivi du CSE.

Il n'est raccordé ni au Runtime, ni à un expert existant. Il ne lit aucun
document, ne réalise aucune recherche sémantique et n'effectue aucun appel
réseau.

## Architecture

Le moteur dépend uniquement de l'API publique `DocumentNavigationService`.
Le Document Intelligence Center ne dépend pas du moteur.

```text
Document Intelligence Center
        |
        | NavigationDocument / DocumentRelation
        v
CSEKnowledgeEngine
        |
        | CSEKnowledgeReport metadata-only
        v
Futurs consommateurs CSE
```

Le paquet contient :

- `contracts.py` : protocole public indépendant des futurs consommateurs ;
- `models.py` : requêtes, faits, synthèses, récurrences, ordre du jour et
  rapport immuables ;
- `policy.py` : règles lexicales, catégories contrôlées et statuts ouverts ;
- `engine.py` : navigation, agrégation et production déterministe du rapport.

## Sources de vérité

Le moteur ne déduit pas une décision, un engagement ou une consultation à
partir d'un texte. Ces faits doivent être représentés par des nœuds metadata-only
et des relations explicites :

- `DECIDES_ON` vers un nœud de nature `DECISION` ;
- `DISCUSSES` ou `IMPLEMENTS` vers `MANAGEMENT_COMMITMENT` ;
- `DISCUSSES` ou `REFERENCES` vers `CONSULTATION`.

Les sujets récurrents utilisent uniquement la famille documentaire contrôlée.
La recherche par sujet est une correspondance lexicale normalisée sur le titre,
la famille et la nature publics. Elle ne constitue pas une recherche
sémantique.

## Fonctions publiques

- `find_minutes_by_subject()` retrouve les PV CSE liés à un sujet ;
- `find_decisions()` retrouve les décisions explicites ;
- `track_management_commitments()` regroupe le suivi des engagements ;
- `past_consultations()` restitue les consultations passées ;
- `recurring_subjects()` identifie les familles présentes dans plusieurs PV ;
- `prepare_agenda()` priorise les engagements ouverts et sujets récurrents ;
- `summarize_meetings()` produit une synthèse metadata-only par réunion ;
- `build_report()` assemble ces vues dans un rapport sérialisable.

## Déterminisme

Les nœuds, faits, relations, sujets et éléments d'ordre du jour sont dédupliqués
et triés par clés stables. Une même requête sur un même graphe produit le même
JSON. Le moteur est en lecture seule et ne modifie pas le graphe.

## Confidentialité

Les sorties ne contiennent que les projections sûres de l'API de navigation :
identifiants pseudonymisés, titres, dates, familles, natures, statuts et
instances. Sont exclus :

- contenu documentaire, extraits et chunks ;
- PDF et HTML ;
- URL canoniques et chemins locaux ;
- identifiants de stockage ;
- données personnelles et secrets.

Les requêtes et tous les libellés produits passent par la validation de
métadonnées sûre du Document Intelligence Center.

## Limites du lot

Ce lot ne contient ni IA générative, ni LLM, ni embeddings, ni recherche
sémantique, ni réseau. Il n'évalue pas la portée juridique d'une décision et ne
génère pas de texte de réunion. L'ordre du jour est une liste explicable de
métadonnées historiques, destinée à être consommée ultérieurement.
