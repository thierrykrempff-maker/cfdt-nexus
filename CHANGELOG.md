# Changelog

## Assistant DS Router V1.2 corrective

- Correction du routage des questions de reunion CSE pendant repos 5x8 : le cas est traite comme articulation mandat CSE / temps de travail, sans declencher une preparation de projet collectif.
- Renforcement du reranking pour ecarter les sources restauration, interessement, harmonisation remuneration et forfait jours lorsqu'elles sont hors population ou hors sujet.
- Ajout d'une reponse courte avant la methode de controle dans `ask`, avec prudence explicite lorsque les sources ne permettent pas de conclure.
- Repriorisation des constats, documents et questions metier pour les sujets multi-domaines astreinte + repos + paie.
- Ajout de 3 scenarios `ask` V1.2 exacts : `classification`, reunion CSE pendant repos 5x8, astreinte + repos + paie.

## Assistant DS Router V1.1

- Ajout d'une couche de reranking contextuel dans `assistant_ds_router.py` sans modifier le scoring de `agreements_bible.py`.
- Limitation et diversification des sources principales avec option CLI `--source-limit`.
- Ajout d'une deduplication semantique legere pour constats, documents, questions et avertissements.
- Correction de `working_position`, maintenant construite explicitement par domaine au lieu de reprendre le premier document/point.
- Ajout de `issue_groups` pour les demandes multi-domaines, notamment astreinte + repos + paie.
- Separation des garde-fous generiques dans un bloc court de prudence.
- Extension de `run-scenarios` avec 8 validations `ask` V1.1 couvrant les 3 cas reels et 5 tests supplementaires.
- Documentation V1.1 ajoutee dans `docs/architecture/ASSISTANT_DS_ROUTER_V1_1.md`.

## Assistant DS Router V1

- Ajout du routeur central `automation/scripts/assistant_ds_router.py`.
- Classification des demandes par domaines metier et intentions utilisateur.
- Orchestration locale de `agreements_bible.py` et `nexus_bible_bridge.py` sans reecrire les moteurs specialistes.
- Ajout des commandes `ask`, `route`, `diagnose` et `run-scenarios` avec sorties `text` et `json`.
- Ajout de 25 scenarios de routage, dont les 20 cas obligatoires et 5 cas multi-domaines.
- Documentation de l'architecture dans `docs/architecture/ASSISTANT_DS_ROUTER_V1.md`.
- Les modules non connectes restent signales explicitement : Document Intelligence, controle paie dedie et veille juridique.

## Profil CSSCT sécurité process maintenance

- Ajout du profil métier `CSSCT / sécurité process / maintenance`.
- Détection prioritaire des sujets DUERP, RPS, PROVOX, SNCC, analyseurs, climatisation, panne, pièces critiques et plan de contingence.
- Filtrage des sources rémunération/paie/NAO/CET lorsque le sujet est CSSCT ou sécurité process.
- Adaptation de la fiche CSE avec risques techniques, sécurité process, continuité d'exploitation, charge mentale, RPS, maintenance préventive, pièces critiques et documents techniques à demander.
- Ajout du scénario métier PROVOX / DUERP / RPS.

## Analyse comparative locale CSE V1

- Transformation de `analyze-cse` en fiche de preparation syndicale detaillee.
- Ajout des sections situation actuelle, comparaison avant/apres, consequences salaries, beneficiaire probable, risques, informations manquantes, documents a demander, questions CSE, relances, point CSSCT, position CFDT et synthese elu.
- Ajout du scenario prime de nuit / dimanche / jour ferie.
- Renforcement des tests scenarios pour verifier les rubriques metier de la fiche CSE.
- Documentation de la commande `--format detailed`.

## Connexion Bible Accords au Cycle CSE et Document Intelligence

- Ajout du pont local `automation/scripts/nexus_bible_bridge.py`.
- Connexion reelle au moteur de recherche et de scoring `agreements_bible.py`.
- Ajout des commandes `diagnose`, `analyze-cse`, `analyze-document` et `run-scenarios`.
- Ajout de rapports locaux prives sous `local-index/agreements/integration/`.
- Documentation du Document Intelligence Center, du Cycle CSE, des contrats d'integration et de l'architecture.
- Extension du cockpit avec l'indicateur de pont local Bible Accords / DIC / Cycle CSE sans contenu prive.

## Profil droit syndical Bible Accords

