# Bible Accords Sarralbe V1

## Audit de l'existant

Le dépôt CFDT Nexus contenait déjà :

- `automation/scripts/inventory-corpus.ps1` pour l'inventaire local sécurisé ;
- `database/` pour les schémas documentaires et règles de sécurité ;
- `local-index/` ignoré par Git ;
- `cockpit/` avec une bibliothèque statique ;
- `apps/cycle-cse-intelligent/` pour le futur usage CSE ;
- `agents/` pour les rôles spécialisés.

La V1 réutilise ces briques et ne crée pas de deuxième Document Intelligence Center ni de nouveau cockpit.

## Architecture retenue

```text
automation/scripts/agreements_bible.py
database/agreements/
local-index/agreements/
cockpit/
apps/cycle-cse-intelligent/
```

## Pipeline local

1. `scan` : inventaire incrémental, SHA-256, détection NEW / MODIFIED / UNCHANGED / MISSING / DUPLICATE_EXACT.
2. `extract` : extraction PDF/DOCX/TXT locale.
3. `index` : chunking juridique et index lexical.
4. `search` : recherche locale sourcée avec citations.
5. `test` : tests métier locaux.
6. `missing` : aide "Que me manque-t-il ?".
7. `diagnose` : bilan local des extractions par statut.
8. `update` : chaîne complète.

## Diagnostic OCR

Un PDF peut être techniquement lisible tout en ne contenant aucun texte exploitable, par exemple lorsqu'il s'agit d'un scan.

La règle V1 est :

- `page_count > 0` et `char_count = 0` sur un PDF : `OCR_REQUIRED` ;
- aucun parseur capable de lire le PDF ou ses pages : `ERROR` ;
- texte PDF très faible : `OCR_REQUIRED` ou contrôle humain ;
- format hors PDF/DOCX/TXT : `UNSUPPORTED`.

Les rapports privés ajoutent :

- `extraction_note` pour comprendre le classement ;
- `error_message` lorsqu'un parseur a renvoyé une erreur technique.

## Sécurité

Le chemin du corpus n'est pas codé en dur.

Il est fourni par :

- `--source` ;
- ou `CFDT_NEXUS_CORPUS_PATH`.

Les sorties réelles sont privées :

```text
local-index/agreements/
```

Ce dossier est ignoré par Git.

## Citations

Une citation doit contenir au mieux :

- document ;
- page ;
- article ou section ;
- extrait ;
- score de correspondance.

Si la page ou l'article n'est pas disponible, la sortie doit indiquer :

```text
LOCALISATION NON DÉTERMINÉE
```

## Limites V1

- Recherche lexicale uniquement.
- Pas de recherche sémantique.
- Pas d'OCR cloud.
- Les OCR nécessaires sont signalés, pas inventés.
- Les relations entre accords restent potentielles tant qu'elles ne sont pas validées.
- La Bible Accords ne produit pas seule une conclusion juridique.

## Articulation droit vivant

La future analyse devra distinguer :

1. accord local ;
2. règlement intérieur ;
3. convention collective ;
4. loi ;
5. jurisprudence ;
6. sources institutionnelles ;
7. analyse syndicale ;
8. faits du dossier.
