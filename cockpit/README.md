# Cockpit CFDT Nexus V2

## Objectif

Le Cockpit CFDT Nexus V2 transforme la V1 en véritable espace de travail privé pour Thierry Krempff, délégué syndical CFDT Chimie Énergie INEOS Sarralbe.

L'objectif est de donner l'impression d'ouvrir un bureau numérique syndical : dossiers, assistant IA, bibliothèque, communication, veille, statistiques et paramètres au même endroit.

Cette version reste volontairement statique, sans backend et sans connexion réelle.

## Structure des fichiers

- `index.html` : structure de l'interface, sections et zones fonctionnelles.
- `styles.css` : design responsive, sobre et professionnel.
- `app.js` : données fictives, rendu des composants et interactions locales.
- `README.md` : documentation du cockpit.

## Fonctionnalités V2

### Accueil

- Bonjour Thierry.
- Date du jour.
- Résumé de la journée.
- Statistiques synthétiques fictives.
- Actions prioritaires.
- Dernières activités.
- Zone actualités prévue.
- Barre d'action rapide.

### Dossiers salariés

- Création locale d'un dossier.
- Modification d'un dossier.
- Archivage / restauration.
- Recherche.
- Filtres par statut et priorité.
- Structure compatible avec une future base de données.

Chaque dossier contient :

- numéro ;
- titre ;
- type ;
- statut ;
- priorité ;
- date ;
- notes ;
- documents.

### Assistant IA

- Interface proche d'un chat.
- Historique visuel.
- Réponses simulées en V2.
- Boutons rapides : sanction, CSE, NAO, article, tract, courrier, prompt Codex.
- Préparation à une future connexion au GPT CFDT Nexus.

### Bibliothèque

- Interface de recherche.
- Catégories : Convention Chimie, Accords INEOS, Règlement intérieur, Modèles, Jurisprudence, Documentation CFDT.
- Métadonnées : titre, description, catégorie, mots-clés, date, version, niveau documentaire.

### Communication

- Modèles pour article, tract, flash info, courrier et publication web.
- Génération locale simulée d'une trame.
- Validation humaine prévue avant diffusion.

### Veille & Sources

- Vue statique du socle sources et veille V1.
- Blocs : Aujourd'hui, Mes sources, À vérifier, Veilles validées.
- Filtres simples : priorité, thème et domaine.
- Affichage d'un score de démonstration, d'une justification courte et d'une action suggérée.
- Rappel permanent : aucune publication automatique.
- Préparation d'une future connexion n8n, GitHub, agents CFDT Nexus et Document Intelligence Center.

### Statistiques

- Cartes prêtes à recevoir Google Analytics, Search Console, GitHub et n8n.
- Données fictives uniquement.

### Paramètres

- Version.
- GitHub.
- Hostinger.
- Google Analytics.
- Google Search Console.
- Automatisations.
- Configuration IA.
- Niveaux documentaires : public, privé, confidentiel.

## Sécurité

La V2 prévoit trois niveaux documentaires :

- `PUBLIC` : contenu diffusable ou utilisable par un futur chatbot public.
- `PRIVÉ` : contenu réservé à l'assistant privé.
- `CONFIDENTIEL` : documents qui ne devront jamais être chargés automatiquement.

Aucune donnée réelle n'est connectée, stockée ou envoyée à un service externe.

## Architecture future

Le cockpit est préparé pour connecter progressivement :

- GPT CFDT Nexus ;
- n8n ;
- GitHub ;
- Google Analytics ;
- Google Search Console ;
- Hostinger ;
- une future base de données sécurisée.

## Prochaines évolutions

- Ajouter une authentification.
- Connecter les dossiers à une base sécurisée.
- Ajouter des tests d'accessibilité et responsive.
- Brancher le Routeur d'Intelligence et les agents spécialisés.
- Créer les premiers workflows n8n.
- Connecter les statistiques réelles.
- Ajouter un mode brouillon / validation avant publication.
