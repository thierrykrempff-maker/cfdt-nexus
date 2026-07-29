# LOT 1 — compréhension factuelle et questions exploitables

Comparaison effectuée sur les onze fixtures inchangées avec la grille de 100 points existante.

- Moyenne avant : **29.27/100**
  (baseline initiale : 32.67/100 ; second lot : 25.2/100)
- Moyenne après : **71.55/100**
- Variation : **+42.28 points**
- Compréhension factuelle ≥ 14/20 : **11/11**
- Taille publique moyenne : **29978 octets**
- Projection brute réduite moyenne : **13543 octets**
- Instantanés réduits historiques moyens : **92424 octets**

## Comparaison cas par cas

| Cas | Avant | Après | Variation | Faits | Échecs éliminatoires restants |
|---|---:|---:|---:|---:|---|
| REAL-01-INSULTING_EMAILS_ALCOHOL | 38 | 72 | +34 | 18/20 | aucun |
| REAL-02-SMOKING_BREAKS_SEVESO_BADGE | 27 | 73 | +46 | 19/20 | aucun |
| REAL-03-TAG_INSTALLATION | 50 | 72 | +22 | 18/20 | aucun |
| REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY | 47 | 72 | +25 | 18/20 | aucun |
| REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE | 22 | 70 | +48 | 19/20 | aucun |
| REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED | 12 | 68 | +56 | 20/20 | aucun |
| REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE | 16 | 72 | +56 | 18/20 | aucun |
| REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL | 28 | 72 | +44 | 18/20 | aucun |
| REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE | 15 | 72 | +57 | 18/20 | aucun |
| REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION | 30 | 72 | +42 | 18/20 | aucun |
| REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT | 37 | 72 | +35 | 18/20 | aucun |

## Constats transversaux

- Les onze faits principaux sont stables et aucun dossier n'est contaminé par un autre scénario.
- Le parcours explicitement demandé est respecté sur onze cas.
- Les questions sont structurées, hiérarchisées et directement utilisables.
- Les ambiguïtés déterminantes suspendent correctement la conclusion.
- Le risque résiduel principal est la comparaison règle-faits lorsque les sources ne remontent pas.

## Inventaire d'utilisation des connecteurs

État observé pendant le rejeu des onze cas :

- runtime officiel appelé : **false** ;
- résultats officiels exploités : **0** ;
- motif : NEXUS_RUNTIME_OFFICIAL_CONNECTORS_ENABLED was disabled during the baseline. Metadata-only connectors therefore remained fail-closed.

