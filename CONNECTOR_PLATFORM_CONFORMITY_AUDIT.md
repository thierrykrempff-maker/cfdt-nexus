# Audit transversal de conformité des connecteurs officiels

Date de l'audit : 17 juillet 2026  
Branche : audit-connectors-platform-conformity  
Révision auditée : 5d42cbfa5a87736602e9e239914d75499b85f633 (main et origin/main avant création de la branche)

## 1. Conclusion exécutive

L'inventaire réel contient neuf unités logiques à auditer :

1. ANACT ;
2. CARSAT ;
3. CNIL ;
4. DREETS Grand Est ;
5. INRS ;
6. Légifrance PISTE ;
7. JUDILIBRE PISTE ;
8. Code du travail numérique / pratique officielle, avec deux implémentations historiques ;
9. Veille multi-source V1, qui automatise actuellement INRS, France Chimie et CNIL.

Les cinq premiers utilisent Connector Platform. Les quatre derniers sont des implémentations historiques ou transverses hors plateforme. Le fichier automation/scripts/legifrance_api.py est une interface en ligne de commande du client Légifrance et non un dixième connecteur.

Aucun P0 n'est constaté : aucun secret, corpus confidentiel, PDF officiel, cache réel ou résultat de veille n'est suivi par Git. Les risques importants sont architecturaux et opérationnels, sans preuve d'incident : transports historiques hors contrat commun, contrôles réseau incomplets, divergence entre registre désactivé et clients directement appelables, couverture de tests inégale et jetons OAuth conservés localement en clair dans un dossier ignoré.

ANACT est la référence la plus complète : transport désactivé par défaut, domaines et redirections contrôlés, réponses bornées, politique robots, requêtes conditionnelles, classification déterministe et revue humaine. Il n'est toutefois pas parfait : son ConnectorContract ne déclare que MANUAL alors que des transports SITEMAP et HTML sont implémentés hors de ce contrat.

## 2. Périmètre et méthode

L'audit est statique et dynamique, sans trafic réseau :

- inventaire des packages, scripts, registres, documentations et tests suivis ;
- lecture des contrats Connector Platform et des politiques Official Knowledge ;
- inspection des primitives réseau, configurations, caches et protections ;
- exécution hors ligne des tests existants avec fixtures synthétiques ;
- contrôle Git des espaces de données et des extensions sensibles ;
- comparaison selon une grille commune de 58 critères.

Les statuts autorisés sont exclusivement : conforme, partiellement conforme, non conforme, non applicable et non vérifiable.

Le statut synthétique d'un domaine n'est pas un score mathématique. Il retient le constat le plus significatif, en distinguant ce qui est obligatoire, recommandé ou propre au connecteur. Les critères réseau sont non applicables lorsqu'aucun transport de production n'existe. Aucun pourcentage global n'est calculé, afin de ne pas masquer un écart P1.

## 3. Référentiel réellement imposé

### Exigences de plateforme

Les exigences suivantes sont codées dans le dépôt :

- ConnectorContract est désactivé par défaut, refuse l'état ENABLED et les capacités AUTHENTICATION, SYNC et DOWNLOAD : automation/connector_platform/connector_contract.py ;
- SecurityPolicy impose réseau désactivé, lecture seule, absence de POST, suppression, authentification, secret, endpoint privé et redirection externe : automation/connector_platform/connector_security.py ;
- validate_contract refuse une politique documentaire supérieure aux droits de la licence et impose network_disabled_by_default : automation/connector_platform/connector_validation.py ;
- les licences UNKNOWN et DOCUMENT_SPECIFIC sont limitées à METADATA_ONLY et exigent une revue : automation/connector_platform/connector_license.py ;
- ConnectorRegistry refuse les identifiants en doublon : automation/connector_platform/connector_registry.py ;
- le registre Official Knowledge déclare les sources désactivées en architecture_only : automation/official_knowledge/source_registry.py.

Cette plateforme est encore un socle fail-closed de conception. Elle ne définit pas de profil opérationnel pour les API officielles nécessitant POST ou OAuth. Légifrance et JUDILIBRE ne peuvent donc pas être migrés fidèlement sans évolution préalable et explicitement validée de la plateforme.

### Bonnes pratiques recommandées

Les contrôles HTTPS, allowlist, redirections, taille, MIME, ETag, Last-Modified, 304 et robots sont recommandés pour tout transport concerné. Ils sont présents ensemble dans ANACT, mais ne sont pas universellement imposés par un validateur commun.

