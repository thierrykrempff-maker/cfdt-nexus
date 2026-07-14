# Expert Paie, Temps de Travail et Conges INEOS V1.2 - Lot 3

## Objectif

Le lot 3 integre le moteur `PayrollRuleEngine` dans l'expert paie existant.

Cette integration reste :

- locale ;
- en lecture seule ;
- sans calcul automatique ;
- sans activation de regle reelle ;
- sans modification du routeur Nexus.

Le but est d'enrichir l'analyse paie avec les regles candidates du catalogue `PayrollRule`, tout en conservant les sorties historiques de `automation/experts/paie.py`.

## Fichiers concernes

```text
automation/experts/paie.py
automation/experts/report_generator.py
automation/experts/test_paie_payroll_integration.py
docs/architecture/EXPERT_PAIE_CONGES_INEOS_V1_2.md
```

Le routeur principal n'est pas modifie.

## Integration dans paie.py

L'expert paie appelle le moteur du lot 2 uniquement apres avoir determine que la question releve de la paie, des conges, du temps de travail ou des compteurs.

L'appel suit ce flux :

```text
paie.enrich(answer)
-> payroll_rule_analysis(answer)
-> payroll_rule_engine.analyze_payroll_query(query, context)
-> normalisation dans payroll_rule_analysis
```

Le contexte transmis au moteur est construit a partir des donnees deja disponibles :

- `payroll_rule_context` ;
- `payroll_context` ;
- `context` ;
- `variables` ;
- `reference_date` ;
- `employee_population` ;
- `employment_category` ;
- `work_schedule` ;
- `site` ;
- documents presents si fournis.

Les documents demandes par Nexus ne sont pas consideres comme documents presents.

## Compatibilite descendante

Les champs historiques de l'expert paie sont conserves :

- `objet_du_controle` ;
- `elements_du_bulletin_concernes` ;
- `regles_ou_sources_disponibles` ;
- `donnees_necessaires_au_calcul` ;
- `methode_de_controle` ;
- `anomalies_potentielles` ;
- `calcul_detaille` ;
- `documents_necessaires` ;
- `sources_utilisees` ;
- `niveau_de_confiance` ;
- `limites`.

Le lot 3 ajoute seulement une section dediee :

```json
{
  "payroll_rule_analysis": {
    "engine_available": true,
    "query_topics": [],
    "candidate_rules": [],
    "selected_rules": [],
    "rejected_rules": [],
    "variables": {
      "present": {},
      "missing": [],
      "ambiguous": []
    },
    "documents_to_request": [],
    "calculation_ready": false,
    "warnings": [],
    "confidence": "faible"
  }
}
```

Les regles et candidats sont limites en affichage afin de ne pas exposer tout le catalogue.

## Filtrage d'affichage LOT 3

Le moteur du lot 2 conserve sa selection complete en interne, mais le lot 3 applique un filtrage d'affichage plus strict avant de presenter les resultats dans l'expert paie.

Ce filtrage utilise :

- les `query_topics` detectes ;
- le sujet principal de la demande ;
- les `matched_topics` et `rule_id` des regles candidates ;
- l'exclusion des themes purement contextuels ou trop generiques comme `5x8`, `jour`, `poste`, `roulement`, `conges_payes` au sens large ou `maintien`.

Objectif : eviter qu'une question ciblee fasse remonter des regles utiles dans un autre contexte mais hors sujet pour la demande immediate.

Exemples :

- une question de conge refuse affiche la regle de delai/demande de conge, pas les compteurs RJFJ/RCTP/RCTR ;
- une question maladie affiche la regle maladie/prevoyance, pas les regles conges payes ;
- une question RJFJ affiche les regles RJFJ/RJFN/JR, pas les regles conges ou maladie ;
- une question heures supplementaires affiche la regle heures supplementaires, pas les regles maladie ou conges.

Les regles ecartees par ce filtrage peuvent rester signalees comme ecartees pour faible pertinence, mais elles ne sont plus presentees comme potentiellement applicables.

## Variables et pieces associees

Apres filtrage des regles affichees, le lot 3 reconstruit :

- `variables.present` ;
- `variables.missing` ;
- `variables.ambiguous` ;
- `documents_to_request`.

Ces champs ne sont plus repris en bloc depuis la selection complete du moteur. Ils sont limites aux regles effectivement affichees, afin d'eviter des pieces hors sujet.

Exemples :

