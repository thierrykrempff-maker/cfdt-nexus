---
name: convention-chimie
description: Expertise dédiée à la Convention collective nationale des industries chimiques (IDCC 44). Domaine non encore rédigé — ce Skill est un squelette, pas un expert opérationnel.
status: draft
source: aucune — agents/convention-chimie/ est actuellement vide
---

# Skill — Convention collective Chimie (IDCC 44)

**Statut : draft / incomplet. Ne pas traiter comme un expert opérationnel.** Aucun prompt
expert dédié n'existe aujourd'hui dans `agents/convention-chimie/` (dossier vide).
`knowledge-base/conventions/` ne contient qu'un `.gitkeep`, aucun document source.

## Ce qui existe déjà et peut servir de point de départ

- La hiérarchie des sources générale (`.claude/rules/hierarchie-sources.md`,
  `agents/core/ROUTEUR_INTELLIGENCE_V1.md`) place déjà la convention collective Chimie en
  position 2, après les accords INEOS et avant le Code du travail.
- `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md` décrit comment croiser la convention
  collective avec les autres sources, sans contenu spécifique à la Chimie.

## Ce qu'il ne faut pas faire

Ne pas inventer de disposition de la convention collective Chimie pour combler ce vide. En
l'absence de ce Skill rédigé et de documents source dans `knowledge-base/conventions/`, traiter
toute question spécifique à la CCNIC comme nécessitant une vérification directe de la source
officielle avant toute réponse ferme.

## Reste à faire

- Déposer les documents source de la CCNIC dans `knowledge-base/conventions/`.
- Rédiger un prompt expert dédié dans `agents/convention-chimie/`, sur le modèle de
  `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md`.
- Revenir mettre à jour ce Skill (`status: operational`) une fois ce travail fait.
