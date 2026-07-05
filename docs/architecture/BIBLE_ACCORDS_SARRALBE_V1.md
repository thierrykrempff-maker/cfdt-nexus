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
5. `search-debug` : explication locale du score de pertinence.
6. `test` : tests métier locaux.
7. `missing` : aide "Que me manque-t-il ?".
8. `diagnose` : bilan local des extractions par statut.
9. `ocr-diagnose` : diagnostic des dépendances OCR locales.
10. `ocr-run` : OCR local sur copie de travail des PDF `OCR_REQUIRED`.
11. `update` : chaîne complète.

## Pertinence de recherche

Le moteur de recherche V1 pondère désormais :

- score lexical ;
- expression exacte ;
- proximité des mots ;
- synonymes métier ;
- thème du document ;
- type de document ;
- titre ou chemin du document ;
- pénalité de thème non pertinent.

Pour une requête comme `repos entre deux postes`, le profil `temps de travail / repos` favorise :

- repos quotidien ;
- repos entre deux journées ;
- temps de repos ;
- temps de travail ;
- organisation du travail ;
- 5x8 ;
- travail posté ;
- horaires de postes.

Les documents NAO, salaires, primes, intéressement ou participation sont pénalisés lorsque la requête ne porte pas sur la rémunération.

Le profil `relations collectives / droit syndical` favorise :

- heures de délégation ;
- crédit d'heures ;
- temps de délégation ;
- mandat ;
- représentant du personnel ;
- élu CSE ;
- membre CSE ;
- délégué syndical ;
- représentant syndical ;
- moyens syndicaux ;
- local syndical ;
- affichage syndical ;
- réunions syndicales.

Il favorise fortement les titres contenant `CSE`, `droit syndical`, `RP` ou `dialogue social`, et pénalise les documents paie, CET, forfait jours ou rémunération lorsque la requête porte clairement sur les relations collectives.

La commande de contrôle local est :

```powershell
python automation/scripts/agreements_bible.py search-debug --query "repos entre deux postes"
```

## OCR local

L'OCR local est strictement privé.

Architecture :

```text
Dossier source privé
  -> copie de travail locale
  -> local-index/agreements/ocr/
  -> extraction texte OCR
  -> chunks
  -> index lexical
  -> citations document/page
```

Les PDF originaux du corpus privé ne sont jamais modifiés.

Le moteur privilégie :

- OCRmyPDF ;
- Tesseract OCR avec langue `fra` ;
- Ghostscript ;
- repli local `pdftoppm + tesseract` si OCRmyPDF n'est pas disponible.

Si la confiance OCR est faible, le statut `OCR_LOW_CONFIDENCE` est utilisé et la citation doit porter un avertissement.

La reprise après interruption repose sur :

```text
local-index/agreements/ocr/<document_id>/ocr-status.private.json
```

Un document déjà OCRisé avec succès n'est pas retraité sans `--force-ocr`.

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
local-index/agreements/ocr/
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

## Connexion Document Intelligence / Cycle CSE

La Bible Accords est maintenant accessible via un pont local :

```text
automation/scripts/nexus_bible_bridge.py
```

Ce pont sert deux usages V1 :

- analyser un document local dans le Document Intelligence Center ;
- analyser un point CSE avant reunion.

Le pont reutilise le scoring, les citations et les profils metier de `automation/scripts/agreements_bible.py`.

Il genere des rapports prives dans :

```text
local-index/agreements/integration/
```

Ces rapports ne doivent pas etre committes.

Les commandes de controle sont :

```powershell
python automation/scripts/nexus_bible_bridge.py diagnose
python automation/scripts/nexus_bible_bridge.py run-scenarios
python automation/scripts/nexus_bible_bridge.py analyze-cse --title "..." --subject "..." --limit 5 --format detailed
python automation/scripts/nexus_bible_bridge.py analyze-document --path "C:\chemin\document.pdf"
```

La sortie `analyze-cse` est maintenant une fiche de preparation CSE detaillee : situation actuelle a verifier, comparaison avant/apres, consequences salaries, risques, documents a demander, questions CSE, relances conditionnelles, point CSSCT et synthese pour l'elu.

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
