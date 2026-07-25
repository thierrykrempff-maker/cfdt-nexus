# Architecture UI1 — Portail métier CFDT Nexus

## Structure

Le portail comporte quatre espaces : Questions salariés, CSE, Négociations et accords, Paie et rémunération. Quatre accès secondaires préparent la recherche documentaire, les dossiers, l’historique de session et les modèles.

L’identité d’en-tête utilise le logo CFDT INEOS Sarralbe servi localement depuis `apps/nexus-local-interface/assets/`. Ses proportions sont conservées avec une hauteur automatique et une largeur maximale responsive.

## Navigation

Chaque carte ouvre un assistant en cinq étapes : besoin, description, repères, documents et résultat souhaité. La navigation est réversible et le retour à l’accueil n’entraîne aucune persistance.

## Contrat Assistant Final

`buildStructuredRequest()` produit `query`, `source_limit` et `portal_context`. Le contexte contient l’espace, la situation, les faits, les documents, la période, l’urgence, le résultat, le mode, les moteurs autorisés et la confidentialité. Le routeur et l’Assistant Final restent seuls responsables de la qualification et du routage.

## Modes

Les modes QUICK, CASE et EXPERT sont présentés avec CASE par défaut. Le mode EXPERT déplie les détails disponibles ; les autres modes privilégient une restitution métier.

## Résultat

La page hiérarchise résumé, domaines, confiance, position, éléments manquants, questions, sources, arguments, risques et plan d’action. Les sorties brutes ne sont jamais affichées par défaut.

## Feature flags et compatibilité

Les flags Assistant Final et Expert Paie V2 restent désactivés par défaut. Le portail ne peut pas les activer. En mode désactivé, `/api/analyze` conserve le comportement historique et l’interface l’indique sans exposer le nom technique du flag.

## Confidentialité

Pas de stockage local, d’analytics, de nouvel appel réseau ou de journalisation front-end. Les consignes d’anonymisation sont visibles et le CSP limite les ressources à l’origine locale.

## Accessibilité et responsive

Landmarks, hiérarchie de titres, labels, zones live, alertes, navigation clavier, focus visible et réduction des animations sont prévus. La grille passe de quatre à deux puis une colonne.

## Limites

Les dossiers et l’historique persistant ne sont pas implémentés. La recherche et les modèles utilisent les capacités déjà disponibles au travers d’une analyse guidée.
