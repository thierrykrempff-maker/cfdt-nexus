# Veille CFDT Nexus V1

## Objectif

Ce dossier définit le socle du futur moteur de veille CFDT Nexus.

Il permet de préparer une surveillance structurée des sources juridiques, sociales, CFDT, branche Chimie, santé-sécurité et industrie, sans connecter encore de robot de collecte.

## Contenu

- `watch-channels.json` : canaux de veille prioritaires.
- `validation-rules.md` : règles de qualification, vérification et validation humaine.
- `relation-models.json` : liens prévus avec Cycle CSE, Bible Accords Sarralbe et agents spécialisés.
- `veille-item.schema.json` : schéma d'une fiche de veille.
- `jurisprudence.schema.json` : schéma d'une fiche jurisprudence.
- `bulletin.schema.json` : schéma d'un bulletin lundi / mercredi / vendredi.
- `*.example.json` : exemples fictifs sans donnée réelle.

## Sécurité

- Aucun accord INEOS réel.
- Aucun PV CSE réel.
- Aucune BDESE.
- Aucune donnée nominative.
- Aucune publication automatique.
- Aucune récupération agressive.
- Aucune API ou RSS inventé.

## Cycle cible

1. Détecter une information.
2. Identifier la source.
3. Qualifier le niveau de confiance.
4. Retrouver la source primaire si nécessaire.
5. Produire une fiche claire.
6. Transmettre aux agents utiles.
7. Préparer un bulletin.
8. Attendre validation humaine.

## Prochaines évolutions

- Ajouter un connecteur n8n après validation des sources activables.
- Ajouter un tableau de suivi des sources à vérifier.
- Ajouter des tests de conformité JSON Schema.
- Préparer une intégration privée avec le Document Intelligence Center.
- Préparer les premières fiches validées de la future Bible Accords Sarralbe.

