# Guide technique CFDT Nexus V1

## Architecture

Le serveur local `apps/nexus-local-interface/server.py` expose l'interface et
`/api/analyze`. La demande traverse le routeur factuel, les experts historiques,
la comparaison sources–faits, puis le moteur de restitution. Le payload public
sépare `public_summary` et `detailed_analysis`.

Le service écoute sur `127.0.0.1`. Il n'assure ni authentification multi-utilisateur
ni persistance serveur des dossiers. Les moteurs avancés et connecteurs Runtime
sont derrière des feature flags désactivés par défaut.

## Version

`VERSION` est l'unique source de version produit. Le module
`NEXUS_RUNTIME_INTEGRATION.version` l'expose à `/health`, aux payloads et aux
exports. Les versions de schéma restent indépendantes.

## Dépendances

Installer le cœur :

```powershell
python -m pip install -r requirements.txt
```

Installer les formats facultatifs :

```powershell
python -m pip install -r requirements-optional.txt
```

`reportlab`, `python-pptx` et `openpyxl` sont facultatifs. Leur absence doit
produire un statut indisponible ou un test `SKIPPED`, jamais un échec global.

## Configuration locale

Le lanceur peut charger `local-index\nexus-local-secrets.cmd`, ignoré par Git.
Variables reconnues :

- `CFDT_NEXUS_LEGIFRANCE_CLIENT_ID`
- `CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET`
- `CFDT_NEXUS_JUDILIBRE_CLIENT_ID`
- `CFDT_NEXUS_JUDILIBRE_CLIENT_SECRET`
- `CFDT_NEXUS_PYTHON`

Ne jamais journaliser leurs valeurs. Les feature flags avancés restent absents ou à
`false` par défaut.

## Lancement

```powershell
apps\nexus-local-interface\start-nexus-local.bat
```

Vérification :

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

Arrêt :

```powershell
apps\nexus-local-interface\stop-nexus-local.bat
```

## Tests et baselines

```powershell
python -m pytest tests/test_v1_release_contract.py
python -m pytest tests/test_v1_release_security.py
python -m pytest tests/test_v1_release_end_to_end.py
python tools/run_v1_release_validation.py
python -m pytest
```

La baseline de release est sous
`tests/fixtures/real_business_cases/v1_release_validation/`. Elle est synthétique
et anonymisée.

## Logs, sauvegarde et restauration

Les erreurs HTTP publiques sont génériques. Les journaux techniques ne doivent
contenir ni secrets, ni contenu intégral, ni chemin exposé au frontend. Les corpus
locaux et `local-index/` ne sont pas versionnés : leur sauvegarde relève de
l'exploitant local. Pour restaurer l'application, réinstaller les dépendances,
restaurer les corpus autorisés puis relancer les tests.

## Mise à jour

Avant toute mise à jour : sauvegarder les données locales autorisées, vérifier le
SHA, installer les dépendances déclarées, exécuter la suite obligatoire et
contrôler `/health`. Revenir au commit validé si un test supporté échoue.
