---
name: paie
description: Analyse de la paie, des primes, des congés, du temps de travail et des éléments variables pour un salarié INEOS Sarralbe, selon le protocole de raisonnement en 12 étapes déjà documenté (hiérarchie des sources à 3 niveaux, niveaux de confiance, politique de refus). À utiliser pour toute question paie individuelle ou collective.
status: operational
source: agents/paie/EXPERT_PAIE_INEOS_V1.md
---

# Skill — Paie

Ce Skill active le prompt expert `agents/paie/EXPERT_PAIE_INEOS_V1.md`, rédigé à partir de la
documentation technique déjà existante dans le dépôt (`docs/architecture/REFERENTIEL_PAIE_INEOS_V1.md`,
`docs/architecture/PAYROLL_REASONING_PROTOCOL.md`, `docs/architecture/EXPERT_PAIE_CONGES_INEOS_V1*.md`).
Ce prompt ne contient aucun taux, aucune règle de calcul ni aucune donnée INEOS réelle : il
structure uniquement la méthode de raisonnement déjà spécifiée par ces documents.

## Comment l'utiliser

1. Lire intégralement `agents/paie/EXPERT_PAIE_INEOS_V1.md`.
2. Appliquer le protocole en 12 étapes, la hiérarchie des sources à 3 niveaux (opposable /
   interprétation / mémoire interne), la table des pièces à demander, les niveaux de confiance et
   la politique de refus qu'il décrit.
3. Ne jamais modifier ni exécuter `EXPERT_PAIE_V2/` ni les scripts `automation/payroll/`,
   `automation/experts/paie.py` sans demande explicite portant précisément sur ce code — ce Skill
   s'appuie sur leur documentation, pas sur leur exécution directe.
4. Ne jamais inventer un montant, un taux ou une règle de calcul absente des sources fournies.
5. Appliquer strictement `.claude/rules/confidentialite.md` : ce domaine touche à des données de
   paie potentiellement sensibles (bulletins, matricules).

## Quand l'invoquer

Toute question sur un bulletin, une prime, des heures supplémentaires, des congés payés, un
compteur de temps de travail ou un élément variable de paie pour un salarié INEOS Sarralbe.
