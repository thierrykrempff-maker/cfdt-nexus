# LOT R0 — Architecture du moteur de raisonnement syndical

## Principe

Le moteur est une couche de raisonnement déterministe et non décisionnelle. Il
ne recherche aucun document, n'exécute aucun moteur métier et ne remplace ni le
routeur ni les experts. Il assemble des faits et métadonnées déjà disponibles.

```text
Question / payload historique
            |
            v
Pont Runtime optionnel (désactivé par défaut)
            |
            v
SyndicalCaseInput
            |
            v
Protocole observable en 18 étapes
  |         |          |          |
  v         v          v          v
Sources   Prudence   Stratégies   Contradictions
  \         |          |          /
            v
SyndicalReasoningReport
     |                 |
     v                 v
Vue courte        Vue experte
```

## Frontières

`SYNDICAL_REASONING_ENGINE` ne dépend d'aucun expert, connecteur, corpus,
Runtime ou composant d'interface. Le Runtime dépend du moteur, jamais
l'inverse.

Le moteur ne reçoit que :

- faits catégorisés ;
- métadonnées de pièces ;
- métadonnées de sources ;
- contexte, urgence et confidentialité ;
- informations manquantes.

Il ne reçoit ni PDF, ni HTML, ni chunk, ni contenu complet.

## Contrats

- `SyndicalCaseInput` : dossier incomplet accepté par conception ;
- `CaseFact` : fait déclaré, établi ou hypothèse ;
- `SourceReference` : source metadata-only, vérifiée ou non ;
- `ActionOption` : option graduée, risques et prérequis ;
- `SyndicalReasoningReport` : rapport complet avec deux projections.

Tous les contrats publics sont des dataclasses immuables.

## Protocole

Les 18 étapes sont définies dans un Enum ordonné et sont restituées dans chaque
rapport. Le moteur sépare les catégories de faits, détecte les domaines,
hiérarchise les seules sources fournies, signale les contradictions explicites,
évalue la confiance, construit des options graduées et conclut avec prudence.

## Hiérarchie des sources

La politique attribue un rang de base, puis applique des ajustements
observables selon :

- pertinence au domaine ;
- vérification de la source ;
- caractère interne ;
- nécessité d'une comparaison aux normes supérieures ;
- portée factuelle de la jurisprudence.

Aucune source absente n'est créée. Toute source non vérifiée est signalée.

## Runtime

Le pont `RuntimeSyndicalReasoningIntegration` :

1. vérifie le feature flag ;
2. réutilise domaines et intentions du routeur ;
3. pseudonymise les identités techniques de sources ;
4. ne conserve que les URLs HTTPS et métadonnées ;
5. construit le contrat d'entrée ;
6. appelle le moteur ;
7. renvoie un diagnostic à codes stables ;
8. bascule en fallback sans modifier le rapport historique.

Feature flag :

`NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED`

Valeur par défaut : désactivée.

## Confidentialité

- aucun document réel dans Git ;
- fixtures entièrement synthétiques ;
- aucune valeur personnelle dans les diagnostics ;
- aucun accès réseau ;
- aucun chemin local dans les vues ;
- citations limitées aux métadonnées publiques ;
- les pièces internes ne sont représentées que par leur titre et leur type.

## Limites R0

- aucune décision juridique automatique ;
- aucune recherche documentaire ;
- aucune génération de courrier final ;
- aucune extraction de document ;
- aucune règle paie ou retraite ;
- contradictions uniquement lorsqu'elles sont explicitement décrites par les
  métadonnées ;
- qualification volontairement provisoire.
