# Corpus de cas métier réels Nexus

Ce répertoire prépare une validation métier fondée sur des situations réelles
anonymisées. Il ne contient ni réponse juridique pré-écrite, ni règle ajoutée à
un moteur Nexus.

## Séparation obligatoire des données

Chaque fixture comporte deux compartiments :

- `case_input` : seules données qui pourront être présentées à Nexus ;
- `evaluation_only` : données réservées à l'évaluateur, jamais injectées dans
  la demande initiale.

L'issue réellement connue est conservée dans
`evaluation_only.known_outcome`. Elle sert uniquement, après production de la
réponse, à vérifier que Nexus a envisagé des options réalistes. Elle ne doit
jamais :

- servir à rédiger la demande envoyée à Nexus ;
- imposer à Nexus de prédire l'issue exacte ;
- augmenter artificiellement la note d'une réponse rétrospective ;
- remplacer l'analyse des faits disponibles au moment de la demande.

## Fichiers de méthode

- `fixture.schema.json` définit le format commun des six futurs cas ;
- `scoring-rubric.json` définit les huit notes, les seuils et les échecs
  éliminatoires ;
- `tag-on-installation.example.json` est le premier exemple rempli.

Le cas 5 devra porter `completeness.status: "incomplete"` et ne comporter
aucune fin inventée. Le cas 6 devra inclure comme question bloquante la demande
de définition de la « règle des 10 % » ; aucune analyse de fond ne devra être
notée comme satisfaisante avant cette clarification.

## Protocole d'évaluation

1. Construire la demande Nexus exclusivement depuis `case_input`.
2. Conserver `evaluation_expectations` côté évaluateur.
3. Produire la réponse sans accès à `evaluation_only`.
4. Noter séparément les huit dimensions de `scoring-rubric.json`.
5. Appliquer les échecs éliminatoires avant de regarder le total.
6. Ouvrir seulement ensuite `evaluation_only.known_outcome` afin de vérifier
   que l'éventail des issues proposées contenait des options réalistes.

Une réponse riche en sources mais qui déforme le fait principal échoue, quel
que soit son score arithmétique.
