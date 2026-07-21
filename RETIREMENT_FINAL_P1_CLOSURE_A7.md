# A7 — Fermeture ciblée des deux P1 partiellement résolus

Date : 2026-07-21

Branche : `retirement-penibility-a7-final-p1-closure`

Parent : audit final `720409edf116dee01e75576c06bad65ba8f0b821`

## Périmètre strict

A7 traite uniquement :

1. la résolution documentaire insuffisamment sensible au type métier ;
2. la duplication technique résiduelle entre les cinq connecteurs.

Les sept P2, les deux P3 et le P1 de diagnostic Privacy Gate découvert par
l’audit ne sont pas corrigés. Aucun connecteur, convertisseur, validateur,
report builder, référentiel ou calcul métier n’est modifié.

## Cartographie avant correction

### Rapprochement documentaire

A6 ordonnait tous les documents selon une liste globale : contrat/avenant,
relevé de carrière, bulletin, Kelio, autres preuves. Le merger sélectionnait
la première valeur selon cet ordre, indépendamment de la nature du fait.

En outre, `CareerReconstructionEngine.build_candidates()` regroupe les
`ImportedCareerRecord` par classe et `CareerReconstructionMatcher._COMPARABLE`
n’utilise pas `career_event_type`. Deux événements différents sur la même
période pouvaient donc atteindre le merger comme compatibles.

Critères de fermeture retenus :

- rôles documentaires explicites ;
- priorités différentes selon la famille de fait ;
- type, confiance, période, provenance, précision et corroboration pris en
  compte ;
- types d’événement incompatibles transformés en conflit sans valeur choisie ;
- alternatives, provenance et confiance conservées ;
- ordre déterministe ;
- aucune règle juridique ou calcul nouveau.

### Duplication des connecteurs

A2 avait réduit de 19 à 3 les blocs techniques dupliqués au-delà du premier.
L’audit final a distingué :

- orchestration, Privacy Gate et pipeline : comportements techniques communs ;
- validations, policies, messages et rapports : comportements propres aux
  sources ou dette P2 volontairement hors A7.

Une duplication technique injustifiée subsistait dans
`ConnectorFoundation.convert_validated()` : `assert_safe()` était appelé une
première fois directement, puis une seconde fois par `convert()`.

Critères de fermeture retenus : suppression de cette double inspection,
signatures inchangées, aucun déplacement de logique métier et justification
explicite des différences conservées.

## Modèle de résolution A7

`document_resolution_models.py` introduit des modèles techniques immuables :

- `DocumentRole` : Employment Contract, Employment Amendment, Career
  Statement, Payslip, Kelio, Nibelis, Other Evidence ;
- `FactFamily` : uniquement les familles représentées par les valeurs Career
  Import existantes ;
- `FactResolutionStatus` : `RESOLVED`, `RESOLVED_WITH_WARNINGS`, `CONFLICT`,
  `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_FACT_TYPE` ;
- `FactResolution` : valeur proposée, sources candidates, rôles, confiance,
  provenance et justification.

`ReconstructionMerge.fact_resolutions` expose ces décisions sans supprimer les
champs A6. Les alternatives contradictoires restent dans
`alternative_values`; les conflits restent dans `ReconstructionConflict`.

## Priorités par famille de faits

| Famille | Priorité principale |
|---|---|
| période d’emploi / carrière | Career Statement, avenant, contrat, bulletin, Nibelis, Kelio, autre |
| employeur | avenant, contrat, Career Statement, bulletin, Nibelis, Kelio, autre |
| poste | avenant, contrat, bulletin, Nibelis, Career Statement, Kelio, autre |
| classification contractuelle | avenant, contrat, bulletin, Nibelis, Career Statement, Kelio, autre |
| classification appliquée | bulletin, Nibelis, avenant, contrat, Career Statement, Kelio, autre |
| coefficient | bulletin, Nibelis, avenant, contrat, Career Statement, Kelio, autre |
| horaire générique A6 | bulletin, Kelio, Nibelis, avenant, contrat, Career Statement, autre |
| horaire explicitement enregistré | Kelio, bulletin, Nibelis, avenant, contrat, Career Statement, autre |
| nuit / 5x8 | Kelio, bulletin, Nibelis, avenant, contrat, Career Statement, autre |
| astreinte / intervention / absence | Kelio, bulletin, Nibelis, autre, sources contractuelles, Career Statement |
| rubrique / contribution | Nibelis, bulletin, autre, sources contractuelles, Career Statement, Kelio |

La nature `CONTRACTUAL`, `APPLIED` ou `RECORDED` doit être explicite dans les
métadonnées de reconstruction. En son absence, A6 reste compatible : la
classification générique favorise le contrat et l’horaire générique favorise
le bulletin.

