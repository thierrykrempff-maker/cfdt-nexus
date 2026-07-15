# Referentiel Paie INEOS Sarralbe V1 - LOT 4A

## Objectif

Le LOT 4A cree le socle technique du futur referentiel metier Paie INEOS Sarralbe.

Il ne modifie pas le moteur de regles, l'expert paie, le routeur Nexus, les interfaces ou le site public.

Son role est de preparer trois familles de donnees distinctes :

- rubriques Nibelis ;
- compteurs Kelio ;
- parametres de paie.

Ces donnees restent separees des regles metier `PayrollRule`.

## Principe de securite

Les fichiers ajoutes dans ce lot ne contiennent que des exemples synthetiques.

Interdictions maintenues :

- aucun bulletin reel ;
- aucun matricule ;
- aucune donnee bancaire ;
- aucune donnee de sante nominative ;
- aucune adresse personnelle ;
- aucun export Kelio reel ;
- aucun parametre confidentiel applique a un salarie.

Les exemples portent `fixture_type = synthetic_example` et chaque enregistrement porte `synthetic_only = true`.

## Fichiers crees

Schemas :

```text
database/payroll/referentials/nibelis-rubrics.schema.json
database/payroll/referentials/kelio-counters.schema.json
database/payroll/referentials/payroll-parameters.schema.json
```

Exemples synthetiques :

```text
database/payroll/referentials/nibelis-rubrics.example.json
database/payroll/referentials/kelio-counters.example.json
database/payroll/referentials/payroll-parameters.example.json
```

Validation :

```text
automation/payroll/payroll_referential_validator.py
automation/payroll/test_payroll_referential_validator.py
```

## Distinction des donnees

Chaque enregistrement declare `data_role` :

- `source_data` : donnee lue dans un systeme ou document source ;
- `calculated_data` : donnee issue d'un calcul ou d'une transformation ;
- `controlled_data` : donnee a verifier ou rapprocher, par exemple une ligne bulletin.

Cette distinction evite de confondre :

- une regle juridique ;
- un compteur Kelio ;
- une ligne de bulletin ;
- un parametre de calcul.

## Rubriques Nibelis

Le schema Nibelis modelise uniquement la presentation ou le controle d'une ligne de bulletin.

Une rubrique Nibelis ne devient pas une source juridique INEOS.

Champs importants :

- `rubric_id` ;
- `rubric_code` ;
- `category` ;
- `payroll_topic` ;
- `unit` ;
- `linked_rule_ids` ;
- `linked_variables` ;
- `linked_kelio_counter_ids` ;
- `data_role` ;
- `calculation_allowed`.

Dans les exemples LOT 4A, `calculation_allowed` reste toujours `false`.

## Compteurs Kelio

Le schema Kelio modelise une donnee de temps, absence, repos, planning ou compteur.

Champs importants :

- `counter_id` ;
- `counter_code` ;
- `counter_type` ;
- `unit` ;
- `work_schedule` ;
- `employee_population` ;
- `linked_rule_ids` ;
- `linked_variables` ;
- `linked_nibelis_rubric_ids` ;
- `reading_method`.

Un compteur Kelio peut aider a etablir un fait, mais il ne suffit pas a lui seul a conclure sur un droit.

## LOT 4B - Referentiel metier Kelio synthetique

Le LOT 4B enrichit le referentiel Kelio avec des compteurs synthetiques pedagogiques.

Objectif :

- aider Nexus a comprendre ce qu'un compteur represente ;
- expliquer comment il peut augmenter ou diminuer ;
- lister les documents a demander ;
- signaler les anomalies frequentes ;
- preparer les points de controle ;
- conserver une separation nette entre compteur, variable metier et regle de paie.

### Compteurs couverts

Le referentiel synthetique couvre notamment :

- `JR_SYN` ;
- `RJFJ_SYN` ;
- `RJFN_SYN` ;
- `RCTP_SYN` ;
- `RCTR_SYN` ;
- `CP_SYN` ;
- `HS_SYN` ;
- `AST_SYN` ;
- `INT_SYN` ;
- `RC_SYN` ;
- `RQ_SYN` ;
- `RH_SYN` ;
- `PNT_SYN` ;
- `ABS_SYN` ;
- `NUIT_SYN` ;
- `DIM_SYN` ;
- `FERIE_SYN`.