La classification déterministe, la revue humaine et le catalogue documentaire sont recommandés lorsque le connecteur découvre ou classe des URL. Ils ne sont pas exigés d'un squelette architecture_only sans transport.

### Différences légitimes

- Légifrance et JUDILIBRE utilisent des API officielles authentifiées ; POST et OAuth sont inhérents à ces API.
- ANACT utilise un sitemap et des pages HTML ciblées.
- CARSAT, CNIL, DREETS et INRS restent des contrats documentaires sans transport.
- CDTN utilise un endpoint public de prérecherche.
- La veille V1 est un outil transversal de surveillance de pages, pas un connecteur documentaire Connector Platform.

## 4. Grille de conformité — 58 critères

### Architecture (A01 à A08)

| ID | Critère | Nature |
|---|---|---|
| A01 | Structure et responsabilités identifiables | exigence de maintenabilité |
| A02 | Contrat explicite | exigence plateforme pour connecteur natif |
| A03 | Modèles typés | exigence plateforme pour connecteur natif |
| A04 | Façade ou point d'entrée identifiable | exigence |
| A05 | Catalogue ou déclaration des sources | exigence Official Knowledge |
| A06 | Enregistrement Connector Platform | exigence pour connecteur natif |
| A07 | Séparation transport, parsing, modèles et logique | bonne pratique |
| A08 | Absence de couplage injustifié à un moteur d'expertise | exigence |

### Activation et politique (P01 à P04)

| ID | Critère |
|---|---|
| P01 | Désactivation par défaut |
| P02 | État architecture_only cohérent lorsqu'applicable |
| P03 | Politique documentaire et licence explicites, fail-closed |
| P04 | Cohérence documentation, capacités déclarées et comportement |

### Réseau et transport (N01 à N13)

| ID | Critère |
|---|---|
| N01 | HTTPS uniquement |
| N02 | Domaines autorisés explicitement |
| N03 | Validation des redirections |
| N04 | Refus des redirections externes |
| N05 | Timeout borné |
| N06 | Taille de réponse bornée |
| N07 | Statuts HTTP traités |
| N08 | MIME contrôlé |
| N09 | ETag conservé et réutilisé |
| N10 | Last-Modified conservé et réutilisé |
| N11 | 304 Not Modified traité |
| N12 | Politique robots lorsqu'applicable |
| N13 | Découverte bornée, sans crawl incontrôlé |

### Métadonnées et provenance (M01 à M08)

| ID | Critère |
|---|---|
| M01 | URL source |
| M02 | URL finale ou canonique lorsqu'elle existe |
| M03 | Organisme producteur et type de source |
| M04 | Dates de collecte, publication ou mise à jour disponibles |
| M05 | Identifiant ou empreinte stable |
| M06 | Version du parseur ou classificateur |
| M07 | Confiance et état de validation |
| M08 | Traçabilité de la découverte |

### Classification et validation (C01 à C05)

| ID | Critère |
|---|---|
| C01 | Classification déterministe |
| C02 | Ambiguïtés explicites |
| C03 | Revue humaine possible |
| C04 | Absence de validation implicite dangereuse |
| C05 | Décision et provenance conservées |

### Confidentialité et sécurité (S01 à S07)

| ID | Critère |
|---|---|
| S01 | Aucun secret suivi |
| S02 | Aucun jeton ou identifiant réel dans les fixtures |
| S03 | Aucune donnée personnelle ou confidentielle réelle suivie |
| S04 | Aucun contenu complet conservé sans justification |
| S05 | Aucun cookie persistant inutile |
| S06 | Journaux, caches et sorties assainis et ignorés |
| S07 | Chemins locaux et temporaires contrôlés |

### Tests (T01 à T07)

| ID | Critère |
|---|---|
| T01 | Tests propres au connecteur |
| T02 | Tests hors ligne et fixtures synthétiques |
| T03 | Déterminisme |
| T04 | Erreurs réseau et parsing invalide |
| T05 | Redirections et limites de taille |
| T06 | Aucun service réel pendant les tests |
| T07 | Compatibilité Connector Platform et Official Knowledge |

### Documentation (D01 à D06)

| ID | Critère |
|---|---|
| D01 | Architecture documentée |
| D02 | Sources officielles documentées |
| D03 | Limites et exclusions documentées |
| D04 | Mise à jour et comportement réseau documentés |
| D05 | Données conservées documentées |
| D06 | Lot suivant proposé lorsqu'il existe |