À rôle documentaire égal, la résolution applique successivement : confiance,
précision, complétude de période et corroboration. La provenance puis le
`record_id` servent uniquement à stabiliser l’ordre, jamais à créer une
supériorité probatoire.

## Gestion des conflits

- Des `career_event_type` distincts produisent toujours `CONFLICT` et aucune
  valeur fusionnée.
- Un fait non cartographié et contradictoire produit
  `UNSUPPORTED_FACT_TYPE`.
- Deux preuves contradictoires de rang égal restent en `CONFLICT`.
- Une source prioritaire peut produire `RESOLVED_WITH_WARNINGS`, mais toutes
  les alternatives et un conflit explicite sont conservés pour revue humaine.
- Aucune moyenne, dernière valeur, correction ou suppression automatique.

## Duplication avant / après

| Mesure | Avant A2 | Après A2 / avant A7 | Après A7 |
|---|---:|---:|---:|
| Blocs techniques redondants au-delà du premier | 19 | 3 | 2 |
| Inspections Privacy Gate par conversion validée | 2 | 2 | 1 |
| Signatures de connecteur modifiées | — | 0 | 0 |
| Fichiers connecteur modifiés | — | 0 | 0 |
| Validations métier déplacées | — | 0 | 0 |
| Rapports métier déplacés | — | 0 | 0 |

Les deux familles résiduelles correspondent aux validateurs/policies et aux
rapports spécifiques. Elles sont explicitement classées P2 dans l’audit et ne
sont pas traitées par A7. Les wrappers publics des cinq connecteurs restent
nécessaires pour préserver leurs signatures.

## Comportements volontairement non mutualisés

- extractions et modèles propres à chaque source ;
- messages, erreurs et avertissements métier ;
- Employee/Expert Views propres aux connecteurs ;
- anonymisation Kelio ;
- lookup et projection du référentiel Kelio ;
- lookup Nibelis et refus fermé sans référentiel ;
- convertisseurs et validations structurelles propres.

## Tests A7

`test_document_type_resolution_a7.py` couvre les priorités contractuelle et
appliquée, l’horaire enregistré, Career Statement, Nibelis, les avenants, les
périodes partielles, la confiance, la précision, la corroboration, les
provenances, les conflits, les faits non supportés, le pipeline réel et
l’absence de priorité globale unique.

`test_connector_residual_duplication_a7.py` couvre l’unique Privacy Gate, les
signatures, les rapports et validateurs spécifiques, Kelio, Nibelis, Career
Import, l’absence de cycle/import dynamique/réseau/API/OCR et les métriques.

Résultats établis :

- tests A7 : 27/27 ;
- A1 à A6 : 236/236 ;
- cinq connecteurs : 97/97 ;
- ensemble des 21 suites Retraite & Pénibilité : 482/482 ;
- suite complète : 1 939 réussites, 128 sous-tests réussis et uniquement les
  trois anomalies historiques déjà qualifiées ;
- `git diff --check` : réussi ;
- syntaxe Python 3.10 : 106 modules et 21 suites validés ;
- cycles, imports dynamiques A7 et capacités réseau/API/OCR : zéro.

## Réaudit ciblé

### Rapprochement documentaire

- Statut initial : `PARTIALLY_RESOLVED`.
- Preuve initiale : priorité A6 globale et types d’événement différents encore
  fusionnables.
- Correction : matrice par famille, rôles explicites, rang multifactoriel et
  conflits de type.
- Preuve finale : tests A7 sur les mêmes périodes, les sept rôles, les natures
  contractuelle/appliquée/enregistrée et le pipeline réel.
- Statut final : `RESOLVED`.

### Duplication des connecteurs

- Statut initial : `PARTIALLY_RESOLVED`.
- Preuve initiale : trois familles techniques résiduelles après A2, dont une
  double inspection identique dans la fondation.
- Correction : une seule frontière Privacy Gate dans `convert()` ; aucune
  modification des cinq connecteurs.
- Preuve finale : inspection comptée une fois, signatures et comportements
  spécifiques vérifiés, réduction 3 → 2 justifiée par le périmètre P2.
- Statut final : `RESOLVED` au niveau P1.

## Risques et dettes inchangés

Les sept P2 et deux P3 décrits dans l’audit final restent inchangés. Le défaut
de diagnostic Privacy Gate P1-N2 est également hors de la mission telle que
définie, qui cible exclusivement les deux statuts `PARTIALLY_RESOLVED`.
A7 n’autorise aucune donnée réelle, API, réseau, OCR, PDF, stockage ou calcul
de retraite.
