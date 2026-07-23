# CFDT Nexus V1 — Stabilisation P1-2 CSE Memory

## Périmètre

Ce LOT corrige uniquement la sélection et l'activation effective de CSE Memory.
Il ne modifie ni les moteurs métier, ni les connecteurs officiels, ni les
accords, ni le corpus CSE, ni Nexus Core V3.

- Branche : `nexus-v1-stabilization-p1-cse-memory`
- HEAD de départ : `d0ad37e4114e6aa4059a4fb0954868cbdf34e8e8`
- Feature flag inchangé : `NEXUS_CSE_MEMORY_RUNTIME_ENABLED`

## Analyse préalable

Avant le LOT, 13 scénarios attendaient CSE Memory :

- 8 étaient correctement enrichis ;
- 5 restaient manquants ;
- 2 scénarios hors périmètre CSE déclenchaient CSE Memory inutilement ;
- 1 appel CSE Memory terminait en fallback.

| Scénario | Cause avant correction | Correction |
|---|---|---|
| `V1-CSE-004` | Le besoin était sélectionné, mais un hash pseudonyme contenait fortuitement dix chiffres consécutifs après normalisation et était rejeté par le Privacy Gate du Core. | Encodage alphabétique et déterministe des hashes techniques CSE. |
| `V1-IN-004` | La recherche d'un ancien accord, de documents et de dates n'était pas reconnue comme besoin documentaire historique. | Condition composée `ancien accord` + `document/date`. |
| `V1-MD-006` | Le projet industriel multidomaine mentionnait le CSE et les impacts, sans marqueur documentaire reconnu. | Marqueurs bornés `projet` et `impact` sous domaine CSE. |
| `V1-PS-004` | Le changement de garanties santé sans document clair n'était pas relié à la mémoire documentaire. | Condition composée `garanties santé` + `changement/document`. |
| `V1-RG-005` | L'outil de classement automatisé n'était pas reconnu comme sujet nécessitant les antécédents CSE. | Condition composée `outil` + `classe automatiquement`. |
| `V1-DT-013` | L'expression générique `démarches collectives` déclenchait l'intent documentaire. | Suppression de ce marqueur trop large. |
| `V1-DT-018` | L'expression générique `enquête interne` déclenchait l'intent documentaire. | Suppression de ce marqueur trop large. |

## Correction

- Les marqueurs CSE Memory sont désormais fondés sur un besoin documentaire
  explicite ou une combinaison métier fermée.
- Les expressions collectives génériques ne suffisent plus à déclencher la
  mémoire.
- Les identifiants Runtime CSE restent pseudonymes et déterministes, mais leur
  partie dérivée du hash ne contient plus de chiffres susceptibles de former
  fortuitement une donnée personnelle apparente.
- Le parcours existant reste inchangé :
  recherche locale en lecture seule, CSE Adapter, Core V3, PipelineExecutor,
  CommonExpertOrchestrator et rapport enrichi.
- Aucun document, chunk, index ou fichier du corpus n'est modifié.

## Métriques

| Mesure CSE Memory | Avant | Après |
|---|---:|---:|
| Scénarios avec CSE Memory attendu | 13 | 13 |
| Scénarios correctement enrichis | 8 | 13 |
| Taux d'utilisation effective sur les scénarios attendus | 61,54 % | 100,00 % |
| Scénarios attendus manquants | 5 | 0 |
| Activations injustifiées | 2 | 0 |
| Fallbacks CSE Memory | 1 | 0 |
| Scénarios observant CSE Memory au total | 10 | 13 |

Scénarios corrigés :

- `V1-CSE-004`
- `V1-IN-004`
- `V1-MD-006`
- `V1-PS-004`
- `V1-RG-005`

## Impact transversal

- Campagne : 100/100 succès techniques.
- Routage principal : 100/100, inchangé.
- Scénarios avec activation complète de tous les connecteurs : 36 → 39.
- Observations des autres connecteurs : inchangées.
- Fallbacks Runtime globaux : 66 → 66 ; le fallback CSE a disparu, les
  fallbacks restants relèvent des autres composants et sont hors périmètre.
- Anomalie CSE Memory restante : aucune.

## Tests

- Tests CSE Memory ciblés : 15 réussites.
- Tests Runtime : 94 réussites, 668 désélectionnés.
- Tests d'architecture : 12 réussites.
- Suite complète : 2 219 réussites, 128 sous-tests réussis et uniquement les
  3 échecs historiques qualifiés.
- Nouvel échec : aucun.
- `git diff --check` : réussi.
