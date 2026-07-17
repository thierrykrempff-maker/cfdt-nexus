# ANACT — LOT 1 — Audit officiel limité des sources

## Trace d'audit

- Date : 17 juillet 2026.
- Environnement : requêtes HTTP GET/HEAD simples en lecture seule depuis l'environnement de développement.
- Domaine : exclusivement `www.anact.fr` et sa variante canonique sans `www`.
- Stockage : aucun HTML, PDF ou document téléchargé n'est conservé.
- Portée : onze points d'entrée HTTP ciblés et lecture limitée de `robots.txt` et d'un échantillon du sitemap.

## Résultats techniques confirmés

L'accueil répond `200 text/html`, en français, avec Drupal 10. `robots.txt` répond `200 text/plain`, fournit ETag et Last-Modified, et interdit notamment la recherche, les listes facettées et les variantes paginées par paramètres. Ces surfaces sont rejetées pour la découverte automatisée.

Le sitemap `/sitemap.xml` répond `200 text/xml`; il s'agit d'un `urlset` contenant `loc`, `lastmod`, `changefreq` et parfois `priority`. Il expose des slugs stables, la page `/themes`, la page `/regions`, des pages ARACT intégrées au domaine national et des ressources comme outils, autoformations, webinaires ou podcasts. Il est retenu comme meilleure surface future de découverte de métadonnées, sans transport dans ce lot.

Les pages `/themes`, `/regions`, `/grand-est`, `/mentions-legales`, `/politique-generale-de-protection-des-donnees-caractere-personnel` et `/accessibilite` répondent `200 text/html`. L'URL supposée `/reseau-anact-aract` répond `404` et n'est pas enregistrée.

## Mécanismes différés ou rejetés

API publique, RSS/Atom, JSON-LD, Open Graph, canonical HTML, Dublin Core et fichiers téléchargeables ne sont pas confirmés dans l'audit limité. Aucun endpoint correspondant n'est déclaré. La recherche interne et le crawl des variantes facettées/paginées sont rejetés conformément à `robots.txt`.

## Réseau ARACT

Le sitemap et les réponses ciblées montrent une représentation centralisée sur `anact.fr`, avec des slugs régionaux. Grand Est est confirmé par réponse HTTP; Centre-Val de Loire, Guadeloupe, Hauts-de-France, Île-de-France, Corse et La Réunion sont observés dans le sitemap. L'homogénéité complète et l'exhaustivité territoriale restent à vérifier; aucun connecteur régional distinct n'est créé.

## Mentions légales et prudence

Les pages légales, de protection des données et d'accessibilité existent. Leur présence ne suffit pas à établir un droit général de réutilisation. Aucun contenu juridique n'est interprété définitivement et aucune licence globale n'est déduite. La politique reste `DOCUMENT_SPECIFIC`, `METADATA_ONLY`, sans cache, texte intégral ni extrait, avec validation humaine obligatoire.

## Fraîcheur proposée

Actualités et événements : revalidation quotidienne. Publications : quatorze jours. Pages thématiques, guides, outils, dossiers, études, fiches et ressources régionales : trente jours. Données structurées non confirmées : revue manuelle à quatre-vingt-dix jours. Les prochains lots devront conserver première observation, dernière vérification, dates officielles, ETag, Last-Modified, empreinte, URL canonique et cycle actif/déplacé/supprimé/archivé.

## État final et recommandation LOT 2

Le connecteur reste désactivé, sans réseau opérationnel. Le LOT 2 proposé est un transport strictement limité au sitemap XML, en lecture seule, désactivé par défaut, respectant ETag/Last-Modified et ne produisant que des métadonnées. Il devra être précédé d'une validation humaine des conditions de réutilisation et ne devra ni suivre la recherche interne ni crawler les variantes interdites.
