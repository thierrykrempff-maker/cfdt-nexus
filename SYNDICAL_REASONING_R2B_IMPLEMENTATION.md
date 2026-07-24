# Implémentation R2B — Fonctionnement, réunions et avis du CSE

## Architecture et modèles

R2B comprend des modèles immuables, une politique centrale, un moteur déterministe
et dix-huit scénarios synthétiques. Il décrit réunion, ordre du jour, convocation,
documents, questions, réponses, avis, réserves, résolution, vote, PV, engagement,
échéance et chronologie.

## Rôles

La politique distingue président, secrétaire, trésorier par le cadre commun du
CSE, titulaires, suppléants, représentants syndicaux, délégués syndicaux,
commissions, représentants de proximité, direction/RH, experts, inspection,
service juridique et salarié demandeur. Les droits de proposer, décider, voter,
recevoir l'information et relancer restent explicites.

## Ordre du jour, convocation et documents

Le moteur produit une formulation structurée mais non certifiée : intitulé,
contexte, questions, documents, résultat attendu, échéance et suivi. Les
convocations et documents sont qualifiés sans conclusion d'irrégularité.

## Délais et questions

Chaque délai conserve point de départ, événement déclencheur, source, incertitude,
urgence et action. `legally_calculated` reste toujours faux. Les questions sont
factuelles, procédurales, d'impact ou de suivi, hiérarchisées et non redondantes.

## Avis, réserves et résolutions

Plusieurs trames d'avis sont proposées sans décider à la place des élus. Les
réserves relient fait, information manquante, risque, demande et suivi. Les
résolutions sont des projets dont la validité et les règles de vote restent à
confirmer.

## PV, engagements et historique

La frontière `CSEHistoryLookup` accepte exclusivement titre, date, instance,
thème, point, indicateurs de réponse/engagement, échéance et occurrence. Aucun
identifiant interne ni contenu n'est exposé. Tout engagement reste à confirmer
dans le document source.

## Stratégies et articulation

Cinq niveaux couvrent préparation, demande formelle, action en réunion, suivi et
appui extérieur. R2A reste principal pour une réorganisation ; R2B complète la
préparation de la réunion. R1A à R1E conservent leurs responsabilités.

## Runtime, confidentialité et limites

Le feature flag existant, l'activation contextuelle et le fallback R0 sont
conservés. Une réunion non CSE n'active pas R2B. Les fixtures sont anonymes,
synthétiques et metadata-only. Aucun réseau, document réel, expertise complète,
droit d'alerte complet ou raisonnement CSSCT n'est ajouté.
