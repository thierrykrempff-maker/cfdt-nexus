# Moteur d'export des rapports V1 — LOT 5E

## Objectif et architecture

Le moteur transforme un rapport d'analyse LOT 5B ou un résultat comparatif LOT 5D en une représentation exportable. Il reste indépendant du pipeline, des experts, du générateur de rapport, du comparateur et du Cockpit.

`ReportExporter` applique successivement quatre opérations :

1. validation du type et du caractère synthétique de la source ;
2. projection correspondant au niveau de confidentialité ;
3. rendu par l'adaptateur de format ;
4. création des métadonnées d'intégrité et d'archivage logique.

Le résultat reste un objet Python sérialisable. Le moteur n'ouvre aucun fichier et n'écrit jamais sur disque.

## Formats V1

- `json` conserve une structure de dictionnaires et de listes ;
- `markdown` produit un texte hiérarchisé ;
- `text` produit une représentation textuelle simple.

La table interne des adaptateurs et des extensions permet d'ajouter ultérieurement des rendus PDF, HTML ou DOCX. Aucun paquet externe et aucune bibliothèque PDF ne sont utilisés dans cette version.

## Niveaux de confidentialité

- `standard` exporte l'objet source complet ;
- `employee` exporte exclusivement `employee_view` ;
- `expert` exporte exclusivement `expert_view`.

Le rendu travaille uniquement sur la projection sélectionnée. Il ne peut donc pas réintroduire un champ métier absent de cette vue. L'enveloppe ajoute seulement les métadonnées techniques indispensables au nommage, à l'intégrité et à l'archivage. Si une vue filtrée ne contient pas d'identifiant de dossier, le nom logique emploie `REPORT` ou `COMPARISON` plutôt que de relire cet identifiant dans la source complète.

## Contenu

En mode standard, la structure complète conserve selon le type de source l'en-tête, le résumé exécutif, les documents, les thèmes, les analyses, les contradictions, les actions, la confiance, les limites et les métadonnées. Les vues salarié et expert conservent exactement les champs préparés par les LOTS 5B et 5D, sans enrichissement métier.

Le champ `source_type` distingue explicitement un `report` simple d'une `comparison`.

## Nommage stable

Le nom suit la convention :

```text
<identifiant>_<date UTC>_<type>_v<version>.<extension>
```

Exemple :

```text
CASE_REPORT_SYN_2026-07-15_report_v1-0.md
```

Les caractères non sûrs de l'identifiant et de la version sont remplacés. À contenu source, date, format et horloge identiques, le nom est stable.

## Empreinte logique

Une empreinte SHA-256 est calculée sur le contenu effectivement exporté : JSON canonique pour le format structuré, texte UTF-8 rendu pour Markdown et texte brut. L'empreinte ne porte pas sur l'enveloppe de métadonnées et pourra servir à une vérification ultérieure d'intégrité.

Changer la vue, le contenu ou le format peut donc changer l'empreinte.

## Archivage logique

La structure produite est :

```text
<année UTC>/<identifiant du dossier>/<nom du fichier>
```

Elle est fournie dans `logical_archive_path`, avec l'année, le nom et l'identifiant normalisé. `automatic_disk_write` et `disk_write_performed` restent toujours faux. Une future couche de persistance devra appliquer séparément ses contrôles d'accès et de conservation.

## Métadonnées

L'export expose :

- version du moteur d'export ;
- version de la source ;
- date UTC ;
- format ;
- niveau de confidentialité ;
- algorithme et empreinte logique ;
- nom de fichier ;
- chemin logique d'archive ;
- année et identifiant ;
- indicateurs d'absence d'écriture et de données réelles.

## Limites et extensions futures

Le moteur ne signe pas cryptographiquement le rapport, ne chiffre pas le contenu et ne garantit pas sa conservation. L'empreinte détecte une modification si une valeur de référence fiable est conservée ailleurs ; elle ne remplace pas une signature.

Les futurs adaptateurs PDF, HTML et DOCX devront recevoir la projection déjà filtrée, sans accéder de nouveau à la source complète. Leur ajout ne devra introduire ni calcul de paie, ni appel expert, ni analyse documentaire réelle.
