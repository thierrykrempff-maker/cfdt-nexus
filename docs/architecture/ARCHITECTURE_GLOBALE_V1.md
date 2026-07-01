# Architecture Globale V1

## Objectif

CFDT Nexus doit rester maintenable pendant plusieurs années. L'architecture sépare donc clairement :

- les agents ;
- les prompts ;
- la base documentaire ;
- les applications ;
- les workflows ;
- les automatisations ;
- les tests ;
- la configuration ;
- la documentation.

## Principes

- Séparer les responsabilités.
- Versionner les spécifications.
- Ne pas mélanger données internes et contenus publics.
- Prévoir les tests dès le départ.
- Documenter les décisions structurantes.
- Garder une validation humaine sur les sujets sensibles.

## Vue d'ensemble

```text
agents/          Spécifications des agents IA
prompts/         Prompts réutilisables
knowledge-base/  Documents et sources classés
apps/            Futures applications
site/            Interface ou site web
workflows/       n8n, GitHub, veille
automation/      Scripts et jobs
tests/           Vérifications agents, prompts, workflows, site
config/          Environnements et schémas
docs/            Documentation durable
```

## Séparation public / privé

Le futur assistant privé peut utiliser des informations internes validées.

Le futur chatbot public doit uniquement utiliser des contenus publics ou validés pour diffusion.

Cette séparation doit être respectée dans `knowledge-base/`, `apps/` et `workflows/`.

## Agents

Les agents décrivent des responsabilités et des méthodes. Ils ne doivent pas stocker directement les sources documentaires.

Exemple :

- `agents/convention-chimie/` décrit l'agent ;
- `knowledge-base/conventions/` stocke les références conventionnelles.

## Workflows

Les workflows doivent être documentés avant automatisation, surtout lorsqu'ils manipulent des données sensibles.

Chaque workflow important doit indiquer :

- son objectif ;
- ses entrées ;
- ses sorties ;
- les validations humaines ;
- les risques ;
- les logs attendus.

## Tests

Les tests devront vérifier au minimum :

- qu'un agent ne promet pas de résultat juridique ;
- qu'un prompt respecte les règles de confidentialité ;
- qu'un workflow ne publie pas sans validation ;
- que le site reste accessible, responsive et cohérent.
