# Implémentation R1D

## Architecture

`DiscriminationHarassmentReasoningEngine` compose le moteur R0 et des composants déterministes dédiés : chronologie, comparateurs, questions, preuves, argumentation, articulation et stratégies. Les modèles sont des dataclasses gelées et sérialisables.

## Analyse

- La chronologie conserve la nature déclarée, établie ou hypothétique des éléments.
- Les qualifications sont toujours des hypothèses concurrentes.
- Les critères protégés et mesures défavorables sont détectés séparément.
- Le lien causal n'est jamais inféré automatiquement.
- Les comparateurs explicitent similitudes, différences objectives, données manquantes et explications alternatives.
- Les questions sont classées en quatre niveaux et évitent les pièces déjà disponibles.
- Les preuves sont classées en indispensables, utiles et complémentaires, avec limites et règle d'obtention licite.
- Les positions salarié et employeur sont produites séparément.

## Urgence et protection

Une menace, une violence imminente ou un risque suicidaire explicitement déclaré déclenche une urgence immédiate. Le moteur recommande alors une mise en sécurité et une orientation vers les professionnels ou secours compétents, sans diagnostic et sans retarder la protection par une analyse juridique ordinaire.

Les stratégies couvrent : sécurisation, documentation, protection interne, action collective ou institutionnelle, puis recours.

## Articulation

- R1D est principal lorsque les indices de harcèlement, discrimination ou égalité structurent la demande.
- R1B reste principal pour une sanction postérieure à un signalement, avec R1D complémentaire.
- R1A reste principal pour une mutation ou un retrait de fonctions d'un représentant, avec R1D complémentaire.
- R1C reste principal pour une différence d'horaires sans indice R1D suffisant.
- R1D peut conserver R1A, R1B et R1C comme domaines complémentaires sans modifier leurs conclusions.

## Runtime et confidentialité

Le feature flag existant est conservé. Toute erreur R1D produit le fallback technique existant. Un conflit isolé ne suffit pas à activer R1D. Les sorties ne contiennent ni document réel, ni contenu intégral, ni chemin local, ni donnée médicale, personnelle ou syndicale réelle.

## Limites

R1D ne déclare jamais un harcèlement ou une discrimination établi, ne remplace pas une enquête, ne tranche pas un litige, ne réalise aucun calcul de rémunération et ne fournit aucun diagnostic médical.
