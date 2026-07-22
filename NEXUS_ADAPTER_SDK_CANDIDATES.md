# Audit de réutilisation — candidats SDK des adaptateurs Nexus

## Périmètre comparé

Comparaison statique entre `NEXUS_ADAPTERS/payroll`,
`NEXUS_ADAPTERS/retirement` et `NEXUS_ADAPTERS/cse`. Aucun SDK, factory, classe abstraite ou registre
d'adaptateurs n'est créé dans ce lot.

## Similarité observée

| Élément | Similarité estimée | Candidat commun | Décision |
|---|---:|---|---|
| Génération d'identifiants pseudonymes | 100 % | `StableAdapterIdentity` | Reporter |
| Modèle de diagnostic technique | 95 % | `AdapterDiagnostic` | Reporter |
| Enveloppe de résultat | 85 % | `AdapterResultEnvelope` générique | Reporter |
| Filtrage par domaine des producteurs | 90 % | Helper de Protocols | Reporter |
| Construction d'`ExecutionResult` | 85 % | `ExecutionResultBuilder` | Reporter |
| Mapping confidentialité/redaction | 85 % | Politique commune | Reporter |
| Mapping des preuves et provenance | 65 % | Primitives ciblées seulement | Conserver métier |
| Mapping des constats | 60 % | Aucune abstraction immédiate | Conserver métier |
| Mapping des recommandations | 70 % | Helper possible après un 3e adaptateur | Reporter |
| Mapping carrière et conflits | < 30 % | Aucun | Spécifique Retraite |
| Mappers Meeting, Decision et Vote | < 20 % | Aucun | Spécifique CSE |

## Candidats dépassant 80 %

Les cinq premiers candidats et la politique de confidentialité dépassent le seuil
de 80 % sur trois adaptateurs. La factorisation est désormais techniquement
justifiable pour les primitives étroites suivantes : identité pseudonyme,
diagnostic sûr, filtrage par domaine et assemblage d'`ExecutionResult`.

## Recommandation

Préparer un lot SDK séparé, après validation des trois adaptateurs, sans modifier
leurs contrats publics. Extraire uniquement les primitives confirmées par trois
usages : identité technique, diagnostic sûr, assemblage d'exécution et filtrage des
Protocols. Les tables de mapping, la carrière, les conflits et les modèles
Meeting/Decision/Vote doivent rester dans chaque adaptateur.

## Apport du troisième adaptateur

Le CSE confirme la structure commune de la façade, des Protocols et des diagnostics.
Il confirme aussi que les mappers de domaine doivent rester spécialisés : Paie
traduit un rapport expert, Retraite traduit carrière et conflits documentaires,
tandis que CSE traduit réunions, décisions et votes. Une factorisation limitée
d'environ 15 à 20 % du code total des adaptateurs paraît réaliste ; une hiérarchie
de classes abstraites serait excessive.
