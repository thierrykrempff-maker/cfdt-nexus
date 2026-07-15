# Protocole de raisonnement de l'Expert Paie INEOS - LOT 4G

## Objet et limites

Ce protocole impose une methode d'analyse identique avant toute reponse de l'Expert Paie. Il est declaratif, deterministe et independant de l'architecture d'execution actuelle.

Il ne calcule aucun montant, droit, compteur ou bulletin. Il ne modifie ni le moteur de calcul, ni l'expert existant, ni l'orchestrateur, ni les referentiels, ni les 23 regles. Son integration future pourra consommer le diagnostic structure sans changer ces composants.

## Les 12 etapes obligatoires

1. Comprendre la demande : type de question, theme, portee individuelle ou collective et urgence.
2. Identifier la population : salarie concerne ou collectif applicable.
3. Identifier la periode : periode des faits et paie concernee.
4. Identifier les documents necessaires.
5. Rechercher les regles applicables.
6. Rechercher les variables concernees.
7. Rechercher les compteurs Kelio concernes.
8. Rechercher les rubriques Nibelis concernees.
9. Rechercher les parametres concernes.
10. Identifier les informations manquantes.
11. Determiner le niveau de confiance.
12. Produire la reponse adaptee au destinataire.

L'ordre est porte par `PROTOCOL_STEPS`. Une integration ne doit ni omettre ni reordonner une etape.

## Collecte et verification des documents

Les categories reconnues sont :

| Categorie | Utilite |
|---|---|
| `agreement` | Accord d'entreprise ou d'etablissement applicable |
| `collective_agreement` | Convention collective applicable |
| `labour_code` | Texte legal applicable et date |
| `kelio` | Planning, pointage ou compteur de temps |
| `nibelis` | Rubrique ou trace de parametrage Nibelis |
| `payslip` | Bulletin de la periode controlee |
| `hr_letter` | Courrier ou notification RH |
| `manager_decision` | Decision ou validation du manager |
| `other` | Justificatif metier non classe |

Pour chaque question, l'analyse distingue les documents presents, absents, indispensables et seulement recommandes. La presence d'un document ne prouve pas a elle seule que son contenu est coherent ou applicable.

## Table des pieces a demander

| Sujet | Pieces indispensables | Pieces recommandees | Ordre de collecte |
|---|---|---|---|
| Heures supplementaires | Kelio, bulletin, accord | convention, decision manager | planning -> Kelio -> bulletin -> accord |
| Conges payes | Kelio, bulletin | accord, convention | demande validee -> compteur Kelio -> bulletin -> accord |
| Absence | Kelio, bulletin | courrier RH, accord | justificatif -> Kelio -> bulletin -> courrier RH |
| Prime | bulletin | accord, decision manager, Nibelis | accord/decision -> conditions -> bulletin -> rubrique Nibelis |
| Temps de travail | Kelio, accord | bulletin, decision manager | planning -> Kelio -> accord -> bulletin |
| Autre sujet | selon la question | accord, convention, Code du travail | question precise -> source -> document de situation |

Cette table indique quoi demander. Elle ne fournit aucune formule et ne declenche aucun calcul.

## Recherche dans les sources et referentiels

Le protocole produit cinq listes de recherche distinctes :

- regles applicables ;
- variables metier ;
- compteurs Kelio ;
- rubriques Nibelis ;
- parametres de paie.

Ces listes contiennent des candidats a verifier. Un compteur, une rubrique ou un parametre n'est jamais transforme en source juridique.

## Controles

Avant la reponse, l'Expert controle :

- la coherence de la periode entre les documents ;
- la coherence de la population ;
- le lien entre chaque fait et sa source ;
- les contradictions entre accord, planning, compteur et bulletin ;
- les donnees et pieces manquantes ;
- le risque d'une conclusion insuffisamment etayee.

## Niveaux de confiance

| Niveau | Signification |
|---|---|
| `VERY_HIGH` | Documents indispensables presents, au moins deux elements de source/regle, au moins trois familles de referentiels renseignees, aucune information manquante |
| `HIGH` | Documents indispensables presents, au moins une source et une famille de referentiel, aucune information manquante |
| `MEDIUM` | Analyse partielle possible, mais preuve ou information complementaire utile |
| `LOW` | Au moins un cas de refus empeche une conclusion certaine |
| `UNKNOWN` | Demande ou theme inexploitable, evaluation impossible |

Le niveau est une mesure de qualite du dossier, pas une probabilite mathematique et pas une validation de paie.

## Politique de refus

Le protocole repond exactement `Impossible de conclure avec certitude.` lorsqu'au moins un cas bloquant est constate :

1. periode absente ;
2. population ou salarie non identifie ;
3. aucune source applicable ;
4. bulletin absent alors qu'il est indispensable au sujet ;
5. compteur ou releve Kelio absent alors qu'il est indispensable au sujet ;
6. accord absent alors qu'il est indispensable au sujet ;
7. documents contradictoires.

Tous les motifs sont conserves dans le diagnostic. Le protocole ne choisit pas arbitrairement le premier motif et indique les pieces indispensables manquantes.

## Deux formats de reponse

### Version salarie

La version salarie emploie des termes simples. Elle contient une conclusion courte, une explication accessible, les documents a fournir et le niveau de confiance. Elle masque les details techniques de recherche.

### Version expert

La version expert expose la conclusion, les sources, les cinq listes de recherche, les points de controle, les documents a verifier, les informations manquantes, les limites et le niveau de confiance.

Les deux versions partagent le meme diagnostic : seule la presentation change.

## Exemple d'utilisation future

```python
question = PayrollQuestion(
    question="Verifier des heures supplementaires",
    question_type="controle",
    subject="heures_supplementaires",
    scope=QuestionScope("employee"),
    population="salarie concerne",
    period="juin 2026",
)
diagnostic = assess(question)
reponse = render_response(question, diagnostic, Audience("employee"))
```

Le resultat demande des preuves et decrit les recherches a mener. Il ne calcule ni heures, ni taux, ni montant.

Les valeurs d'enumeration sont construites ici depuis leur valeur metier en minuscules. Cette ecriture cible uniquement
l'exemple documentaire et evite qu'un controle generique de chaines en majuscules ne confonde le nom symbolique de
l'audience avec un code bancaire. Aucune exception au detecteur de BIC n'est ajoutee et sa detection reste inchangee.
