# Socle sources juridiques, CFDT et veille V1

## Audit de l'existant

Le dépôt CFDT Nexus possédait déjà :

- un routeur d'intelligence dans `agents/core/` ;
- un agent Défenseur Syndical V1 ;
- un agent Cycle CSE Intelligent V1 ;
- un agent Analyse Financière Sarralbe V1 ;
- une base documentaire privée V1 ;
- un inventaire sécurisé local du corpus documentaire ;
- un cockpit statique V2 avec une rubrique veille encore générique.

Il manquait :

- un registre des sources externes ;
- une hiérarchie de confiance ;
- des canaux de veille structurés ;
- des schémas de fiche de veille ;
- un modèle de bulletin périodique ;
- des règles de validation avant publication ;
- une intégration cockpit plus lisible pour la veille.

## Choix d'architecture

Les sources vivent dans :

`knowledge-base/sources/`

Les workflows de veille vivent dans :

`workflows/veille/`

L'agent spécialisé vit dans :

`agents/veille/`

Le cockpit affiche une version statique privée, sans backend :

`cockpit/`

Ce découpage évite de mélanger :

- la connaissance ;
- les règles de traitement ;
- les prompts agents ;
- l'interface de pilotage.

## Sources retenues

### Sources A - primaires ou officielles

- Légifrance ;
- Convention collective Chimie IDCC 44 sur Légifrance ;
- Code du travail numérique ;
- Cour de cassation ;
- Conseil d'État ;
- Conseil constitutionnel ;
- Ministère du Travail ;
- Service-Public.fr ;
- BOSS, à vérifier manuellement avant activation ;
- URSSAF, à vérifier manuellement avant activation.

### Sources B - institutionnelles, statistiques, prévention ou CFDT

- INRS ;
- ANACT ;
- Assurance Maladie - santé au travail ;
- DARES ;
- INSEE ;
- CFDT ;
- FCE-CFDT ;
- France Chimie.

### Sources C - veille spécialisée

- Actuel RH ;
- Éditions Tissot ;
- Liaisons Sociales ;
- Dalloz Actualité ;
- Village de la Justice, à vérifier manuellement avant activation.

### Sources D - réseaux sociaux officiels

Seuls les comptes CFDT relevés depuis le site officiel CFDT ont été intégrés :

- LinkedIn ;
- Bluesky ;
- Facebook ;
- YouTube ;
- Instagram ;
- TikTok ;
- Threads.

Les liens sociaux FCE-CFDT sont signalés comme à capturer précisément avant automatisation, afin de ne pas inventer d'URL.

## Règles de sécurité

- Aucun document réel n'est ajouté.
- Aucun contenu confidentiel n'est indexé.
- Aucun accord INEOS n'est publié.
- Aucun PV CSE n'est publié.
- Aucune BDESE n'est ajoutée.
- Aucune donnée personnelle n'est utilisée.
- Aucune source secondaire ne suffit à produire une réponse juridique.
- Aucune publication publique ne part sans validation humaine.

## Intégrations prévues

### Cycle CSE

Les veilles CSE, emploi, industrie, restructuration et santé sécurité peuvent générer :

- questions CSE ;
- demandes de documents ;
- points à inscrire à l'ordre du jour ;
- alertes à suivre.

### Bible Accords Sarralbe

Les veilles sur paie, primes, temps de travail, 5x8, congés ou classification peuvent déclencher une comparaison avec les accords locaux privés.

Cette comparaison doit rester hors GitHub si elle exploite des documents internes.

### Document Intelligence Center

Le Document Intelligence Center pourra recevoir uniquement :

- fiches validées ;
- métadonnées ;
- sources publiques ;
- résumés non confidentiels.

## Prochaines étapes recommandées

1. Vérifier manuellement BOSS, URSSAF, Village de la Justice et les réseaux sociaux FCE-CFDT.
2. Ajouter des tests JSON Schema.
3. Créer un premier workflow n8n de veille manuelle assistée, sans scraping agressif.
4. Définir une table locale des fiches validées.
5. Connecter la rubrique cockpit à un fichier de données local ou à une API privée.

