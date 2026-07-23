# CFDT Nexus V1 — Stabilisation P1-1 Routage

## Périmètre

Le LOT corrige uniquement les décisions de sélection du Runtime : domaines,
experts et connecteurs existants. Il ne modifie ni les règles métier, ni les
réponses juridiques, ni les connecteurs, ni les corpus, ni Nexus Core V3.

Branche : `nexus-v1-stabilization-p1-routing`

HEAD de départ : `25d5fe07f1d65d5c66a70db9ef38e7afcc7f2413`

## Causes identifiées

1. Le routeur ne possédait pas de domaines explicites pour le droit du travail
   général, le RGPD/CNIL, la protection sociale et la retraite/pénibilité.
2. Les vocabulaires santé-sécurité, temps de travail et CSE ne couvraient pas
   plusieurs formulations réelles de la campagne.
3. Le besoin de recherche dans CSE Memory n'était pas exprimé comme un intent
   documentaire.
4. Les sélections JUDILIBRE et CDTN reposaient sur des domaines et intents trop
   génériques, ce qui produisait des activations sans besoin métier.
5. CNIL, DREETS Grand Est et INRS ne pouvaient être appelés par le Runtime
   officiel qu'en présence de métadonnées déjà produites ; la sélection est
   désormais fondée sur un besoin métier explicite, avec injection locale vide
   autorisée et sans accès réseau.
6. L'observabilité de campagne ne comptabilisait pas uniformément les appels
   réels des experts et connecteurs et interrompait la campagne sur une erreur
   Runtime isolée.
7. Un échec inattendu de CSE Memory pouvait remonter au serveur au lieu de
   préserver le rapport historique.

## Règles modifiées

- Ajout de domaines de routage explicites pour le droit du travail général,
  RGPD/CNIL, protection sociale et retraite/pénibilité.
- Extension ciblée des marqueurs contrat, CDD/CDI, période d'essai,
  discrimination, harcèlement, durée du travail, pause, équipes alternantes,
  CSE, protocole électoral, santé-sécurité et pénibilité.
- Ajout de l'intent `rechercher_cse_memory`.
- Sélection JUDILIBRE réservée aux litiges et questions d'interprétation
  jurisprudentielle ; sélection CDTN réservée aux questions pratiques.
- Activation bornée de CNIL, DREETS Grand Est et INRS par besoin métier,
  en conservant `METADATA_ONLY`, l'absence de réseau et les quotas existants.
- Alias de domaine retraite raccordé au pont Runtime existant.
- Fallback CSE au niveau serveur et observabilité de campagne renforcée.

## Métriques finales

| Mesure | Avant | Après |
|---|---:|---:|
| Scénarios exécutés avec succès | 100/100 | 100/100 |
| Routage principal correct | 75/100 (75,00 %) | 100/100 (100,00 %) |
| Activation complète parmi les 94 scénarios concernés | 19/94 (20,21 %) | 36/94 (38,30 %) |
| Scénarios avec activation manquante | 75 | 58 |
| Activations attendues manquantes | 133 | 73 |
| Activations inutiles | 79 | 13 |
| Scénarios avec activation inutile | 64 | 13 |
| Experts attendus correctement sélectionnés | 117/185 | 151/185 |
| Scénarios avec tous les experts attendus | 43/100 | 69/100 |
| Fallbacks Runtime | 62 | 66 |

Les 25 anomalies de routage principal sont corrigées. En appliquant le critère
strict « routage correct et tous les connecteurs attendus observés », 22
scénarios précédemment anormaux sont totalement corrigés.

## Activation par connecteur

| Connecteur | Manquants avant | Manquants après | Inutiles après |
|---|---:|---:|---:|
| CDTN | 16 | 7 | 0 |
| CNIL | 7 | 1 | 0 |
| CSE Memory | 9 | 5 | 2 |
| DREETS Grand Est | 7 | 1 | 1 |
| INRS | 19 | 4 | 5 |
| JUDILIBRE | 7 | 0 | 0 |
| Légifrance | 56 | 43 | 5 |
| Protection Sociale locale | 12 | 12 | 0 |

## Anomalies restantes

- Routage principal : aucune.
- Activation complète : 58 scénarios restent incomplets.
- Activations attendues manquantes : 73 occurrences.
- Activations inutiles : 13 occurrences sur 13 scénarios.
- Experts attendus manquants : 34 occurrences ; 31 scénarios n'ont pas encore
  tous leurs experts attendus.
- Fallbacks Runtime : 66. Leur traitement fonctionnel et leurs performances
  sont hors périmètre de ce LOT de routage.
- Suite complète : les trois échecs historiques qualifiés subsistent ; aucun
  nouvel échec n'est introduit.

## Validations

- Campagne fonctionnelle : 100/100 scénarios exécutés, 100 succès techniques,
  aucune réponse vide.
- Tests Runtime : 90 réussites, 668 désélectionnés.
- Tests d'architecture : 12 réussites.
- Suite complète : 2 215 réussites, 128 sous-tests réussis, 3 échecs historiques.
- `git diff --check` : réussi.
