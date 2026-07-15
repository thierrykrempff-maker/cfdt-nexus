# Pipeline d'analyse d'un dossier salarie V1 - LOT 5A

[Index et navigation du LOT 5](LOT_5_EMPLOYEE_CASE_INDEX.md)

## Finalite

Le LOT 5A cree le socle d'orchestration d'un dossier salarie entierement synthetique. Il inventorie et classe les
pieces, controle la confidentialite et la completude, prepare des contextes experts puis assemble les analyses recues.

Il ne lit aucun PDF reel, ne fait pas d'OCR, ne calcule aucune paie, ne produit aucun avis juridique definitif et ne
modifie ni le cockpit ni l'orchestrateur general.

## Modele du dossier

`EmployeeCase` contient : identifiant synthetique, titre, question, description, periode, population, themes, urgence,
statut, documents presents et manquants, faits fournis, hypotheses, confidentialite, date injectee et historique des
etapes. `synthetic_only` doit toujours valoir `true`.

`EmployeeDocument` contient : identifiant, type controle, titre generique, periode, source declaree, format,
disponibilite, confidentialite, controle, resume et metadonnees minimales. Aucun contenu documentaire reel n'est stocke.

`ExpertAnalysis` fournit un contrat commun pour les analyses recues : expert, statut, resume, constats, sources,
documents, controles, risques, confiance, refus et limites.

## Typologie documentaire

La liste controlee couvre bulletin, releve de temps, planning, contrat, avenant, accord, convention, courrier RH,
decision manager, justificatif d'absence anonymise, demande de conge, notification de prime, document CSE et autre.
Elle ajoute les categories techniques necessaires aux matrices : releve d'astreinte, interventions, IJSS, fiche de
poste, fonctions exercees, compteur de conges, periode d'acquisition et regle applicable.

## Douze etapes

1. validation du dossier ;
2. validation des documents ;
3. controle de confidentialite ;
4. classification documentaire ;
5. identification des themes ;
6. determination des pieces necessaires ;
7. evaluation de la completude documentaire ;
8. preparation des contextes experts ;
9. collecte des analyses expertes ;
10. agregation des resultats ;
11. detection des contradictions ;
12. production du diagnostic.

Chaque etape porte un statut parmi `not_started`, `running`, `completed`, `warning`, `blocked` et `failed`. Une erreur
bloquante arrete le pipeline et les etapes suivantes restent `not_started`.

## Completude documentaire

La matrice couvre : heures supplementaires, astreinte, maladie et maintien, conges payes, classification, jours feries
et repos. Chaque piece est obligatoire, recommandee, facultative ou non pertinente selon le theme.

Une piece obligatoire absente bloque uniquement le theme concerne. Les autres themes complets peuvent continuer vers
les experts. Le pourcentage produit mesure uniquement la presence documentaire ; ce n'est jamais un calcul de paie.

## Contextes experts

Deux contextes sont prepares sans appeler directement les experts :

- Expert Paie : pistes de controle non calculatoires ;
- Juriste Travail : sources a identifier sans avis definitif.

Les interfaces CSE et securite sont seulement reservees pour une integration future. Les contextes contiennent la
question, la periode, la population, les themes, les pieces presentes/manquantes, les faits synthetiques, les references,
les alertes de confidentialite et une demande precise. Aucune valeur de parametre paie n'est transmise.

## Agregation et contradictions

L'agregateur assemble les analyses recues sans creer de constat. Il conserve les refus, choisit le niveau de confiance
le plus prudent et signale les convergences.

Il rend visibles : periodes expertes differentes, documents cites mais absents, niveaux de confiance incompatibles,
conclusion malgre une piece obligatoire absente, sources a reconcilier et faits documentaires contradictoires.

## Confidentialite

Le pipeline reutilise `payroll_data_privacy_validator.py` du LOT 4F. Il ne duplique aucune expression de detection. Un
dossier ou document non synthetique est bloque avant analyse. La fixture de confidentialite stocke seulement un marqueur
inoffensif ; la valeur interdite de test est assemblee en memoire pour verifier le garde-fou sans polluer Git.

## Fixtures

`automation/cases/fixtures/employee-cases.synthetic.json` contient six cas fictifs :

1. heures supplementaires complet ;
2. astreinte incomplete ;
3. maladie avec faits contradictoires ;
4. classification sans fiche de poste ;
5. conges payes complet ;
6. marqueur de confidentialite devant bloquer le dossier.

## Limites V1

- aucune lecture de fichier documentaire reel ;
- aucun OCR ou traitement d'image ;
- aucun appel automatique aux experts ;
- aucune persistance de dossier ;
- aucune API externe ;
- aucun calcul ou avis juridique ;
- aucune interface utilisateur.

Une version future pourra connecter un import documentaire anonymise, des interfaces expertes stabilisees et le cockpit,
apres validation de leurs contrats et garde-fous de confidentialite.