- un conge refuse ne doit pas demander de releve Kelio sauf si le sujet parle explicitement de compteur ;
- une maladie ne doit pas demander de document de conge sans lien direct ;
- un compteur RJFJ peut demander une capture Kelio ;
- les heures supplementaires restent rattachees au planning, au bulletin et aux donnees horaires.

## Gestion des erreurs

Si le moteur paie est indisponible, si le catalogue est invalide ou si une exception apparait :

- Nexus ne tombe pas ;
- l'ancien comportement de `paie.py` reste disponible ;
- `payroll_rule_analysis.engine_available` vaut `false` ;
- un warning explicite indique la cause ;
- `calculation_ready` reste `false`.

Cette logique permet de deployer progressivement le moteur sans rendre l'expert paie dependant du catalogue.

## Presentation dans le rapport

`automation/experts/report_generator.py` ajoute une section :

```text
Analyse Paie INEOS
```

Elle n'est affichee que si `payroll_rule_analysis` contient un signal utile :

- moteur indisponible ;
- themes detectes ;
- regles affichees ou ecartees ;
- variables presentes, manquantes ou ambigues ;
- pieces a fournir ;
- avertissements ;
- niveau de confiance exploitable.

Elle presente uniquement les informations utiles :

- themes detectes ;
- regles potentiellement applicables ;
- statut de validation ;
- population concernee ;
- donnees manquantes ;
- donnees ambigues ;
- pieces a fournir ;
- avertissements ;
- refus de calcul automatique.

Les 23 regles du catalogue ne sont jamais affichees en bloc.

## Absence de calcul

Le lot 3 ne cree aucun moteur de calcul.

Il ne fait jamais :

- d'execution de formule ;
- d'application de taux ;
- d'estimation de montant ;
- de rappel de salaire chiffre ;
- d'activation de `calculation_allowed` ;
- de passage d'une regle en `active`.

Avec le catalogue reel actuel :

```json
{
  "calculation_ready_true_rule_ids": []
}
```

La mention de calcul reste prudente :

```text
Calcul automatique: non execute dans le LOT 3. Validation humaine obligatoire avant tout chiffrage.
```

Cette formulation reste identique meme si un moteur de test renvoie `calculation_ready = true`.
Le lot 3 peut indiquer que des donnees sont presentes ou manquantes, mais il ne presente jamais le calcul automatique comme pret, disponible ou valide.

## Securite des sources

Les garanties du lot 2 restent valables :

- une regle `to_verify` n'est jamais presentee comme certaine ;
- une source `memoire_entreprise` ne devient pas un droit applicable ;
- `pratique_officielle` et `jurisprudence` ne sont pas calculables ;
- une regle future est bloquee ;
- un conflit de regles bloque `calculation_ready` ;
- une variable manquante ou ambigue bloque `calculation_ready`.

## Scenarios couverts

Les tests d'integration couvrent :

- heures supplementaires non payees ;
- deux nuits et un dimanche en 5x8 ;
- changement de roulement tardif ;
- conge refuse ;
- compteur RJFJ/JR ;
- maladie ;
- 13e mois ;
- erreur catalogue ;
- question hors paie ;
- rapport lisible `Analyse Paie INEOS` ;
- filtrage anti-surselection conge refuse / maladie / RJFJ / heures supplementaires ;
- absence de section `Analyse Paie INEOS` si l'analyse est absente, vide ou mal formee ;
- presence de section pour warning utile, moteur indisponible ou piece a demander ;
- formulation prudente lorsque `calculation_ready = true` dans un scenario synthetique ;
- preuve que le catalogue reel ne rend aucun scenario calculable.

## Limites

- La classification reste une logique deterministe par mots-cles.
- Les regles restent `to_verify` tant qu'une validation humaine n'est pas faite.
- Certaines questions larges peuvent remonter plusieurs regles candidates ; l'affichage est donc volontairement limite.
- Le moteur ne lit pas les bulletins ni les documents reels.
- Le routeur Nexus n'utilise pas encore cette analyse pour modifier ses domaines ou sa strategie globale.

## Prochaine etape

La prochaine etape pourra etre une validation humaine progressive de quelques regles pilotes.

Chaque regle candidate devra etre :

- rattachee a une source sure ;
- relue humainement ;
- testee sur cas fictifs ;
- documentee ;
- puis seulement eventuellement autorisee au calcul dans un lot separe.

Tant que cette validation n'est pas terminee, CFDT Nexus informe, structure les controles et liste les pieces, mais ne chiffre rien.
