# CFDT Nexus — Audit final de préparation de la V1

## Décision

**READY WITH KNOWN LIMITATIONS**

La branche de stabilisation peut être fusionnée dans `main`. Aucun défaut bloquant,
aucune fuite de confidentialité et aucun nouvel échec de test ne sont observés.
Les limites restantes concernent l'alimentation documentaire de connecteurs
optionnels, la couverture locale Protection sociale, la latence de certains
scénarios et l'absence d'un guide d'exploitation V1 consolidé.

## État Git

- Branche auditée : `nexus-v1-release-readiness-final-audit`
- HEAD : `390117af456466fbbbf1059f232b253d55512057`
- Branche source de la future fusion :
  `nexus-v1-stabilization-p1-privacy-gate`
- Cible : `main`
- Divergence avec `main` : 0 commit derrière, 20 commits devant
- Chaîne : linéaire, sans rupture ni commit parasite
- Fichiers confidentiels LOT 0 suivis : aucun
- Artefacts `.pyc`, `__pycache__`, `.pytest_cache` ou journaux suivis : aucun
- Fichiers de production modifiés par l'audit : aucun

### Commits à fusionner, dans l'ordre

1. `50c4879` — Ajoute le modèle métier commun de Nexus Core V3
2. `3a066aa` — Ajoute le graphe de preuves de Nexus Core V3
3. `17bb025` — Ajoute le moteur de raisonnement générique de Nexus Core V3
4. `b5775a4` — Ajoute le moteur de classification des conflits de Nexus Core V3
5. `c6566bc` — Ajoute le framework d orchestration de Nexus Core V3
6. `a5c3587` — Ajoute l adaptateur Expert Paie vers Nexus Core V3
7. `9bba8f6` — Ajoute l adaptateur Retraite et Penibilite vers Nexus Core V3
8. `66d315c` — Ajoute l adaptateur CSE Memory vers Nexus Core V3
9. `20210c4` — Ajoute le socle générique des adaptateurs de connecteurs
10. `9075800` — Raccorde le Core V3 au runtime Juriste et Paie
11. `b0b1ac0` — Raccorde les connecteurs officiels au Runtime via Connector Adapter
12. `22b5913` — Raccorde CSE Memory au Runtime via le Core V3
13. `08a7262` — Raccorde le domaine Retraite au Runtime via le Core V3
14. `c1321c8` — Raccorde le domaine Protection Sociale au Runtime via le Core V3
15. `46be03f` — Raccorde les connecteurs officiels existants au Runtime
16. `8287b84` — Ajoute la campagne de validation fonctionnelle V1
17. `25d5fe0` — Supprime les fuites techniques des réponses publiques
18. `d0ad37e` — Améliore le routage Runtime et l'activation des connecteurs
19. `0668629` — Améliore l'activation et le routage de CSE Memory
20. `390117a` — Corrige les faux positifs du Privacy Gate Runtime

Les branches Core V3, adaptateurs, Runtime LOT 1 à 6, campagne fonctionnelle,
stabilisation P0, routage P1, CSE Memory P1 et Privacy Gate P1 sont incorporées
dans cette chaîne.

## Campagne fonctionnelle finale

- Scénarios exécutés : 100/100
- Réussites techniques : 100
- Réponses vides : 0
- Routage principal correct : 100/100
- Violations de confidentialité publiques : 0
- Scénarios avec au moins un fallback : 36
- Événements de fallback : 38
- Anomalies techniques : 0
- Anomalies de confidentialité : 0
- Anomalies bloquantes : 0

## Classification des 38 fallbacks

| Catégorie | Code | Événements | Qualification | Correctif avant release |
|---|---|---:|---|---|
| B | `OFFICIAL_CONNECTORS_NO_RESULT` | 27 | Connecteur optionnel sélectionné mais aucune métadonnée locale injectée | Non |
| A | `PROTECTION_SOCIALE_NO_RESULT` | 9 | Recherche locale sans document correspondant | Non |
| C | `NO_RUNTIME_EXPERT_PAYLOAD` | 2 | Aucun payload Juriste, Paie ou connecteur applicable au pont Core principal | Non |

Chaque événement conserve une réponse finale non vide et le fallback historique.
La liste individuelle complète figure dans
`V1_FINAL_RELEASE_READINESS_MATRIX.json`.

### Connecteurs officiels sans résultat

