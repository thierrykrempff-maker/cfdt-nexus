# Changelog

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
