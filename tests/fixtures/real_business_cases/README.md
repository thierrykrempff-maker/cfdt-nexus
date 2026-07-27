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

- `fixture.schema.json` définit le format commun des six cas ;
- `scoring-rubric.json` définit les huit notes, les seuils et les échecs
  éliminatoires ;
- `tag-on-installation.example.json` décrit le tag sur installation ;
- `insulting-emails-alcohol.json` décrit les courriels insultants ;
- `smoking-breaks-seveso-badge.json` décrit les pauses et le badgeage ;
- `forced-day-to-shift-laboratory.json` décrit le passage jour/poste ;
- `delegation-hours-cssct-incomplete.json` décrit le cas CSSCT incomplet ;
- `annual-leave-ten-percent-rule-unresolved.json` conserve l'ambiguïté des
  « 10 % ».

Le cas 5 porte `completeness.status: "incomplete"` et ne comporte aucune fin
inventée. Le cas 6 porte
`analysis_state: "unresolved_pending_clarification"` et inclut comme question
bloquante la demande de définition de la « règle des 10 % » ; aucune analyse de
fond n'est notée comme satisfaisante avant cette clarification.

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

## Baseline

Les réponses publiques brutes sont produites avec :

```text
python tools/run_real_business_cases_baseline.py run --source-limit 8
```

Le runner affecte explicitement le parcours disciplinaire aux cas 1 à 3 et le
parcours Question salarié aux cas 4 à 6. Il construit chaque demande par
`build_case_prompt()` à partir du seul objet `case_input`.

Après relecture sémantique consignée dans
`baseline/baseline-assessment.json`, les scores et le rapport sont produits
avec :

```text
python tools/run_real_business_cases_baseline.py evaluate
```

Le contrôle d'empreinte vérifie que chaque réponse brute correspond toujours à
la version exacte de `case_input` qui a été exécutée.