Les 27 événements concernent 20 sélections INRS, 7 DREETS Grand Est et 6 CNIL ;
certains scénarios sélectionnent plusieurs connecteurs au sein d'un seul événement.
Le Runtime et les connecteurs fonctionnent hors ligne mais la campagne ne leur
injecte aucun snapshot documentaire exploitable. C'est une limitation
d'alimentation, pas une panne.

### Protection sociale

Le Runtime Protection sociale est appelé sur 13 scénarios. Quatre appels produisent
8 éléments exploitables ; neuf recherches locales ne trouvent aucun résultat. Le
rapport historique reste disponible.

### Pont Core non applicable

`V1-PS-007` et `V1-RE-003` n'ont aucun payload applicable au pont Core principal.
Les domaines spécialisés continuent leur parcours indépendant. Ce comportement est
volontaire et non bloquant.

## Scénarios métier prioritaires

### CSE

- Scénarios CSE principaux : 10/10 réussis
- Scénarios attendant CSE Memory dans toute la campagne : 13
- CSE Memory observé : 13/13
- Fallback CSE Memory : 0
- Fuite de confidentialité : 0

`V1-CSE-006` présente uniquement un fallback DREETS sans résultat. CSE Memory et la
réponse finale restent disponibles. Aucun défaut CSE bloquant n'est détecté.

### Accords d'entreprise

- Scénarios Accords INEOS : 8/8 réussis
- Routage correct : 8/8
- Source `bible_accords` observée : 8/8
- Fuite de confidentialité : 0

`V1-IN-004` ne reçoit aucun résultat INRS et `V1-IN-005` aucun résultat Protection
sociale. L'accord d'entreprise reste utilisé dans les deux réponses. Aucun défaut
bloquant sur les accords n'est détecté.

## Confidentialité

Les 100 réponses publiques ont été contrôlées par le runner après sanitation :

- `chunk_id` : absent ;
- chemin Windows ou Linux : absent ;
- hash et UUID internes : absents ;
- `storage_id` : absent ;
- diagnostic technique : absent des sorties publiques ;
- contenu brut ou confidentiel : absent ;
- donnée personnelle interdite : absente.

Les tests confirment le blocage des NIR, IBAN, courriels interdits, namespaces
sensibles, chemins locaux et identifiants invalides. Les identifiants Runtime
pseudonymisés valides ne produisent plus de faux positif.

## État effectif des connecteurs et mémoires

| Composant | Intégré | Activable | Appelé dans la campagne | Résultat exploitable | Limitation / impact release |
|---|---|---|---|---|---|
| Légifrance | Oui | Oui | 87 scénarios | Oui | API externe réelle non qualifiée par cette campagne locale |
| CDTN | Oui | Oui | 31 scénarios | Oui | Même limite d'environnement |
| JUDILIBRE | Oui | Oui | 23 scénarios | Oui | Même limite d'environnement |
| CNIL | Oui | Oui, flag global | 6 scénarios | Non | Aucune métadonnée injectée ; limitation connue |
| DREETS Grand Est | Oui | Oui, flag global | 7 scénarios | Non | Aucune métadonnée injectée ; limitation connue |
| INRS | Oui | Oui, flag global | 20 scénarios | Non | Aucune métadonnée injectée ; limitation connue |
| Protection sociale | Oui | Oui, flag dédié | 13 scénarios | 4 réussites, 9 sans résultat | Couverture locale partielle |
| CSE Memory | Oui | Oui, flag dédié | 13 scénarios attendus et observés | Oui | Corpus local requis |
| Retraite | Oui | Oui, flag dédié | 12 scénarios | Oui, 24 éléments | Moteur spécialisé, aucun fallback |

Un connecteur intégré n'est donc pas nécessairement alimenté. La V1 ne doit pas
présenter CNIL, DREETS ou INRS comme des sources documentaires actives tant que
leurs métadonnées ne sont pas fournies.

## Tests

| Suite | Résultat | Durée |
|---|---|---:|
| Campagne fonctionnelle | 100/100 réussites | 6 min 51,79 s |
| Runtime | 129 réussites, 692 désélectionnés | 1,35 s |
| CSE Memory | 78 réussites | 1,26 s |
| Confidentialité | 148 réussites | 0,74 s |
| Architecture | 12 réussites | 0,23 s |
| Connecteurs pertinents et Connector Adapter | 290 réussites, 79 sous-tests | 0,56 s |
| Suite complète | 2 278 réussites, 128 sous-tests, 3 échecs historiques | 36,05 s |

Échecs historiques uniquement :

