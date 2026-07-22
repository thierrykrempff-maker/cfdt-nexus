# NEXUS Connector Adapter 0

## Rôle

Cette couche transforme un résultat déjà produit par un connecteur en objets
`NEXUS_CORE`. Elle ne contacte aucune API, ne gère ni OAuth, ni HTTP, ni pagination,
ni authentification et ne contient aucune logique juridique.

Flux : `Connecteur existant → snapshot immuable → GenericConnectorAdapter → Nexus Core`.

## Architecture

Le paquet autonome `NEXUS_ADAPTERS/connectors/` contient :

- modèles immuables de descripteur, source, document, enregistrement, requête et réponse ;
- Protocols de fournisseur, adaptateur, validation et reporting ;
- normalisation fermée vers les enums Core existants ;
- mappers de documents, preuves, métadonnées, provenance et confiance ;
- validateur structurel et contrôle de confidentialité ;
- rapport déterministe et sérialiseur JSON ;
- `GenericConnectorAdapter`, compatible `ExecutableEngine`.

## Modèles et transformation

`ConnectorAdapterInput` regroupe le descripteur, la source, la requête, la réponse
et la date d'acquisition. `ConnectorDocumentSnapshot` conserve les références,
dates, version, auteur, URL, type, langue, contenu/extrait éventuel, empreinte et
validité. `ConnectorRecordSnapshot` n'engendre un `Finding` que si une conclusion
explicite est fournie par le connecteur.

Les identifiants sont produits par SHA-256 tronqué. Aucun `hash()` Python n'est
utilisé. L'ordre d'exécution n'intervient jamais dans l'identité.

## Protocols

- `ConnectorSnapshotProvider`
- `ConnectorAdapter`
- `ConnectorAdapterReporter`
- `ConnectorAdapterValidatorProtocol`
- compatibilité structurelle avec `ExecutableEngine`

## Normalisation des sources

Les catégories législation, réglementation et jurisprudence utilisent
`LEGAL_DATABASE`. Doctrine, autorité indépendante, organisme social et autre source
officielle utilisent `OFFICIAL_WEBSITE`. Les accords et documents internes utilisent
`INTERNAL_REFERENTIAL`. Une catégorie inconnue utilise `UNKNOWN`; sa valeur originale
reste disponible dans les métadonnées.

## Confiance

Seul un score fourni est traduit. Un score absent produit
`ReasoningConfidence.INSUFFICIENT`, un score technique nul et le diagnostic
`CONNECTOR_CONFIDENCE_MISSING`. La couche n'invente aucune autorité ni certitude.

## Validation et confidentialité

Le validateur contrôle identité, unicité, sérialisabilité, déterminisme et motifs de
secret/donnée personnelle. Une donnée métier incomplète produit un diagnostic et ne
stoppe pas l'adaptation. Les diagnostics ne contiennent que des codes techniques,
catégories, gravités et références pseudonymisées.

Les tokens, clés, secrets, cookies, mots de passe et en-têtes d'autorisation ne sont
jamais sérialisés dans un diagnostic ou un rapport. Le contenu documentaire reste
dans la valeur `Evidence`, masquée dans les représentations Core.

## Reporting et orchestration

`ConnectorAdapterReportBuilder` compte entrées et sorties. Le JSON est trié et sans
espaces variables. `execute()` transforme uniquement le snapshot en mémoire et
retourne un `ExecutionResult`; aucun appel externe n'est possible.

## Limites

Ce lot ne fournit aucun adaptateur concret. Il n'interprète ni loi, ni jurisprudence,
ni doctrine. Il ne crée aucune recommandation métier et n'effectue aucune collecte.

## Ordre recommandé des futurs adaptateurs

1. Légifrance ;
2. JUDILIBRE ;
3. Code du travail numérique ;
4. CNIL ;
5. CARSAT ;
6. autres connecteurs.
