# Connexion Bible Accords - Document Intelligence - Cycle CSE V1

## Objectif

Relier localement trois briques de CFDT Nexus :

- Bible Accords Sarralbe ;
- Document Intelligence Center ;
- Cycle CSE intelligent.

Cette connexion doit aider Thierry a preparer une analyse, une question CSE ou une comparaison documentaire sans exposer les accords et documents prives.

## Principe d'architecture

```text
Document local ou sujet CSE
  -> automation/scripts/nexus_bible_bridge.py
  -> detection de themes metier
  -> requetes locales vers automation/scripts/agreements_bible.py
  -> scoring Bible Accords existant
  -> sources document + page + article si disponibles
  -> questions / relances / documents manquants
  -> rapport prive local
```

Le pont ne remplace pas la Bible Accords. Il l'utilise.

Le scoring de reference reste celui de :

```text
automation/scripts/agreements_bible.py
```

## Commandes locales

Diagnostic :

```powershell
python automation/scripts/nexus_bible_bridge.py diagnose
```

Analyser un point CSE :

```powershell
python automation/scripts/nexus_bible_bridge.py analyze-cse --title "Repos entre deux postes" --subject "La direction souhaite modifier le repos entre deux postes pour les salaries en 5x8." --limit 5 --format detailed
```

Analyser un document local :

```powershell
python automation/scripts/nexus_bible_bridge.py analyze-document --path "C:\chemin\document.pdf"
```

Tester les scenarios V1 :

```powershell
python automation/scripts/nexus_bible_bridge.py run-scenarios
```

## Sorties

Le pont produit des rapports prives dans :

```text
local-index/agreements/integration/
```

Ces rapports peuvent contenir des noms de documents locaux, des scores, des pages ou des extraits. Ils ne doivent jamais etre ajoutes a Git.

## Statuts

Le pont distingue :

```text
SOURCE LOCALE TROUVEE
SOURCE LOCALE A VERIFIER
AUCUNE SOURCE LOCALE PERTINENTE TROUVEE
```

Ces statuts qualifient la recherche documentaire locale. Ils ne constituent pas une conclusion juridique.

## Scenarios de test V1

Les scenarios fictifs couvrent :

- repos entre deux postes / 5x8 ;
- astreinte ;
- procedure disciplinaire / reglement interieur ;
- heures de delegation / droit syndical.
- prime de nuit / dimanche / jour ferie.

Ils servent a verifier que la connexion utilise bien les profils metier construits dans la Bible Accords.

## Format CSE detaille

`analyze-cse` produit une fiche de preparation syndicale en 14 parties :

1. ce que la direction semble vouloir faire ;
2. textes locaux potentiellement concernes ;
3. situation actuelle a verifier ;
4. points a comparer avant/apres ;
5. consequences concretes pour les salaries ;
6. a qui profite le changement ;
7. risques et points de vigilance ;
8. informations manquantes ;
9. documents a demander ;
10. questions principales a poser en CSE ;
11. relances conditionnelles ;
12. point CSSCT eventuel ;
13. position CFDT a construire ;
14. synthese pour l'elu.

Le moteur formule des hypotheses prudentes. Il ne remplace pas l'analyse juridique, la lecture des sources citees ni le retour des salaries concernes.

## Principe de prudence

L'analyse automatique constitue une aide a la preparation. Verifier les textes cites, leur date, leur champ d'application et leur articulation avec les normes superieures avant toute position definitive en CSE, CSSCT ou negociation.

Ne jamais interpreter l'absence de resultat comme l'absence de droit.

## Limites V1

- Pas de backend securise.
- Pas de recherche semantique.
- Pas d'appel a une API externe.
- Pas de Code du travail externe.
- Pas de jurisprudence connectee.
- Pas de PV CSE reel.
- Pas de BDESE.
- Pas de publication automatique.

## Evolutions possibles

- Brancher un backend prive avec authentification.
- Ajouter une validation humaine dans le cockpit.
- Relier les questions generees au suivi CSE.
- Ajouter une recherche dans les PV CSE lorsque le corpus sera securise.
- Relier le Document Intelligence Center aux agents CSE, CSSCT, Accords Sarralbe et Defenseur Syndical.
