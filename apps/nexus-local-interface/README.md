# Nexus Local Interface

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
- enrichissement local par `automation/experts/juriste_travail.py`.

## Perimetre V2

L'interface affiche :

- reponse courte ;
- position de travail ;
- sources locales principales ;
- niveau de confiance ;
- points a verifier ;
- documents a recuperer ;
- questions utiles ;
- groupes d'enjeux ;
- bloc Expert Juriste droit du travail V0.
