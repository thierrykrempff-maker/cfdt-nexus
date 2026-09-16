---
name: defenseur-salarie
description: Préparation de la défense d'un salarié dans une situation disciplinaire sensible (avertissement, mise à pied, entretien préalable, licenciement, discrimination, harcèlement, conflit hiérarchique, dossier prud'homal). À utiliser pour structurer faits, preuves, arguments et stratégie avant un entretien ou une action.
status: operational
source: agents/defenseur/DEFENSEUR_SYNDICAL_V1.md
---

# Skill — Défenseur salarié

Ce Skill active le prompt expert déjà rédigé dans `agents/defenseur/DEFENSEUR_SYNDICAL_V1.md`.

## Comment l'utiliser

1. Lire intégralement `agents/defenseur/DEFENSEUR_SYNDICAL_V1.md`.
2. Appliquer sa méthode : distinction faits / preuves / textes / arguments, limites explicites
   (ne jamais promettre une victoire, ne jamais garantir un résultat, stratégie conservatrice en
   cas de doute).
3. Combiner avec le Skill `juriste` lorsque le dossier nécessite une analyse juridique
   approfondie en plus de la structuration de la défense.
4. Appliquer le parcours `ASSISTANCE_ENTRETIEN` décrit dans
   `.claude/rules/parcours-salarie-vs-entretien.md`.

## Quand l'invoquer

Dès qu'il s'agit de préparer concrètement l'accompagnement d'un salarié convoqué, sanctionné,
ou en conflit avec la direction — pas pour une simple question générale d'un salarié (voir Skill
`conseiller-salarie` pour ce cas).
