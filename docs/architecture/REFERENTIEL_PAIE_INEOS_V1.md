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

Objectif : eviter qu'une rubrique, un compteur ou un parametre fasse reference a une regle inexistante ou a une variable non connue du moteur.

## Detection de donnees sensibles

Le validateur detecte dans les fixtures :

- email ;
- IBAN ;
- numero de securite sociale ;
- telephone ;
- mention de matricule ;
- adresse personnelle simple.

Cette detection est volontairement prudente. Elle ne remplace pas une revue humaine avant tout ajout de donnees privees locales.

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
```

Tests :

```powershell
python automation/payroll/test_payroll_referential_validator.py
```

## Limites

- Aucun vrai referentiel Nibelis n'est ajoute.
- Aucun vrai referentiel Kelio n'est ajoute.
- Aucun parametre INEOS reel n'est ajoute.
- Aucun calcul n'est active.
- Le moteur `payroll_rule_engine.py` n'est pas modifie.
- `automation/experts/paie.py` n'est pas modifie.

## Prochaines etapes

LOT 4B :

- enrichir le referentiel Kelio avec des exemples plus representatifs ;
- conserver uniquement des fixtures synthetiques ;
- ajouter des controles de lecture par type de compteur.

LOT 4C :

- enrichir le referentiel Nibelis avec des rubriques synthetiques plus completes ;
- preparer une procedure d'anonymisation avant toute analyse de bulletin reel.

LOT 4D :

- structurer les parametres de paie ;
- conserver `calculation_allowed = false` tant que la validation humaine et la source documentaire ne sont pas completes.

## Conclusion

Le LOT 4A pose le cadre de securite et de validation. Il ne rend pas CFDT Nexus plus calculateur ; il le rend plus prudent, plus structure et plus difficile a polluer avec des donnees non verifiees.
