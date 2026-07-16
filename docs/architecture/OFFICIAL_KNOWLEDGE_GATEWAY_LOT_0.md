# Official Knowledge Gateway — LOT 0

## Objectif

Ce lot crée un socle commun, déclaratif et sécurisé pour de futures connexions à des sources publiques officielles. Il ne contient aucun connecteur opérationnel, client HTTP, scraping, téléchargement, synchronisation, indexation ou embedding. Toute tentative de transport échoue avec `NETWORK_DISABLED_BY_DEFAULT`.

## Sources prévues et registre

Le registre versionné contient onze sources : CNIL, INRS, ANACT, Ameli, Service-Public.fr, URSSAF, Assurance retraite, Agirc-Arrco, Légifrance, JUDILIBRE et Code du travail numérique. Toutes restent `enabled = false` et `connector_status = architecture_only`. Une information non démontrée reste `unknown` ou `pending_review`; aucun point d'accès supposé n'est enregistré.

Les domaines PISTE et Code du travail numérique déjà démontrés par les connecteurs existants sont référencés sans modifier ces connecteurs. Les autres listes restent vides jusqu'à une revue dédiée.

## Séparation public/confidentiel

Le cache public futur est limité à `OFFICIAL_KNOWLEDGE_DATA/`. Il ne lit ni n'écrit dans `CCSEMEMORYENGINE` ou `PROTECTION_SOCIALE_ENGINE`. Les données publiques utilisent `confidentiality_level = public_official`; elles ne deviennent jamais des documents internes. Les répertoires `RAW`, `CACHE`, `PROCESSED`, `INDEX`, `SYNC_LOGS`, `AUDIT` et `LISEZ_MOI.txt` sont ignorés par Git.

## Autorisation et listes blanches

La politique valide HTTPS, domaine et sous-domaines explicitement autorisés, absence d'identifiants dans l'URL, IP globales, type MIME et taille. Elle refuse HTTP, `file://`, localhost, réseaux privés et redirections externes. Aucune résolution DNS ni requête n'est effectuée.

Le réseau est refusé si `OFFICIAL_KNOWLEDGE_NETWORK_ENABLED` est absent ou invalide. Une source exige en plus `OFFICIAL_KNOWLEDGE_SOURCE_<SOURCE_ID>_ENABLED`. Même avec ces variables, le LOT 0 bloque le transport : leur présence prépare seulement une autorisation future qui nécessitera un lot distinct. Des interrupteurs séparés sont prévus pour synchronisations automatiques et téléchargements.

## Provenance et autorité

La provenance relie URI source et canonique, éditeur, dates, empreinte, en-têtes de cache, licence, autorité, domaines, langue, méthode et version de connecteur. Aucun chemin local absolu n'est admis.

Les niveaux explicites couvrent loi primaire, jurisprudence officielle, réglementation, guidance, information pratique, prévention, sécurité sociale, information institutionnelle et inconnu. Un domaine officiel ne suffit jamais à classer automatiquement un contenu comme loi ou jurisprudence.

## Licences

Une licence non revue interdit par défaut réutilisation, redistribution, cache, stockage intégral permanent, téléchargement automatisé et versionnement Git. L'autorisation requiert une revue documentée (`approved`, `restricted` ou `prohibited`) dans un lot de connecteur ultérieur.

## Cache, empreintes et journal

Le modèle de cache conserve seulement métadonnées de provenance et chemin relatif. Les fonctions SHA-256 produisent empreintes de contenu, URI canonique et version, et détectent contenu inchangé ou nouvelle version. Le journal synthétique prévoit les états `planned`, `blocked`, `running`, `completed`, `completed_with_warnings`, `failed` et `cancelled`, ainsi que compteurs, erreurs et avertissements.

La limitation de débit calcule intervalle minimal, backoff, `Retry-After`, tentatives, limite quotidienne et arrêt sur erreurs répétées. Elle n'attend jamais et n'envoie aucune requête.

## Inventaire existant

Les connecteurs Légifrance, JUDILIBRE, Code du travail numérique et pratique officielle restent sous `automation/scripts`. Ils exposent configurations par environnement, erreurs dédiées, recherche et caches locaux; certains utilisent `urllib`. Le LOT 0 ne les importe, ne les refactorise et ne les intègre pas au routeur.

## Autorisation d'un futur connecteur

Un lot séparé devra vérifier source et conditions, renseigner domaines et modes, approuver licence, choisir l'autorité par type de contenu, fixer quotas et types MIME, tester redirections et erreurs avec doubles, puis obtenir une validation explicite avant toute activation réseau. Le premier candidat prévu est la CNIL; aucune API ni URL CNIL n'est présumée ici.

## Limites

Le package fournit modèles, registre, règles pures et garde réseau seulement. Il ne crée ni données réelles, ni cache réel, ni journal réel sur disque. Aucun secret, jeton ou contenu public réel n'est inclus.
