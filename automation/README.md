# Automatisation

Ce dossier accueillera les scripts, jobs et traitements automatisés.

## Assistant DS Router V1.1 / V1.2 corrective

Le script `scripts/assistant_ds_router.py` est le point d'entree naturel de l'Assistant DS CFDT Nexus.

Il classe une question libre par domaines metier et intentions, choisit les moteurs locaux disponibles, execute la Bible Accords et le pont Nexus/Bible si necessaire, puis fusionne une reponse courte avec sources, documents a recuperer, questions a poser, position de travail et points de prudence.

La V1.1 ajoute le reranking contextuel des sources, la limitation lisible des sources principales, le dedoublonnage semantique leger, `issue_groups` pour les sujets multi-domaines et une `working_position` construite explicitement par domaine. La V1.2 corrective affine l'intention reunion CSE/repos, repousse les sources hors sujet et ajoute une reponse courte avant la methode de controle.

Commandes principales :

```powershell
python automation/scripts/assistant_ds_router.py route --query "Combien de repos entre deux postes en 5x8 ?"
python automation/scripts/assistant_ds_router.py ask --query "La direction veut reduire le repos entre deux postes. Prepare le CSE." --source-limit 6
python automation/scripts/assistant_ds_router.py diagnose
python automation/scripts/assistant_ds_router.py run-scenarios
```

Les sorties `--format text` et `--format json` sont disponibles pour preparer une future interface.

Le routeur n'execute jamais un module non connecte : Document Intelligence, controle paie dedie et veille juridique sont signales explicitement lorsqu'ils sont detectes mais indisponibles.

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

Le profil CSSCT / securite process / maintenance couvre notamment :

- DUERP / DUER ;
- RPS et charge mentale ;
- PROVOX / SNCC / analyseurs ;
- climatisation ;
- pannes et scenarios de panne ;
- pieces de rechange et pieces critiques ;
- plan de contingence ;
- maintenance preventive ;
- risques industriels et securite process.

## Zones

- `scripts/` : scripts réutilisables ;
- `jobs/` : tâches planifiées ou automatisées.

## Règles

- Pas d'automatisation sensible sans validation humaine.
- Documenter les entrées, sorties et risques.
- Prévoir des logs exploitables.