La matrice exhaustive par critère est dans CONNECTOR_PLATFORM_CONFORMITY_MATRIX.json.

## 5. Synthèse par connecteur

| Connecteur | Architecture | Activation | Réseau | Métadonnées | Classification | Sécurité | Tests | Documentation | Conclusion |
|---|---|---|---|---|---|---|---|---|---|
| ANACT | conforme | partiellement conforme | conforme | conforme | conforme | conforme | conforme, 174 | conforme | référence récente ; capacité plateforme incomplète |
| CARSAT | conforme | conforme | non applicable | partiellement conforme | non applicable | conforme | conforme, 50 | partiellement conforme | squelette sain, sans transport |
| CNIL | conforme | conforme | non applicable | partiellement conforme | partiellement conforme | conforme | conforme, 40 | conforme | migration plateforme saine, revue juridique maintenue |
| DREETS Grand Est | conforme | conforme | non applicable | partiellement conforme | partiellement conforme | conforme | conforme, 62 | conforme | architecture fail-closed cohérente |
| INRS | conforme | conforme | non applicable | partiellement conforme | non applicable | conforme | conforme, 50 | partiellement conforme | squelette sain, sans transport |
| Légifrance PISTE | non conforme | partiellement conforme | non conforme | partiellement conforme | non applicable | partiellement conforme | partiellement conforme, 5 tests d'intégration routeur | partiellement conforme | client opérationnel historique hors plateforme |
| JUDILIBRE PISTE | non conforme | partiellement conforme | non conforme | partiellement conforme | non applicable | partiellement conforme | non conforme, aucun test dédié | partiellement conforme | client opérationnel historique hors plateforme |
| CDTN / pratique officielle | partiellement conforme | non conforme | partiellement conforme | partiellement conforme | non applicable | partiellement conforme | partiellement conforme, 8 tests sur l'implémentation durcie | conforme | deux implémentations divergentes hors plateforme |
| Veille multi-source V1 | non conforme | non conforme | non conforme | partiellement conforme | partiellement conforme | partiellement conforme | non conforme, aucun test dédié | conforme | outil réseau transversal actif à l'invocation, hors plateforme |

## 6. Constats détaillés et preuves

### ANACT

- Contrat natif, registre local, sécurité commune et état architecture_only : automation/official_knowledge/connectors/anact/anact_platform.py.
- Transport sitemap explicitement désactivé, redirections restreintes, GET HTTPS, timeout et lecture bornée : automation/official_knowledge/connectors/anact/anact_sitemap_transport.py.
- Contrôles URL et robots : automation/official_knowledge/connectors/anact/anact_robots_policy.py.
- Métadonnées de page bornées, ETag, Last-Modified, 304, MIME et canonical : automation/official_knowledge/connectors/anact/anact_page_metadata_transport.py et anact_page_metadata_parser.py.
- Classification déterministe et file de revue : anact_url_classifier.py et anact_review_queue.py.
- Écart : ANACT_CAPABILITIES ne déclare que MANUAL dans anact_platform.py alors que le contrat historique annonce sitemap_transport_implemented et page_metadata_transport_implemented dans anact_contract.py.

### CARSAT

- Contrat et fail-closed : carsat_contract.py et carsat_platform.py.
- Identités déterministes, sérialisation, empreinte, citation et provenance : carsat_models.py.
- Accès futurs non opérationnels : carsat_catalog.py.
- Absence légitime de critères réseau et de classification d'URL ; les dates de collecte, la version d'un futur parseur et l'état de revue d'une ressource réelle ne sont pas encore définis.

### CNIL

- Migration Connector Platform : cnil_platform.py et MIGRATION_CONNECTOR_PLATFORM_LOT_2.md.
- CC_BY_ND avec METADATA_ONLY, état désactivé : cnil_platform.py.
- Ressource, URI canonique, dates, empreinte, citation et provenance : cnil_models.py.
- Découverte et récupération bloquées : cnil_connector.py et cnil_sync.py.
- Les statuts de licence pending protègent contre une validation implicite ; il n'existe pas encore de file de décision ou d'historique de revue.

### DREETS Grand Est

