# Nexus Local Interface - Cockpit V3

Interface locale privee pour interroger Nexus sans taper de commande PowerShell.

## Lancement

Double-cliquer sur :

```text
apps\nexus-local-interface\start-nexus-local.bat
```

ou lancer :

```text
python apps\nexus-local-interface\server.py --open
```

Le serveur ecoute par defaut sur :

```text
http://127.0.0.1:8765/
```

## Securite

- aucune publication web ;
- aucun acces internet requis ;
- aucun document interne envoye a l'exterieur ;
- appel local au routeur `automation/scripts/assistant_ds_router.py ask --format json` ;
- enrichissement local par `automation/experts/orchestrator.py` ;
- rapport d'analyse local par `automation/experts/report_generator.py`, uniquement a partir du resultat reel Nexus ;
- experts locaux Juriste et Paie, sans service IA externe.

## Perimetre V3

Le Cockpit V3 conserve toutes les fonctions V2.2 et ajoute un dossier salarie synthetique connecte au pipeline LOT 5A
et au rapport LOT 5B.

Endpoints locaux ajoutes :

```text
GET /api/employee-case/scenarios
GET /api/employee-case/demo?scenario=<identifiant>
```

Les cinq scenarios publics sont strictement fictifs. La fixture de confidentialite n'est jamais exposee dans la liste
de demonstration. Le navigateur ne fournit aucun chemin de fichier et ne stocke aucun dossier.

Le flux V3 est documente dans `docs/architecture/COCKPIT_V3_EMPLOYEE_CASE.md`.

## Perimetre V2.2 conserve

L'interface affiche :

- question posee ;
- domaines detectes ;
- experts mobilises ;
- reponse synthetique Nexus ;
- position de travail ;
- sources locales principales ;
- niveau de confiance ;
- points a verifier ;
- documents a recuperer ;
- questions utiles ;
- groupes d'enjeux ;
- analyses par expertise Juriste et/ou Paie ;
- rapport d'analyse structure ;
- copie du rapport ;
- telechargement Markdown ;
- prudence et limites.

L'orchestration conserve le routeur V1.2 : elle enrichit la reponse apres `assistant_ds_router.py ask --format json` sans remplacer le routage.

Flux du rapport :

```text
question utilisateur
-> apps/nexus-local-interface/server.py
-> automation/scripts/assistant_ds_router.py ask --format json
-> automation/experts/orchestrator.py
-> automation/experts/juriste_travail.py et/ou automation/experts/paie.py
-> automation/experts/report_generator.py
-> affichage dans apps/nexus-local-interface
```
