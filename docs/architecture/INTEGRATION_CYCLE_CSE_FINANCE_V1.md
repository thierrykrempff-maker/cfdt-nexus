# Integration Cycle CSE Intelligent + Analyse Financiere Sarralbe V1

Date : 4 juillet 2026

## Audit de l'existant

Le depot `cfdt-nexus` contient deja les fondations suivantes :

- `agents/core/ROUTEUR_INTELLIGENCE_V1.md` : routeur central des demandes.
- `agents/core/CFDT_NEXUS_CORE_PROMPT_V1.md` : prompt principal de CFDT Nexus.
- `agents/defenseur/DEFENSEUR_SYNDICAL_V1.md` : module de defense disciplinaire.
- `cockpit/` : interface privee statique de pilotage.
- `docs/architecture/ARCHITECTURE_GLOBALE_V1.md` : architecture cible.
- `docs/security/`, `docs/data-governance/`, `docs/operations/` : premiers cadres de gouvernance.
- `apps/` : espace prevu pour les interfaces applicatives.

Constat CTO : le bon emplacement pour cette mission n'est pas le site public. Le Cycle CSE et l'analyse financiere sont des outils internes de travail syndical ; ils doivent donc vivre dans `cfdt-nexus`, pas dans le depot du site CFDT public.

## Modules deja construits

Les modules deja disponibles avant integration sont :

- noyau de decision : Routeur d'Intelligence V1 ;
- prompt principal : Core Prompt V1 ;
- module disciplinaire : Defenseur Syndical V1 ;
- cockpit prive : V1/V2 statique ;
- documentation d'architecture et de gouvernance.

Il manquait encore :

- une methode CSE versionnee ;
- une methode d'analyse financiere Sarralbe versionnee ;
- un agent CSE specialise ;
- un agent d'analyse financiere specialise ;
- une application statique dediee au cycle CSE.

## Plan d'integration retenu

1. Stocker les methodes dans `docs/methodology/`.
2. Creer un agent CSE dans `agents/cse/`.
3. Creer un agent d'analyse financiere dans `agents/analyse-financiere/`.
4. Installer le prototype statique dans `apps/cycle-cse-intelligent/`.
5. Corriger les liens internes du prototype pour ne pas pointer vers des modules absents du depot.
6. Documenter les limites : aucune donnee reelle, aucun PV reel, aucune BDESE, aucune donnee nominative.
7. Garder le site public hors perimetre.

## Resultat cible V1

La V1 doit permettre de tester :

- preparation d'un ordre du jour CSE ;
- analyse des points direction ;
- questions terrain ;
- questions CFDT et autres organisations ;
- information-consultation ;
- assistant de seance manuel ;
- marqueurs de reunion ;
- analyse de reponses ;
- compte rendu adherents ;
- memoire interne ;
- suivi des engagements ;
- lecture financiere Sarralbe HDPE / PP sur donnees fictives.

## Limites V1

- Pas de backend.
- Pas de vraie IA connectee.
- Pas de transcription automatique.
- Pas de stockage documentaire confidentiel.
- Pas de donnees nominatives.
- Pas de chiffres financiers reels.
- Donnees de demonstration stockees uniquement dans le navigateur via `localStorage`.

## Evolutions recommandees

Avant usage reel :

- ajouter authentification ;
- creer une matrice droits d'acces ;
- connecter une base documentaire privee ;
- definir une politique de conservation ;
- ajouter export PDF/Markdown controle ;
- ajouter journal d'audit ;
- connecter n8n uniquement avec validation humaine ;
- ajouter tests JavaScript et tests de non-fuite documentaire.