- Ajout du profil `relations collectives / droit syndical`.
- Ajout de synonymes pour heures de délégation, crédit d'heures, mandat, CSE, RP, délégué syndical et moyens syndicaux.
- Bonus de titre pour CSE, droit syndical, RP et dialogue social.
- Pénalisation des documents paie, CET, forfait jours et rémunération lorsque la requête porte sur le droit syndical.

## Amélioration pertinence recherche Bible Accords

- Ajout d'un scoring explicable par score lexical, expression exacte, proximité, synonymes métier, thème, type et titre.
- Ajout d'une pénalisation des documents NAO/salariaux lorsque la requête ne porte pas sur la rémunération.
- Ajout de la commande `search-debug` pour auditer les raisons d'un classement localement.
- Amélioration du classement de la requête `repos entre deux postes` vers les documents 5x8, horaires, temps de travail et travail posté.

## OCR local Bible Accords Sarralbe V1

- Ajout du diagnostic OCR local pour Tesseract, Ghostscript, OCRmyPDF, `pdftoppm` et langue `fra`.
- Ajout de la commande `ocr-run` avec `--limit`, `--document-id`, reprise après interruption et copie de travail locale.
- Ajout du dossier privé cible `local-index/agreements/ocr/` sans contenu versionné.
- Ajout du statut `OCR_LOW_CONFIDENCE` et des avertissements de source OCR faible.
- Extension minimale du cockpit avec indicateurs de couverture documentaire sans contenu privé.
- Documentation Windows et sécurité OCR ajoutées.

## Correctif classification OCR Bible Accords

- Reclassement en `OCR_REQUIRED` des PDF avec pages détectées mais sans texte extrait.
- Ajout des champs `extraction_note` et `error_message` dans les diagnostics locaux.
- Ajout de la commande `diagnose` pour distinguer extractions OK, OCR requis, erreurs techniques et formats non supportés.
- Documentation mise à jour sans ajout de document réel ni d'inventaire privé.

## Bible Accords Sarralbe V1

- Ajout du pipeline local sécurisé d'inventaire, extraction, indexation et recherche des accords Sarralbe.
- Ajout des schémas d'index et de résultat de recherche sourcé.
- Ajout des contrats d'intégration avec DIC, Cycle CSE et agents CFDT Nexus.
- Extension légère du cockpit dans la bibliothèque avec l'entrée `Bible Accords Sarralbe`.
- Les documents réels, textes extraits, inventaires, résultats et chemins privés restent dans `local-index/` et ne sont pas versionnés.

## Socle sources juridiques CFDT et veille V1

- Ajout du registre des sources juridiques, institutionnelles, CFDT, branche Chimie et veille spécialisée.
- Ajout de la hiérarchie de confiance des sources A / B / C / D.
- Ajout des 13 canaux de veille V1.
- Ajout des schémas de fiche de veille, fiche jurisprudence et bulletin.
- Ajout de l'agent Veille Juridique et Sociale V1.
- Extension du cockpit avec la vue statique `Veille & Sources`.
- Aucune donnée confidentielle, aucun accord réel et aucun document privé n'ont été ajoutés.

## Filtre pertinence Sarralbe V1

- Ajout du filtre local déterministe de pertinence Sarralbe.
- Ajout des règles de scoring explicables sur 100.
- Ajout de la CNIL comme source institutionnelle prioritaire.
- Ajout du canal de veille données personnelles / CNIL.
- Extension légère de la vue `Veille & Sources` avec filtres, score, justification et action suggérée.
- Les rapports réels restent dans `local-index/` et ne sont pas versionnés.

## Cycle CSE Intelligent et Analyse Financiere Sarralbe V1

- Ajout des methodologies Cycle CSE Intelligent V1 et Analyse Financiere Sarralbe V1.
- Ajout des agents CSE et Analyse Financiere Sarralbe.
- Ajout du prototype statique `apps/cycle-cse-intelligent/`.
- Ajout du document d'integration architecture V1.
- Les donnees de demonstration restent fictives et sans donnee nominative.

## Architecture professionnelle CFDT Nexus

- Ajout de l'architecture cible pour un projet durable.
- Ajout des zones applications, base documentaire, automatisation, tests et configuration.
- Ajout des documents d'architecture globale et de décision initiale.
- Ajout des README de cadrage pour les principaux domaines du dépôt.

## Initial architecture

- Création de l'architecture professionnelle du projet CFDT Nexus.
- Ajout des dossiers de documentation, agents, prompts, workflows et site.
- Ajout des documents racine de pilotage du projet.
