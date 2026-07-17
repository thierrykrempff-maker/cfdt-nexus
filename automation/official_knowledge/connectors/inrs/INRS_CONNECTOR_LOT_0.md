# INRS — LOT 0 — Audit et architecture du connecteur

## Périmètre

Ce lot consigne une étude limitée des ressources publiques de l'INRS. Il ne crée aucun transport, endpoint, synchronisation, téléchargement, scraping, cache, ordonnanceur ou authentification. Le connecteur reste `enabled = false`, `architecture_only` et soumis à `NETWORK_DISABLED_BY_DEFAULT`.

## Architecture et accès observés

Le site public organise plus de 2 000 ressources autour de pages HTML, dossiers, brochures, dépliants, fiches, articles de revue, outils, bases de données, affiches et vidéos. Les fiches de publication exposent généralement un titre, un type, une référence INRS (`ED`, `TJ`, `A`, `AD`, `AR`) et une date. Les pages de nouveautés distinguent nouvelles publications et mises à jour ; ces dernières peuvent annuler et remplacer une édition précédente.

Des fichiers PDF sont proposés, mais aucun n'a été téléchargé pendant l'étude. Un flux RSS est visible sur le portail documentaire ; il n'est pas validé ni retenu comme mécanisme opérationnel. Aucun accès API, OpenAPI ou documentation développeur n'a été identifié dans la revue limitée. Les charges de `robots.txt` et `sitemap.xml` n'ont pas pu être validées par l'outil et restent à revoir.

## Droits et politique documentaire

Les mentions légales indiquent que les productions INRS ne sont pas dans le domaine public. La reproduction, adaptation, diffusion ou communication, intégrale ou partielle, est interdite hors usage privé sans autorisation. Elles précisent notamment qu'un extrait de brochure ou un PDF ne peut pas être copié sur un site ou intranet. Les liens sont autorisés sous conditions, avec URL affichée, titre de la page et source INRS.

Le contrat est donc `METADATA_ONLY` avec licence `DOCUMENT_SPECIFIC`. Aucun texte, extrait, PDF, image, vidéo ou son n'est conservé. Citation et provenance doivent contenir au minimum le lien, le titre, la source INRS, la référence, la date éventuelle et l'empreinte des métadonnées. Toute extension exige une autorisation et une revue juridique documentée.

## Intégration Connector Platform

`inrs_platform.py` compose `ConnectorContract`, `ConnectorState`, `Capability`, `ConnectorMetadata`, `DocumentPolicy`, `LicenseId`, `ConnectorRegistry`, `ConnectorStatistics`, `Metric`, `HealthReport`, `SecurityPolicy`, validation et erreurs génériques. Seules les capacités documentaires `HTML`, `PDF` et `MANUAL` sont déclarées ; elles ne confèrent aucun droit d'accès. L'API, l'authentification, le cache, la synchronisation, la découverte et le téléchargement sont absents.

## Intérêt et priorités

| Famille | Nexus | Juriste | Paie | Protection sociale | CSSCT | HSE | Priorité |
|---|---|---|---|---|---|---|---:|
| Brochures | Élevé | Élevé | Moyen | Moyen | Très élevé | Très élevé | 1 |
| Fiches pratiques | Élevé | Élevé | Moyen | Moyen | Très élevé | Très élevé | 1 |
| Dossiers | Élevé | Élevé | Moyen | Moyen | Très élevé | Très élevé | 1 |
| Actualités | Moyen | Moyen | Faible | Faible | Élevé | Élevé | 3 |
| Questions/Réponses | Élevé | Élevé | Moyen | Moyen | Élevé | Élevé | 2 |
| Outils | Élevé | Moyen | Moyen | Faible | Très élevé | Très élevé | 2 |
| Bases documentaires | Élevé | Élevé | Faible | Moyen | Très élevé | Très élevé | 2 |
| Vidéos | Moyen | Moyen | Faible | Faible | Élevé | Élevé | 4 |
| Podcasts | Faible | Faible | Faible | Faible | Moyen | Moyen | 5 |
| Affiches | Moyen | Faible | Faible | Faible | Élevé | Élevé | 4 |
| Documents PDF | Élevé | Élevé | Moyen | Moyen | Très élevé | Très élevé | 1 |

Pour Expert Juriste, l'intérêt principal porte sur les aide-mémoires, focus juridiques, dossiers et questions/réponses, avec rappel obligatoire que seul Légifrance fait foi pour les textes normatifs. Pour Expert Paie, l'intérêt est indirect : accidents du travail, maladies professionnelles, obligations de prévention et organisation du travail, sans calcul de paie. Pour Protection sociale, les tableaux de maladies professionnelles et ressources de santé au travail sont utiles mais ne remplacent pas les sources assurantielles ou réglementaires. CSSCT et HSE sont les consommateurs prioritaires.

## Risques techniques

- droits d'auteur restrictifs et revue document par document ;
- diversité des formats et sous-sites ;
- identifiants et éditions remplacées à gérer sans perdre l'historique ;
- ressources pouvant contenir des synthèses réglementaires qui ne font pas foi ;
- RSS, robots et sitemap à revalider officiellement ;
- absence d'API publique identifiée ;
- dépendances possibles vers des sites tiers ou outils interactifs.

## Feuille de route proposée

1. LOT 1A : validation juridique écrite de la conservation des métadonnées, citations et liens.
2. LOT 1B : vérification technique contrôlée de robots, sitemap et RSS, sans ingestion.
3. LOT 1C : contrat de découverte métadonnées uniquement sur un échantillon synthétique.
4. LOT 1D : gestion des références et versions `ED`/`TJ`, sans contenu.
5. LOT 2 : éventuel transport lecture seule, soumis à validation explicite séparée.

## Évolution documentaire transverse recommandée

Un futur lot transverse devrait définir un modèle documentaire commun, partagé par les connecteurs institutionnels sans modifier rétroactivement leur contrat. Cette évolution est uniquement documentée ici : elle n'est pas implémentée dans le LOT 0 et n'impose aucune modification actuelle de Connector Platform.

Le modèle envisagé est `DocumentType`, avec les valeurs suivantes :

- `BROCHURE`
- `FICHE`
- `DOSSIER`
- `QUESTION_REPONSE`
- `GUIDE`
- `OUTIL`
- `FAQ`
- `ACTUALITE`
- `VIDEO`
- `PODCAST`
- `AFFICHE`
- `BASE_DOCUMENTAIRE`
- `PUBLICATION`
- `AUTRE`

Ce vocabulaire commun devra pouvoir être adopté ultérieurement par INRS, ANACT, Ameli, URSSAF, France Chimie, OPCO2i, Observatoire, DREAL, INERIS, ARIA et AIDA. Sa conception devra préserver les catégories propres à chaque source, définir une valeur de repli explicite et faire l'objet d'un lot séparé avec tests de compatibilité.

## Limites

L'étude n'affirme pas l'inexistence d'une API, d'un sitemap ou d'autres flux ; elle indique seulement qu'ils n'ont pas été validés dans le périmètre observé. Aucun développement opérationnel n'est autorisé par cette architecture.
