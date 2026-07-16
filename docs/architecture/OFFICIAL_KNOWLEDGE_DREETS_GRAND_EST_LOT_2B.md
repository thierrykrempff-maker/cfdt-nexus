# Official Knowledge — DREETS Grand Est — LOT 2B

## Objet et périmètre

Le LOT 2B consigne une vérification officielle, limitée et non destructive des accès publics. Il ne crée ni transport réseau, ni connecteur actif, ni synchronisation, ni cache, ni index. La consultation a été limitée à `grand-est.dreets.gouv.fr` et à `dreets.gouv.fr`, domaine administratif directement référencé pour les mentions légales.

Le connecteur reste `enabled = false`, `connector_status = architecture_only` et protégé par `NETWORK_DISABLED_BY_DEFAULT`. Le contrat `DREETS_GRAND_EST_CONNECTOR_NETWORK_NOT_IMPLEMENTED` reste applicable.

## Journal synthétique de consultation

Date de revue : 16 juillet 2026. Dix-huit opérations logiques ont été effectuées par l'outil de consultation (recherches ciblées, ouvertures de pages HTML et suivi de liens officiels). Ce nombre ne prétend pas représenter les requêtes HTTP internes de l'outil, qui ne sont pas exposées.

Domaines consultés :

- `grand-est.dreets.gouv.fr` ;
- `dreets.gouv.fr` pour les mentions légales directement liées.

Aucun PDF n'a été téléchargé. Aucun POST, authentification, réseau social, domaine privé, service publicitaire ou outil d'analytics n'a été consulté. Aucun crawl, scraping ou téléchargement massif n'a été réalisé.

## Résultats de l'étude d'accès

- RSS : un lien officiel expose `spip.php?page=backend`. L'outil n'a pas pu valider sa charge ; il s'agit donc d'un candidat futur, pas d'un accès déclaré opérationnel.
- Atom : non identifié dans cette revue limitée.
- Sitemap : un plan du site HTML SPIP est publié via `spip.php?page=plan`. Aucun sitemap XML n'a été établi.
- API publique, OpenAPI, Swagger ou documentation développeur : non identifiés dans cette revue limitée. Cette formulation ne constitue pas une preuve d'inexistence.
- Pages ciblées : disponibles en HTML, structurées par rubriques et catégories, avec pagination sur les listes, titres et dates de publication ; une date de mise à jour apparaît sur certaines fiches.
- Auteur : non exposé de manière homogène au niveau des articles. Les mentions légales identifient l'éditeur et le directeur de publication, sans permettre d'attribuer automatiquement chaque document à un auteur individuel.
- Canonical : non vérifiable avec l'outil de rendu utilisé ; aucune assertion n'est enregistrée.
- PDF : seuls URL, titre présenté, date éventuelle, famille et type documentaire sont conservés dans l'échantillon. Aucun contenu n'est stocké.

## Mentions légales et politique documentaire

Les mentions légales distinguent les documents officiels (notamment discours, communiqués et textes réglementaires ou législatifs), librement reproductibles avec bonne pratique d'identification claire de l'auteur, de la source et du lien original, des autres contenus éditoriaux protégés, dont la reproduction requiert l'accord de l'auteur et l'indication de la source.

Cette distinction impose une politique par catégorie de document, appliquée en échec fermé :

- indexation `METADATA_ONLY` ;
- aucun cache ;
- aucun texte intégral ;
- aucun extrait conservé ;
- provenance et citation obligatoires ;
- revue de licence spécifique avant toute extension de droits.

Le LOT 2B n'accorde donc aucun droit technique supplémentaire, même lorsqu'une réutilisation pourrait être juridiquement permise après qualification du document.

## Comparaison des architectures

| Mode | Avantages | Limites et conformité | Recommandation |
|---|---|---|---|
| API | Modèle structuré potentiel | Aucun accès officiel identifié ; stabilité et licence inconnues | Non retenu |
| RSS | Découverte légère, dates et liens potentiellement stables | Charge non validée et politique à confirmer | Candidat après validation explicite |
| Sitemap | Découverte large possible | Seul un plan HTML a été observé, aucun XML établi | Ne pas utiliser comme ingestion |
| Pages ciblées | Citation directe, structure et métadonnées observables | Maintenance sélective ; classification juridique par document | Architecture actuelle recommandée, métadonnées seules |
| Ingestion manuelle | Validation humaine forte | Coût de maintenance élevé | Repli exceptionnel avec revue juridique |

La recommandation est donc : pages ciblées et métadonnées seules ; RSS comme candidat de découverte uniquement après validation technique et documentaire ; ingestion manuelle comme repli. La fréquence proposée est une revue manuelle hebdomadaire, sans planificateur ni synchronisation dans ce lot.

## Échantillon minimal

L'échantillon couvre les familles relations collectives, inspection du travail, santé au travail, CSE et dialogue social en Moselle. Il ne contient que l'URL officielle, le titre, la date lorsqu'elle est explicitement disponible, la famille et le type. Il ne contient ni texte, ni résumé, ni chemin local, ni donnée personnelle.

## Limites et préparation éventuelle

La validité technique du RSS, l'existence d'un sitemap XML, les balises canonical, la licence applicable à chaque document et la stabilité des gabarits restent à confirmer avant tout développement ultérieur. Aucun LOT suivant n'est engagé par cette étude.
