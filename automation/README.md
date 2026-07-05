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

## Connexion Document Intelligence / Cycle CSE

Le script `scripts/nexus_bible_bridge.py` relie localement :

- le Document Intelligence Center ;
- le Cycle CSE intelligent ;
- la Bible Accords Sarralbe.

Commandes principales :

```powershell
python automation/scripts/nexus_bible_bridge.py diagnose
python automation/scripts/nexus_bible_bridge.py analyze-cse --title "..." --subject "..." --limit 5 --format detailed
python automation/scripts/nexus_bible_bridge.py analyze-document --path "C:\chemin\document.pdf"
python automation/scripts/nexus_bible_bridge.py run-scenarios
```

Le pont ne cree pas de nouvelle base de score. Il appelle le moteur de recherche et de scoring de `scripts/agreements_bible.py`.

Les rapports reels restent dans `local-index/agreements/integration/` et ne doivent jamais etre committes.

La sortie CSE detaillee produit une fiche de preparation avec :

- situation actuelle a verifier ;
- points a comparer avant/apres ;
- consequences concretes pour les salaries ;
- beneficiaire probable du changement ;
- risques et points de vigilance ;
- informations manquantes ;
- documents a demander ;
- questions CSE ;
- relances conditionnelles ;
- point CSSCT eventuel ;
- position CFDT a construire ;
- synthese pour l'elu.

## Zones

- `scripts/` : scripts réutilisables ;
- `jobs/` : tâches planifiées ou automatisées.

## Règles

- Pas d'automatisation sensible sans validation humaine.
- Documenter les entrées, sorties et risques.
- Prévoir des logs exploitables.