- Migration Connector Platform : dreets_platform.py et MIGRATION_CONNECTOR_PLATFORM_LOT_1.md.
- Licence UNKNOWN limitée à METADATA_ONLY et provenance obligatoire : dreets_models.py.
- Accès officiels uniquement étudiés et synchronisation désactivée : dreets_access_review.py et dreets_sync.py.
- Classificateur déterministe limité : dreets_policy.py.
- Aucun transport n'est implémenté ; les critères HTTP sont donc non applicables.

### INRS

- Contrat, registre et fail-closed : inrs_contract.py et inrs_platform.py.
- Familles, identités, empreinte, citation et provenance : inrs_models.py.
- Possibilités d'accès déclaratives et non opérationnelles : inrs_catalog.py.
- Aucun transport ni classificateur d'URL ; ces critères sont non applicables.

### Légifrance PISTE

- Client OAuth et API opérationnel avec POST : automation/scripts/legifrance_connector.py.
- Les URL token, base API et endpoints peuvent être remplacées par environnement ; endpoint_url accepte aussi une URL absolue HTTP ou HTTPS. Il n'existe pas d'allowlist ni de validation de la destination finale après redirection.
- Timeout présent, mais response.read est non borné ; MIME, ETag, Last-Modified et 304 ne sont pas gérés.
- Jeton et réponses sont écrits en JSON privé sous local-index/legifrance, dossier ignoré par Git. L'absence de suivi est conforme, mais le jeton reste en clair sur le poste.
- Le registre Official Knowledge déclare pourtant legifrance désactivé en architecture_only. Le script reste directement appelable lorsqu'il reçoit des identifiants.
- Les cinq tests test_legifrance_fallback.py testent le comportement de repli du routeur avec un faux connecteur, pas le transport OAuth/API lui-même.

### JUDILIBRE PISTE

- Client OAuth et API opérationnel : automation/scripts/judilibre_connector.py.
- Même classe d'écarts que Légifrance : endpoints configurables sans allowlist, redirections non validées, réponses non bornées, pas de validation MIME ni de requêtes conditionnelles.
- Cache privé ignoré, incluant un jeton OAuth en clair.
- Le registre le déclare désactivé, mais le client est appelable avec ses identifiants.
- Aucun fichier de test dédié n'a été détecté.

### Code du travail numérique / pratique officielle

- Ancien client : automation/scripts/cdtn_connector.py.
- Implémentation durcie : automation/scripts/pratique_officielle_connector.py.
- La version durcie impose code.travail.gouv.fr en HTTPS, permet seulement des hôtes locaux de test sur opt-in, borne la réponse et teste erreurs, timeout et cache.
- La redirection finale n'est pas contrôlée explicitement par un handler ; le Content-Type n'est pas exigé avant le décodage JSON ; ETag, Last-Modified et 304 sont absents.
- L'ancien client reste moins strict : base configurable, réponse non bornée et absence d'allowlist. La coexistence rend la politique effective dépendante du point d'entrée.
- Huit tests dédiés couvrent seulement pratique_officielle_connector.py. Aucun test dédié de cdtn_connector.py n'a été détecté.
- Documentation : docs/architecture/PRATIQUE_OFFICIELLE_V1.md et CDTN_PRATIQUE_OFFICIELLE_V1.md.

### Veille multi-source V1

- Sources et activation : watch/connectors/sources-status.json.
- Trois sources sont enabled=true et status=actif : INRS, France Chimie et CNIL. Cette configuration est distincte du registre Official Knowledge, qui les déclare désactivées.
- fetch-watch.js utilise fetch, un timeout et une limite de huit éléments par source, mais lit response.text sans limite d'octets, suit les redirections par défaut et ne revalide ni schéma, ni hôte final, ni robots.
- Les résultats sont limités aux titres, dates et liens et écrits dans local-index/watch-connectors, ignoré par Git.
- Aucun test dédié n'a été trouvé. La syntaxe JavaScript a été validée avec le runtime Node fourni, sans lancer le script.

## 7. Fonctionnalités avancées

