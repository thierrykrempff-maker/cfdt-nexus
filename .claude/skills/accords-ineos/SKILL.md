---
name: accords-ineos
description: Expertise dédiée aux accords d'entreprise INEOS Sarralbe applicables. Domaine non encore rédigé — ce Skill est un squelette, pas un expert opérationnel.
status: draft
source: aucune — agents/accords-ineos/ est actuellement vide
---

# Skill — Accords d'entreprise INEOS

**Statut : draft / incomplet. Ne pas traiter comme un expert opérationnel.** Aucun prompt
expert dédié n'existe aujourd'hui dans `agents/accords-ineos/` (dossier vide).
`knowledge-base/accords/` ne contient qu'un `.gitkeep`, aucun document source.

## Ce qui existe déjà et peut servir de point de départ

- La hiérarchie des sources générale place déjà les accords INEOS en position 1, avant la
  convention collective et le Code du travail (`.claude/rules/hierarchie-sources.md`).
- `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md` décrit le niveau de détail attendu pour
  analyser un accord d'entreprise (texte, date, article, page, extrait, champ d'application,
  salariés concernés).
- `docs/architecture/BIBLE_ACCORDS_SARRALBE_V1.md` existe dans le dépôt : à consulter avant de
  rédiger ce Skill, il peut déjà contenir une partie de la matière nécessaire.

## Ce qu'il ne faut pas faire

Ne jamais citer le contenu d'un accord INEOS de mémoire ou par déduction. Sans document source
réellement disponible, indiquer clairement que l'accord doit être vérifié directement.

## Reste à faire

- Vérifier le contenu de `docs/architecture/BIBLE_ACCORDS_SARRALBE_V1.md` et évaluer s'il peut
  servir de base à ce Skill.
- Déposer les accords eux-mêmes (ou leurs références) dans `knowledge-base/accords/`.
- Rédiger un prompt expert dédié dans `agents/accords-ineos/`.
- Revenir mettre à jour ce Skill (`status: operational`) une fois ce travail fait.
