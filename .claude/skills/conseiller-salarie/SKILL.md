---
name: conseiller-salarie
description: Première orientation d'un salarié qui pose une question générale (parcours QUESTION_SALARIE). Destiné notamment au futur chatbot public du site. Aucun prompt expert dédié encore rédigé dans agents/, mais une application associée existe déjà côté code.
status: draft
source: aucun prompt dans agents/conseiller-salarie/ (vide) — voir apps/public-chatbot/ (squelette applicatif vide lui aussi) et README.md racine pour la définition du parcours
---

# Skill — Conseiller salarié

**Statut : draft / incomplet. Ne pas traiter comme un expert opérationnel.**
`agents/conseiller-salarie/` est vide. `apps/public-chatbot/` existe comme emplacement prévu
côté code mais ne contient qu'un `.gitkeep` — l'application n'est pas encore développée.

## Ce qui existe déjà et qu'il faut réutiliser

- Le parcours `QUESTION_SALARIE` est déjà défini dans `README.md` (racine) et repris dans
  `.claude/rules/parcours-salarie-vs-entretien.md` : réponse pédagogique, courte, prudente,
  sourcée, sans jargon.
- `agents/core/CFDT_NEXUS_CORE_PROMPT_V1.md` et `agents/core/ROUTEUR_INTELLIGENCE_V1.md`
  définissent déjà le ton général et le mécanisme de routage vers les experts pertinents — ce
  Skill doit s'appuyer dessus plutôt que redéfinir un ton propre.

## Comment l'utiliser en attendant un prompt dédié

1. Appliquer le parcours `QUESTION_SALARIE` de `.claude/rules/parcours-salarie-vs-entretien.md`.
2. Router vers le Skill de fond pertinent (`juriste`, `paie`, `protection-sociale`, etc.) pour le
   contenu réel de la réponse ; ce Skill ne fait qu'encadrer le ton et le niveau de prudence
   adaptés à un salarié non-juriste.
3. Appliquer strictement `.claude/rules/confidentialite.md` : ce parcours est le plus
   exposé au public.

## Reste à faire

- Rédiger un prompt expert dédié dans `agents/conseiller-salarie/`, précisant notamment la
  gestion des cas où la question dépasse ce qu'un chatbot public peut traiter seul (redirection
  vers Thierry ou un représentant CFDT).
- Décider si `apps/public-chatbot/` doit être développé avant que ce Skill devienne réellement
  utile en production.
- Une fois rédigé, mettre à jour ce Skill (`status: operational`).
