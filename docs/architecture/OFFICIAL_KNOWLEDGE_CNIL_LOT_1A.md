# Connecteur CNIL — LOT 1A — étude d’accès et contrat

Date de vérification : 16 juillet 2026. Décision : **conditional_go** pour un futur prototype, sans activation réseau.

## Sources officielles consultées

- CNIL, [mentions légales et réutilisation](https://www.cnil.fr/fr/mentions-legales) ;
- CNIL, [recherche](https://www.cnil.fr/fr/recherche) et [actualités](https://www.cnil.fr/fr/actualite) ;
- data.gouv.fr, [organisation CNIL et jeux de données](https://www.data.gouv.fr/organizations/cnil/datasets) ;
- Légifrance, [collection des délibérations CNIL](https://www.legifrance.gouv.fr/cnil/).

Aucun contenu de ces pages n’est copié dans le dépôt. La consultation a été manuelle et limitée.

## Accès confirmés

Le site CNIL expose des pages HTML ciblées, une recherche distinguant articles et délibérations avec filtre particulier/professionnel, des pages thématiques dont « Travail », des catalogues de ressources téléchargeables et une liste d’actualités paginée. Ces éléments permettent d’envisager une découverte à faible profondeur, par liste blanche.

L’organisation CNIL sur data.gouv.fr publie 16 jeux de données au jour de l’étude. La page indique zéro API rattachée à l’organisation ; elle ne démontre donc pas une API de contenu CNIL. Les formats et calendriers sont propres à chaque jeu.

Les mentions légales CNIL précisent que seules les délibérations adoptées en séance plénière et publiées sur Légifrance engagent la CNIL. Légifrance doit donc être la source canonique des délibérations, via un contrat futur séparé.

## Accès non confirmés

Aucune documentation officielle explicite d’une API publique de recherche ou de contenu CNIL n’a été trouvée. RSS/Atom, sitemap exploitable, ETag, Last-Modified et contraintes détaillées de `robots.txt` restent non confirmés. Ils devront être revérifiés avant tout transport. Aucune URL d’API supposée n’est enregistrée.

## Licences et restrictions

Sauf mention particulière, les textes et articles de cnil.fr sont sous CC BY-ND 4.0 FR : attribution, lien vers la licence et date d’extraction obligatoires, sans modification. Les images et vidéos appartenant exclusivement à la CNIL sont annoncées sous CC BY-NC-ND 4.0 FR, sous réserve des droits de tiers. Elles sont hors stockage intégral initial.

Les données ouvertes CNIL sont annoncées par défaut sous Licence Ouverte, avec attribution. Chaque jeu data.gouv.fr nécessite néanmoins une revue individuelle de licence, de schéma et de présence éventuelle de données personnelles.

Pour fiches, actualités, FAQ, guides, rapports et PDF, la copie intégrale en cache, l’extraction transformatrice et la conservation d’extraits restent `pending` jusqu’à validation juridique de la clause ND et des mentions particulières. Les délibérations suivent les conditions de Légifrance. Aucune catégorie `pending`, `restricted` ou `prohibited` n’est indexable.

## Périmètre fonctionnel

Priorité haute : surveillance, vidéosurveillance, géolocalisation, badgeuses et temps de travail, biométrie, messagerie et outils professionnels, droit d’accès, dossiers du personnel, santé, données syndicales, télétravail, IA au travail, cybersécurité et violations, recrutement et conservation.

Priorité moyenne : questionnaires, photos et annuaires, sous-traitance et transferts. Les services transactionnels, formulaires, espaces authentifiés, annuaires de personnes et données personnelles inutiles sont refusés.

## Architecture proposée

Le futur connecteur sépare découverte, récupération, validation, extraction, provenance, licence, cache, synchronisation et rejet. Le modèle porte type, URI canonique, dates, thèmes, audience, autorité, licence, format, empreinte, provenance et décision d’indexabilité.

La sélection impose domaine, préfixe de chemin, type, thème, MIME, taille maximale de 5 Mo, français et profondeur un. Images et vidéos ne sont jamais stockées intégralement.

Les interfaces prévues sont `discover_resources`, `fetch_resource`, `validate_resource` et `parse_resource`. Dans ce lot, chacune lève `CNIL_CONNECTOR_NETWORK_NOT_IMPLEMENTED`; `NETWORK_DISABLED_BY_DEFAULT` demeure inchangé.

## Risques et décision

Décision `conditional_go` : les voies HTML ciblées, data.gouv.fr et Légifrance sont techniquement identifiées, mais le connecteur réel reste bloqué par la revue juridique de CC BY-ND, la politique de cache/extraits, la validation individuelle des jeux ouverts et la vérification de `robots.txt` et des mécanismes HTTP.

Avant activation : approbation juridique documentée, sélection finale des chemins, quotas prudents, revue robots/conditions, tests de redirections et d’en-têtes, autorisation explicite du réseau et lot d’implémentation distinct. La source CNIL reste `enabled = false` et `architecture_only`.
