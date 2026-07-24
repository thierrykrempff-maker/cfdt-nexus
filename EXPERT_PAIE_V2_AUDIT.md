# Audit Expert Paie V2

## Cartographie existante

Le parcours historique relie l'entrée utilisateur à `automation.experts.paie`,
au sélecteur de règles, au validateur du catalogue, aux référentiels
synthétiques Kelio/Nibelis/paramètres, au graphe de connaissances et au
protocole de raisonnement. Le Runtime transforme ensuite le rapport historique
via Payroll Adapter et Common Expert Orchestrator.

La chaîne auditée est :

1. entrée utilisateur ;
2. événement métier identifié par le moteur historique ou R1C/R1E ;
3. données temps et planning ;
4. données paie synthétiques ;
5. sélection explicable des règles ;
6. validation bloquante ;
7. comparaisons planning/Kelio/Nibelis ;
8. calcul autorisé ou refusé ;
9. explication salarié et expert ;
10. restitution structurée ;
11. articulation avec R1C, R1E et R2C.

## Composants réutilisables

- catalogue INEOS et son schéma ;
- sélecteur et validateur de règles ;
- référentiels synthétiques Kelio, Nibelis et paramètres ;
- graphe de connaissance paie ;
- protocole de raisonnement ;
- façade et adaptateur paie historiques ;
- politiques de confidentialité ;
- articulations R1C et R1E.

## Risques maîtrisés

- confusion détection/calcul : phases explicites ;
- règle hors contexte : correspondance par type d'événement et hiérarchie ;
- règle `to_verify` ou inactive : refus bloquant ;
- calcul interdit : contrôle de `calculation_allowed` ;
- valeur inventée : variables obligatoires et provenance ;
- flottants monétaires : usage exclusif de `Decimal` ;
- erreur silencieuse : refus et explications alternatives ;
- données personnelles : fixtures synthétiques et Runtime séparé.

## Limites

Le moteur ne transforme aucun référentiel non autorisé en moteur de calcul. Les
résultats restent synthétiques et soumis à validation humaine. Les événements
insuffisamment modélisés sont signalés sans résultat inventé.