| Fonction | ANACT | CARSAT | CNIL | DREETS | INRS | Légifrance | JUDILIBRE | CDTN | Veille V1 |
|---|---|---|---|---|---|---|---|---|---|
| Sitemap | requise et présente | non pertinente | optionnelle absente | optionnelle absente | à étudier | non pertinente | non pertinente | non pertinente | absente optionnelle |
| Classification URL | requise et présente | non pertinente | optionnelle absente | classifieur métier déclaratif seulement | non pertinente | non pertinente | non pertinente | non pertinente | heuristique partielle |
| Lecture métadonnées | présente | modèle préparé | modèle préparé | modèle préparé | modèle préparé | présente via API | présente via API | présente via API | présente partiellement |
| Catalogue documentaire | LOT 5 non présent dans main ; optionnel | catalogue déclaratif | catalogue déclaratif | catalogue déclaratif | catalogue déclaratif | absent optionnel | absent optionnel | absent optionnel | absent optionnel |
| Déduplication | empreintes candidates | empreinte identité | empreinte ressource | empreinte ressource | empreinte identité | cache par clé | cache par clé | cache par clé | titre + URL |
| Versionnement | fraîcheur HTTP et cycle | métadonnées préparées | schema_version | validité/révision déclaratives | version_note | dates légales/API | métadonnées API | date source | absent optionnel |
| Recherche locale | non requise à ce stade | non pertinente | non pertinente | non pertinente | non pertinente | recherche API, pas locale | recherche API, pas locale | recherche API, pas locale | non pertinente |
| Export interne | modèles internes | modèles internes | modèles internes | modèles internes | modèles internes | dictionnaires | dictionnaires | dictionnaires | JSON local temporaire |

## 8. Confidentialité et sécurité

Contrôles réalisés :

- git ls-files OFFICIAL_KNOWLEDGE_DATA : aucun résultat ;
- git ls-files PROTECTION_SOCIALE_ENGINE : aucun résultat ;
- git ls-files CCSEMEMORYENGINE : aucun résultat ;
- git ls-files local-index : aucun résultat ;
- aucun PDF, document Office, ZIP, fichier private.json, .env ou cache OAuth suivi dans les périmètres connecteurs ;
- aucune valeur de secret codée en dur détectée dans les sources de production auditées ;
- les seules pages HTML suivies sont les interfaces applicatives du dépôt, hors périmètre des connecteurs ;
- .gitignore protège local-index et les trois espaces de données.

Risques résiduels :

- Légifrance et JUDILIBRE stockent les jetons OAuth en clair dans des fichiers locaux ignorés ; aucune fuite Git n'est observée, mais les droits de fichier, le chiffrement et la purge ne sont pas explicités.
- Les caches historiques peuvent contenir des réponses officielles complètes sans politique Connector Platform associée.
- La veille V1 conserve uniquement des métadonnées extraites, mais charge le HTML complet en mémoire sans borne.

Aucune sonde réseau réelle n'a été exécutée pendant l'audit.

## 9. Résultats de tests

| Suite | Résultat | Nature |
|---|---:|---|
| ANACT | 174/174 | unittest, adaptateurs synthétiques |
| CARSAT | 50/50 | unittest, données synthétiques |
| CNIL | 40/40 | unittest, données synthétiques |
| DREETS Grand Est | 62/62 | unittest, données synthétiques |
| INRS | 50/50 | unittest, données synthétiques |
| Connector Platform | 118/118 | unittest |
| Official Knowledge complet | 452/452 | unittest ; inclut les cinq connecteurs natifs |
| Tests généraux isolés | 324/324 | lanceur isolé validé |
| Test général sensible à l'état | 1/1 | exécution isolée séparée |
| Total tests généraux | 325/325 | sans service réel |
| Syntaxe veille V1 | valide | node --check, aucun fetch exécuté |

Les tests de pratique officielle (8) et de repli Légifrance (5) sont inclus dans les 324 tests généraux. Aucun test dédié JUDILIBRE, ancien CDTN ou veille V1 n'a été détecté. L'absence initiale de node dans le PATH a été contournée par le runtime local fourni ; aucun paquet n'a été installé.

## 10. Écarts priorisés

### P0

Aucun.

### P1

1. **P1-01 — Modèle opérationnel manquant dans Connector Platform.** Le contrat actuel interdit toute activation, authentification, synchronisation et téléchargement. Il ne peut pas représenter fidèlement Légifrance ou JUDILIBRE. Définir un profil opérationnel versionné avant toute migration, sans affaiblir le profil fail-closed.
2. **P1-02 — Connecteurs historiques hors plateforme.** Légifrance, JUDILIBRE et les deux clients CDTN sont appelables indépendamment alors que le registre Official Knowledge les décrit désactivés en architecture_only. Unifier état, kill switch et validation.
3. **P1-03 — Contrôles réseau historiques incomplets.** Ajouter, via une future couche commune, allowlists, HTTPS strict, validation de chaque redirection, taille maximale, MIME et requêtes conditionnelles lorsque l'API les supporte.
4. **P1-04 — Veille multi-source hors plateforme.** Trois sources sont activées dans sources-status.json ; le transport ne borne pas le corps et ne contrôle pas la destination finale ni robots. Suspendre son statut actif ou le migrer avant usage régulier.
5. **P1-05 — Couverture de tests insuffisante.** Aucun test dédié JUDILIBRE, ancien CDTN ou veille V1 ; les tests Légifrance ciblent le fallback du routeur et non le client.
6. **P1-06 — Deux implémentations CDTN divergentes.** Désigner une façade canonique et déprécier l'autre après tests de compatibilité.
7. **P1-07 — Jetons OAuth locaux en clair.** Définir permissions, durée, purge et stockage sûr ; ne jamais déplacer ces fichiers hors des dossiers ignorés.

