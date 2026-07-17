# ANACT — LOT 3 — Classification déterministe des URL

## Objectif et périmètre

Le LOT 3 classe hors réseau les métadonnées `SitemapCandidate` produites par le LOT 2. Il ne relit pas le sitemap, ne suit aucune URL et ne conserve ni page, ni PDF, ni texte intégral. Le traitement des 3 466 candidats observés peut être réalisé en mémoire à partir du résultat explicitement fourni par le LOT 2 ; aucun corpus distant n'est enregistré.

## Règles

Le jeu `anact-url-rules-v1` utilise uniquement le domaine, le chemin, les segments, le registre ARACT et les familles explicites du catalogue. Les règles sont ordonnées par priorité croissante : politique URL/robots, registre régional, chemins spécifiques, pages institutionnelles, puis indices de slug. Une règle spécifique précède toujours une règle générique. Deux règles de même priorité et de catégories différentes imposent une revue humaine.

Catégories : page thématique, publication, guide, outil, étude, dossier, fiche pratique, actualité, événement, page régionale ARACT, page institutionnelle, page légale et ressource inconnue.

Les chemins certains produisent `auto_accepted` avec une confiance `high` ou `very_high`. Un indice de slug produit `human_review_required` avec une confiance `medium`. Une URL sans règle fiable reste `unclassified`; une URL invalide, externe ou interdite devient `rejected`.

Chaque résultat conserve l'URL brute et normalisée, la catégorie, la confiance, la règle et sa version, la justification, la région certaine, le motif de rejet, l'empreinte stable et le statut de validation humaine. Aucun titre, auteur, résumé, date de publication, licence précise ou type documentaire réel n'est déduit.

## File de validation

`AnactReviewQueue` est une structure en mémoire contenant uniquement ces métadonnées. Elle déduplique par empreinte, trie par priorité, filtre par catégorie, région et statut, et enregistre explicitement acceptation, rejet ou demande de nouvelle vérification. Chaque action exige un motif et ajoute un numéro de séquence à l'historique minimal. Aucune décision n'est simulée et aucune persistance n'est fournie.

## Invariants et limites

Le connecteur reste désactivé, `architecture_only`, `HealthStatus.DISABLED`, `METADATA_ONLY` et `DOCUMENT_SPECIFIC`. La classification n'importe aucun transport et n'écrit aucun fichier. Les slugs ambigus ne deviennent jamais une vérité documentaire. Aucune logique CSSCT, juridique ou d'expertise n'est introduite.

## Éléments exclus et LOT 4 proposé

Sont exclus : récupération HTML/PDF, extraction, résumé, indexation, embeddings, crawler, cache persistant, scheduler et interface graphique. Un LOT 4 pourrait définir un export local explicitement autorisé des seules décisions humaines validées, avec schéma versionné, journal d'audit et procédure d'import contrôlée, toujours sans contenu intégral.
