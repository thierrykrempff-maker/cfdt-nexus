---
name: cssct
description: Santé, sécurité et conditions de travail. Domaine explicitement désigné comme futur par Thierry — non encore rédigé, ni prompt expert ni documentation technique dédiée.
status: draft
source: aucune — agents/cssct/ est actuellement vide, aucun document dédié identifié dans docs/architecture/
---

# Skill — CSSCT

**Statut : draft / incomplet. Ne pas traiter comme un expert opérationnel.** `agents/cssct/`
est vide. Contrairement à Paie et Protection sociale, aucune documentation technique
substantielle déjà rédigée spécifiquement pour ce domaine n'a été identifiée dans
`docs/architecture/`.

## Ce qui existe déjà et qui touche à ce sujet, sans lui être dédié

- `agents/cse/CYCLE_CSE_INTELLIGENT_V1.md` couvre le cycle CSE en général et peut s'appliquer
  aux réunions CSSCT, mais ne traite pas spécifiquement des enjeux santé-sécurité.
- `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md` liste la santé et la sécurité au travail
  parmi ses domaines de compétence, mais sans méthode CSSCT dédiée.
- `agents/veille/VEILLE_JURIDIQUE_SOCIALE_V1.md` couvre la veille santé-sécurité.

## Ce qu'il ne faut pas faire

Ne pas inventer de procédure ou de méthode CSSCT spécifique pour combler ce vide. Pour une
question CSSCT, s'appuyer sur le Skill `juriste` et le Skill `cse`, en signalant explicitement
qu'aucune méthode CSSCT dédiée n'existe encore.

## Reste à faire

- Rédiger un prompt expert dédié dans `agents/cssct/`, sur le modèle de
  `agents/cse/CYCLE_CSE_INTELLIGENT_V1.md`.
- Une fois rédigé, mettre à jour ce Skill (`status: operational`).
