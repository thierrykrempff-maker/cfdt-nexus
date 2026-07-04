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
7. `update` : chaîne complète.

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

