# Expert Paie, Temps de Travail et Conges INEOS V1.1

## Objectif

Le lot V1.1 cree le socle structurel du futur Expert Remuneration, Temps de travail et Conges INEOS Sarralbe.

Il ne calcule pas encore une paie complete. Il transforme des informations metier en regles structurees, tracables et validables, sans inventer de taux, de prime, de majoration ou de condition.

## Perimetre du lot 1

Le lot 1 ajoute :

- un schema `PayrollRule` ;
- un catalogue initial de regles INEOS Sarralbe ;
- un validateur local ;
- des tests dedies ;
- une documentation d'architecture.

Le lot 1 ne modifie pas :

- le routeur Nexus ;
- l'orchestrateur ;
- l'expert paie V0 ;
- le moteur de recherche Bible Accords ;
- le site public CFDT.

## Hierarchie des sources

Nexus doit conserver trois niveaux separes.

### Niveau 1 - Sources opposables

- accords INEOS ;
- avenants ;
- decisions unilaterales valides ;
- convention collective Chimie ;
- Code du travail.

Ces sources peuvent devenir des regles applicables, uniquement apres rattachement documentaire clair.

### Niveau 2 - Interpretation

- jurisprudence ;
- pratique officielle.

Ces sources aident a comprendre ou interpreter. Elles ne remplacent pas l'accord INEOS, la convention collective ou le Code du travail.

### Niveau 3 - Memoire interne

- PV CSE ;
- notes RH ;
- historiques ;
- reponses de direction.

La memoire interne ne doit jamais etre presentee comme une source juridique opposable. La bonne formulation est :

```text
Ce sujet a ete evoque dans le PV CSE du...
```

La mauvaise formulation est :

```text
Le PV impose que...
```

## Statut des regles

Les statuts controles sont :

- `draft` ;
- `active` ;
- `expired` ;
- `superseded` ;
- `disputed` ;
- `to_verify`.

Dans le catalogue initial, les regles issues des informations metier sont marquees `to_verify` tant que l'accord, l'avenant, la decision, l'article CCNIC ou l'article du Code du travail exact n'est pas rattache.

## Politique de non-invention

Le moteur ne doit jamais inventer :

- un taux ;
- une prime ;
- une majoration ;
- une condition d'eligibilite ;
- une date d'effet ;
- une formule de calcul ;
- une population couverte.

Le champ `calculation_allowed` reste `false` tant que la formule complete, les valeurs de reference, les variables et la source exacte ne sont pas securisees.

## Schema PayrollRule

Le schema est defini dans :

```text
database/payroll/payroll-rule.schema.json
```

Il structure notamment :

- l'identifiant de regle ;
- la source ;
- la date d'effet ;
- le statut ;
- les themes paie, conges et temps de travail ;
- la population concernee ;
- les variables necessaires ;
- la formule eventuelle ;
- les lignes bulletin a controler ;
- les compteurs Kelio ;
- le niveau de priorite juridique ;
- le statut de validation.

## Catalogue initial

Le catalogue initial est defini dans :

```text
database/payroll/ineos-sarralbe-payroll-rules-v1.json
```

Il couvre un premier lot representatif :

- jours dus 5x8 ;
- RCTP ;
- RCTR ;
- RJFJ, RJFN et JR ;
- acquisition et prise des conges payes ;
- rappel pendant conge selon CCNIC ;
- indemnite de conges payes ;
- jours feries jour/poste ;
- heures supplementaires ;
- repos quotidien ;
- changement de roulement ;
- maintien au poste ;
- rappel hors astreinte ;
- rappel en astreinte ;
- 13e mois ;
- maladie et prevoyance ;
- indemnite kilometrique.

Les regles restent non calculables dans ce lot.

## Sources a ne pas mal qualifier

Le document Nibelis ne doit pas etre utilise comme source d'un droit INEOS. Il sert uniquement a comprendre la presentation des rubriques du bulletin.

La fiche relative au conge supplementaire de naissance doit etre traitee comme `pratique_officielle`, pas comme accord INEOS.

Un PV CSE doit etre classe comme `memoire_entreprise`, avec `historical_only = true` par defaut.