Ces codes sont volontairement fictifs. Ils ne doivent jamais etre presentes comme des codes Kelio reels ou des codes INEOS confirmes.

### Compteur, variable et regle

Un compteur Kelio est une donnee de lecture ou de controle.

Exemple :

```text
KELIO_HS_SYN
```

Une variable metier est une information attendue par une regle.

Exemple :

```text
heures_validees
```

Une regle de paie est une structure issue du catalogue `PayrollRule`.

Exemple :

```text
PAY_HSUP_TRANCHES_001
```

Le compteur peut aider a renseigner ou verifier une variable, mais il ne remplace pas la regle et ne suffit pas a calculer une paie.

### Documentation metier obligatoire

Chaque compteur Kelio synthetique doit contenir :

- une description metier ;
- des conditions generales d'alimentation ;
- des conditions generales de diminution ;
- des documents a controler ;
- des anomalies frequentes ;
- des points de controle ;
- au moins un exemple synthetique de lecture ;
- un niveau de risque.

Le validateur refuse une fixture Kelio si cette documentation minimale est absente.

### Limites du referentiel synthetique

Le referentiel Kelio du LOT 4B :

- ne contient aucun export Kelio reel ;
- ne contient aucun compteur individuel ;
- ne contient aucun planning nominatif ;
- ne prouve aucun droit a lui seul ;
- ne cree aucune formule ;
- ne change pas `calculation_allowed` ;
- ne modifie pas le moteur de regles.

Les compteurs de nuit, dimanche et repos hebdomadaire sont presents comme indicateurs de controle, mais le catalogue actuel ne contient pas encore forcement de regle de paie dediee pour chacun d'eux.

### Introduction future de donnees reelles

Avant toute donnee Kelio reelle, il faudra :

1. anonymiser strictement les exports ou captures ;
2. supprimer noms, matricules, horaires individuels identifiants si non indispensables, services trop precis et commentaires libres ;
3. conserver les donnees reelles hors GitHub ;
4. documenter la source, la date du releve et la methode de lecture ;
5. faire valider humainement le rattachement compteur -> variable -> regle ;
6. garder `calculation_allowed = false` tant que la source et le calcul ne sont pas audites.

### Validation humaine future

La validation devra confirmer :

- que le code correspond bien au compteur attendu ;
- que le libelle est stable ;
- que l'unite est correcte ;
- que la population concernee est exacte ;
- que la periode d'effet est connue ;
- que le compteur ne duplique pas un autre compteur ;
- que les regles rattachees sont les bonnes ;
- que les limites d'interpretation sont comprises.

## LOT 4C - Referentiel metier Nibelis synthetique

Le LOT 4C enrichit le referentiel Nibelis avec des rubriques synthetiques pedagogiques.

Objectif :

- modeliser les grandes familles visibles ou controlables sur un bulletin ;
- expliquer le role metier d'une rubrique sans utiliser de code Nibelis reel ;
- relier prudemment une rubrique a une variable metier, un compteur Kelio ou une regle existante ;
- preparer les futurs rapprochements bulletin / Kelio / accords sans activer de calcul ;
- imposer l'anonymisation avant toute utilisation de bulletin reel.

### Rubriques couvertes

Le referentiel synthetique contient 26 rubriques couvrant notamment :

- salaire de base ;
- primes ;
- heures supplementaires ;
- nuit, dimanche et jours feries ;
- astreinte et intervention ;
- conges payes ;
- absences et retenues ;
- maladie, IJSS, subrogation et accident du travail ;
- 13e mois ;
- indemnite kilometrique ;
- panier repas ;
- regularisations et rappels ;
- informations de compteurs.

Tous les codes finissent par `_SYN`. Ils sont volontairement fictifs et ne doivent jamais etre presentes comme des codes Nibelis reels, des codes INEOS confirmes ou des parametres de paie utilisables.

### Rubrique, compteur, variable et regle

Une rubrique Nibelis represente une ligne de presentation ou de controle.

Exemple :

