# ANACT — LOT 0 — Audit d'architecture du connecteur officiel

## Décision

L'intégration officielle de l'ANACT doit converger vers l'architecture du connecteur France Chimie, avec INRS comme référence secondaire pour la découverte de métadonnées et CARSAT comme référence minimale pour les événements de synchronisation.

Un paquet `automation/official_knowledge/connectors/anact/` existe déjà dans le dépôt. Il contient un socle Connector Platform, des modèles, des classifications et des transports HTTP désactivés par défaut. Le présent audit ne le modifie pas et ne considère pas ces transports comme autorisés pour le futur parcours officiel. Les premiers lots officiels doivent rester entièrement hors ligne et réutiliser uniquement des métadonnées injectées.

Aucun accès réseau, scraping ou téléchargement n'a été effectué pour cet audit.

## Rôle attendu dans CFDT Nexus

Le connecteur ANACT doit fournir des métadonnées institutionnelles utiles aux représentants du personnel sur les thèmes suivants :

- conditions de travail ;
- organisation du travail ;
- prévention des risques professionnels ;
- qualité de vie et conditions de travail — QVCT ;
- transformations du travail ;
- dialogue social.

Il doit rester une source documentaire officielle et traçable. Il ne doit pas intégrer de logique de moteur expert, produire une interprétation juridique, ni stocker le contenu des publications.

## État existant constaté hors ligne

Le paquet ANACT actuel comporte notamment :

- une composition Connector Platform en `ARCHITECTURE_ONLY`, désactivée et `METADATA_ONLY` ;
- des modèles nationaux et régionaux ANACT/ARACT ;
- un catalogue de familles et de thèmes ;
- des règles de classification et une file de revue humaine ;
- des transports sitemap et page HTML avec adaptateur HTTP, tous désactivés par défaut ;
- des documents internes décrivant des LOTS 0 à 4.

Il ne suit pas encore le modèle commun le plus récent sur deux points structurants : aucune identité `stable_document_id("anact", canonical_url)` n'est utilisée dans les modèles ANACT existants, et aucune synchronisation générique `NEW`, `UPDATED`, `REMOVED`, `REDIRECTED`, `UNCHANGED` n'est reliée au Document Registry.

Les transports existants importent `urllib.request` et peuvent lire du XML ou du HTML lorsqu'ils sont explicitement activés. Ils ne doivent pas être importés ni activés dans les premiers lots du parcours officiel. Leur maintien, isolation, remplacement ou suppression devra faire l'objet d'un lot séparé et d'une décision explicite.

## Sources et domaines potentiellement admissibles

Les informations déjà présentes dans le dépôt déclarent `https://www.anact.fr` comme racine nationale et représentent certaines ARACT sous des chemins de ce même hôte.

Politique recommandée, sans validation réseau :

- candidat principal : `www.anact.fr` ;
- alias potentiel à qualifier : `anact.fr` ;
- ressources ARACT centralisées : chemins explicites sous `www.anact.fr`, après validation individuelle ;
- sous-domaines `*.anact.fr` : interdits par défaut, sans wildcard ;
- domaines régionaux distincts : interdits tant qu'ils ne sont pas validés individuellement ;
- domaines externes liés depuis une page ANACT : interdits comme sources documentaires ANACT.

La future allowlist active doit rester vide jusqu'à une revue officielle des domaines, redirections, mentions légales et droits. La présence d'une URL dans le code historique ne vaut pas validation actuelle.

## Catégories documentaires envisagées

Les catégories à préparer sans collecte sont :

- guides ;
- études ;
- fiches pratiques ;
- outils ;
- dossiers thématiques ;
- publications régionales ARACT éventuelles.

Des pages thématiques et actualités peuvent être conservées comme catégories secondaires à expertiser. Les documents PDF, médias, formulaires externes et contenus archivés ne doivent jamais être admis implicitement.

## Référence architecturale

### Référence principale : France Chimie

France Chimie constitue le meilleur modèle parce qu'il fournit la chaîne commune la plus récente et la plus stricte :

- domaines candidats déclarés mais allowlist active vide ;
- métadonnées uniquement injectées localement ;
- refus des champs de contenu, du HTML brut, des PDF et des données binaires ;
- identité produite par `stable_document_id()` ;
- intégration exclusive à l'API publique du Document Registry ;
- cinq événements de synchronisation immuables et déterministes ;
- absence totale de client réseau dans le paquet opérationnel officiel.

### Références secondaires

- INRS : normalisation, découverte bornée, taxonomie et déduplication des métadonnées injectées.
- CARSAT : moteur de synchronisation minimal, suppressions logiques, redirections et idempotence.

Le paquet ANACT historique ne doit pas être copié tel quel : ses transports sont plus avancés que le périmètre autorisé et précèdent l'adoption du Document Registry commun.

## Architecture recommandée

Le paquet cible reste :

`automation/official_knowledge/connectors/anact/`

Répartition fonctionnelle recommandée pour sa convergence future :

