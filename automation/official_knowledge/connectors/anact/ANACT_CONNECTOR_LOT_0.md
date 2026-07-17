# ANACT — LOT 0 — Socle d'architecture du connecteur

## Finalité et périmètre

Le connecteur prépare l'exploitation progressive des ressources institutionnelles de l'ANACT relatives aux conditions de travail, à la QVCT, à la prévention, à l'organisation et aux transformations du travail, au dialogue social, au maintien en emploi, à l'absentéisme, à l'usure professionnelle, aux risques psychosociaux, à l'égalité professionnelle, à la charge de travail, au télétravail, au management et à la santé au travail.

Le LOT 0 est exclusivement déclaratif et hors ligne. Il ne télécharge, ne collecte, n'indexe et ne résume aucun contenu. Le connecteur reste indépendant des moteurs CSSCT, Juriste, Paie, CSE et Protection sociale.

## Sources et familles envisagées

Le domaine institutionnel `anact.fr`, déjà présent dans le catalogue du dépôt, constitue l'unique racine déclarée. Les pages thématiques, publications, guides, outils, dossiers, études, fiches pratiques, ressources régionales ARACT, actualités, événements et éventuelles données structurées sont représentés comme familles à expertiser. Aucune URL de rubrique, API ou flux n'est inventé.

Les modes API officielle, flux officiel, HTML officiel, document officiel et import manuel contrôlé sont uniquement des possibilités contractuelles. Tous restent `pending_official_review`; aucune capacité opérationnelle correspondante n'est activée dans Connector Platform.

## Modèles et traçabilité

Une source décrit son identité, sa racine officielle éventuelle, sa portée nationale ou régionale, l'ARACT concernée et ses modes d'accès candidats. Une ressource décrit type, thème, titre, résumé éventuel, URL canonique, dates disponibles, organisme, portée, langue, format, droits, validation, confiance, empreinte et provenance.

Les dates absentes restent `None`. Les droits inconnus restent `None`. Aucune métadonnée n'est fabriquée. Les tests emploient exclusivement `synthetic_only = true` et `official_content = false`. Citations et provenance sont déterministes à partir des seules métadonnées.

## Fraîcheur, validation et indisponibilité

Aucune fréquence de collecte n'est définie avant l'étude officielle des sources. Un futur lot devra enregistrer dates de publication, mise à jour, collecte et validation, puis définir une stratégie par famille. L'indisponibilité, la source inconnue et l'absence de métadonnées doivent produire des diagnostics explicites sans contenu inventé.

## Sécurité et confidentialité

Le contrat est `architecture_only`, `enabled = false`, `NETWORK_DISABLED_BY_DEFAULT`, `METADATA_ONLY`, `DOCUMENT_SPECIFIC` et `HealthStatus.DISABLED`. Les statistiques et métriques valent zéro. Découverte, récupération et synchronisation lèvent `ANACT_CONNECTOR_NETWORK_NOT_IMPLEMENTED`, compatible avec `RuntimeError`.

Aucun secret, cookie, identifiant personnel, document INEOS, cache, scheduler, endpoint, transport ou dépendance à un moteur d'expertise n'est autorisé.

## Limites et lots proposés

Les mentions légales, licences, identifiants, politiques de réutilisation, mécanismes de version, flux, sitemap ou API n'ont pas été vérifiés dans ce lot. Prochains lots proposés : revue officielle des accès et droits ; validation des métadonnées sur un échantillon minimal ; conception d'un transport en lecture seule séparé ; stratégie de fraîcheur ; éventuelle activation soumise à validation explicite.