```text
NIB_RUB_HSUP_MAJ / HS_MAJ_SYN
```

Un compteur Kelio represente une donnee de temps ou de planning.

Exemple :

```text
KELIO_HS_SYN
```

Une variable metier est une information attendue par une regle.

Exemple :

```text
heures_validees
```

Une regle de paie reste la seule structure destinee a porter une logique metier opposable, quand elle sera verifiee.

Exemple :

```text
PAY_HSUP_TRANCHES_001
```

Le lien Nibelis -> Kelio -> variable -> regle aide a organiser le controle. Il ne prouve pas un droit et ne declenche aucun calcul automatique.

### Documentation metier obligatoire

Chaque rubrique Nibelis synthetique doit contenir :

- une description metier ;
- une source generique ;
- des documents a controler ;
- des anomalies frequentes ;
- des points de controle ;
- au moins un exemple synthetique de lecture ;
- l'indication de presence sur bulletin ;
- l'impact brut attendu ;
- l'obligation d'anonymisation.

Le validateur refuse une fixture Nibelis si cette documentation minimale est absente.

### Controles metier specifiques

Le validateur ajoute des garde-fous propres a Nibelis :

- une rubrique de retenue doit avoir `gross_impact = negative` ;
- une rubrique informative ne peut pas impacter le brut ;
- une rubrique `counter_information` doit rester informative ;
- une rubrique annoncee non visible ne peut pas etre decrite comme visible sur bulletin ;
- une rubrique visible sur bulletin doit imposer `anonymization_required = true`.

### Anonymisation avant donnees reelles

Avant toute analyse d'un bulletin reel, il faudra supprimer ou masquer :

- nom et prenom ;
- matricule ;
- adresse ;
- donnees bancaires ;
- numero de securite sociale ;
- informations de sante nominatives ;
- service ou contexte permettant d'identifier directement un salarie si non indispensable ;
- commentaires libres ou mentions individuelles.

Les bulletins reels, exports Nibelis et rapprochements individuels doivent rester hors GitHub.

### Rapprochement futur bulletin / Kelio / accords

Le LOT 4C prepare une future methode de controle :

1. identifier une rubrique de bulletin ;
2. verifier son code et son libelle dans un referentiel local prive ;
3. rapprocher la rubrique du ou des compteurs Kelio utiles ;
4. relier les donnees aux variables attendues par une regle ;
5. citer l'accord, la convention ou la source juridique applicable ;
6. demander une validation humaine avant toute conclusion.

Tant que cette chaine n'est pas complete, `calculation_allowed` reste `false`.

## LOT 4D - Referentiel des parametres de paie synthetiques

Le LOT 4D enrichit le referentiel des parametres de paie.

Objectif :

- identifier les valeurs dont un calcul aurait besoin ;
- documenter leur type, leur unite, leur periode et leur source ;
- verifier les liens avec les regles, variables, compteurs Kelio et rubriques Nibelis ;
- empecher toute utilisation d'une valeur fictive comme valeur INEOS ;
- preparer une future validation humaine avant tout calcul.

### Role d'un parametre de paie

Un parametre est une valeur, un seuil, un taux, une date, une methode ou un plafond necessaire a l'interpretation d'une regle.

Exemples :

- seuil de declenchement d'heures supplementaires ;
- niveau de majoration ;
- valeur d'une astreinte ;
- duree minimale de repos ;
- methode de comparaison pour les conges payes ;
- valeur kilometrique ;
- date de regularisation.

Un parametre ne remplace jamais la regle.

### Regle, variable, compteur, rubrique et parametre

Une regle de paie porte la logique metier.

Exemple :

```text
PAY_HSUP_TRANCHES_001
```

Une variable est une information attendue par la regle.

Exemple :

```text
heures_validees
```

Un compteur Kelio aide a verifier un fait de temps ou de planning.

Exemple :

```text
KELIO_HS_SYN
```

Une rubrique Nibelis aide a identifier une ligne de bulletin.

Exemple :

```text
NIB_RUB_HSUP_MAJ
```

Un parametre documente la valeur ou la methode qui pourrait etre necessaire.

Exemple :

```text
PARAM_HSUP_MAJ_SYN
```

