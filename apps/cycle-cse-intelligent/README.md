# CFDT Nexus - Cycle CSE intelligent

Version V1 - Cycle CSE + analyse financiere Sarralbe.

## Objectif

Ce module prive structure le travail d'un elu CSE avant, pendant et apres une reunion.

Il couvre :

- tableau de bord "Ma prochaine reunion" ;
- preparation de l'ordre du jour direction ;
- fiches d'analyse des points direction ;
- questions du terrain ;
- analyse des questions CFDT et des autres organisations ;
- recherche historique PV simulee ;
- information-consultation ;
- aide au projet d'avis motive ;
- assistant de seance V1 ;
- marqueurs de seance ;
- analyse des reponses ;
- compte rendu adherents ;
- memoire interne ;
- suivi des engagements ;
- analyse financiere Sarralbe HDPE / PP avec donnees fictives.

## Limite V1

La V1 est une application statique locale.

Elle ne contient :

- aucune IA reelle ;
- aucune transcription automatique ;
- aucun backend securise ;
- aucun stockage documentaire confidentiel ;
- aucun vrai PV CSE ;
- aucune donnee nominative ;
- aucun chiffre financier reel.

Les donnees sont stockees dans le `localStorage` du navigateur pour valider les parcours et les modeles.

## Donnees de demonstration

Les exemples HDPE et PP sont fictifs.

Ils servent uniquement a tester deux situations :

- Cas A : volume sous budget + marge sous budget + RC EBITDA degrade ;
- Cas B : volume sous budget + marge superieure au budget + RC EBITDA sous budget.

Le module adapte les questions CSE aux signaux detectes et rappelle que toute conclusion strategique doit rester une hypothese a verifier.

## Securite documentaire

Ne jamais stocker dans ce depot :

- accord INEOS reel ;
- PV CSE reel ;
- BDESE ;
- enregistrement CSE reel ;
- transcription reelle ;
- dossier salarie reel ;
- donnee nominative.

Avant usage reel, il faudra ajouter :

- authentification ;
- droits d'acces ;
- stockage prive ;
- chiffrement ;
- journal d'audit ;
- politique de conservation ;
- suppression securisee ;
- cloisonnement par organisation.

## Connexion Bible Accords V1

Le Cycle CSE peut maintenant appeler localement la Bible Accords Sarralbe via le pont :

```text
automation/scripts/nexus_bible_bridge.py
```

Cette connexion sert a preparer un point CSE sans exposer les documents prives.

Pour un sujet CSE, le pont peut produire :

- ce que la direction semble vouloir presenter ;
- les textes locaux potentiellement lies ;
- les accords ou documents a verifier avec page et article si disponibles ;
- les questions a poser a la direction ;
- les questions de relance selon la reponse ;
- les documents complementaires a demander ;
- les risques et opportunites a qualifier ;
- les informations manquantes avant de prendre position.

Commande locale :

```powershell
python automation/scripts/nexus_bible_bridge.py analyze-cse --title "Repos entre deux postes" --subject "La direction souhaite modifier le repos entre deux postes pour les salaries en 5x8." --limit 5 --format detailed
```

Les rapports reels sont crees uniquement dans :

```text
local-index/agreements/integration/
```

Ils ne doivent jamais etre committes.

## Analyse comparative locale CSE V1

Le format detaille transforme un point CSE en fiche de preparation syndicale.

La fiche contient :

- ce que la direction semble vouloir faire ;
- les textes locaux potentiellement concernes ;
- la situation actuelle a verifier ;
- les points a comparer avant/apres ;
- les consequences concretes pour les salaries ;
- les avantages probables pour l'entreprise et les avantages eventuels pour les salaries ;
- les risques et points de vigilance ;
- les informations manquantes ;
- les documents a demander ;
- les questions principales a poser en CSE ;
- les relances conditionnelles ;
- le point CSSCT eventuel ;
- les elements de position CFDT a construire ;
- la synthese pour l'elu.

Le module ne conclut jamais seul qu'une mesure est legale ou illegale. Il prepare la discussion CSE et impose une verification humaine.

### Profil CSSCT / securite process / maintenance

La fiche CSE detaillee sait maintenant qualifier les sujets techniques de type PROVOX, SNCC, analyseurs, climatisation, pieces de rechange, pannes, DUERP et RPS.

Elle prepare :

- les risques techniques ;
- la securite process ;
- la continuite d'exploitation ;
- la charge mentale ;
- les questions CSSCT ;
- les documents techniques a demander.

## Integrations futures

Le module prepare les connexions futures avec :

- Document Intelligence Center ;
- Bibliotheque documentaire ;
- Bible Accords Sarralbe pour rechercher les accords locaux liés à un point CSE ;
- recherche semantique dans les PV ;
- transcription et analyse de reponses ;
- backend documentaire prive ;
- n8n pour les relances, validations et exports.
