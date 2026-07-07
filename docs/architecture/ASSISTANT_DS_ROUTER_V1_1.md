# Assistant DS Router V1.1 / V1.2 corrective

## Role

`automation/scripts/assistant_ds_router.py` reste le routeur local de l'Assistant DS CFDT Nexus. La version 1.1 ne remplace pas les moteurs specialistes (`agreements_bible.py`, `nexus_bible_bridge.py`) : elle ameliore la fusion finale produite par `ask`.

La correction V1.2 conserve l'interface V1.1 et cible trois points : intention reelle des questions reunion CSE/repos, hierarchisation des sources par sous-probleme, et reponse courte avant methode de controle.

## Correctifs V1.2

- une reunion CSE pendant un repos 5x8 est traitee comme une articulation mandat CSE / temps de travail, pas comme un projet collectif de reduction du repos ;
- le simple mot `CSE` ne suffit plus a declencher `preparer_cse` ;
- les sources restauration, interessement, harmonisation remuneration et forfait jours sont repoussees lorsqu'elles sont hors sujet ou hors population ;
- les sujets astreinte + repos + paie priorisent l'accord Astreinte, les sources repos/temps de travail, puis les complements paie ;
- `ask` affiche une reponse courte avant les sources, la position, les points a verifier, les documents et les questions.

## Nouveautes V1.1

- reranking contextuel des sources fusionnees selon domaine principal, domaines secondaires, intention, question, titre, type implicite et moteur d'origine ;
- selection finale lisible de 4 a 6 sources principales par defaut avec `--source-limit` ;
- limitation des pages d'un meme document, tout en conservant plusieurs pages quand elles restent tres pertinentes ;
- dedoublonnage semantique leger des constats, documents, questions et avertissements ;
- construction explicite de `working_position` par patron metier ;
- ajout de `issue_groups` pour les demandes multi-domaines ;
- profondeur de reponse adaptee aux questions simples, dossiers individuels, points CSE et sujets multi-domaines ;
- separation des garde-fous generiques dans un bloc court de prudence.

## Reranking Contextuel

Le routeur conserve les scores des moteurs, puis ajoute un score d'orchestration deterministe. Ce score utilise :

- les domaines detectes (`classification_carriere`, `temps_travail`, `astreinte`, etc.) ;
- les intentions (`preparer_cse`, `analyser_paie`, `verifier_conformite`, etc.) ;
- les mots significatifs de la question ;
- le document, la page, l'article et le contexte de pertinence fourni par les moteurs ;
- des bonus metier, par exemple accord astreinte, accord 5x8, GEPP, CCNIC ;
- des penalites contextuelles, par exemple teletravail, CET ou forfait jours lorsqu'ils ne sont pas directement pertinents.

Une source n'est pas exclue uniquement a cause de son titre. Un document bruite peut rester si le passage porte reellement sur le sujet.

## Dedoublonnage

La V1.1 applique une deduplication semantique simple et reproductible :

- normalisation via la Bible Accords ;
- minuscules, accents neutralises par le moteur existant ;
- tokens significatifs ;
- racinisation legere ;
- similarite Jaccard.

Elle s'applique aux listes finales `findings`, `documents_to_request`, `questions_to_ask`, `warnings` et aux groupes d'enjeux.

## Working Position

`working_position` n'est plus extraite du premier document ou de la premiere condition minimale du pont CSE. Elle est construite par `build_working_position(route, findings, engine_results)`.

Patrons couverts :

- classification/carriere ;
- temps de travail + preparation CSE ;
- astreinte + repos + paie ;
- inaptitude/reclassement ;
- disciplinaire ;
- droit syndical ;
- paie/remuneration ;
- conges payes ;
- CSSCT/securite ;
- question simple de droit local.

La phrase reste prudente, complete et adaptee au domaine.

## Issue Groups

Les demandes multi-domaines ajoutent une structure compatible JSON :

```json
{
  "issue_groups": [
    {
      "id": "repos",
      "name": "Repos et reprise du poste",
      "findings": [],
      "documents": [],
      "questions": []
    }
  ]
}
```

Les listes globales V1 (`findings`, `documents_to_request`, `questions_to_ask`) restent presentes pour compatibilite cockpit.

## Profondeur Adaptative

- `question_simple` : reponse courte, sources limitees.
- `situation_individuelle` : fiche dossier salarie concise.
- `preparation_cse` : synthese du moteur CSE sans recopier toute la fiche detaillee.
- `multi_domain` : presentation par enjeux.

## CLI

```powershell
python automation/scripts/assistant_ds_router.py ask --query "..." --source-limit 6
python automation/scripts/assistant_ds_router.py ask --query "..." --format json
python automation/scripts/assistant_ds_router.py diagnose
python automation/scripts/assistant_ds_router.py run-scenarios
```

`--source-limit` vaut 6 par defaut et reste plafonne raisonnablement.

## Compatibilite JSON

La V1.1 preserve les champs V1 et ajoute proprement :

- `route.router_version`
- `route.primary_domain`
- `route.secondary_domains`
- `issue_groups`
- `response_depth`

Les champs internes de reranking ne sont pas exposes dans les sources finales.

## Limites

- Le routeur ne remplace pas l'analyse juridique humaine.
- Les modules paie dedie, veille juridique et analyse documentaire directe restent signales comme non connectes lorsqu'ils ne sont pas executables.
- Les resultats locaux et rapports prives restent dans `local-index/` et ne doivent pas etre committes.

## Exemples

Classification :

> Objectiver l'ecart entre la classification actuelle et les fonctions reellement exercees avant de demander un reexamen motive du coefficient.

CSE repos 5x8 :

> Ne pas accepter une reduction du repos sans projet ecrit, base juridique precise, comparaison avant/apres, evaluation des impacts sur la fatigue et garanties de prevention et de compensation.

Astreinte + repos + paie :

> Verifier separement le respect du repos apres intervention, la comptabilisation du temps d'intervention et l'application des majorations, puis rapprocher l'accord d'astreinte, les horaires reels, les compteurs et les bulletins de paie.