La chaine complete reste :

```text
source reelle -> parametre valide -> variable -> regle -> controle humain -> conclusion prudente
```

### Etats possibles d'une valeur

Le champ `value_state` distingue :

- `identified_value_unknown` : parametre identifie, valeur inconnue ;
- `synthetic_test_value` : valeur fictive de test ;
- `awaiting_source` : valeur en attente de source ;
- `awaiting_human_validation` : valeur a verifier humainement ;
- `structurally_checked_not_applicable` : structure controlee mais non applicable ;
- `calculation_ready` : etat futur interdit dans les fixtures synthetiques.

Dans les exemples LOT 4D, aucun parametre n'est `calculation_ready`.

### Nature de la donnee

Les champs `data_role` et `value_kind` permettent de distinguer :

- donnee source ;
- donnee saisie ;
- donnee derivee ;
- donnee controlee ;
- donnee validee.

Cette separation evite de confondre une valeur lue, une valeur recopiee, une methode et une valeur juridiquement utilisable.

### Dates d'effet et de fin

Chaque parametre porte :

- `effective_date` ;
- `end_date` ;
- `application_period.start_date` ;
- `application_period.end_date`.

Le validateur refuse :

- une date ISO invalide ;
- une date de fin anterieure a la date d'effet ;
- une periode d'application incoherente ;
- deux parametres mutuellement exclusifs qui se chevauchent.

### Cycle de validation humaine

Un parametre futur ne pourra devenir exploitable que si les conditions suivantes sont reunies :

- source identifiable ;
- reference precise ;
- date d'effet valide ;
- valeur compatible avec le type, l'unite, la devise ou le pourcentage ;
- `validation_status = human_validated` ;
- `human_validation.status = validated` ;
- `confidence = high` ;
- `synthetic_only = false` ;
- `value_state = calculation_ready` ;
- validation par un role generique autorise, par exemple `expert_paie_humain`.

Les fixtures synthetiques ne remplissent volontairement pas ces conditions.

### Valeurs par defaut interdites

Le LOT 4D interdit les valeurs de secours silencieuses.

Un parametre peut exister sans valeur exploitable, mais il doit alors :

- porter un etat clair comme `identified_value_unknown` ou `awaiting_source` ;
- conserver `calculation_allowed = false` ;
- lister les documents necessaires ;
- expliquer le risque d'usage errone ;
- ne pas utiliser `0`, `1`, `100` ou une autre valeur par defaut comme substitut.

Le validateur refuse un parametre marque `is_fallback_value = true`.

### Parametres couverts

Le referentiel synthetique couvre 23 parametres :

- durees mensuelle et hebdomadaire de reference ;
- seuil et majoration heures supplementaires ;
- majorations nuit, dimanche et jours feries ;
- valorisation astreinte et intervention ;
- repos quotidien et hebdomadaire ;
- repos compensateur ;
- conges payes ;
- maintien maladie et subrogation ;
- 13e mois ;
- anciennete ;
- indemnite kilometrique ;
- panier repas ;
- plafond interne fictif ;
- date de regularisation ;
- parametre informatif sans valeur exploitable.

Tous les identifiants et codes finissent par `_SYN`.

### Limites des parametres synthetiques

Les parametres LOT 4D :

- ne contiennent aucun bareme reel INEOS ;
- ne contiennent aucun bulletin ;
- ne contiennent aucune valeur individuelle ;
- ne prouvent aucun droit ;
- ne modifient pas le moteur de calcul ;
- ne rendent aucune regle calculable.

### Integration future de baremes reels

Avant d'ajouter un bareme reel, il faudra :

1. conserver la source hors GitHub si elle est interne ou confidentielle ;
2. creer une entree locale privee ;
3. renseigner la source, la reference et la date d'effet ;
4. verifier les liens avec les regles, variables, Kelio et Nibelis ;
5. faire valider humainement le parametre ;
6. documenter les risques et limites ;
7. activer `calculation_allowed` uniquement apres revue technique et metier.

## LOT 4E - Graphe de connaissances metier Paie synthetique

Le LOT 4E ajoute un graphe de connaissances synthetique.

Objectif :