1. `DependencyTests::test_import_does_not_load_forbidden_packages`
2. `IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `test_integration_failure_preserves_legacy_expert_payload`

Nouveaux échecs : aucun.

## Performance

- Moyenne : 4 056,16 ms
- Médiane : 2 524 ms
- P95 : 10 238 ms
- Maximum : 18 232 ms (`V1-CH-011`)

Domaines les plus lents en moyenne :

1. Multidomaine : 6 363 ms
2. Convention Chimie : 6 262,6 ms
3. Paie : 4 841,1 ms
4. Sécurité / INRS : 4 706,6 ms

Les composants spécialisés instrumentés sont peu coûteux : Retraite est de l'ordre
de 1 ms et Protection sociale de 15 ms en moyenne. Les diagnostics actuels ne
séparent pas précisément le routeur, les experts historiques, le Core,
`PipelineExecutor` et l'orchestrateur ; la majorité du temps est donc attribuable
au parcours historique et aux enrichissements de sources sans ventilation plus
fine.

La performance n'empêche pas un usage local, mais le P95 supérieur à 10 secondes
doit être annoncé pour les dossiers multidomaines, Convention Chimie et Paie.

## Documentation et exploitation

Éléments présents :

- procédure de lancement dans `README.md` et
  `apps/nexus-local-interface/README.md` ;
- documentation des six feature flags Runtime dans les LOT 1 à 6 ;
- campagne reproductible via `tools/run_v1_functional_campaign.py` ;
- tests Pytest ;
- fallback historique et flags désactivés par défaut ;
- corpus confidentiels maintenus hors Git.

Éléments manquants ou dispersés, non bloquants pour une fusion :

- aucun guide d'exploitation V1 unique regroupant lancement, flags et répertoires ;
- aucun manifeste de dépendances Python consolidé détecté ;
- aucune procédure de rollback release formalisée ;
- limitations documentaires réparties entre plusieurs LOT ;
- les fichiers confidentiels non suivis exigent une discipline de staging stricte.

## Risques de fusion

| Risque | Niveau | Motif |
|---|---|---|
| Fonctionnel | Moyen | Connecteurs officiels non alimentés et couverture Protection sociale partielle |
| Confidentialité | Faible | 0 fuite sur 100 scénarios et 148 tests dédiés réussis |
| Git | Moyen | 20 commits et nombreux fichiers non suivis ; utiliser un worktree propre |
| Régression | Faible | Aucun nouvel échec, suites ciblées intégralement vertes |
| Fichiers non suivis | Moyen | Deux fichiers Retraite confidentiels et audits locaux à exclure |
| Trois échecs historiques | Faible | Reproduits et qualifiés avant ces LOT |
| Fallbacks restants | Moyen | Non techniques, réponse historique préservée |
| Performance | Moyen | P95 10,2 s et maximum 18,2 s |

## Plan de fusion sûr

1. Utiliser un clone ou worktree propre afin d'exclure tous les fichiers non suivis.
2. Exécuter `git fetch origin`.
3. Vérifier que la source distante pointe sur
   `390117af456466fbbbf1059f232b253d55512057`.
4. Vérifier que `main` local et `origin/main` sont identiques et que le dépôt est
   propre.
5. Fusionner explicitement
   `nexus-v1-stabilization-p1-privacy-gate` dans `main` avec `--no-ff`.
6. Vérifier les deux parents du commit de fusion et le périmètre des 20 commits.
7. Rejouer les suites Runtime, CSE Memory, confidentialité, architecture,
   connecteurs et la suite complète.
8. Rejouer les 100 scénarios avec tous les flags activés.
9. Vérifier `git diff HEAD^1..HEAD --check` et `git status --short`.
10. Pousser `main` uniquement si les résultats restent identiques.
11. Vérifier `HEAD == origin/main` et une divergence `0 0`.

Avant push, un merge non conforme doit être abandonné dans le worktree propre.
Après push, le retour arrière doit utiliser un commit de revert du merge
(`git revert -m 1 <merge>`), sans réécriture de l'historique partagé.

## Conclusion

La V1 est **READY WITH KNOWN LIMITATIONS**.

La fusion est autorisable sous réserve d'un worktree propre, des contrôles
pré-fusion et de la campagne post-fusion. Les connecteurs CNIL, DREETS et INRS ne
doivent pas être présentés comme alimentés, la couverture Protection sociale reste
partielle et les latences élevées doivent être documentées.

Aucun commit, push ou merge n'a été réalisé pendant cet audit.
