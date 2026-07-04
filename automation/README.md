# Automatisation

Ce dossier accueillera les scripts, jobs et traitements automatisés.

## Bible Accords Sarralbe

Le script `scripts/agreements_bible.py` pilote le pipeline local privé :

- inventaire incrémental ;
- extraction texte ;
- détection OCR ;
- chunking juridique ;
- index lexical ;
- recherche sourcée ;
- tests métier ;
- aide "Que me manque-t-il ?" ;
- diagnostic local des extractions OCR_REQUIRED / erreurs techniques / formats non supportés ;
- OCR local sécurisé des PDF scannés avec reprise après interruption.

Les sorties réelles restent dans `local-index/agreements/` et ne doivent jamais être committées.

## Zones

- `scripts/` : scripts réutilisables ;
- `jobs/` : tâches planifiées ou automatisées.

## Règles

- Pas d'automatisation sensible sans validation humaine.
- Documenter les entrées, sorties et risques.
- Prévoir des logs exploitables.
