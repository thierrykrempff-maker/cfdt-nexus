# A5 — Intégration du référentiel Kelio

## Anomalie initiale

Le connecteur Kelio Retraite & Pénibilité acceptait un `counter_id` local dès
que son libellé, sa valeur décimale et sa date étaient structurellement
valides. Il ne vérifiait ni l'existence du compteur dans le référentiel paie,
ni son statut, ni ses garde-fous de confidentialité. Un identifiant inconnu
pouvait donc circuler jusqu'aux rapports sans résolution explicite.

## Référentiel et validateur réutilisés

La source de vérité existante est composée de :

- `database/payroll/referentials/kelio-counters.schema.json` ;
- `database/payroll/referentials/kelio-counters.example.json` ;
- `automation/payroll/payroll_referential_validator.py`.

Le catalogue `kelio-counters-synthetic-v1`, version `1.1.0`, contient 17
compteurs. Tous sont des exemples synthétiques, ont le statut
`synthetic_example` et interdisent le calcul. Le validateur existant contrôle
le schéma, l'unicité, les liens, la documentation métier, les données
sensibles et les garde-fous de calcul.

## Cartographie avant / après

| Sujet | Avant A5 | Après A5 |
|---|---|---|
| Identité | identifiant local libre | résolution par `counter_id` ou `counter_code`, projection vers l'identifiant canonique |
| Catalogue | non consulté | catalogue partagé chargé une seule fois et paresseusement par l'adaptateur |
| Validation | format local uniquement | validateur paie existant, puis contrôle d'usage Retraite |
| Inconnu | accepté silencieusement | `UNKNOWN`, conversion refusée |
| Ambiguïté | non détectée | `LOOKUP_ERROR`, conversion refusée |
| Métadonnées | libellé et valeur brute | catégorie, source, statut, preuve, provenance et garde-fous techniques |
| Preuve | compteur absent de Career Evidence | référence canonique ajoutée comme `ImportedEvidence`, sans valeur brute |
| Pipeline | Privacy Gate puis conversion | Privacy Gate, lookup, Career Import, Reconstruction |

## Architecture

`KelioReferentialLookup` est un Protocol indépendant du système de fichiers et
de son implémentation. `PayrollKelioReferentialLookup` est l'unique adaptateur
vers le référentiel paie existant. Il charge et valide le catalogue au premier
appel, puis conserve seulement son index en mémoire pour la durée de l'objet.
Le connecteur reste injectable avec un lookup en mémoire dans les tests.

Le flux est strictement :

`Export Kelio synthétique → Validation Kelio → Privacy Gate → Kelio Referential Lookup → Career Import → Career Reconstruction → Timeline / Evidence / Potential Rights`

Le connecteur n'importe jamais directement `CareerReconstructionEngine` et ne
connaît ni chemin JSON ni schéma physique.

## Statuts de résolution

- `RESOLVED` : compteur synthétique et compatible ;
- `RESOLVED_WITH_WARNINGS` : statut `draft` ou `to_verify`, revue humaine ;
- `UNKNOWN` : identifiant vide ou absent du catalogue ;
- `INCOMPATIBLE` : non synthétique, calcul activé, confidentialité privée,
  rejet ou statut non admis ;
- `LOOKUP_ERROR` : catalogue absent/invalide, ambiguïté ou erreur technique.

Seuls les deux premiers statuts sont utilisables. Tous les autres bloquent la
conversion avec un code déterministe sans fallback générique et sans recopier
la valeur brute.

Le schéma actuel ne définit pas de statut `disabled`. Si un tel statut est
ajouté ultérieurement sans adaptation explicite, il sera incompatible par
défaut.

## Compteurs et métadonnées

Les 17 compteurs couvrent les familles réellement présentes : repos, congés,
heures supplémentaires, astreinte, intervention, pointage, absence, travail
de nuit, dimanche et jour férié. Aucun compteur maladie distinct n'existe dans
la version auditée ; aucune correspondance n'est inventée.

Pour un compteur résolu, A5 projette uniquement : identifiant du référentiel,
identifiant canonique, catégorie, type de source, statut de résolution, type
de preuve, indicateur synthétique, interdiction de calcul et provenance. La
valeur brute reste inchangée dans l'export injecté et n'est jamais ajoutée à
la preuve Career Import.

## Anti-duplication et compatibilité

Aucune liste Python des 17 compteurs et aucun JSON concurrent ne sont créés.
Les catégories et identifiants viennent exclusivement du catalogue partagé.
Les méthodes publiques Kelio, les rapports, l'anonymisation, le Privacy Gate
A4, le pipeline A3, la fondation A2 et les frontières A1 sont conservés.
Nibelis et les autres connecteurs ne sont pas modifiés.

## Limites et hors périmètre

Le référentiel qualifie la métadonnée mais ne crée aucun droit, calcul de
retraite, calcul de pénibilité, point C2P ou exposition. A5 n'ajoute ni API,
réseau, authentification, OCR, PDF, stockage, fichier salarié réel, interface
utilisateur ou refonte des référentiels paie. Les rapprochements métier
sensibles et la normalisation transversale des rapports restent hors périmètre
et pourront être étudiés en A6.
