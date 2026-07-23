# CSE Meeting Preparation Engine — V2-2C

## Objet

Le CSE Meeting Preparation Engine construit un dossier metadata-only pour une
future réunion CSE à partir de l'historique déjà structuré dans le Document
Intelligence Center.

Il assemble les services existants sans les modifier :

- `DocumentNavigationService` ;
- `CSEKnowledgeEngine` ;
- `CSEDecisionTracker`.

Il n'est raccordé ni au Runtime, ni aux experts existants.

## Architecture

```text
Document Intelligence Center
        |
        v
Document Navigation API
        |
        +--> CSE Knowledge Engine
        |
        +--> CSE Decision Tracker
                    |
                    v
        CSE Meeting Preparation Engine
                    |
                    v
      Dossier metadata-only sérialisable
```

Le paquet contient :

- `contracts.py` : protocole public de préparation ;
- `models.py` : requête, références documentaires, ordre du jour, indicateurs
  et dossier immuables ;
- `policy.py` : dates, priorités et règles de sélection explicites ;
- `engine.py` : assemblage déterministe en lecture seule.

## Date de référence

La date de réunion est obligatoire et injectée par l'appelant. Elle sert à
identifier les engagements dont l'échéance explicite `effective_to` intervient
avant ou le jour de la réunion.

Le moteur ne consulte jamais l'horloge système. Un engagement sans échéance
explicite n'est pas qualifié comme arrivant à échéance.

## Sources des points préparatoires

Le dossier reprend uniquement :

- décisions non clôturées ou non annulées ;
- engagements de la Direction arrivant à échéance ;
- actions d'élus non clôturées ;
- consultations non clôturées ;
- sujets récurrents issus des familles documentaires ;
- PV précédents correspondant au sujet ;
- accords explicitement liés à ces PV.

Aucune relation n'est déduite depuis le texte d'un document.

## Ordre du jour

Les points sont classés selon trois priorités opérationnelles :

1. `REQUIRED_FOLLOW_UP` pour une décision ouverte ou un engagement arrivé à
   échéance ;
2. `HIGH` pour une action d'élu ou une consultation en cours ;
3. `NORMAL` pour un sujet récurrent.

Cette priorité exprime un besoin de suivi documentaire. Elle ne constitue
jamais une qualification juridique d'obligation de consultation.

Chaque point conserve les identifiants pseudonymisés de ses sources et des
accords explicitement liés. Les tris utilisent des clés stables.

## Indicateurs

Le dossier expose :

- nombre de PV précédents ;
- nombre d'accords liés ;
- décisions ouvertes ;
- engagements arrivant à échéance ;
- actions d'élus ouvertes ;
- consultations en cours ;
- sujets récurrents ;
- points d'ordre du jour.

## Déterminisme et idempotence

À graphe et requête identiques, le moteur produit les mêmes objets et le même
JSON. Il ne modifie ni le graphe, ni le CSE Knowledge Engine, ni le Decision
Tracker.

## Confidentialité

Les sorties contiennent uniquement des métadonnées sûres :

- identifiants pseudonymisés ;
- titres ;
- types documentaires ;
- dates ;
- familles ;
- statuts.

Elles ne contiennent jamais de contenu de PV, extrait, chunk, PDF, HTML, URL,
chemin local, identifiant de stockage, donnée personnelle ou secret.

## Limites

Le lot ne contient ni LLM, ni IA générative, ni recherche sémantique, ni OCR,
ni embedding, ni base vectorielle, ni réseau. Il ne rédige pas un ordre du
jour juridique : il prépare une liste metadata-only explicable à faire valider
par les utilisateurs compétents.
