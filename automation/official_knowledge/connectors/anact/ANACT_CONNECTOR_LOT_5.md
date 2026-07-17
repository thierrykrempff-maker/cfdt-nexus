# ANACT — LOT 5 — Catalogue documentaire de métadonnées

## Architecture

Le LOT 5 construit un catalogue strictement en mémoire à partir d'une classification LOT 3 validée et de métadonnées LOT 4 cohérentes. Il ne déclenche aucun transport et ne connaît ni HTML, ni PDF, ni contenu intégral. `InMemoryAnactDocumentCatalog` assure l'identité, la déduplication, le cycle de vie, les versions, la recherche structurée et l'export vers des modèles internes immuables.

## Modèle documentaire

Chaque `CatalogDocument` contient un identifiant stable dérivé de l'URL canonique, URL demandée, canonical, alias de redirection, catégorie, région, langue, titre et description facultatifs, dates explicites, MIME, ETag, Last-Modified, confiance, décisions de validation, source sitemap et version du classificateur. `METADATA_ONLY` et `DOCUMENT_SPECIFIC` sont conservés. Aucun champ de texte intégral n'existe.

## Déduplication et versionnement

La canonical, l'URL finale et l'URL demandée forment l'ensemble d'alias. Toute correspondance rattache la ressource au même identifiant. Les empreintes Connector Platform excluent les dates techniques de collecte et couvrent uniquement les métadonnées normalisées.

Une empreinte de version associe métadonnées et état `active` ou `disappeared`. Le catalogue produit `new`, `modified`, `unchanged` ou `disappeared`, puis utilise `DocumentVersion` et `changed` de Connector Platform. Une réconciliation vide marque les ressources actives comme disparues sans les supprimer ni récupérer leur contenu.

## Recherche et export

La recherche locale filtre catégorie, région, langue, cycle de vie, décision, validation humaine et dates, ou cherche un terme dans le titre et la description seulement. Aucun autre champ et aucun contenu de page ne sont parcourus. L'export retourne un `CatalogExport` composé de modèles internes triés et de leurs versions ; aucun fichier, JSON ou base de données n'est produit.

## Limites et LOT 6 proposé

Le catalogue dépend de métadonnées déjà validées et ne déduit aucune information absente. Il ne résout pas de conflit éditorial et n'automatise pas la validation humaine. Un LOT 6 pourrait ajouter un journal Connector Platform des changements de métadonnées et une politique de rétention/export explicitement autorisée, toujours sans corpus intégral ni moteur d'expertise.
