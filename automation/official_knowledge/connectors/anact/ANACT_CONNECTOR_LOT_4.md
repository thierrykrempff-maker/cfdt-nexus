# ANACT — LOT 4 — Lecture bornée des métadonnées de pages

## Objectif

Le LOT 4 permet une requête HTTP explicite vers une seule page préalablement validée par le LOT 3. Il réutilise l'adaptateur HTTPS, les limites, les redirections contrôlées, les erreurs et l'état conditionnel du transport sitemap. Le connecteur et ce nouveau transport restent désactivés par défaut.

## Métadonnées prises en charge

Le résultat peut contenir, uniquement lorsqu'ils sont explicitement présents : URL finale et canonique, `<title>`, meta description, langue HTML, dates de publication et de modification, type explicite, propriétés Open Graph autorisées, sous-ensemble sûr de JSON-LD, ETag, Last-Modified, type MIME et longueur de réponse.

Le JSON-LD est réduit à `@type`, nom ou titre, description, URL et dates. Un éventuel `articleBody`, les scripts et le corps de page ne sont jamais retournés. La canonical externe ou interdite est ignorée avec un avertissement.

## Validation et sécurité

Une classification `auto_accepted` est directement admissible. Une classification ambiguë ou non classée exige un statut humain `accepted`. Une URL rejetée reste interdite. Chaque appel effectue au plus une lecture de page, sans parcours, recherche, pagination ni suivi de liens. HTTPS, domaines ANACT, politique robots, délai, redirections et taille maximale restent imposés. Les PDF et autres documents téléchargeables sont refusés.

Le transport accepte `text/html` et `application/xhtml+xml`, gère 304, 403, 404, 429 et 5xx, et conserve les validateurs conditionnels. Le HTML n'est présent qu'en mémoire le temps du parsing et n'est ni retourné, ni journalisé, ni écrit.

## Limites et exclusions

Le parseur ne déduit rien d'un contenu éditorial et n'extrait pas le corps de l'article. Il ne garantit pas de réparer un HTML invalide. Sont exclus : PDF, texte intégral, résumé généré, indexation, embeddings, cache persistant, scheduler, crawler, moteur métier et activation automatique.

## LOT 5 proposé

Un LOT 5 pourrait normaliser et comparer les versions des seules métadonnées validées, avec journal local d'évolution, règles de rétention et validation humaine préalable, sans stockage de contenu intégral.
