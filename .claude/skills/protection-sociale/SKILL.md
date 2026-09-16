---
name: protection-sociale
description: Analyse des sujets de protection sociale, mutuelle, prévoyance et retraite pour un salarié INEOS Sarralbe. Documentation technique disponible mais aucun dossier agents/ ni prompt expert dédié n'existe encore pour ce domaine.
status: draft
source: docs/architecture/PROTECTION_SOCIALE_ENGINE_LOT_0.md et LOT_1A à LOT_1D, moteur PROTECTION_SOCIALE_ENGINE/ (code, à ne pas modifier depuis ce Skill), RETIREMENT_PENIBILITY_ENGINE/ pour le volet pénibilité/retraite
---

# Skill — Protection sociale

**Statut : draft / incomplet. Ne pas traiter comme un expert opérationnel.** Il n'existe même
pas de dossier `agents/protection-sociale/` dans le dépôt actuel — ce domaine n'a pas encore de
slot dans `agents/`, contrairement aux autres experts listés dans `agents/README.md`.

## Ce qui existe déjà et qu'il faut réutiliser

- `docs/architecture/PROTECTION_SOCIALE_ENGINE_LOT_0.md`,
  `PROTECTION_SOCIALE_ENGINE_LOT_1A.md` à `LOT_1D.md` : spécifications du moteur.
- Moteur applicatif `PROTECTION_SOCIALE_ENGINE/` (code Python).
- `RETIREMENT_PENIBILITY_ENGINE/` et les documents `RETIREMENT_*` à la racine du dépôt pour le
  volet retraite et pénibilité, connexe à la protection sociale.

## Comment l'utiliser en attendant un prompt dédié

1. Lire les documents ci-dessus avant de répondre à une question de protection sociale.
2. Appliquer la méthode générale de `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md` pour la
   hiérarchie des sources et le format de réponse, en l'adaptant : ce domaine touche souvent à
   des données médicales ou personnelles sensibles — appliquer strictement
   `.claude/rules/confidentialite.md`.
3. Ne jamais modifier `PROTECTION_SOCIALE_ENGINE/` ni `RETIREMENT_PENIBILITY_ENGINE/` sans
   demande explicite portant précisément sur ce code.
4. Ne jamais inventer un droit, un montant ou une garantie de mutuelle/prévoyance absente de
   ces documents.

## Reste à faire

- Créer `agents/protection-sociale/` et y rédiger un prompt expert dédié.
- Clarifier si la retraite/pénibilité doit être un Skill séparé ou une section de ce Skill,
  selon le volume réel de matière disponible.
- Une fois rédigé, mettre à jour ce Skill (`status: operational`).
