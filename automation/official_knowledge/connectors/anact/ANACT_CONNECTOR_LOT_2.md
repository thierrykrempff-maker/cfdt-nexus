# ANACT — LOT 2 — Transport sitemap XML limité

## Objectif et source

Le LOT 2 implémente un transport HTTPS en lecture seule, strictement limité au sitemap officiel audité `https://www.anact.fr/sitemap.xml`. Il produit uniquement des métadonnées candidates et ne suit aucune URL découverte.

## Invariants et activation

Le connecteur reste `enabled = false`, `architecture_only`, `HealthStatus.DISABLED`, `METADATA_ONLY` et `DOCUMENT_SPECIFIC`. Le transport est implémenté mais désactivé par défaut. Son usage exige une construction explicite avec `SitemapTransportConfig(enabled=True)` et un appel manuel `inspect_sitemap`. Cette opération n'est ni une synchronisation ni une activation du connecteur.

## Sécurité réseau

HTTPS est obligatoire. Seuls `www.anact.fr` et sa variante sans `www` sont acceptés. Les identifiants intégrés, redirections externes, requêtes avec paramètres, routes de recherche, facettes, pagination et extensions téléchargeables sont refusés. Le client utilise un User-Agent identifiable, aucun cookie, secret ou authentification, un délai explicite, deux redirections au maximum et une réponse limitée à deux mégaoctets.

Les statuts 200 et 304 sont supportés. Les accès refusés, absences, limitations 429, erreurs 5xx, timeouts, erreurs TLS, types MIME inattendus, réponses trop volumineuses et XML mal formés produisent des statuts ou erreurs structurés. Les diagnostics ne conservent jamais le corps XML.

## Requêtes conditionnelles et parsing

ETag/If-None-Match et Last-Modified/If-Modified-Since sont pris en charge par un état injecté, sans cache persistant. Le parseur hors réseau accepte `urlset` et `sitemapindex`, namespaces standards, `loc`, `lastmod`, `changefreq` et balises inconnues. Il refuse DTD et entités, limite les URL, sous-sitemaps, profondeur et taille, et ne suit jamais récursivement un index.

Chaque candidat conserve URL brute, URL normalisée, domaine, chemin, type d'entrée, dates brutes et normalisées, fréquence, famille pressentie par règle explicite, portée et ARACT lorsqu'elles sont établies, dates d'observation, source sitemap, ETag, Last-Modified, décision, motif de rejet et empreinte. Aucun titre, auteur, résumé, licence précise ou type documentaire n'est inventé; `fulltext` reste `None`.

## Robots, limites et exclusions

La politique LOT 1 est codée de façon déclarative. Recherche, facettes et pagination interdites restent refusées. En cas d'ambiguïté, l'URL est rejetée. Le LOT 2 ne récupère aucun HTML ou PDF, n'extrait aucun texte, n'indexe rien, n'alimente aucun moteur d'expertise et ne constitue pas un crawler.

## Tests et risques

Les tests injectent des réponses synthétiques et n'utilisent aucun réseau. Une sonde réelle facultative peut être déclenchée séparément contre le seul sitemap, sans suivre les URL ni conserver le XML. Les risques restants concernent les changements de MIME, taille, structure sitemap, règles robots, disponibilité et conditions de réutilisation.

## Proposition LOT 3

Le LOT 3 pourra classer déterministement les URL candidates et créer une file de validation humaine, sans récupérer le texte intégral. Il devra conserver les décisions, motifs, versions de règles et provenance.
