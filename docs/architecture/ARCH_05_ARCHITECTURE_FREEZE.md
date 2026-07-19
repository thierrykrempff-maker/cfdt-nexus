# ARCH-05 — Validation finale et gel de l’architecture

## Décision

L’architecture ARCH-01 à ARCH-04 est désormais considérée comme stable.

Toute évolution future doit s’appuyer sur cette architecture sans modifier les contrats fondamentaux, sauf correction de bug exceptionnelle.

ARCH-05 clôt les lots d’architecture commune. Il n’ajoute aucune fonctionnalité métier, ne migre aucun consommateur historique et ne crée aucun connecteur ou endpoint. Son rôle est de rendre les frontières vérifiables, de publier un rapport déterministe et de formaliser les règles qui s’appliquent aux développements futurs.

## Architecture finale

| Couche | Module | Responsabilité | Dépendances ARCH autorisées |
|---|---|---|---|
| ARCH-01 | `automation.contracts` | Requêtes, rapports, sources, preuves et vocabulaires communs | aucune |
| ARCH-02 | `automation.adapters` | Conversion explicite entre contrats communs et formats historiques | ARCH-01 |
| ARCH-03 | `automation.expert_facades` | Façades stables et registre explicite des experts | ARCH-01, ARCH-02 |
| ARCH-04 | `automation.orchestrator_common` | Sélection, exécution isolée et agrégation technique | ARCH-01, ARCH-03 |
| ARCH-05 | `automation.architecture_validation` | Validation statique et rapport de stabilité | analyse les couches sans participer au flux métier |

Le flux commun stable est : `ExpertRequest` → sélection déterministe → `ExpertFacade` → `ExpertReport` → agrégation technique → `OrchestrationResult`. Les raisonnements, sources, preuves et désaccords demeurent la responsabilité de chaque expert.

## Frontières obligatoires

Les dépendances entre couches suivent uniquement le sens du tableau. Toute dépendance inverse est interdite. En particulier :

- ARCH-01 ne connaît aucune couche ultérieure ;
- ARCH-02 ne connaît ni façades ni orchestrateur ;
- ARCH-03 ne connaît pas l’orchestrateur commun ;
- ARCH-04 ne contourne jamais les façades pour appeler directement un moteur historique ;
- les experts historiques ne dépendent pas directement des modules ARCH ;
- les couches ARCH ne dépendent ni des connecteurs, ni des endpoints, ni d’un client réseau ;
- les cycles d’import entre modules ARCH sont interdits.

Les tests sont exclus de l’analyse de production afin que leurs fixtures et bibliothèques de test ne deviennent pas de fausses dépendances d’exécution.

## Validation publique

`validate_architecture()` analyse les fichiers Python par leur arbre syntaxique, sans importer les moteurs métier et sans accès réseau. Il retourne un `ArchitectureReport` contenant :

- la validité globale ;
- les modules présents et manquants ;
- la conformité des dépendances ;
- la conformité des frontières ;
- une liste triée de violations sûres et structurées.

Le rapport ne dépend ni de l’heure, ni du système d’exploitation, ni d’un identifiant aléatoire. Pour un même arbre source, son dictionnaire sérialisable est identique.

## Règles pour les développements futurs

1. Réutiliser `ExpertRequest` et `ExpertReport`; ne pas créer de contrats métier concurrents.
2. Adapter un moteur historique à la frontière ARCH-02, puis l’exposer uniquement par une façade ARCH-03.
3. Enregistrer explicitement la façade avec son statut; ne pas ajouter de routage sémantique au registre.
4. Faire exécuter les experts communs par ARCH-04; ne pas brancher un endpoint directement sur un moteur.
5. Conserver l’isolation des erreurs, l’immuabilité des contrats et le déterminisme.
6. Ajouter des tests de frontière à toute extension et maintenir le rapport ARCH-05 valide.
7. Une modification d’un contrat fondamental exige une correction de bug exceptionnelle, documentée, compatible et revue comme une évolution d’architecture.

## Migration des futurs moteurs

La migration reste progressive : caractériser le comportement historique, définir la conversion ARCH-02, construire la façade ARCH-03, valider les rapports ARCH-01, déclarer le statut dans le registre, puis intégrer explicitement l’exécution ARCH-04. Le moteur historique reste isolé derrière sa façade pendant la transition. Une migration ne doit ni déplacer sa logique métier dans l’orchestrateur ni imposer une dépendance inverse vers ARCH.

## Stratégie des futurs connecteurs

Les connecteurs officiels constituent une couche d’infrastructure séparée. Ils doivent appliquer leurs propres politiques de sécurité, licence, preuve de consultation, cache et échec. Leurs résultats sont transformés en contrats de sources ARCH-01 à une frontière dédiée; ils ne sont jamais appelés directement depuis ARCH-01 à ARCH-04. La future sélection des sources précède la sélection des experts et reste séparée du raisonnement métier.

## Politique de stabilité

Les API publiques d’ARCH-01 à ARCH-04 sont la base stable des futurs développements. Les ajouts compatibles sont préférés aux modifications. Les consommateurs migrent progressivement et explicitement. Toute exception doit identifier le bug, mesurer la compatibilité, prévoir les tests de non-régression et documenter la décision. Le gel n’interdit pas les corrections : il interdit les contournements silencieux et les changements de contrat non maîtrisés.

## Limites

Le validateur est statique : il contrôle les imports Python explicites et les primitives réseau reconnaissables, mais ne remplace ni les tests d’intégration ni une analyse de sécurité générale. Il ne juge aucune conclusion métier. Les anomalies historiques de tests déjà qualifiées restent hors du périmètre d’ARCH-05.