## Validateur

Le validateur est defini dans :

```text
automation/payroll/payroll_rule_validator.py
```

Le lot 1 n'ajoute pas de dependance externe `jsonschema`. Le validateur implemente donc une validation interne stricte du sous-ensemble JSON Schema utilise par `payroll-rule.schema.json`.

Cette validation controle :

- les champs obligatoires ;
- les champs inconnus interdits par `additionalProperties: false` ;
- les types exacts : string, integer, number, boolean, array, object, null ;
- les tableaux reels, sans accepter une chaine a la place d'une liste ;
- les objets imbriques `calculation_formula` et `sourced_values` ;
- les enums ;
- les dates ISO pour `source_date`, `effective_date` et `end_date` ;
- les valeurs null uniquement lorsque le schema les autorise ;
- les boolens reels, sans coercition de chaines comme `"false"`.

Il refuse ou signale notamment :

- une regle sans source ;
- une regle interne sans page ou trace documentaire ;
- une regle calculable sans variables obligatoires ;
- une regle `memoire_entreprise` calculable ;
- une regle `memoire_entreprise` avec une priorite autre que `memory_only` ;
- une regle issue d'un PV CSE mal classee ;
- une regle active dont la date de fin est depassee ;
- une regle active mais remplacee ;
- une formule avec taux ou montant non source ;
- une regle 5x8, GN ou Polyolefines sans population ;
- une contradiction potentielle avec une version plus recente.

### Regles particulieres PV CSE

Toute regle dont `document_type` vaut `pv_cse` doit obligatoirement respecter :

```text
source_layer = memoire_entreprise
historical_only = true
calculation_allowed = false
legal_priority = memory_only
```

Toute autre combinaison est rejetee. Un PV CSE reste une memoire de ce qui a ete dit ou repondu ; il ne devient pas une regle de paie opposable.

### References entre regles

Le validateur de catalogue controle les champs :

- `supersedes` ;
- `superseded_by`.

Chaque `rule_id` reference doit exister dans le catalogue. Le validateur rejette aussi :

- les auto-references ;
- les doublons dans une liste de references ;
- les references vers une regle inconnue ;
- les incoherences reciproques lorsque les deux sens sont renseignes.

## Fonctionnement futur du moteur

La prochaine etape devra rester limitee a la selection de la regle applicable, sans calcul.

Flux cible :

1. Comprendre la question.
2. Identifier les themes : paie, conges, temps de travail.
3. Selectionner les regles candidates.
4. Appliquer la hierarchie des sources.
5. Exclure les regles expirees ou remplacees.
6. Presenter les variables manquantes.
7. Refuser le calcul si les donnees ne sont pas suffisantes.
8. Citer les sources avec niveau de confiance.

## Limites connues du lot 1

- Les regles issues des informations metier ne sont pas encore rattachees aux documents sources reels.
- Les pages et articles exacts restent a completer.
- Aucune integration au routeur Nexus n'est realisee.
- Aucun calcul automatique n'est autorise.
- Les PV CSE ne sont pas encore importes.
- Les rubriques Nibelis ne sont pas encore modelisees comme presentation de bulletin.
- Les tableaux maladie, anciennete, primes A/B/C/D et degressivite restent a detailler.
- Le validateur interne couvre uniquement le sous-ensemble JSON Schema utilise dans ce lot. Si le schema devient plus complexe, une dependance explicite a `jsonschema` devra etre reconsideree.

## Regles encore a confirmer humainement

Toutes les regles `to_verify` doivent etre relues avec :

- l'accord INEOS ou l'avenant applicable ;
- la CCNIC si le sujet est conventionnel ;
- le Code du travail si le sujet est legal ;
- la date d'effet ;
- la population couverte ;
- les exclusions ;
- le texte eventuellement remplace.

## Prochaine etape

Le lot suivant recommande est :

```text
Selection de la regle applicable, sans calcul.
```

Il devra lire le catalogue, choisir les regles candidates, expliquer pourquoi une regle est retenue ou ecartee, puis afficher les donnees manquantes avant toute tentative de calcul.
