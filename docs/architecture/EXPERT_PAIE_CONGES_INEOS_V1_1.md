# Expert Paie, Temps de Travail et Conges INEOS V1.1 - Lot 2

## Objectif

Le lot 2 ajoute un moteur local de selection des regles `PayrollRule`.

Il ne calcule aucune paie et ne modifie pas le routeur Nexus. Son role est de transformer une question salarie et un contexte structure en une reponse preparatoire :

- themes detectes ;
- regles candidates ;
- regles selectionnees ;
- regles ecartees ;
- variables presentes, manquantes ou ambigues ;
- pieces justificatives a demander ;
- avertissements de prudence ;
- refus explicite du calcul lorsque les conditions ne sont pas reunies.

## Fichier principal

```text
automation/payroll/payroll_rule_engine.py
```

Le module reste autonome. Il n'est pas branche dans :

- `assistant_ds_router.py` ;
- `paie.py` ;
- `orchestrator.py` ;
- `report_generator.py` ;
- l'interface.

## Chargement du catalogue

La fonction `load_validated_catalog` charge :

```text
database/payroll/ineos-sarralbe-payroll-rules-v1.json
```

Elle utilise le validateur du lot 1 :

```text
automation/payroll/payroll_rule_validator.py
```

Le catalogue est refuse si :

- le schema n'est pas respecte ;
- le catalogue est vide ;
- une erreur metier du validateur est presente.

La structure retournee est une copie profonde pour eviter toute modification involontaire des regles en memoire.

## Classification

La fonction `classify_query` detecte des themes a partir de la question et du contexte.

Themes couverts dans ce lot :

- heures supplementaires ;
- nuit ;
- dimanche ;
- jour ferie ;
- 5x8 ;
- rappel ;
- maintien ;
- astreinte ;
- intervention ;
- changement de roulement ;
- conges payes ;
- fractionnement ;
- RTT ;
- CET ;
- maladie ;
- 13e mois ;
- indemnite kilometrique ;
- RCTP ;
- RCTR ;
- RJFJ ;
- RJFN ;
- JR ;
- classification ;
- coefficient ;
- repos.

Synonymes integres :

- `heures en plus` vers `heures_supplementaires` ;
- `travail de nuit` vers `nuit` ;
- `jour rouge` vers `jour_ferie` ;
- `kilometres`, `frais kilometriques`, `trajet domicile-usine` vers `indemnite_kilometrique` ;
- `jours de remonte` vers `JR` ;
- `recuperation jour ferie` vers `RJFJ/RJFN` selon le contexte ;
- `changement de couleur` vers `changement_roulement` uniquement si le contexte 5x8/poste est present.

La formulation disciplinaire `mettre a pied` n'est pas classee comme paie.

Le mot `repos` seul ne suffit pas a selectionner une regle. Le moteur attend un contexte plus precis comme `repos compensateur`, `repos entre deux postes`, `repos quotidien` ou `recuperation jour ferie`.

## Selection des regles

Le moteur analyse les champs suivants :

- `payroll_topic` ;
- `leave_topic` ;
- `work_time_topic` ;
- `employee_population` ;
- `employment_category` ;
- `work_schedule` ;
- `site` ;
- `effective_date` ;
- `end_date` ;
- `status` ;
- `historical_only` ;
- `source_layer` ;
- `confidence` ;
- `legal_priority`.

Les regles sont evaluees selon :

1. correspondance theme/question ;
2. compatibilite population ;
3. compatibilite regime de travail ;
4. compatibilite site ;
5. compatibilite date, par rapport a `reference_date` si elle est fournie ;
6. statut ;
7. niveau de source ;
8. confiance.

Le 5x8 est traite comme un contexte de travail. Il ne suffit pas, seul, a selectionner toutes les regles 5x8. Une question sur RJFJ/RJFN/JR priorise les regles directement liees aux compteurs, transferts et regularisations.

Le champ `employment_category` est filtre reellement : une regle `cadres` est rejetee pour un contexte `non_cadres`, une regle `non_cadres` est rejetee pour un contexte `cadres`, une regle `ouvriers` est rejetee pour un contexte `cadres`, et une regle `tous` reste compatible. Si la categorie manque dans le contexte et que la regle est specifique, le moteur signale une incertitude.

