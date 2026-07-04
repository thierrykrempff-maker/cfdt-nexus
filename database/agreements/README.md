# Bible Accords Sarralbe V1

## Objectif

La Bible Accords Sarralbe V1 est un pipeline local et sécurisé pour inventorier, extraire, indexer et rechercher dans le corpus privé des accords et textes collectifs de Sarralbe.

Elle ne contient aucun document réel dans GitHub.

## Emplacement des données privées

Les résultats locaux sont écrits dans :

```text
local-index/agreements/
```

Ce dossier est ignoré par Git.

## Commandes locales

Depuis la racine du dépôt :

```powershell
$env:CFDT_NEXUS_CORPUS_PATH="C:\chemin\vers\corpus-prive"
python automation/scripts/agreements_bible.py update
python automation/scripts/agreements_bible.py search --query "repos entre deux postes"
python automation/scripts/agreements_bible.py test
python automation/scripts/agreements_bible.py missing --query "astreinte"
python automation/scripts/agreements_bible.py diagnose
```

Le chemin du corpus peut aussi être passé par argument :

```powershell
python automation/scripts/agreements_bible.py update --source "C:\chemin\vers\corpus-prive"
```

## Commandes disponibles

- `scan` : inventorie le corpus, calcule les SHA-256 et détecte les changements.
- `extract` : extrait localement le texte des documents nouveaux ou modifiés.
- `index` : crée les chunks juridiques et l'index lexical local.
- `update` : lance `scan`, `extract` puis `index`.
- `search` : recherche locale lexicale avec citations.
- `test` : lance une série de requêtes métier et produit un rapport privé.
- `missing` : prépare une sortie "Que me manque-t-il ?" pour une situation donnée.
- `diagnose` : affiche le bilan local des extractions : OK, OCR_REQUIRED, erreurs techniques et formats non supportés.

## Capacités V1

- inventaire incrémental ;
- extraction PDF texte ;
- extraction DOCX ;
- extraction TXT ;
- détection OCR_REQUIRED ;
- reclassement en `OCR_REQUIRED` des PDF dont les pages sont lisibles mais dont le texte extrait est vide ;
- rapport avec `extraction_note` et `error_message` pour distinguer OCR requis et erreur technique réelle ;
- chunks avec page, section/article quand détectable ;
- recherche lexicale multi-termes ;
- filtre par thème, type, document et dates ;
- citations sourcées avec extrait court ;
- classification prudente ;
- relations potentielles à vérifier.

## Limites V1

- recherche lexicale, pas recherche sémantique ;
- pas d'OCR cloud ;
- un PDF classé `OCR_REQUIRED` doit être traité par OCR local ou validé manuellement avant indexation ;
- pas de conclusion juridique automatique ;
- les relations entre accords et avenants sont seulement potentielles tant qu'elles ne sont pas établies ou validées ;
- les pages ne sont disponibles que lorsque le format source permet de les conserver ;
- les articles et sections ne sont jamais inventés.

## Sécurité

GitHub ne doit jamais contenir :

- PDF réel ;
- DOCX réel ;
- règlement intérieur réel ;
- texte extrait réel ;
- chunks réels ;
- inventaire réel ;
- résultats de recherche réels ;
- chemin absolu privé ;
- donnée nominative.
