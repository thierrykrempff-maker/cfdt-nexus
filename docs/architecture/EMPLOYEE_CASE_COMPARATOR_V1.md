# Comparateur de dossiers salariés V1 — LOT 5D

## Objectif

Le comparateur rapproche deux dossiers salariés synthétiques ou deux rapports LOT 5B. Il décrit les écarts documentaires entre une situation A et une situation B sans recalculer la paie, sans appeler un expert et sans produire de conclusion juridique nouvelle.

Le module est indépendant du pipeline LOT 5A, du générateur LOT 5B et du Cockpit LOT 5C. Il ne modifie jamais ses entrées et refuse tout objet dont `synthetic_only` n'est pas vrai.

## Entrées et normalisation

`EmployeeCaseComparator.compare(case_a, case_b)` accepte :

- deux objets `EmployeeCase` ;
- deux rapports `employee_case_analysis` ;
- ou une combinaison de ces formats.

Un rapport fournit l'analyse la plus riche. Pour un dossier brut, la confiance reste `UNKNOWN`, la complétude est `not_assessed` et aucune analyse experte n'est inventée.

## Structure du résultat

Le résultat JSON contient :

1. l'identité et le type des deux sources ;
2. les quatre catégories de différences ;
3. un résumé exécutif ;
4. les différences de fond par dimension ;
5. les différences de présentation ;
6. une analyse par thème ;
7. les contradictions à contrôler ;
8. une vue salarié ;
9. une vue expert ;
10. les limites et les indicateurs de sécurité.

Les dimensions de fond sont la période, le statut, les thèmes, les documents présents et manquants, la complétude, la confiance, les contradictions, les analyses expertes et les actions recommandées. Le titre et l'identifiant sont isolés comme éléments de présentation : leur évolution ne devient pas un constat métier.

## Catégories de différences

- `new` : information uniquement présente dans B ;
- `removed` : information présente dans A mais absente de B ;
- `modified` : même champ avec un contenu différent ;
- `unchanged` : contenu identique dans A et B.

Les collections sont comparées élément par élément. Les objets structurés, notamment les synthèses expertes et les actions, restent visibles avant et après afin de préserver le contexte documentaire.

## Analyse par thème

Chaque thème expose son état A, son état B, sa catégorie de différence, les conséquences documentaires et les nouvelles pièces à demander. Le comparateur couvre tout thème fourni par les dossiers, notamment les heures supplémentaires, l'astreinte, les congés, la maladie, la classification et le repos.

Un thème débloqué sans nouvelle pièce est signalé comme un point de contrôle. Le comparateur ne prétend pas que ce changement est erroné : une justification peut exister hors des objets reçus.

## Contradictions documentaires

Les contrôles mettent en évidence :

- une baisse du niveau de confiance ;
- un changement de disponibilité documentaire ;
- un thème débloqué sans nouvelle pièce ;
- des constats experts devenus incompatibles.

Ces alertes demandent une vérification humaine. Elles n'attribuent aucune cause certaine et ne qualifient jamais une erreur de paie.

## Deux vues

La vue salarié résume simplement ce qui change, ce qui reste identique, les pièces à demander et les thèmes bloqués ou débloqués. Elle évite le détail des structures expertes.

La vue expert conserve les écarts détaillés, les états par thème, les contrôles documentaires, les différences de présentation et les limites méthodologiques.

## Limites et futurs usages

Le comparateur traite exclusivement des données synthétiques déjà structurées. Il ne lit aucun bulletin ou relevé réel, ne fait ni OCR ni calcul, et ne déduit pas de causalité. Une différence ne prouve ni anomalie de paie ni violation juridique.

Cette structure pourra ultérieurement alimenter :

- la comparaison documentaire de deux bulletins préalablement structurés ;
- la comparaison de relevés Kelio synthétiques ;
- le suivi avant et après régularisation ;
- la comparaison de versions d'un même dossier ;
- une future vue comparative du Cockpit.
