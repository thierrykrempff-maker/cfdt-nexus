# Implémentation R1E

## Architecture

`HealthAbsenceReasoningEngine` produit une projection immuable au-dessus du rapport R0. Des modules séparés portent les modèles, acteurs, chronologie, comparaisons, questions, preuves, stratégies, articulation et scénarios.

## Couverture

Le moteur couvre les absences maladie, AT/MP et trajet déclarés, instruction CPAM, IJSS, subrogation, maintien, prévoyance, mutuelle, portabilité, reprise, visites, temps partiel thérapeutique, aménagement, restrictions déclarées, inaptitude, reclassement, congés familiaux et incidences potentielles sur paie, congés et ancienneté.

Les qualifications utilisent exclusivement des formulations prudentes : reconnaissance en attente, droit potentiel, traitement à vérifier, anomalie apparente, régularisation possible ou données insuffisantes.

## Acteurs et documents

La CPAM, le médecin du travail, l'employeur, les RH, la paie, la prévoyance, la mutuelle, l'URSSAF, Agirc-Arrco, le CSE, le conseil juridique et le représentant syndical conservent des responsabilités distinctes.

Les comparaisons restent metadata-only et ne concluent ni à une erreur de paie ni à une violation. Les preuves indiquent leur fournisseur, leur limite et leur niveau de confidentialité.

## Articulation et Runtime

- R1B reste principal pour une sanction liée à une absence.
- R1D reste principal pour un harcèlement accompagné d'un arrêt.
- R1A peut rester principal pour une modification isolée du poste.
- R1E est principal pour l'arrêt, l'indemnisation potentielle, la reprise, l'inaptitude, le reclassement ou la protection sociale.
- R1A, R1C et R1D peuvent être complémentaires.

Le feature flag existant et le fallback technique sont conservés. Le mot « maladie » sans contexte professionnel ne suffit pas à activer R1E.

## Limites

R1E ne remplace aucun organisme, professionnel médical ou juriste. Il ne conserve aucun détail médical, ne calcule aucun montant et ne promet aucune reconnaissance ou garantie.
