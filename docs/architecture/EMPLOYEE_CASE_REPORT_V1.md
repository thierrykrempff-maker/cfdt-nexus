# Generateur de rapport d'analyse salarie V1 - LOT 5B

[Index et navigation du LOT 5](LOT_5_EMPLOYEE_CASE_INDEX.md)

## Finalite

Le LOT 5B transforme le diagnostic structure du pipeline LOT 5A et les analyses expertes deja disponibles en un objet
de rapport Python serialisable en JSON. Il ne dialogue avec aucun expert et ne relance aucun calcul.

Le rapport pourra servir plus tard de contrat de donnees pour le cockpit, un export PDF, une version imprimable ou une
API. Aucun de ces canaux n'est implemente dans cette version.

## Douze sections ordonnees

1. en-tete : dossier, titre, date, statut, version et confidentialite ;
2. resume executif : sujet, constats, themes bloques et confiance ;
3. situation analysee : periode, population, contexte et question ;
4. documents : presents, recommandes, manquants et bloquants ;
5. analyse par theme : statut, resume, pieces, constats et limites ;
6. synthese Expert Paie ;
7. synthese Juriste Travail ;
8. contradictions ;
9. actions recommandees, separees en verification, demande, controle et complement ;
10. confiance : niveau, causes, facteurs favorables et facteurs defavorables ;
11. limites et hypotheses ;
12. metadonnees techniques.

L'ordre est expose par `SECTION_ORDER` et fait partie du contrat V1.

## Entrees et principe d'assemblage

`EmployeeCaseReportGenerator.generate()` recoit uniquement :

- le resultat du pipeline LOT 5A ;
- une collection d'objets `ExpertAnalysis` ou de dictionnaires equivalents.

Les entrees sont copiees avant lecture et ne sont jamais modifiees. Le generateur reprend seulement les informations
fournies. Il ne cree aucune regle, aucun constat, aucune valeur et aucune conclusion juridique.

Lorsqu'une metadonnee non exposee par LOT 5A manque, le rapport utilise une valeur de repli visible. Par exemple, le
titre devient `Rapport du dossier <case_id>` et la confidentialite devient `restricted`.

## Vue salarie

La vue salarie contient une synthese courte, la situation, les documents, le statut simple de chaque theme, les actions,
la confiance et les limites. Les identifiants de regles, sources techniques et points de controle detailles n'y sont pas
exposes.

## Vue expert

La vue expert conserve les douze sections, les sources citees, documents, constats, controles, risques, refus, limites
et details de confiance. Elle reste une restitution des donnees recues, pas une nouvelle analyse.

## Confidentialite et metadonnees

Le rapport porte `synthetic_only = true`, le niveau de confidentialite, la version du rapport, la version du pipeline,
le protocole et la date de generation. Il ne contient ni contenu documentaire reel ni valeur de parametre de paie.

## Limites V1

- aucune generation de PDF, HTML ou document bureautique ;
- aucune interface graphique ;
- aucune API ;
- aucun OCR ou import documentaire ;
- aucun appel expert ;
- aucun calcul de paie ;
- aucun conseil juridique definitif ;
- aucune persistance du rapport.

## Integrations futures

Le cockpit pourra consommer la vue salarie ou la vue expert sans modifier le pipeline. Un futur export PDF devra rendre
le meme ordre de sections et appliquer ses propres controles de confidentialite, sans ajouter de conclusion ni de
calcul. Toute API future devra utiliser le meme objet versionne et conserver `synthetic_only` et la confidentialite.
