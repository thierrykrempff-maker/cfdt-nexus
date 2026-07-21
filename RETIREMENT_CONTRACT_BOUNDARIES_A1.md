# A1 — Frontières des contrats Retraite & Pénibilité

## Objet

Le correctif A1 supprime exclusivement les dépendances allant des modules
`*_contract.py` vers des implémentations concrètes. Il ne modifie ni les règles
métier, ni les conversions, ni les rapports, ni le pipeline fonctionnel.

Sens de dépendance retenu :

```text
modèles neutres
      ↓
contrats / Protocol
      ↓
implémentations concrètes
```

## Cartographie avant correction

Quinze modules de contrat ont été audités. Onze contenaient au moins une
dépendance interdite.

| Contrat | Dépendances concrètes initiales |
|---|---|
| `career_evidence_contract.py` | `career_evidence_graph`, `career_evidence_report`, `career_evidence_resolver` et façade `CareerEvidenceEngine` définie dans le contrat |
| `career_import_contract.py` | `career_import_engine.CareerImportEngine` |
| `career_reconstruction_contract.py` | `career_reconstruction_engine.CareerReconstructionEngine` |
| `career_statement_contract.py` | `career_statement_connector.CareerStatementConnector` |
| `document_knowledge_contract.py` | `document_context_builder`, `document_selector`, `document_version_resolver` et façade `DocumentKnowledgeEngine` définie dans le contrat |
| `employment_contract_contract.py` | `employment_contract_connector.EmploymentContractConnector` |
| `kelio_contract.py` | `kelio_connector.KelioConnector` |
| `nibelis_contract.py` | `nibelis_connector.NibelisConnector` et `InjectedNibelisReferentialLookup` |
| `payslip_contract.py` | `payslip_connector.PayslipConnector` |
| `potential_rights_contract.py` | `potential_rights_engine.PotentialRightsEngine` |
| `rule_reasoning_contract.py` | `rule_reasoning_engine.RetirementRuleReasoningEngine` |

Les quatre contrats déjà conformes étaient :

- `career_document_search_contract.py` ;
- `career_timeline_contract.py` ;
- `document_provider_contract.py` ;
- `retirement_contract.py`.

## Corrections réalisées

- Tous les imports directs vers `*_connector`, `*_engine`, `*_validator`,
  `*_converter`, `*_report` et `*_policy` ont été retirés des contrats.
- Les réexports d'implémentations ont été retirés des `__all__` concernés.
- `CareerEvidenceEngine` a été déplacé sans changement fonctionnel vers
  `career_evidence_engine.py`.
- `DocumentKnowledgeEngine` a été déplacé sans changement fonctionnel vers
  `document_knowledge_engine.py`.
- Les contrats correspondants exposent désormais `CareerEvidencePort` et
  `DocumentKnowledgePort`.
- Les tests historiques importent désormais les implémentations depuis leurs
  modules concrets et les contrats depuis leurs modules abstraits.

## Types déplacés

Aucun modèle ni type partagé n'a été déplacé. Aucun module de types communs n'a
été créé, car les annotations des ports peuvent s'appuyer directement sur les
modèles neutres existants.

Seules deux façades d'implémentation ont changé de module :

- `CareerEvidenceEngine` ;
- `DocumentKnowledgeEngine`.

## Compatibilité

- Les noms, signatures et comportements des implémentations sont conservés.
- Les constantes de sécurité et les Protocol existants sont conservés.
- Les implémentations satisfont structurellement leurs Protocol.
- Les annotations de chaque Protocol sont résolubles sans charger de nouvelle
  implémentation concrète.
- Les anciens imports d'implémentations depuis un module `*_contract.py` sont
  remplacés par les chemins canoniques `*_engine.py` ou `*_connector.py`. Cette
  migration est nécessaire pour garantir une frontière contractuelle réelle ;
  les imports utilisés dans le dépôt ont été adaptés.
- Aucun import dynamique, import différé, `Any` généralisé ou type opaque n'a
  été introduit.

## Validation automatique

`tests/test_retirement_contract_boundaries.py` contrôle par AST :

1. les quinze contrats attendus ;
2. l'absence d'import vers les six familles interdites ;
3. l'absence de façade concrète définie dans un contrat ;
4. l'import indépendant de chaque contrat ;
5. l'absence de cycle dans le paquet ;
6. la conformité structurelle des implémentations aux Protocol ;
7. la résolution des annotations sans chargement d'implémentation par le
   contrat.

## Hors périmètre volontaire

A1 ne traite pas :

- la duplication entre connecteurs ou un éventuel `AbstractConnector` ;
- la normalisation des rapports ;
- le chaînage Career Import → Reconstruction ;
- le rapprochement sensible au type métier ;
- le référentiel Kelio ;
- les contrôles actifs de confidentialité ;
- les anomalies P2 ;
- l'accès aux données réelles, API, OCR ou réseau.