`legal_priority` peut ajouter un avertissement ou participer a une future securisation de calcul. Il ne compense jamais une incompatibilite de theme, population, categorie, regime de travail ou site.

## Hierarchie des sources

Ordre utilise :

1. `accord_entreprise`
2. `convention_collective`
3. `code_travail`
4. `jurisprudence`
5. `pratique_officielle`
6. `memoire_entreprise`

Une source `memoire_entreprise` ne peut jamais devenir une regle applicable. Elle peut seulement apparaitre comme element historique separe.

## Statuts

- `to_verify` : la regle peut etre proposee comme candidate, avec avertissement.
- `expired` : la regle est ecartee.
- `superseded` : la regle est ecartee.
- `disputed` : la regle peut etre conservee, avec prudence renforcee.
- `active` : la regle pourrait etre selectionnee, mais le catalogue initial ne contient aucune regle active.

La regle la plus recente ne remplace pas automatiquement une autre regle sans relation explicite `supersedes` ou `superseded_by`.

## Variables

Le moteur lit les `required_variables` des regles selectionnees.

Il produit :

```json
{
  "required": [],
  "present": {},
  "missing": [],
  "ambiguous": [],
  "documents_to_request": [],
  "calculation_ready": false
}
```

Les variables peuvent etre fournies dans le contexte :

- directement a la racine ;
- dans un objet `variables` ;
- avec quelques synonymes metier, par exemple `hourly_rate` pour `base_horaire`.

Les valeurs numeriques a zero sont conservees comme donnees presentes. Exemple : `hours_worked = 0` ou `hourly_rate = 0` ne sont pas confondus avec une absence.

Les chaines vides, `null` et les tableaux vides restent des donnees manquantes.

Le moteur signale une ambiguite lorsque :

- une valeur contient `?`, `environ`, `peut-etre`, `je crois`, `a confirmer` ;
- plusieurs alias donnent des valeurs differentes pour une meme variable ;
- le contexte contient plusieurs regimes de travail, populations ou categories contradictoires ;
- une date est incertaine ;
- un compteur Kelio est fourni sans date de releve.

## Pieces justificatives

Le moteur associe les variables manquantes a des pieces utiles :

- heures travaillees : planning ou releve Kelio ;
- base horaire : bulletin de paie ;
- coefficient ou categorie : bulletin ou contrat ;
- jours feries : planning et Kelio ;
- RJ/RJFJ/RJFN/RCTP/RCTR : capture Kelio ;
- maladie : arret de travail et bulletin ;
- conges : demande, reponse hierarchique et compteur ;
- indemnite kilometrique : adresse declaree, distance, bulletin.

Une piece deja presente est signalee dans `documents_present` et n'est pas redemandee.

## Absence de calcul

Le moteur calcule `calculation_ready`.

La date de reference est lue dans le contexte via `reference_date`.
Si elle n'est pas fournie, la barriere de securite du calcul utilise la date du jour.

Dans ce lot, `calculation_ready` reste `false` dans les cas suivants :

- une variable obligatoire manque ;
- une variable est ambigue ;
- au moins une regle selectionnee a `calculation_allowed = false` ;
- la regle est `to_verify`, `disputed`, `expired` ou `superseded` ;
- la source n'est pas opposable ;
- la source est `jurisprudence`, `pratique_officielle` ou `memoire_entreprise` ;
- la date d'effet est absente ou incertaine ;
- la date d'effet est future par rapport a `reference_date` ou a la date du jour ;
- la date de fin est depassee ;
- plusieurs regles incompatibles restent selectionnees ;
- la population ou la categorie d'emploi n'est pas confirmee pour une regle specifique ;
- un avertissement bloquant existe.

La fonction centrale est :

```text
is_safe_for_calculation(rule, selection_context)
```

Une regle non encore entree en vigueur produit un avertissement explicite :

```text
rule_not_yet_effective: RULE_ID applicable a partir de YYYY-MM-DD.
```

Sources qui pourraient etre autorisees pour un futur calcul, sous reserve de validation complete :

- `accord_entreprise` ;
- `convention_collective` ;
- `code_travail`.

