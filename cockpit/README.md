# Cockpit CFDT Nexus V1

## Objectif

Le Cockpit CFDT Nexus V1 est une première interface privée de pilotage pour Thierry Krempff, délégué syndical CFDT Chimie Énergie sur le site INEOS Sarralbe.

Cette version est volontairement statique, sans backend et sans connexion réelle. Elle sert à valider l'organisation fonctionnelle avant de connecter progressivement n8n, GitHub, Google Analytics, Search Console, Hostinger et un assistant GPT.

## Structure des fichiers

- `index.html` : structure de l'interface et sections du tableau de bord.
- `styles.css` : design responsive inspiré des tableaux de bord modernes.
- `app.js` : interactions locales et données de démonstration.
- `README.md` : documentation du cockpit.

## Fonctionnalités V1

- Accueil avec résumé du jour et actions rapides.
- Suivi de dossiers salariés avec création locale de démonstration.
- Espace Défense syndicale avec checklist et pièces à demander.
- Bibliothèque documentaire structurée.
- Espace Communication pour article, tract et flash info.
- Assistant IA simulé avec zone de chat et actions rapides.
- Statistiques fictives.
- Paramètres de connexion à venir : GitHub, Hostinger, Google Analytics, Search Console.

## Données

La V1 utilise uniquement des données de démonstration.

Aucune donnée réelle n'est connectée, stockée ou envoyée à un service externe.

## Prochaines évolutions

- Connecter les dossiers salariés à une base sécurisée.
- Ajouter une authentification privée.
- Connecter l'assistant IA au Core Prompt et au Routeur d'Intelligence.
- Brancher les workflows n8n.
- Récupérer les statistiques Google Analytics et Search Console.
- Afficher l'état de déploiement Hostinger.
- Connecter les issues, commits et automatisations GitHub.
- Ajouter des tests d'accessibilité, responsive et sécurité.
