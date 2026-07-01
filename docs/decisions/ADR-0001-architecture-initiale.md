# ADR-0001 - Architecture initiale professionnelle

## Statut

Acceptée.

## Contexte

CFDT Nexus doit évoluer vers une plateforme IA syndicale complète : assistant privé, chatbot public, base documentaire, agents, workflows n8n, site, veille automatique, automatisations GitHub, tests et documentation technique.

L'architecture initiale était utile pour démarrer, mais insuffisante pour gérer proprement les responsabilités, la sécurité, les tests et la séparation public / privé.

## Décision

Adopter une architecture modulaire avec des domaines séparés :

- `agents/`
- `prompts/`
- `knowledge-base/`
- `apps/`
- `site/`
- `workflows/`
- `automation/`
- `tests/`
- `config/`
- `docs/`

## Conséquences positives

- Projet plus lisible.
- Évolutivité sur plusieurs années.
- Meilleure séparation entre expertise, données, applications et automatisations.
- Meilleure préparation aux tests et à la sécurité.
- Documentation plus robuste.

## Points de vigilance

- Éviter de créer des dossiers inutilisés trop longtemps.
- Documenter progressivement les contenus.
- Garder la base documentaire propre et vérifiée.
- Ne pas exposer de données internes dans les zones publiques.