- `__init__.py` : API publique minimale, sans import implicite d'un transport ;
- `anact_catalog.py` : familles documentaires, thèmes, domaines candidats et allowlist inactive ;
- `anact_contract.py` : contrat documentaire, port du Document Registry et façade désactivée ;
- `anact_models.py` : identités, taxonomies nationales/régionales et métadonnées déclaratives ;
- `anact_platform.py` : composition Connector Platform unique ;
- `anact_metadata.py` : validation et canonicalisation des métadonnées injectées ;
- `anact_discovery.py` : découverte locale pure, bornée et déterministe ;
- `anact_sync.py` : synchronisation via le Document Registry ;
- tests dédiés : architecture, métadonnées, découverte, synchronisation et garde-fous réseau.

Les modules historiques de transport, sitemap, parsing HTML, robots, classification et revue ne doivent pas être supprimés ou modifiés dans le LOT 0. Ils doivent rester isolés et non importés par défaut jusqu'à leur audit de migration.

## Contrat recommandé

- `ConnectorState.ARCHITECTURE_ONLY` ;
- `enabled = false` ;
- `DocumentPolicy.METADATA_ONLY` ;
- `LicenseId.DOCUMENT_SPECIFIC` tant que les droits ne sont pas qualifiés ;
- `DEFAULT_SECURITY_POLICY` et réseau désactivé par défaut ;
- santé `DISABLED`, statistiques et métriques à zéro ;
- aucune capacité `API`, `RSS`, `SITEMAP`, `HTML`, `DISCOVERY`, `SYNC`, `DOWNLOAD`, `CACHE` ou `AUTHENTICATION` activée ;
- aucune collecte, extraction ou conservation de contenu dans les premiers lots ;
- citation, provenance et HTTPS obligatoires ;
- échec fermé pour toute opération non explicitement autorisée.

## Identité documentaire

Toute identité officielle future doit être calculée exclusivement après canonicalisation :

`stable_document_id("anact", canonical_url)`

Une référence ANACT, le nom d'une ARACT, la région et la catégorie restent des métadonnées séparées. Elles ne participent pas au `document_id`. Une redirection explicitement validée conserve l'identité antérieure lorsque la continuité documentaire est établie.

## Synchronisation attendue

Les événements publics sont exclusivement :

- `NEW` ;
- `UPDATED` ;
- `REMOVED` ;
- `REDIRECTED` ;
- `UNCHANGED`.

Ils doivent être immuables, déterministes et triés de manière stable. Les snapshots contiennent uniquement les champs du `DocumentRecord`. Une disparition produit une suppression logique unique. Une redirection exige une ancienne URL connue et une nouvelle métadonnée présente.

## Compatibilité Document Registry

Le futur connecteur doit importer uniquement depuis `automation.official_knowledge.document_registry` :

- `DocumentRecord`, `DocumentStatus`, `ChangeKind` ;
- `DocumentRegistry`, `DocumentValidator`, éventuellement `DocumentStorage` ;
- `stable_document_id()`.

Seules les opérations publiques suivantes sont autorisées :

- `register_document()` ;
- `update_document()` ;
- `mark_removed()` ;
- `find_document()` ;
- `find_by_connector()`.

Le registre est injecté explicitement. Aucun accès à `_storage`, `_validator` ou aux méthodes privées, aucun singleton et aucun cache documentaire ne sont admis.

## Risques et contrôles

### ANACT et ARACT

Le producteur, la portée nationale ou régionale et l'ARACT doivent être des métadonnées explicites. Une publication régionale ne doit pas être attribuée automatiquement à l'ANACT nationale. Une ARACT ne devient pas un connecteur distinct sans décision d'architecture.

### Domaines régionaux et liens externes

Les chemins régionaux centralisés et les domaines distincts doivent être validés séparément. Les redirections externes, raccourcisseurs, réseaux sociaux, plateformes vidéo, outils tiers et hébergeurs documentaires sont refusés.

### Doublons nationaux et régionaux

La canonicalisation précède l'identité. Les doublons exacts sont dédupliqués ; les métadonnées contradictoires échouent fermées. Les republications nationales/régionales sur des URL différentes conservent des identités distinctes, avec un lien de relation éventuel traité dans un lot ultérieur.

### Droits de réutilisation

La licence reste `DOCUMENT_SPECIFIC`. Seules les métadonnées minimales sont conservées avant revue juridique. Citation et provenance restent obligatoires.

### Archives et stabilité des URL

Une archive ne doit pas être assimilée à une suppression. Les statuts `REMOVED` et `REDIRECTED` sont produits uniquement par une observation structurée et reproductible. Les paramètres de suivi doivent être retirés sans supprimer les paramètres d'identité officiellement qualifiés.

### Confidentialité

Les tests utilisent uniquement des domaines `.example.invalid`, des références synthétiques et aucune donnée personnelle. Aucun contenu de page, document réel, secret, cookie, jeton ou chemin utilisateur ne doit être suivi.

## Séquencement recommandé

1. LOT 1 — Harmonisation du socle existant : API publique minimale, transports isolés, contrat et domaines inactifs.
2. LOT 2 — Métadonnées injectées : modèle strict, canonicalisation, identité commune et découverte locale bornée.
3. LOT 3 — Document Registry : synchronisation et cinq événements communs.
4. LOT 4 — Audit séparé des transports historiques, sans activation automatique.
5. Activation éventuelle — uniquement après revue officielle des domaines, droits, sécurité et conformité.

Conclusion : aucun composant partagé ne doit être modifié. Le socle commun actuel suffit ; l'enjeu est d'harmoniser et d'isoler le paquet ANACT existant avant toute activation officielle.