Le catalogue actuel contient 23 regles, toutes non calculables. Le moteur ne doit donc produire aucun montant, taux applique ou rappel estime.

## Conflits entre regles

Le moteur ne considere plus automatiquement plusieurs regles selectionnees comme un conflit.

La fonction centrale est :

```text
detect_rule_conflicts(selected_rules)
```

Elle retourne :

```json
{
  "has_conflict": false,
  "conflicting_rule_ids": [],
  "reason": ""
}
```

La detection reste volontairement prudente et explicite.
Elle distingue le theme metier principal du contexte de travail.

Le theme metier principal vient prioritairement de :

- `payroll_topic` ;
- `leave_topic`.

Les champs de contexte comme `work_time_topic` peuvent confirmer le champ d'application, mais ne suffisent pas a creer un conflit.
Les valeurs generiques suivantes ne sont pas utilisees seules comme preuve de conflit :

- `jour` ;
- `5x8` ;
- `poste_continu` ;
- `roulement` ;
- `personnel_jour` ;
- `personnel_poste`.

De la meme maniere, une consequence metier trop generale ne suffit pas a declarer un conflit sans contradiction effective de formule ou d'effet :

- `droit_salarie` ;
- `obligation_employeur` ;
- `information` ;
- `controle` ;
- `avantage`.

Deux regles sont considerees concurrentes lorsqu'elles se recoupent au minimum sur :

- le theme metier principal precis ;
- la consequence metier precise ou une contradiction de formule ou d'effet ;
- la population ;
- la categorie d'emploi ;
- le regime de travail ;
- la periode d'application.

Une regle principale et une regle complementaire peuvent coexister si elles ne portent pas la meme consequence metier ou si leur champ d'application ne se recoupe pas.
Exemple : une regle sur le 13e mois et une regle sur les conges payes peuvent etre applicables au meme salarie et a la meme date sans etre concurrentes.

En cas de conflit, `calculation_ready` reste `false` et un warning cite les `rule_id` concernes :

```text
rule_conflict: RULE_A, RULE_B (...)
```

Les regles ecartees avant selection, par exemple pour population incompatible ou periode non applicable a `reference_date`, ne participent pas a la detection des conflits.

## Tests

Le fichier de test est :

```text
automation/payroll/test_payroll_rule_engine.py
```

Il couvre notamment :

- heures supplementaires non payees ;
- deux nuits et un dimanche en 5x8 ;
- changement de roulement tardif ;
- conge refuse ;
- compteur JR/RJFJ ;
- maladie ;
- 13e mois ;
- indemnite kilometrique ;
- population incompatible ;
- source `memoire_entreprise` ;
- catalogue invalide ;
- catalogue vide ;
- regle inconnue ;
- contexte vide ;
- date hors periode ;
- statuts `expired`, `superseded`, `disputed`, `to_verify` ;
- plusieurs regles concurrentes ;
- absence de faux conflit entre 13e mois et conges payes ;
- absence de faux conflit cree uniquement par le contexte `jour` ou par `droit_salarie` ;
- contexte complet mais calcul interdit ;
- securisation de `calculation_ready` ;
- filtrage `employment_category` ;
- synonymes kilometriques ;
- repos generique ;
- surselection RJFJ ;
- zeros metier ;
- chaines vides ;
- contradictions ;
- dates ambigues ;
- compteur Kelio non date.

## Limites restantes

- La classification reste une logique par regles explicites, pas une IA.
- Les synonymes devront etre enrichis avec les retours terrain.
- Les regles `nuit` et `dimanche` ne disposent pas encore toutes de regles dediees dans le catalogue.
- Les montants, taux et tranches restent non calcules.
- Les pieces justificatives sont proposees par correspondance metier simple.
- Les conflits entre plusieurs regles calculables sont bloques de maniere conservatrice.
- Aucune integration au routeur n'est realisee.

## Prochaine etape

La prochaine etape pourra etre l'activation progressive de calculs tres limites, uniquement pour les regles :

- sourcees ;
- validees humainement ;
- avec variables completes ;
- avec `calculation_allowed = true` ;
- testees sur des cas exemples.

Tant que ces conditions ne sont pas reunies, Nexus doit expliquer, lister les pieces et refuser le calcul automatique.