- relier les regles de paie ;
- relier les variables metier ;
- relier les compteurs Kelio synthetiques ;
- relier les rubriques Nibelis synthetiques ;
- relier les parametres synthetiques ;
- expliquer les chemins de controle sans calculer.

Le graphe est stocke dans :

```text
database/payroll/referentials/payroll-knowledge-graph.example.json
database/payroll/referentials/payroll-knowledge-graph.schema.json
```

### Role du graphe

Le graphe ne porte aucune regle de calcul.

Il sert a expliquer des dependances comme :

```text
regle -> variable -> compteur Kelio -> rubrique Nibelis -> parametre a sourcer
```

Il permet a Nexus de dire :

- quelle regle est concernee ;
- quelles variables manquent ;
- quel compteur Kelio pourrait aider au controle ;
- quelle rubrique Nibelis pourrait etre rapprochee ;
- quel parametre doit etre source et valide humainement.

### Relations autorisees

Les relations sont limitees a une liste controlee :

- `uses_parameter` ;
- `uses_variable` ;
- `feeds_counter` ;
- `feeds_rubric` ;
- `explains_rubric` ;
- `derived_from` ;
- `requires_document` ;
- `requires_validation` ;
- `may_trigger` ;
- `controls` ;
- `depends_on`.

Le validateur refuse les relations libres.

### Coherence des relations

Chaque relation contient :

- `relation_id` ;
- `source_type` ;
- `source_id` ;
- `target_type` ;
- `target_id` ;
- `relation_type` ;
- `description` ;
- `confidence` ;
- `validation_status` ;
- `synthetic_only` ;
- `calculation_allowed` ;
- `documentation`.

Le validateur controle :

- l'unicite des relations ;
- l'existence des objets source et cible ;
- la compatibilite des types ;
- l'absence de boucle directe incoherente ;
- la couverture des 23 regles ;
- les scenarios qui referencent uniquement des relations existantes.

### Couverture des regles

Le graphe couvre les 23 regles existantes par au moins une relation `rule -> variable`.

Les liens vers parametres, compteurs Kelio ou rubriques Nibelis ne sont ajoutes que lorsque les referentiels precedents contiennent deja un rattachement coherent.

Une absence de relation reste donc une information prudente : Nexus ne doit pas inventer un compteur, une rubrique ou un parametre qui n'existe pas encore.

### Scenarios d'explication

Le LOT 4E documente 6 scenarios synthetiques :

- heures supplementaires ;
- astreinte et intervention ;
- conges payes ;
- maintien maladie ;
- jours feries ;
- repos compensateur.

Chaque scenario decrit un parcours explicatif.

Il ne produit :

- aucun montant ;
- aucun taux applicable ;
- aucune conclusion automatique ;
- aucune preuve de droit.

### Interdiction de calcul

Chaque relation et chaque scenario conservent :

```text
synthetic_only = true
calculation_allowed = false
```

Le validateur refuse toute relation ou scenario qui autoriserait un calcul.

## Parametres de paie

Le schema parametre modelise une valeur, un seuil, un taux, une methode ou un composant de formule.

Champs importants :

- `parameter_id` ;
- `parameter_code` ;
- `parameter_type` ;
- `value` ;
- `source_layer` ;
- `source_document` ;
- `source_reference` ;
- `effective_date` ;
- `end_date` ;
- `human_validation` ;
- `legal_priority` ;
- `calculation_allowed`.

## Conditions avant tout calcul futur

Un enregistrement avec `calculation_allowed = true` est refuse par le validateur si une condition manque :

- source identifiable ;
- reference documentaire ;
- date d'effet valide ;
- source non synthetique ;
- `validation_status = human_validated` ;
- `human_validation.status = validated` si le bloc existe ;
- `confidence = high` ;
- pas de fixture synthetique.

Dans le LOT 4A, aucun exemple ne remplit volontairement ces conditions.

## Validation des liens

Le validateur controle les liens vers :

- les `rule_id` existants du catalogue `PayrollRule` ;
- les variables existantes deja declarees dans les 23 regles ;
- les rubriques Nibelis ;
- les compteurs Kelio.
- les parametres de paie ;
- les relations du graphe de connaissances.

