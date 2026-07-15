# LOT 5 — Index du pipeline dossier salarié

## Vue d'ensemble

Le LOT 5 construit une chaîne documentaire pour analyser des dossiers salariés strictement synthétiques. Chaque sous-lot conserve une responsabilité distincte et transmet des objets structurés au composant suivant.

```text
Dossier → Pipeline → Rapport → Cockpit → Comparateur → Export → Validation E2E
```

## Navigation par sous-lot

### LOT 5A — Pipeline d'analyse

[EMPLOYEE_CASE_PIPELINE_V1.md](EMPLOYEE_CASE_PIPELINE_V1.md) définit les dossiers, documents et analyses expertes synthétiques, les douze étapes déterministes, la matrice documentaire et les contrôles de confidentialité.

### LOT 5B — Rapport d'analyse

[EMPLOYEE_CASE_REPORT_V1.md](EMPLOYEE_CASE_REPORT_V1.md) assemble le résultat du pipeline et les analyses disponibles en douze sections, avec une vue salarié et une vue expert.

### LOT 5C — Cockpit V3

[COCKPIT_V3_EMPLOYEE_CASE.md](COCKPIT_V3_EMPLOYEE_CASE.md) expose cinq scénarios synthétiques dans l'interface locale et présente les étapes, les documents, les blocages, les contradictions et les deux vues.

### LOT 5D — Comparateur

[EMPLOYEE_CASE_COMPARATOR_V1.md](EMPLOYEE_CASE_COMPARATOR_V1.md) compare deux dossiers ou rapports synthétiques et classe leurs différences documentaires sans les interpréter comme des erreurs de paie.

### LOT 5E — Export structuré

[REPORT_EXPORT_ENGINE_V1.md](REPORT_EXPORT_ENGINE_V1.md) projette les vues standard, salarié ou expert et produit des exports JSON, Markdown ou texte avec empreinte et chemin logique d'archivage.

### LOT 5F — Validation de bout en bout

[EMPLOYEE_CASE_END_TO_END_VALIDATION.md](EMPLOYEE_CASE_END_TO_END_VALIDATION.md) vérifie l'intégration réelle des composants, les endpoints locaux, les comparaisons, les exports, la confidentialité et les performances indicatives.

## Limites communes

- données exclusivement synthétiques ;
- aucun calcul de paie ;
- aucun OCR ;
- aucun PDF réel ;
- aucune persistance automatique ;
- aucune conclusion juridique définitive.

Les référentiels, compteurs, rubriques et paramètres éventuellement cités restent des pistes de contrôle. Ils ne remplacent jamais les documents réels, les accords, la convention collective ou le Code du travail.

## Conditions avant utilisation de documents réels

L'utilisation future de documents réels exigera au minimum :

- une décision d'architecture et une analyse de risques dédiées ;
- une base juridique et une politique de minimisation des données ;
- une authentification et des autorisations par rôle ;
- un stockage chiffré avec politique de conservation et suppression ;
- une journalisation sécurisée sans donnée sensible ;
- une analyse documentaire isolée, avec contrôle des formats et contenus ;
- une validation renforcée des protections NIR, coordonnées bancaires, santé et identité ;
- une revue humaine avant toute conclusion métier ou juridique ;
- des tests de sécurité, confidentialité et traçabilité spécifiques.

Ces conditions ne sont pas implémentées par le LOT 5 et ne doivent pas être contournées par le Cockpit ou un futur adaptateur d'export.