### P2

1. **P2-01 — Capacités ANACT incomplètes.** Déclarer de façon cohérente SITEMAP et HTML dans un futur contrat opérationnel ; ne pas activer le connecteur à l'occasion de cette correction.
2. **P2-02 — Registres locaux isolés.** Chaque connecteur natif construit un ConnectorRegistry distinct. Prévoir une composition globale contrôlée pour détecter les doublons inter-connecteurs.
3. **P2-03 — Métadonnées hétérogènes.** Harmoniser URL source/finale, collected_at, parser_version, confidence, validation_status et discovery_provenance.
4. **P2-04 — Historique de revue.** CNIL et DREETS portent des statuts pending, mais pas de journal minimal de décision comparable à ANACT.
5. **P2-05 — Documentation historique dispersée.** Créer des dossiers d'architecture dédiés Légifrance/JUDILIBRE et expliciter cache, rétention, licence, sécurité et tests.

### P3

1. Harmoniser les noms de constantes d'erreur réseau et les sérialisations.
2. Ajouter une table de capacités et une fiche de maturité générée pour chaque connecteur.
3. Uniformiser les messages et diagnostics sans exposer endpoint sensible, requête ou contenu.

## 11. Ordre recommandé des corrections

1. Concevoir dans Connector Platform deux profils distincts : architecture fail-closed et transport officiel opérationnel, avec règles de sécurité non contournables.
2. Désactiver ou encapsuler la veille V1 avant toute exécution planifiée.
3. Ajouter des tests de transport synthétiques pour JUDILIBRE, Légifrance, ancien CDTN et veille V1.
4. Migrer d'abord CDTN vers une façade unique, car il n'exige pas OAuth.
5. Migrer Légifrance et JUDILIBRE après validation du profil OAuth/POST, du stockage de jeton et des politiques de cache.
6. Aligner les capacités ANACT et introduire un registre global composé.
7. Harmoniser les métadonnées, la revue humaine et la documentation.

## 12. Modèle minimal pour les futurs connecteurs

Un futur connecteur devrait fournir au minimum :

- un package dédié avec contract, platform, models, catalog, transport et parser séparés lorsque ces composants existent ;
- un ConnectorContract versionné, une entrée Official Knowledge cohérente et un registre global ;
- enabled=false et architecture_only tant que l'accès n'est pas validé ;
- une politique licence/document fail-closed ;
- un SecurityPolicy explicite et, pour tout transport, HTTPS, allowlist, redirections revalidées, timeout, taille, MIME et limites de découverte ;
- une identité documentaire avec source_url, final_url, canonical_url, publisher, source_type, collected_at, published_at, updated_at, fingerprint, schema/parser/classifier version, confidence, validation status et discovery provenance ;
- une classification déterministe avec ambiguïté explicite et revue humaine lorsqu'elle est pertinente ;
- des sorties locales dans un espace ignoré, sans secret ni contenu complet par défaut ;
- des tests entièrement synthétiques couvrant désactivation, contrat, validation, erreurs, redirects, taille, parsing et déterminisme ;
- une documentation explicitant sources, licence, limites, réseau, données conservées et étapes suivantes.

## 13. Intégrité de l'audit

Les seuls fichiers créés par cet audit sont :

- CONNECTOR_PLATFORM_CONFORMITY_AUDIT.md ;
- CONNECTOR_PLATFORM_CONFORMITY_MATRIX.json.

Aucun connecteur, registre, moteur, routeur, test existant ou configuration n'a été modifié. main est restée sur 5d42cbfa5a87736602e9e239914d75499b85f633 et n'a reçu ni commit, ni fusion, ni push.