Objectif : eviter qu'une rubrique, un compteur ou un parametre fasse reference a une regle inexistante ou a une variable non connue du moteur.

## LOT 4F - Controles d'anonymisation et protection des donnees paie

Le LOT 4F ajoute une couche dediee de confidentialite :

```text
automation/payroll/payroll_data_privacy_validator.py
automation/payroll/check_payroll_privacy_before_commit.py
automation/payroll/test_payroll_data_privacy_validator.py
```

Cette couche scanne localement :

- des objets Python ;
- des fichiers JSON ou texte ;
- des dossiers ;
- les fichiers suivis modifies, stages ou non suivis avant commit.

Elle ne transmet aucune donnee a un service externe.

### Categories surveillees

Le validateur recherche notamment :

- adresse email ;
- telephone ;
- IBAN, BIC et references bancaires ;
- numero de securite sociale ;
- matricule ou identifiant salarie ;
- nom ou prenom dans un champ nominatif ;
- date ou lieu de naissance ;
- numero fiscal ou taux individualise ;
- salaire rattache a une identite ;
- information medicale ou arret de travail nominatif ;
- diagnostic ou pathologie ;
- secrets techniques, tokens, mots de passe et cles API ;
- noms de fichiers a risque : bulletin, payslip, export Kelio, export Nibelis, salaires, matricules, `.env`, sauvegardes et cles privees.

### Rapport structure

Chaque anomalie remonte :

- categorie ;
- chemin ou fichier ;
- extrait masque ;
- niveau de risque ;
- recommandation.

Les rapports ne doivent jamais reproduire la valeur complete detectee. Les extraits sont masques a plus de 70 %.

### Donnees synthetiques autorisees

Les exemples strictement synthetiques peuvent etre acceptes lorsqu'ils sont explicites :

- marqueur `EXEMPLE_SYNTHETIQUE` ;
- domaine reserve `example.com` ;
- exemple invalide documente pour IBAN ou NIR ;
- noms generiques irreels.

Attention : `synthetic_only = true` ne donne pas une autorisation generale d'ajouter des donnees personnelles.

### Integration au validateur referentiel

`payroll_referential_validator.py` appelle la couche LOT 4F. Il ne duplique plus les regles de detection.

Les erreurs bloquantes restent exposees avec le code historique :

```text
sensitive_data_detected
```

Les cas suspects mais non conclusifs peuvent remonter en revue humaine.

### Controle avant commit

Le script local peut etre lance avant un commit :

```powershell
python automation/payroll/check_payroll_privacy_before_commit.py
```

Il renvoie :

- code `1` si une donnee interdite est detectee ;
- code `0` si aucune donnee interdite n'est trouvee ;
- des avertissements pour les fichiers ou contenus a verifier.

Il ignore les dossiers techniques comme `.git`, caches, environnements virtuels et `node_modules`, et evite de charger de gros binaires.

Un audit plus large reste possible en passant un ou plusieurs chemins explicites avec `--path`.

## LOT 4G - Protocole de raisonnement de l'Expert Paie

Le LOT 4G ajoute un protocole metier independant du moteur :

```text
automation/payroll/payroll_reasoning_protocol.py
docs/architecture/PAYROLL_REASONING_PROTOCOL.md
```

Le protocole impose 12 etapes ordonnees avant toute reponse : comprehension de la demande, identification de la
population et de la periode, collecte documentaire, recherche des regles et objets metier, controle des informations
manquantes, evaluation de la confiance et production d'une reponse adaptee.

Il distingue une reponse salarie simple d'une reponse expert detaillee. Sa politique de refus interrompt la conclusion
lorsqu'une information ou une piece indispensable manque, ou lorsque les documents sont contradictoires.

La description complete du protocole est disponible dans
[PAYROLL_REASONING_PROTOCOL.md](PAYROLL_REASONING_PROTOCOL.md).

Le protocole ne calcule aucun montant, droit, compteur ou bulletin. Les variables, compteurs Kelio, rubriques Nibelis
et parametres restent des objets a rechercher et a controler.

## LOT 4H - Integration prudente dans l'Expert Paie

