# CFDT Nexus

CFDT Nexus est une plateforme IA destinée à assister les représentants du personnel et à améliorer le service rendu aux salariés.

Le projet vise à structurer un environnement professionnel capable d'aider les équipes syndicales à préparer leurs analyses, organiser leurs connaissances, suivre les sujets sociaux et produire des réponses plus claires, plus rapides et mieux documentées.

L'intelligence artificielle y est conçue comme un appui au travail humain : elle aide à rechercher, résumer, comparer, préparer et formaliser, mais les décisions, validations et positions syndicales restent sous responsabilité des représentants.

## Ambition

CFDT Nexus doit pouvoir évoluer vers :

- un assistant privé pour Thierry ;
- un chatbot public pour les salariés ;
- une base documentaire structurée ;
- des agents spécialisés ;
- des workflows n8n ;
- un site web ;
- une veille automatique ;
- des automatisations GitHub ;
- des tests ;
- une documentation technique durable.

## Principes

- assistance, pas substitution ;
- validation humaine obligatoire ;
- traçabilité des sources et des décisions ;
- protection des données personnelles ;
- séparation stricte entre informations publiques et internes ;
- architecture lisible et maintenable ;
- amélioration continue par versions.

## Architecture

- `.github/` : automatisations GitHub, modèles d'issues et de pull requests ;
- `docs/` : documentation produit, technique, sécurité et exploitation ;
- `agents/` : agents IA spécialisés et prompts système associés ;
- `prompts/` : prompts réutilisables pour Codex, ChatGPT et systèmes ;
- `knowledge-base/` : base documentaire organisée par nature de source ;
- `apps/` : futurs assistants et interfaces applicatives ;
- `site/` : futur site ou interface web du projet ;
- `workflows/` : workflows n8n, GitHub et veille ;
- `automation/` : scripts, jobs et traitements automatisés ;
- `tests/` : tests agents, prompts, workflows et site ;
- `config/` : configuration, environnements et schémas.

## Documentation clé

- `docs/architecture/ARCHITECTURE_GLOBALE_V1.md`
- `docs/architecture/VEILLE_SOURCES_V1.md`
- `docs/decisions/ADR-0001-architecture-initiale.md`
- `agents/README.md`
- `knowledge-base/README.md`
- `workflows/README.md`
- `tests/README.md`
