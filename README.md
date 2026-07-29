# CFDT Nexus 1.0.0

CFDT Nexus est un assistant syndical local destiné à préparer une analyse prudente,
traçable et exploitable par un délégué syndical. Il aide à structurer les faits, les
questions, les documents utiles et les sources disponibles. Il ne remplace ni la
validation humaine, ni un conseil juridique, médical ou financier compétent.

## Périmètre V1

La V1 garantit deux parcours :

- `QUESTION_SALARIE` : réponse pédagogique fondée sur les faits et les sources
  réellement disponibles ;
- `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE` : préparation concrète d'un entretien,
  avec griefs, preuves, questions, documents, stratégie et formulations.

La comparaison sources–faits n'est produite que lorsque les documents sont
réellement disponibles. En mode dégradé, Nexus signale les sources absentes et
suspend la conclusion lorsque les informations ne suffisent pas.

La V1 ne garantit pas un calcul de paie, une décision juridique définitive, un
conseil médical, un service multi-utilisateur ou un stockage serveur de dossiers.

## Installation

Python 3.10 ou ultérieur est requis.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Les formats documentaires facultatifs s'installent séparément :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
```

Leur absence ne bloque pas le cœur V1 ; le format concerné est simplement indiqué
comme indisponible.

## Lancement et arrêt

Sous Windows, double-cliquer sur :

```text
apps\nexus-local-interface\start-nexus-local.bat
```

ou lancer :

```powershell
python apps\nexus-local-interface\server.py --open
```

L'interface écoute uniquement sur `http://127.0.0.1:8765/`. Le lanceur accepte un
fichier local ignoré par Git, `local-index\nexus-local-secrets.cmd`, mais démarre
aussi en mode dégradé s'il est absent.

Pour arrêter proprement :

```text
apps\nexus-local-interface\stop-nexus-local.bat
```

## Utilisation

1. Choisir le parcours adapté.
2. Décrire uniquement les faits utiles, sans donnée personnelle superflue.
3. Lancer l'analyse.
4. Lire d'abord la synthèse publique.
5. Ouvrir l'analyse détaillée pour la traçabilité.
6. Copier, imprimer ou exporter volontairement la synthèse.

## Sources

Nexus hiérarchise les accords INEOS, la CCNIC IDCC 44, le Code du travail, la
jurisprudence comparable et les sources officielles complémentaires. Les PV CSE ou
CSSCT constituent un contexte documentaire, pas une norme juridique.

Les connecteurs avancés sont désactivés par défaut. Leur disponibilité dépend de la
configuration locale, des métadonnées présentes et, pour les services externes, des
identifiants autorisés. Un connecteur indisponible n'est jamais présenté comme
opérationnel.

## Confidentialité

- serveur lié à l'interface de bouclage uniquement ;
- aucun stockage navigateur automatique ;
- aucun dossier salarié persisté par le serveur ;
- secrets attendus dans un fichier local ignoré par Git ;
- export limité à la synthèse publique et déclenché par l'utilisateur ;
- diagnostics techniques et chemins locaux exclus des réponses publiques.

## Tests

```powershell
python -m pytest
python tools/run_v1_release_validation.py
```

Les dépendances de `requirements-optional.txt` rendent disponibles des tests et
formats supplémentaires. Si elles manquent, les tests associés sont marqués
`SKIPPED`, pas `FAILED`.

## Dépannage

- `/health` ne répond pas : vérifier Python, le port 8765 et le pare-feu local ;
- port occupé : arrêter l'ancienne instance avec le lanceur d'arrêt ;
- source externe absente : vérifier la configuration locale, sans placer de secret
  dans Git ;
- format indisponible : installer `requirements-optional.txt` ;
- résultat suspendu : compléter les faits ou fournir le document demandé.

Guides :

- [Guide utilisateur](V1_USER_GUIDE.md)
- [Guide technique](V1_TECHNICAL_GUIDE.md)
- [Limites connues](V1_KNOWN_LIMITATIONS.md)
- [Rapport de préparation](V1_RELEASE_READINESS_REPORT.md)

La version produit est définie une seule fois dans `VERSION`.
