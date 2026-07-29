# Audit initial de sortie CFDT Nexus V1

## Référence

- SHA de départ : `77341831b1b16e4bcec5ee5c44995c0cca893594`
- Branche de travail : `release/v1-final-validation`
- Version préparée : `1.0.0`

## État observé avant correction

| Élément | État | Constat |
|---|---|---|
| Routeur factuel | READY | Faits, parcours et ambiguïtés structurés. |
| Question salarié | READY | Parcours séparé et testé. |
| Entretien disciplinaire | READY | Préparation concrète et prudente. |
| Sources–faits | READY_WITH_LIMITATION | Dépend des sources réellement obtenues. |
| Réponse finale | READY | Synthèse et détails séparés, plafonds LOT 3 tenus. |
| Interface locale | READY_WITH_LIMITATION | Impression et version produit absentes avant ce lot. |
| Lanceur Windows | BLOCKING | Refusait le mode dégradé sans fichier de secrets local. |
| Arrêt documenté | READY_WITH_LIMITATION | Pas de lanceur d'arrêt dédié. |
| Dépendances | BLOCKING | Aucun manifeste reproductible ; formats facultatifs vus comme échecs. |
| Version produit | BLOCKING | Versions contradictoires dans l'interface et `/health`. |
| Documentation V1 | BLOCKING | Installation, limites et sécurité incomplètes. |
| Confidentialité publique | READY_WITH_LIMITATION | Payload nettoyé, mais erreurs internes à durcir. |
| Calcul paie fiable | OUT_OF_SCOPE_V1 | Non garanti. |
| Multi-utilisateur/cloud | OUT_OF_SCOPE_V1 | Mode local uniquement. |

## Architecture et parcours

Le flux réel est : interface locale → `/api/analyze` → routeur factuel → experts
historiques → sélection de sources → comparaison sources–faits → restitution
`public_summary` / `detailed_analysis`.

Les parcours garantis sont `QUESTION_SALARIE` et
`ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`. Les moteurs Core, CSE Memory, Retraite,
Protection Sociale, connecteurs Runtime, raisonnement syndical avancé, Expert Paie
V2 et Assistant Final sont configurables et désactivés par défaut.

## Sources et connecteurs

Légifrance, JUDILIBRE et CDTN sont pris en charge par le Runtime externe ; leur
opération dépend de la configuration et du réseau. Le Runtime officiel sait
référencer CNIL, DREETS, INRS, CARSAT, ANACT, France Chimie, droit local et les
connecteurs complémentaires présents. Aucun connecteur vide, désactivé ou
indisponible ne doit être simulé.

Les corpus locaux d'accords, CSE Memory et Protection Sociale étaient présents dans
l'environnement audité. Ils restent hors Git lorsqu'ils contiennent des documents
réels.

## Tests et risques

La référence intégrée avant ce lot était 3 190 tests et 128 sous-tests réussis.
Les risques de sortie identifiés étaient la reproductibilité des dépendances, le
lancement dégradé, l'absence d'arrêt dédié, les versions contradictoires, les
erreurs HTTP trop détaillées et une documentation insuffisante.

Les fichiers non suivis préexistants détectés par `git status --short` ont été
inventoriés et laissés intacts ; ils ne font pas partie du LOT 4.

## Dépendances

Obligatoires : `jsonschema`, `pypdf`, `python-docx`, `pytest`.

Facultatives : `reportlab`, `python-pptx`, `openpyxl`. La stratégie V1 retenue est
l'option 2 : disponibilité annoncée, absence non bloquante et tests associés
ignorés proprement.
