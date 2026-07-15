# CSE Memory Engine — LOT 0

## Objectif

Le LOT 0 fournit un inventaire local, reproductible et non destructif du corpus documentaire CSE. Il mesure la volumétrie, classe les formats et les chemins, puis détecte les doublons binaires exacts par SHA-256.

## Emplacement local

Depuis la racine du dépôt, le corpus est attendu dans `CCSEMEMORYENGINE/RAW_DOCUMENTS`. Ce dossier, les résultats d'audit et les futurs espaces de traitement sont exclus de Git.

## Confidentialité

- Aucun document du corpus ne doit être ajouté à Git ou envoyé vers GitHub.
- Aucun fichier source n'est modifié, renommé, déplacé ou supprimé.
- L'audit ne réalise aucun appel réseau et aucun OCR.
- Les rapports utilisent des chemins relatifs au corpus et n'incluent aucun contenu textuel des documents.
- Les tests reposent exclusivement sur des fichiers temporaires synthétiques.

## Fonctionnement

Le script parcourt récursivement le corpus. Il relève les métadonnées de fichiers et calcule les empreintes SHA-256 par blocs. Une erreur de lecture est enregistrée sans interrompre le reste de l'audit. Les années et familles documentaires sont des estimations fondées uniquement sur les noms de fichiers et de dossiers.

Depuis la racine du dépôt :

```powershell
python -m automation.cse_memory.audit_cse_corpus
```

Si `python` n'est pas disponible dans le `PATH`, utiliser un interpréteur Python 3 local et conserver la même invocation avec `-m`.

Les rapports locaux sont produits dans :

- `CCSEMEMORYENGINE/AUDIT/cse_corpus_audit.json`
- `CCSEMEMORYENGINE/AUDIT/cse_corpus_audit.md`

## Limites

Le LOT 0 ne vérifie pas la validité interne des formats et ne déduit pas le sens des documents. Le classement par année et famille peut comporter des faux positifs ou des éléments classés dans « autres ». Un doublon désigne uniquement une identité exacte des octets.

Aucune indexation sémantique, extraction de contenu ou recherche plein texte n'est réalisée à ce stade.

## LOT 1 envisagé

Le LOT 1 pourra définir une chaîne locale et contrôlée de conversion et d'extraction, avec des règles par format, une traçabilité des traitements, des contrôles de qualité et une politique de sécurité préalable à toute indexation. Sa mise en œuvre devra conserver l'exclusion Git du corpus et des artefacts dérivés.
