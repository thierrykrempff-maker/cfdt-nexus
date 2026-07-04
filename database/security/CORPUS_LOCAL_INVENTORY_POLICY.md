# Inventaire sécurisé du corpus documentaire local V1

## Objectif

Cette note décrit la méthode d'inventaire local du corpus documentaire privé utilisé par CFDT Nexus.

L'objectif est de connaître le volume, les formats, les doublons exacts potentiels et une première proposition de classement, sans intégrer les documents réels dans GitHub.

## Règles de sécurité

- Les vrais accords restent hors GitHub.
- Les documents paie restent hors GitHub.
- Les PV CSE resteront hors GitHub.
- La BDESE ne doit pas être intégrée à ce corpus général.
- Les données personnelles sont interdites dans les fixtures et démonstrations.
- Aucun document original ne doit être déplacé.
- Aucun document original ne doit être renommé.
- Aucun document original ne doit être copié dans le dépôt.
- Aucun document ne doit être envoyé vers une API ou un service externe.
- Aucun OCR cloud, embedding ou base vectorielle ne doit être créé à ce stade.

## Ce qui peut être versionné

- Le script générique d'inventaire.
- La documentation de sécurité.
- Les règles `.gitignore`.
- Les schémas ou exemples fictifs.

## Ce qui ne doit jamais être versionné

- L'inventaire réel avec les noms de fichiers.
- Les chemins locaux absolus.
- Les accords réels.
- Les documents de paie réels.
- Les PV CSE réels.
- Les exports BDESE.
- Les doublons ou copies de documents.
- Les fichiers générés dans `local-index/`.

## Emplacement local des inventaires

Les inventaires générés doivent rester dans :

```text
local-index/
```

Ce dossier est exclu de Git.

Les fichiers privés générés utilisent des suffixes du type :

```text
*.private.json
*.private.csv
```

Ils sont également exclus de Git.

## Données extraites par le script

Le script peut extraire uniquement :

- nom du fichier ;
- extension ;
- taille ;
- date de modification ;
- chemin relatif ;
- sous-dossier ;
- empreinte SHA-256 ;
- proposition de classement prudente à partir du nom.

Le script ne doit pas extraire le texte du document.

## Connexions futures

Cette étape prépare les futures briques suivantes :

- Document Intelligence Center ;
- Cycle CSE ;
- Agent Défenseur Syndical ;
- Agent Paie ;
- Agent CSSCT ;
- Agent Convention Chimie ;
- Veille juridique.

Avant ces connexions, une validation humaine est nécessaire pour définir le niveau de confidentialité, les catégories et les règles d'accès.

## Étape suivante attendue

Après validation de l'inventaire local :

```text
BIBLE ACCORDS SARRALBE V1
```

Cette étape ne doit pas démarrer tant que l'inventaire et le plan de classement ne sont pas validés.
