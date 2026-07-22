# Audit des connecteurs existants — Connector Adapter 0

## Périmètre et méthode

Audit statique uniquement, sans instanciation de client et sans accès réseau. Les
connecteurs existants n'ont pas été modifiés.

## Légifrance

- Emplacement : `automation/scripts/legifrance_connector.py` et
  `automation/scripts/legifrance_api.py`.
- Sorties : dictionnaires normalisés retournés par `search_code_sources`,
  `search_jurisprudence_sources` et `article_source`.
- Modèles : configuration `LegifranceConfig`; résultats documentaires sous forme de
  dictionnaires, sans contrat de snapshot partagé.
- Diagnostics : exceptions dédiées et avertissements de qualité dans les payloads.
- Métadonnées : identifiants d'article, références, URL, dates, texte/extraits et
  informations de recherche selon l'opération.
- Confiance : scores et contrôles de qualité locaux, sans `ConfidenceAssessment` Core.
- Écart Core : OAuth, HTTP, cache et normalisation sont réunis dans le connecteur ;
  un futur adaptateur devra recevoir le résultat après ces opérations.

## JUDILIBRE

- Emplacement : `automation/scripts/judilibre_connector.py`.
- Sorties : dictionnaires via `search_decision_hits`, `decision_source` et
  `search_sources`.
- Modèles : `JudilibreConfig`; décisions et audits représentés par dictionnaires.
- Diagnostics : exceptions dédiées, raisons de rejet, limites et audits de pertinence.
- Métadonnées : identifiant officiel, juridiction, dates, solution, références,
  contexte de recherche et extraits lorsque disponibles.
- Confiance : scores de pertinence locaux et audit, sans vocabulaire Core.
- Écart Core : structure riche mais non typée ; aucune `DocumentReference`,
  `Provenance` ou `ConfidenceAssessment` Core.

## Code du travail numérique

- Emplacement : `automation/scripts/cdtn_connector.py`.
- Sorties : dictionnaire de sources via `search_sources`.
- Modèles : `CdtnConfig`; sources représentées par dictionnaires.
- Diagnostics : `CdtnError`, `CdtnAPIError`, avertissements d'endpoint et évaluation
  globale du résultat.
- Métadonnées : URL publique, slug, description, source, scores et contexte de requête.
- Confiance : scores moyens et pertinence pratique locaux.
- Écart Core : aucune enveloppe typée commune et responsabilités HTTP/cache intégrées.

## CNIL

- Emplacement : `automation/official_knowledge/connectors/cnil/`.
- Sorties : `CnilMetadata`, `CnilResource`, `ResourceCandidate`, résultats de
  découverte et synchronisation.
- Diagnostics : refus fermés avec codes stables, validations et warnings.
- Métadonnées : URL canonique, titre, dates, taxonomie, provenance, langue,
  fingerprint et politique `METADATA_ONLY`.
- Confiance : niveaux de citation principalement prudents, sans assessment Core.
- Compatibilité : très proche du snapshot générique ; adaptation nécessaire pour
  les enums, identifiants, documents et provenance Core.

## CARSAT

- Emplacement : `automation/official_knowledge/connectors/carsat/`.
- Sorties : `CarsatMetadata`, `CarsatDocumentIdentity`, événements de synchronisation.
- Diagnostics : `CarsatMetadataRefusal` avec code stable et validations fail-closed.
- Métadonnées : identité Document Registry, URL, titre, date, catégorie, famille,
  type, langue, provenance et référence.
- Confiance : confiance de citation/information locale, sans assessment Core.
- Compatibilité : identité stable et `METADATA_ONLY` réutilisables ; taxonomies à
  normaliser vers les valeurs génériques existantes.

## Autres connecteurs détectés

- INRS : modèles metadata-only riches, identité Document Registry, résumé borné,
  dates, auteur, version, redirection et synchronisation.
- DREETS Grand Est : métadonnées publiques strictes, domaines/MIME validés,
  synchronisation et Document Registry.
- ANACT : paquet plus ancien et étendu comprenant modèles, catalogue, classification,
  transports isolés, synchronisation et politiques.
- France Chimie : socle metadata-only et synchronisation déterministe.

Ces connecteurs produisent des dataclasses ou événements spécialisés, généralement
plus proches du futur snapshot que les trois connecteurs API historiques.

## Connector Platform et Document Registry

`automation/connector_platform/` fournit contrats, opérations, citations,
provenance, sécurité, licences et politiques. Le Document Registry fournit une
identité stable et un `DocumentRecord` metadata-only. Aucun des deux ne produit
directement les modèles `NEXUS_CORE`.

## Conclusion

Le socle générique doit accepter des snapshots déjà construits. Les futurs
adaptateurs concrets auront pour seule responsabilité de traduire chaque format
existant vers ces snapshots. HTTP, OAuth, cache, pagination, découverte et règles
de domaine restent dans les connecteurs.
