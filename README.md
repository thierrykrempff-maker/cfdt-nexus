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

## Assistant DS Router V1.1 / V1.2 corrective

Le prototype `automation/scripts/assistant_ds_router.py` sert de routeur central local.

Il recoit une question naturelle, detecte les domaines metier et l'intention, choisit automatiquement les moteurs locaux disponibles, puis produit une reponse Assistant DS avec reponse courte, sources locales rerankees, documents a recuperer, questions a poser, groupes d'enjeux, position de travail et points de prudence.

Commandes principales :

```powershell
python automation/scripts/assistant_ds_router.py ask --query "Un salarie pense etre mal classe car il exerce plus de responsabilites que sa fiche de poste." --source-limit 6
python automation/scripts/assistant_ds_router.py route --query "Quels documents demander pour controler les compteurs d'heures ?"
python automation/scripts/assistant_ds_router.py diagnose
python automation/scripts/assistant_ds_router.py run-scenarios
```

Documentation : `docs/architecture/ASSISTANT_DS_ROUTER_V1.md` et `docs/architecture/ASSISTANT_DS_ROUTER_V1_1.md`.

## Interface locale Nexus V2.1

`apps/nexus-local-interface/` fournit une interface locale privee pour poser une question a Nexus sans PowerShell.

Lancement :

```text
apps\nexus-local-interface\start-nexus-local.bat
```

L'interface appelle localement `assistant_ds_router.py ask --format json`, puis enrichit la reponse avec une orchestration locale Juriste + Paie. Le routeur V1.2 reste le socle d'aiguillage ; les experts ajoutent qualification, methode de controle, sources, limites et synthese prudente.

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
- `docs/architecture/ASSISTANT_DS_ROUTER_V1.md`
- `docs/architecture/VEILLE_SOURCES_V1.md`
- `docs/decisions/ADR-0001-architecture-initiale.md`
- `agents/README.md`
- `knowledge-base/README.md`
- `workflows/README.md`
- `tests/README.md`