| Connecteur | Identifiant réel | Disponible / santé | Domaine et nature | Cas attendus | Cas déclenchés | Résultats exploités | Raison de l'absence |
|---|---|---|---|---|---|---:|---|
| Légifrance | `legifrance` (`legifrance_code_travail`) | oui — available; recherche et consultation configurées | Code du travail, conventions collectives et textes applicables — **norme obligatoire** | REAL-01/REAL-02/REAL-03/REAL-04/REAL-05/REAL-06/REAL-07/REAL-08/REAL-09/REAL-10/REAL-11 (REAL-05 et REAL-06 seulement après levée de leur ambiguïté bloquante.) | REAL-01/REAL-02/REAL-03/REAL-04/REAL-07/REAL-08/REAL-09/REAL-10/REAL-11 | 0 | Neuf recherches ont été tentées mais n'ont remonté aucun article suffisamment exploitable ; REAL-05 et REAL-06 ont été arrêtés avant recherche. |
| JUDILIBRE | `judilibre` (`judilibre_jurisprudence`) | oui — available; API et cache configurés | Jurisprudence de la Cour de cassation — **jurisprudence** | REAL-01/REAL-02/REAL-03/REAL-04/REAL-05/REAL-06/REAL-07/REAL-08/REAL-09/REAL-10/REAL-11 (Recherche seulement après qualification factuelle ; REAL-05 et REAL-06 restent suspendus.) | aucun | 0 | Le routeur n'a sélectionné aucune recherche jurisprudentielle dans cette exécution factuelle ; aucune décision n'a été inventée. |
| Code du travail numérique | `cdtn` (`cdtn_pratique_officielle`) | oui — available; accès public sans secret | Information pratique en droit du travail — **source pédagogique** | REAL-01/REAL-02/REAL-03/REAL-04/REAL-07/REAL-08/REAL-09/REAL-10/REAL-11 (Appui pédagogique uniquement ; ne remplace jamais accords, convention, Code du travail ou jurisprudence.) | aucun | 0 | Aucune fiche pratique n'a été sélectionnée pendant la baseline. |
| CNIL | `cnil` (`cnil`) | non — disabled; metadata_only_activable; transport non implémenté | Données personnelles et contrôle des salariés — **recommandation officielle** | REAL-02 | aucun | 0 | Contrat désactivé et runtime officiel non appelé ; les délibérations normatives éventuelles doivent être vérifiées sur Légifrance. |
| CARSAT | `carsat` (`carsat`) | non — disabled; architecture_only; transport non implémenté | Prévention des risques professionnels, EPI, RPS et organisation du travail — **pratique de prévention** | REAL-03/REAL-07/REAL-11 | aucun | 0 | Connecteur metadata-only et fail-closed ; ses recommandations ne sont jamais présentées comme des articles de loi. |
| ANACT | `anact` (`anact`) | non — disabled; architecture_only; transport non implémenté | Conditions et organisation du travail, QVCT et RPS — **pratique de prévention** | REAL-03/REAL-11 | aucun | 0 | Runtime officiel désactivé et contrat sans transport. |
| INRS | `inrs` (`inrs`) | non — disabled; architecture_only; transport non implémenté | Santé et sécurité au travail, prévention et EPI — **pratique de prévention** | REAL-03/REAL-07/REAL-09/REAL-10/REAL-11 | aucun | 0 | Runtime officiel désactivé et contrat metadata-only. |
| DREETS Grand Est | `dreets_grand_est` (`dreets_grand_est`) | non — disabled; architecture_only; transport non implémenté | Information administrative régionale en droit du travail — **recommandation officielle** | aucun | aucun | 0 | Aucun besoin déterminant propre aux onze fixtures et connecteur sans transport. |
| Droit local d'Alsace-Moselle | `alsace_moselle_local_law` (`alsace_moselle_local_law`) | non — metadata_only; runtime officiel désactivé | Droit local du travail applicable en Moselle — **norme obligatoire** | REAL-04 (Seulement si le travail des dimanches ou jours fériés appelle une règle locale applicable.) | aucun | 0 | Flux metadata-only non exécuté ; l'applicabilité doit d'abord être démontrée. |
| France Chimie | `france_chimie` (`france_chimie`) | non — disabled; architecture_only; transport non implémenté | Informations de branche des industries chimiques — **élément institutionnel de contexte** | aucun | aucun | 0 | Source patronale de contexte, non requise par les faits et jamais substituable à l'IDCC 44. |
| Défenseur des droits | `defenseur_droits` (`defenseur_droits`) | non — validated; disabled; metadata_only | Discrimination, égalité et libertés — **recommandation officielle** | aucun | aucun | 0 | Aucun fait discriminatoire suffisamment caractérisé dans les onze entrées. |
| Ministère du Travail | `ministere_travail` (`ministere_travail`) | non — validated; disabled; metadata_only | Doctrine et information administrative en droit du travail — **recommandation officielle** | aucun | aucun | 0 | Aucun résultat metadata-only n'a été injecté dans la baseline. |
| Service-Public.fr | `service_public` (`service_public`) | non — validated; disabled; metadata_only | Démarches et information pratique — **source pédagogique** | aucun | aucun | 0 | Aucune démarche administrative déterminante dans les onze cas. |
| Assurance Maladie | `assurance_maladie` (`assurance_maladie`) | non — validated; disabled; metadata_only | Maladie, accident du travail et prestations — **information sociale officielle** | aucun | aucun | 0 | Aucune question de prestation sociale n'est centrale dans ce LOT. |
| URSSAF | `urssaf` (`urssaf`) | non — validated; disabled; metadata_only | Cotisations et assiettes sociales — **information sociale officielle** | aucun | aucun | 0 | Expert Paie et questions de cotisations sont hors périmètre. |
| Agirc-Arrco | `agirc_arrco` (`agirc_arrco`) | non — validated; disabled; metadata_only | Retraite complémentaire — **information sociale officielle** | aucun | aucun | 0 | Aucun sujet de retraite complémentaire dans les onze cas. |

Les accords INEOS et les PV CSE/CSSCT sont des **éléments internes de contexte**, et non des connecteurs officiels. Aucun résultat local n'a été exploité pendant cette baseline.

## Limites

- Les sources disponibles dépendent de la configuration locale et des connecteurs au moment du rejeu.
- Les anciennes baselines et leurs réponses brutes n'ont pas été modifiées.
- L'issue connue et les attentes d'évaluation n'ont jamais été transmises à Nexus.
- Les scores mesurent ce LOT transversal et ne constituent pas une promesse de résultat juridique.
