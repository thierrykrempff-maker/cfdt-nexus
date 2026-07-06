# Assistant DS Router V1

## Role

`automation/scripts/assistant_ds_router.py` est le routeur central local de CFDT Nexus.

Il permet a l'utilisateur de poser une question naturelle sans choisir lui-meme une commande technique. Le routeur :

- classe la demande par domaines metier et intentions ;
- construit un plan d'execution lisible ;
- appelle uniquement les moteurs locaux reellement connectes ;
- fusionne les sources, questions, documents et avertissements ;
- produit une reponse courte de travail pour l'elu ou le DS.

Le routeur orchestre les briques existantes. Il ne remplace pas `agreements_bible.py` ni `nexus_bible_bridge.py`.

## Domaines

Domaines minimum geres en V1 :

- `bible_accords`
- `cse`
- `cssct_securite`
- `paie_remuneration`
- `temps_travail`
- `classification_carriere`
- `inaptitude_reclassement`
- `disciplinaire`
- `droit_syndical`
- `analyse_documentaire`
- `veille_juridique`

Domaines metier complementaires geres car deja utiles dans les scenarios :

- `astreinte`
- `conges_payes`

Une question peut etre multi-domaines. Exemple : une intervention d'astreinte de nuit avec repos reduit et paie contestee route vers `temps_travail`, `astreinte` et `paie_remuneration`.

## Intentions

Intentions detectees :

- `question_simple`
- `rechercher_droit_local`
- `preparer_cse`
- `preparer_cssct`
- `analyser_situation_individuelle`
- `analyser_paie`
- `analyser_document`
- `preparer_negociation`
- `preparer_entretien_direction`
- `construire_argumentaire`
- `demander_documents`
- `verifier_conformite`
- `rechercher_veille`

Le routeur n'affiche pas de chaine de raisonnement detaillee. Il fournit seulement un resume de routage explicable.

## Moteurs

Moteurs connectes en V1 :

- `bible_accords` : recherche locale sourcee dans l'index prive ;
- `nexus_bible_bridge` : fiche metier CSE/RH/Paie construite avec les sources locales.

Modules detectes mais non executes directement en V1 :

- Document Intelligence Center : module present, connecteur d'execution non disponible dans le routeur ;
- Cycle CSE Intelligent : interface presente, execution locale couverte par `nexus_bible_bridge` ;
- controle paie dedie : non connecte ;
- veille juridique : non connectee.

Le routeur ne simule jamais un moteur non connecte. Il ajoute un avertissement explicite.

## Regles d'orchestration

- Question simple sur un droit local : `bible_accords`.
- Projet ou modification a discuter en CSE : `bible_accords` + `nexus_bible_bridge`.
- Sujet CSSCT, DUERP, process, PROVOX, SNCC, chaleur ou pannes : profil CSSCT + Bible + pont metier.
- Classification, emploi, carriere, coefficient : Bible + fiche situation individuelle.
- Inaptitude ou reclassement : Bible + fiche situation individuelle.
- Heures supplementaires, compteurs, pointage, badgeage : Bible + methode de controle temps/paie, sans routage droit syndical.
- Disciplinaire : Bible + fiche situation individuelle, avec vigilance reglement interieur / convention collective.
- Droit syndical : uniquement en presence de mandat, elu CSE, delegue syndical, heures de delegation, credit d'heures, moyens syndicaux ou fonctionnement CSE.
- Analyse documentaire : avertissement si aucun connecteur d'execution documentaire n'est disponible.

## Commandes

```powershell
python automation/scripts/assistant_ds_router.py route --query "Combien de repos entre deux postes en 5x8 ?"
python automation/scripts/assistant_ds_router.py ask --query "La direction veut reduire le repos entre deux postes. Prepare le CSE."
python automation/scripts/assistant_ds_router.py diagnose
python automation/scripts/assistant_ds_router.py run-scenarios
```

Sorties disponibles :

```powershell
--format text
--format json
```

La sortie JSON est prevue pour une future interface cockpit.

## Reponse Assistant DS

La commande `ask` produit :

- question ;
- comprehension ;
- sources locales principales ;
- points a verifier ;
- documents a recuperer ;
- questions a poser ;
- position de travail ;
- prochaine action recommandee ;
- niveau de confiance ;
- avertissements.

Une question simple ne declenche pas une fiche CSE complete. Les situations individuelles produisent une fiche dossier salarie. Les sujets paie produisent une methode de controle.

## Fusion

La fusion V1 :

- dedoublonne les sources, documents et questions ;
- conserve document, page et article si disponibles ;
- distingue les sources locales a verifier des hypotheses ;
- garde les avertissements des modules non connectes ;
- ne transforme jamais une hypothese en regle certaine.

## Securite documentaire

Le routeur travaille uniquement sur les index locaux existants.

Interdits :

- commit de documents prives ;
- commit d'extraits OCR ;
- commit de resultats reels ;
- copie de `local-index/` dans Git ;
- envoi de documents vers un service externe ;
- affichage integral d'un accord prive.

`local-index/` reste ignore par `.gitignore`. La commande `diagnose` le verifie.

## Scenarios

`run-scenarios` couvre 25 scenarios :

- les 20 scenarios metier obligatoires ;
- 5 scenarios complexes multi-domaines ;
- absence de contamination CSSCT sur classification ;
- absence de droit syndical sur heures supplementaires ;
- absence de paie sur PROVOX ;
- absence de fiche CSE complete pour une question simple.

## Evolution

Le routeur prepare une future interface graphique :

- route et reponse en JSON ;
- plan d'execution structure ;
- avertissements exploitables ;
- separation claire entre classification, execution et fusion.

Les prochaines etapes pourront connecter un vrai module documentaire, un controle paie dedie et une veille juridique actualisee.
