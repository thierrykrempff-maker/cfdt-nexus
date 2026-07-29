# LOT 3 V1 — réponse finale courte, lisible et exploitable

## Cause racine

La frontière HTTP reproduisait les mêmes informations dans `answer`,
`orchestration`, les cartes expertes et le rapport Markdown. Elle exposait aussi
des projections détaillées conçues pour l’audit plutôt que pour une utilisation
pendant un entretien. Le raisonnement interne n’était pas en cause.

## Architecture retenue

`build_final_response()` construit deux projections déterministes à partir du
payload interne déjà assaini :

- `public_summary` : douze sections au maximum, aucune section vide, limites
  explicites sur questions, documents, analyses et sources ;
- `detailed_analysis` : noyau factuel, questions et documents complets,
  comparaisons règle–faits, sources secondaires, sources rejetées et limites.

Le payload interne n’est ni modifié ni tronqué. Les champs historiques essentiels
restent disponibles dans `answer`, `orchestration`, `expert_juriste` et
`analysis_report`. La version publique du rapport est `3.0`.

L’interface affiche la synthèse en premier et l’analyse détaillée dans un élément
HTML natif `details`, fermé par défaut et accessible au clavier. L’impression
masque ce bloc. La copie et l’export Markdown sont reconstruits exclusivement à
partir des sections de synthèse.

## Structure publique

Les sections sont ordonnées ainsi lorsqu’elles contiennent des éléments :

1. situation comprise ;
2. niveau d’urgence et justification ;
3. position syndicale provisoire ;
4. points forts et points faibles ;
5. questions prioritaires ;
6. documents à obtenir ;
7. règles comparées aux faits ;
8. stratégie pratique et formulations utiles ;
9. éléments à éviter ;
10. actions suivantes ;
11. sources déterminantes ;
12. limites et incertitudes.

Les questions conservent le destinataire, la formulation, la raison et la
priorité. Les documents conservent le nom, le détenteur probable, l’utilité et la
priorité. Une analyse règle–faits conserve notamment le meilleur argument du
salarié, le meilleur argument de la direction, le fait manquant, la conclusion
provisoire et l’action.

## Compatibilité

- `answer.short_answer`, `answer.working_position`, les domaines et les intents
  restent disponibles ;
- `answer.case_factual_core` conserve les identifiants métier historiques
  nécessaires au routage, sans identifiant technique ;
- `answer.rule_to_facts_analysis` reste non vide lorsqu’une comparaison existe ;
- `analysis_report.sections` reste le contrat d’affichage historique ;
- `analysis_report.export_scope` vaut `PUBLIC_SUMMARY_ONLY`.

## Résultats des onze cas

| Cas | Avant LOT 3 | Après LOT 3 | Score |
|---|---:|---:|---:|
| REAL-01 | 164 791 | 34 170 | 92 |
| REAL-02 | 145 250 | 39 543 | 93 |
| REAL-03 | 124 349 | 34 530 | 92 |
| REAL-04 | 149 333 | 36 595 | 92 |
| REAL-05 | 72 536 | 20 327 | 70, suspendu |
| REAL-06 | 67 802 | 17 967 | 70, suspendu |
| REAL-07 | 132 953 | 35 535 | 92 |
| REAL-08 | 140 110 | 35 752 | 92 |
| REAL-09 | 111 219 | 20 750 | 74 |
| REAL-10 | 144 628 | 28 576 | 90 |
| REAL-11 | 125 360 | 24 490 | 82 |

La taille moyenne passe de 125 303 à 29 839,55 octets. Aucun cas complet ne
dépasse 45 000 octets et aucun cas suspendu ne dépasse 25 000 octets.

REAL-02 met en avant les pauses, le contrôle par tourniquet, les pièces RGPD et
les sources réellement disponibles. REAL-05 reste court et suspendu. REAL-09
indique toujours que la procédure interne applicable manque. REAL-10 conserve le
poste à risque, les faits reconnus et la marge de négociation limitée.

## Garanties

- score moyen inchangé : 85,36/100 ;
- huit cas complets sur neuf au-dessus de 75 ;
- REAL-05 et REAL-06 restent suspendus ;
- aucune règle de compréhension factuelle ou de comparaison source–faits
  modifiée ;
- aucune source, jurisprudence ou fait créé ;
- aucun identifiant de cas utilisé dans le moteur ;
- aucune modification d’un connecteur, d’un feature flag, du moteur Paie, du
  corpus ou du lanceur local.

## Risques résiduels

La cible indicative de 15 000 octets pour les cas suspendus n’est pas atteinte,
mais leur plafond dur de 25 000 octets est respecté et leurs données d’audit
restent disponibles. REAL-09 demeure limité à 74/100 tant que la procédure
chimique interne réellement applicable n’est pas fournie.
