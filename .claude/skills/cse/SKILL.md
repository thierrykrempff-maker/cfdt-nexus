---
name: cse
description: Préparation, suivi et exploitation d'une réunion CSE (documents, questions, compte rendu, mémoire, relances). À utiliser pour tout le cycle CSE, de la réception de l'ordre du jour jusqu'au suivi après réunion.
status: operational
source: agents/cse/CYCLE_CSE_INTELLIGENT_V1.md
---

# Skill — CSE

Ce Skill active le prompt expert déjà rédigé dans `agents/cse/CYCLE_CSE_INTELLIGENT_V1.md`.

## Comment l'utiliser

1. Lire intégralement `agents/cse/CYCLE_CSE_INTELLIGENT_V1.md`.
2. Suivre le cycle qu'il décrit : documents → préparation → questions → réunion → réponses →
   analyse → compte rendu → mémoire → relances → réunion suivante.
3. Respecter ses limites explicites : ne jamais inventer un PV, une réponse de la direction ou
   un engagement absent des documents réellement fournis.
4. S'appuyer sur les moteurs déjà existants côté code (`CSE_KNOWLEDGE_ENGINE/`,
   `CSE_MEETING_ENGINE/`, `CSE_DECISION_TRACKER/`) pour comprendre ce qui est déjà automatisé
   — sans les modifier (voir `CLAUDE.md`, section moteur métier).

## Quand l'invoquer

Préparation d'un ordre du jour, rédaction de questions CSE/CSSCT, analyse d'un PV, suivi d'un
engagement pris par la direction, préparation de la réunion suivante.
