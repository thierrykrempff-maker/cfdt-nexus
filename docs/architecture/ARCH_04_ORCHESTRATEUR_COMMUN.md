# ARCH-04 — Orchestrateur commun minimal

## Objectif et périmètre

ARCH-04 introduit une infrastructure commune, séquentielle et déterministe qui reçoit un `ExpertRequest` ARCH-01, sélectionne explicitement des inscriptions du registre ARCH-03, appelle leurs `ExpertFacade`, puis agrège les résultats techniques dans un `OrchestrationResult`.

ARCH-04 ne remplace pas encore l’orchestrateur historique. Aucun consommateur historique n’est migré dans ce lot. Il n’est relié à aucune route, aucun endpoint, connecteur, cache ou API réseau. Paie, Juriste Travail et CSE ne sont pas migrés ici. Les contrats ARCH-01, adaptateurs ARCH-02, façades et registre ARCH-03 restent inchangés.

## Dépendances et modèles

Le module dépend uniquement des contrats communs ARCH-01 (`ExpertRequest`, `ExpertReport`), des façades et du registre ARCH-03, et de la bibliothèque standard Python.

- `OrchestrationRequest` enveloppe la requête ARCH-01, une liste optionnelle d’identifiants, l’autorisation des experts `PARTIAL`, une politique `CONTINUE`/`STOP` et des métadonnées.
- `OrchestrationError` porte un code stable, un message sûr, une étape, l’expert éventuel et des métadonnées techniques sûres.
- `ExpertExecutionResult` décrit le statut du registre, la tentative, le succès, le rapport ARCH-01 intact ou l’erreur.
- `OrchestrationResult` conserve les experts sélectionnés, exécutions, rapports, erreurs, résumé technique, métadonnées et statut global.
- Les statuts globaux sont `SUCCESS`, `PARTIAL_SUCCESS`, `NO_EXPERT_AVAILABLE` et `FAILED`.

Les métadonnées des modèles sont exposées en lecture seule. Aucun nouveau format concurrent de `ExpertReport` n’est créé.

## Sélection déterministe

Une liste explicite est parcourue dans son ordre d’origine après suppression stable des doublons. Sans liste explicite, les inscriptions du registre sont utilisées dans leur ordre canonique, trié par identifiant par ARCH-03. Aucun mot de la question et aucun domaine métier n’est analysé.

| Statut du registre | Traitement |
|---|---|
| `AVAILABLE` | sélectionné |
| `PARTIAL` | sélectionné seulement si autorisé et si une façade existe |
| `NOT_READY` | refus `EXPERT_NOT_READY` |
| `DISABLED` | refus `EXPERT_DISABLED` |
| inconnu | erreur `UNKNOWN_EXPERT` |

Un registre vide produit `NO_EXPERT_SELECTED` et le statut global `NO_EXPERT_AVAILABLE`. Le registre reste un catalogue : aucune logique de routage ne lui est ajoutée.

## Exécution et isolation des erreurs

`CommonExpertOrchestrator.execute` transmet la même instance immuable de `ExpertRequest` à chaque façade sélectionnée, exclusivement via l’API ARCH-03. Les appels sont séquentiels. Un rapport valide est conservé sans mutation. Une valeur invalide, une incohérence de requête ou une exception devient `EXPERT_EXECUTION_FAILED`; le message et le type d’exception sont sûrs, sans traceback, chemin local ni détail confidentiel.

Avec `CONTINUE`, les façades suivantes sont exécutées. Avec `STOP`, aucune nouvelle exécution n’est commencée après le premier échec. Une défaillance ne modifie ni ne contamine les rapports des autres façades.

## Agrégation minimale et déterminisme

L’agrégation conserve l’ordre d’exécution, compte succès et erreurs, liste les experts tentés et calcule le statut global. Elle ne fusionne, ne réécrit, ne déduplique et n’arbitre aucune conclusion métier. Sources, preuves, contradictions, conclusions et métadonnées restent dans chaque `ExpertReport`; deux avis opposés restent deux avis distincts.

Il n’y a ni horloge, ni identifiant aléatoire, ni parallélisme, ni cache, ni temporisation. À entrées et façades déterministes identiques, sélection, codes, ordre et agrégation sont équivalents.

## Future sélection des sources et migration

La sélection est une fonction séparée de l’exécution. Une future phase pourra donc préparer un contexte de sources avant de construire l’`OrchestrationRequest`, puis laisser ARCH-04 sélectionner les experts. Ce lot ne crée aucun moteur de sources, connecteur, appel, faux résultat ou `SourceEvidence` artificiel et ne modifie aucun contrat.

La migration future pourra brancher progressivement des consommateurs sur cette API après validation dédiée, expert par expert. Le remplacement de l’orchestrateur historique et le routage opérationnel relèvent de lots ultérieurs, avec compatibilité et retour arrière propres.

## Limites connues

La sélection est seulement explicite ou exhaustive sur les inscriptions éligibles; elle n’est pas sémantique. L’exécution est synchrone et sans reprise, délai maximal ou cache. Le résumé est volontairement technique. Un expert `PARTIAL` déclaré sans façade ne peut pas être exécuté, même si la politique l’autorise.

## Exemple

```python
from automation.contracts import ExpertRequest
from automation.expert_facades import build_default_registry
from automation.orchestrator_common import CommonExpertOrchestrator, OrchestrationRequest

request = ExpertRequest("case-1", "Question", "generic")
result = CommonExpertOrchestrator(build_default_registry()).execute(
    OrchestrationRequest(request, requested_experts=("payroll",))
)
```

## Matrice des tests

| Domaine | Couverture |
|---|---|
| Initialisation | import, construction, registre vide et statuts multiples |
| Sélection | available, partial autorisé/refusé, not-ready, disabled, inconnu, doublons, ordre implicite/explicite |
| Exécution | un/plusieurs succès, continuation, arrêt, sortie invalide, exception sûre, identité et immutabilité de requête |
| Agrégation | zéro/un/plusieurs rapports, succès complet/partiel/échec, ordre, métadonnées, désaccord sans arbitrage |
| Compatibilité | types ARCH-01, façades ARCH-03, contrôle des dépendances interdites et réseau |
| Déterminisme | résultats équivalents, ordre et codes stables |
