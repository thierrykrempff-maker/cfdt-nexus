# Source « archive PV » de l'analyse d'ordre du jour CSE

Statut : optionnelle, **désactivée par défaut**, activée localement par `NEXUS_PV_ARCHIVE_ENABLED`.

## Objectif

Pour chaque point d'un ordre du jour CSE, retrouver dans l'archive des PV du CE/CSE (2000-2024, OCR français inclus)
si le sujet a déjà été traité, et afficher des extraits datés dans le bloc « Ce qui a déjà été traité ».

Cette source **complète** les deux sources existantes (PV ajoutés manuellement, corpus CSE Memory). Elle ne les remplace
pas et ne modifie ni leur ordre ni leurs limites.

## Flux

```text
POST /api/cse/agenda-preview
-> apps/nexus-local-interface/server.py (inchangé)
-> cse_agenda_analysis.build_cse_agenda_analysis
     1. _search_uploaded_minutes   (PV ajoutés, inchangé)
     2. _search_previous_minutes   (CSE Memory, inchangé)
     3. _search_pv_archive         (NOUVEAU, une seule requête pour tous les points)
        -> POST http://127.0.0.1:8791/api/passages   (service local du module « Précédents »)
     -> _merge_previous_minutes(uploaded, corpus, archive)
```

## Règles de fusion

- Les passages des deux sources existantes passent d'abord, dans le même ordre et avec la même limite
  (`MAX_PREVIOUS_PASSAGES = 3`).
- L'archive ajoute au plus `MAX_ARCHIVE_PASSAGES = 3` passages par point, dédoublonnés sur l'extrait.
- Chaque passage porte `origin = "PV_ARCHIVE"`, un titre limité au **nom du PV** (jamais de chemin local), une date
  (précision indiquée : jour, mois ou année), l'instance (CE ou CSE), la page, et les limites habituelles
  (« contexte historique, pas une norme juridique », « l'absence de résultat ne prouve pas... »).
- Sans le drapeau, la sortie de `build_cse_agenda_analysis` est strictement identique à l'ancienne (aucun champ ajouté).

## Champs ajoutés (uniquement quand le drapeau est actif)

| Champ | Valeurs |
| --- | --- |
| `archive_status` | `READY` ou `UNAVAILABLE` |
| `points_with_archive_minutes` | nombre de points rapprochés d'au moins un PV de l'archive |
| `corpus_notice` | complété par une phrase sur l'archive (consultée, ou indisponible) |

## Dégradation

Si le service est arrêté, injoignable, lent (10 secondes maximum) ou répond de façon invalide, l'analyse continue sans
l'archive : `archive_status = UNAVAILABLE` et la notice le signale. Aucune exception ne remonte.

## Sécurité et confidentialité

- L'URL du service doit être en `http` et désigner la machine locale (`127.0.0.1`, `localhost`, `::1`). Toute autre
  adresse est refusée sans appel réseau.
- Le service n'écoute que sur `127.0.0.1`. Il ne sert les extraits (`/api/passages`) qu'à un client **non navigateur**
  (toute requête avec `Origin` ou `Sec-Fetch-*` est refusée) et exige les en-têtes `X-Nexus` et `X-Nexus-Server`.
- L'index des PV reste **hors dépôt** (`NEXUS_PV_INDEX`). Aucun PV n'est copié dans ce dépôt ni dans `knowledge-base/`.
- Les PV contiennent des noms : les extraits n'apparaissent que dans l'interface locale, jamais dans les exports
  « synthèse publique » (copie, impression, téléchargement).
- Ce n'est pas un appel à un service externe : aucune donnée ne quitte la machine.

## Configuration

| Variable | Rôle | Défaut |
| --- | --- | --- |
| `NEXUS_PV_ARCHIVE_ENABLED` | active la source (`true`, `1`, `yes`, `on`) | désactivée |
| `NEXUS_PV_ARCHIVE_URL` | adresse du service d'archive | `http://127.0.0.1:8791` |

`start-nexus-local.bat` active le drapeau. Le service d'archive est le module « Précédents » du site CFDT
(`private/cfdt-nexus-precedents/service/server.py`), démarré avec la session Windows.

## Limites connues

- Archive limitée aux PV du CE/CSE : pas de PV de CHSCT/CSSCT.
- Anciens `.ppt` non lus ; OCR imparfait sur les vieux scans ; dates déduites des noms de fichiers.
- Le rapprochement est lexical (notions du titre du point), pas sémantique : un point au titre vague
  (« Divers », « Information ») donne peu de résultats utiles.

## Tests

`tests/test_cse_agenda_analysis.py` : désactivation par défaut, ordre de fusion, une seule requête groupée avec les
en-têtes serveur, service indisponible, réponse malformée, URL non locale refusée, plafond et dédoublonnage.
Les tests utilisent un faux service sur la boucle locale et des données fictives.