Le LOT 4H relie prudemment l'Expert Paie aux composants des LOTS 4A a 4G :

```text
automation/experts/paie.py
automation/payroll/payroll_referential_integration.py
automation/experts/test_paie_referential_integration.py
```

L'integration conserve le comportement historique et le diagnostic `payroll_rule_analysis`. Elle ajoute :

- l'application du protocole LOT 4G ;
- des pistes de regles, variables, compteurs Kelio, rubriques Nibelis et parametres ;
- les relations pertinentes du graphe a partir des regles selectionnees ;
- les documents verifies et les pieces indispensables manquantes ;
- le niveau de confiance et ses causes ;
- des sorties distinctes `reponse_salarie` et `reponse_expert`.

Cette integration reste strictement non calculatoire. Elle ne transmet aucune valeur synthetique a l'Expert, ne cree
aucune formule et ne modifie pas `payroll_rule_engine.py`. Seuls les objets marques `synthetic_only = true` et
`calculation_allowed = false` peuvent etre exposes, toujours comme pistes de controle et jamais comme preuves. Les
accords, la convention collective, le Code du travail et les documents reels restent indispensables a toute conclusion.

## Commandes

Validation complete :

```powershell
python automation/payroll/payroll_referential_validator.py validate-all
```

Validation d'un seul referentiel :

```powershell
python automation/payroll/payroll_referential_validator.py validate-catalog --kind nibelis
python automation/payroll/payroll_referential_validator.py validate-catalog --kind kelio
python automation/payroll/payroll_referential_validator.py validate-catalog --kind parameters
python automation/payroll/payroll_referential_validator.py validate-catalog --kind knowledge_graph
```

Tests :

```powershell
python automation/payroll/test_payroll_referential_validator.py
python automation/payroll/test_payroll_data_privacy_validator.py
```

## Limites

- Aucun vrai referentiel Nibelis n'est ajoute.
- Aucun vrai referentiel Kelio n'est ajoute.
- Aucun parametre INEOS reel n'est ajoute.
- Aucun graphe issu de donnees reelles n'est ajoute.
- Aucun bulletin, export Kelio, export Nibelis ou fichier nominatif reel n'est ajoute.
- Aucun calcul n'est active.
- Le moteur `payroll_rule_engine.py` n'est pas modifie.
- `automation/experts/paie.py` est enrichi par le LOT 4H sans modifier le moteur ni supprimer les garde-fous existants.

## Prochaines etapes

LOT 4B :

- enrichir le referentiel Kelio avec des exemples plus representatifs ;
- conserver uniquement des fixtures synthetiques ;
- ajouter des controles de lecture par type de compteur.

LOT 4C :

- poursuivre la revue humaine des familles Nibelis synthetiques ;
- preparer une procedure locale d'anonymisation avant toute analyse de bulletin reel ;
- ne pas importer de codes Nibelis reels dans GitHub.

LOT 4D :

- poursuivre la revue humaine des parametres synthetiques ;
- preparer le stockage local prive des baremes reels ;
- conserver `calculation_allowed = false` tant que la validation humaine et la source documentaire ne sont pas completes.

LOT 4E :

- poursuivre la revue humaine des relations du graphe ;
- ajouter de futures relations uniquement si les objets existent deja ;
- ne pas utiliser le graphe comme moteur de calcul.

LOT 4F :

- faire tourner le controle de confidentialite avant chaque ajout de fixture paie ;
- refuser tout bulletin reel, matricule, export nominatif ou secret technique dans Git ;
- conserver les controles comme garde-fous, sans remplacer la validation humaine.

LOTS 4G et 4H :

- conserver les 12 etapes du protocole avant toute reponse enrichie ;
- presenter les objets des referentiels uniquement comme pistes de controle ;
- maintenir l'integration strictement non calculatoire ;
- suivre l'optimisation des chargements de catalogues comme dette technique separee.

## Conclusion

Les LOTS 4A a 4H posent le cadre de securite, de validation, de raisonnement et d'integration prudente du referentiel
paie. Ils ne rendent pas CFDT Nexus plus calculateur ; ils le rendent plus prudent, plus structure et plus difficile a
polluer avec des donnees non verifiees ou confidentielles.
