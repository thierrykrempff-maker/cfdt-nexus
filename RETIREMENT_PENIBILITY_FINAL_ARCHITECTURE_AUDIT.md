# Audit final d’architecture — Expert Retraite & Pénibilité

Date : 2026-07-21

Branche : `retirement-penibility-final-architecture-audit`

Commit audité : `b3be9a03c006874414a8a39ed8057590dfa49414`

## 1. Résumé exécutif

Les correctifs A1 à A6 ont supprimé les inversions de dépendances dans les
contrats, imposé Career Import avant Reconstruction, mutualisé l’orchestration
des cinq connecteurs, activé un Privacy Gate fail-closed et raccordé Kelio au
référentiel paie partagé. La résolution A6 classe désormais les sources selon
le type documentaire, la confiance, la période et la provenance.

Quatre des six P1 initiaux sont résolus. Deux sont partiellement résolus : la
duplication technique a fortement diminué mais subsiste dans les validateurs,
policies et rapports ; surtout, le moteur compare encore deux
`ImportedCareerRecord` de types d’événement métier différents lorsque leurs
autres valeurs coïncident. Une seconde anomalie P1, nouvelle et démontrée,
concerne les diagnostics du Privacy Gate : une clé de mapping sensible peut
être reproduite dans `field_path`.

Recommandation : **READY_WITH_RESTRICTIONS**. Le socle est prêt pour poursuivre
les développements hors ligne sur données strictement synthétiques. Il ne doit
pas recevoir de données réelles avant correction des deux P1 restants.

## 2. Périmètre et méthode

L’audit couvre 134 fichiers :

- 105 modules Python de `RETIREMENT_PENIBILITY_ENGINE` ;
- 19 suites de tests Retraite & Pénibilité ;
- l’audit initial et les six documents A1 à A6 ;
- les trois artefacts externes utilisés par l’intégration Kelio : schéma,
  catalogue synthétique et validateur de `database/payroll/referentials` /
  `automation/payroll`.

Les deux fichiers confidentiels LOT 0 sont exclus, non lus par les contrôles
de contenu, non modifiés et non suivis. La méthode combine analyse AST des
imports/classes/Protocols, graphe de dépendances, recherche des capacités
réseau et dynamiques, lecture des flux, scénarios d’exécution en mémoire et
tests pytest.

## 3. Comparaison avant / après

| Mesure | Audit initial | Audit final |
|---|---:|---:|
| Modules métier | 93 | 105 |
| Fichiers de tests | 13 | 19 |
| Types dans `*_models.py` | 277 | 285 |
| Dataclasses immuables dans les modèles | 217 | 221 |
| Énumérations dans les modèles | 59 | 63 |
| Protocol dans un module de modèles | 1 | 1 |
| Modules de contrat | 15 | 17 |
| Interfaces `Protocol` | 14 | 23 |
| Méthodes de Protocol | 84 | 111 |
| Connecteurs | 5 | 5 |
| Convertisseurs | 5 | 5 |
| Policies | 12 | 12 |
| Validateurs | 8 | 8 |
| Modules de rapport | 11 | 11 |
| Fonctions de test | 183 | 269 |
| Cas Retraite exécutés | 219 | 455 |
| Dépendances contractuelles interdites | 11 contrats concernés | 0 |
| Cycles d’import | 0 | 0 |
| Chemins connecteur → Reconstruction contournant Import | 5 | 0 |
| Référentiels Kelio dupliqués | 0 | 0 |

## 4. Statut des six P1 initiaux

### P1-1 — Dépendances inversées contrats / implémentations : RESOLVED

Preuves :

- les 17 fichiers `*_contract.py` n’importent aucun module `*_engine`,
  `*_connector`, `*_validator`, `*_converter`, `*_report` ou `*_policy` ;
- les implémentations `CareerEvidenceEngine` et `DocumentKnowledgeEngine` sont
  dans leurs modules concrets ;
- 23 Protocols portent 111 méthodes sans import concret ;
- `test_retirement_contract_boundaries.py` vérifie les imports indépendants,
  annotations, implémentations structurelles et l’absence de cycle (83 tests).

### P1-2 — Contournement du Career Import Engine : RESOLVED

Preuves :

- `ConnectorFoundation.prepare_reconstruction()` délègue exclusivement à
  `CareerImportPipelineCoordinator` ;
- les cinq connecteurs injectent `CareerImportPipeline` et n’importent pas
  `CareerReconstructionEngine` ;
- `CareerImportPipeline.validate_for_reconstruction()` impose le type exact
  `ImportBatch`, la provenance, `synthetic_only`, le Privacy Gate et
  `CareerImportEngine.validate_batch()` ;
- `CareerReconstructionEngine.add_import_batch()` refuse tout batch dont le
  statut n’est pas `VALIDATED` ;
- `test_career_import_pipeline.py` couvre les cinq connecteurs, les types
  interdits et les batchs invalides (17 tests).

Chemins de contournement détectés : **0**.

### P1-3 — Rapprochement sensible au type métier : PARTIALLY_RESOLVED

A6 apporte `DocumentResolutionStrategy`. Le merger ordonne les sources par
`ImportDocumentType`, puis `ImportConfidence`, complétude de période et clé de
provenance. L’ordre est centralisé, déterministe, exposé dans
`ReconstructionMerge.resolution_order`, et les alternatives/provenances sont
conservées.

Écart démontré : `CareerReconstructionEngine.build_candidates()` groupe encore
par classe Python. Deux `ImportedCareerRecord` portant respectivement
`salary_item` et `absence`, mais la même période, l’employeur et la provenance,
produisent `SAME_PERIOD` puis une fusion. `CareerReconstructionMatcher._COMPARABLE`
n’inclut pas `career_event_type`. Les 12 tests A6 vérifient la priorité
documentaire mais pas cette frontière sémantique.

Statut résiduel : **P1**, à corriger avant ingestion réelle.

### P1-4 — Duplication entre connecteurs : PARTIALLY_RESOLVED

`ConnectorFoundation`, `ConnectorReconstructionSpec` et les Protocols de
`connector_contract.py` centralisent la validation déléguée, le Privacy Gate,
la conversion validée, le contexte et le passage Import → Reconstruction.
A2 documente 16 duplications opérationnelles supprimées et les cinq
connecteurs utilisent cette fondation.

Les contrôles de provenance/synthétique, policies et builders de rapports
restent répétés. Une partie est justifiée par les modèles sources distincts ;
la taxonomie des invariants reste néanmoins dupliquée. Le résidu est classé
P2, sans restaurer le P1 initial dans son niveau d’origine.

### P1-5 — Confidentialité principalement déclarative : RESOLVED

`RetirementPrivacyGate` est actif dans la fondation, Career Import,
Reconstruction, Timeline, Evidence et Potential Rights. Il refuse NIR, IBAN,
RIB, coordonnées, identifiants non synthétiques, chemins/documents réels,
cycles, types inconnus et absence de gate. `require_privacy_gate()` échoue
fermé. Les valeurs inspectées ne sont pas stockées dans `PrivacyFinding`.

Les 44 tests A4 démontrent le blocage avant traitement, la défense en
profondeur, l’absence de rapport après refus et les diagnostics sans valeur
pour les champs ordinaires.

Une nouvelle anomalie de diagnostic, décrite en P1-N2 ci-dessous, limite la
préparation production sans remettre en cause la résolution du caractère
« uniquement déclaratif » du P1 initial.

### P1-6 — Intégration Kelio incomplète : RESOLVED

`KelioReferentialLookup` est un Protocol neutre ;
`PayrollKelioReferentialLookup` adapte le validateur paie existant et résout
les identifiants du catalogue partagé. Les statuts inconnus, ambigus,
incompatibles et erreurs de lookup sont fail-closed. Le connecteur projette
les métadonnées et preuves canoniques sans recopier la taxonomie des 17
compteurs. Les 56 tests A5 couvrent le schéma, l’adaptateur, l’injection, les
échecs et l’absence de duplication.

Référentiels Kelio dupliqués détectés : **0**.

## 5. Preuves transversales

- Aucun cycle dans le graphe des 105 modules.
- Aucun import dynamique (`import_module` / `__import__`).
- Aucun import de client HTTP, `urllib`, `ssl`, `socket`, OCR ou scraper.
- Une seule dépendance Nexus externe dans le moteur :
  `kelio_referential_adapter.py → automation.payroll.payroll_referential_validator`,
  conforme à A5.
- Nibelis reste fail-closed : sans lookup injecté, toute rubrique ou paramètre
  produit `REFERENTIAL_LOOKUP_REQUIRED`.
- Career Reconstruction n’accepte que des `ImportBatch` validés.
- Les provenances et niveaux de confiance sont immuables et conservés lors de
  la résolution A6.
- Le paquet public `__init__.py` n’importe ni connecteur, ni transport, ni
  référentiel externe.

## 6. Anomalies et dette restantes

### P0 — 0

Aucune fuite active sur le chemin nominal, aucun cycle, aucun accès réseau et
aucune violation bloquante immédiate sur données synthétiques.

### P1 — 2 anomalies démontrées

1. **P1-N1 — Frontière de type d’événement incomplète.** Des
   `ImportedCareerRecord` de `career_event_type` différents peuvent être
   classés `SAME_PERIOD` et fusionnés. Preuves :
   `career_reconstruction_engine.py::build_candidates`,
   `career_reconstruction_matcher.py::_COMPARABLE` et scénario en mémoire
   `salary_item` / `absence`.
2. **P1-N2 — Clé sensible divulguée dans un diagnostic.**
   `PrivacyDetector._walk()` concatène directement une clé de mapping à
   `field_path`. Avec une clé synthétique au format NIR et une valeur de type
   inconnu, `sanitize_diagnostic()` renvoie
   `PRIVACY_UNSUPPORTED_TYPE at $.<clé>`. La clé sensible est donc reproduite.
   L’écart est démontré sans donnée réelle et n’est pas couvert par A4.

### P2 — 7 dettes importantes non bloquantes hors données réelles

1. Représentations qui se chevauchent entre Foundation, Timeline, Import,
   Reconstruction et connecteurs, sans schéma de correspondance versionné.
2. Duplication résiduelle des invariants de policies, validateurs et rapports.
3. Façade publique `__init__.py` limitée à la fondation, sans API versionnée
   des lots suivants.
4. Vocabulaire Employee/Expert View et structures de rapports non normalisés ;
   `generate_import_report` reste ambigu.
5. `NibelisReferentialLookup` demeure dans `nibelis_models.py`, contrairement
   aux autres ports placés dans les contrats.
6. Le pipeline annonce Timeline/Evidence/Potential Rights, mais ne fournit pas
   un test bout en bout versionné couvrant toutes ces couches et leurs sorties.
7. Absence de property-based tests, tests de volumétrie, seuil de couverture
   et compatibilité explicite de versions de schéma.

### P3 — 2 améliorations possibles

1. `DocumentResolutionStrategy.preferred_values()` n’est pas utilisé par le
   merger, qui reproduit localement la sélection de valeur prioritaire.
2. Plusieurs constructeurs utilisent une instance de `RetirementPrivacyGate`
   comme valeur par défaut. Elle est sans état mutable aujourd’hui, mais une
   factory explicite rendrait cette propriété plus robuste.

### Hors périmètre volontaire

Accès réels, authentification, contrôle d’accès, rétention, chiffrement,
observabilité, API, OCR, PDF, connecteurs CNAV/CARSAT et calcul de droits ne
sont ni présents ni évalués comme fonctionnalités disponibles.

## 7. Mesures finales

| Mesure | Valeur |
|---|---:|
| Fichiers audités | 134 |
| Fichiers Python du moteur | 105 |
| Fichiers de tests Retraite | 19 |
| Modèles | 285 |
| Contrats / Protocols | 17 modules / 23 Protocols |
| Connecteurs | 5 |
| Policies | 12 |
| Validateurs | 8 |
| Rapports | 11 |
| Fonctions de test | 269 |
| Cas Retraite collectés | 455 |
| Dépendances contractuelles interdites | 0 |
| Cycles | 0 |
| Chemins de contournement Career Import | 0 |
| Référentiels Kelio dupliqués | 0 |
| P0 / P1 / P2 / P3 | 0 / 2 / 7 / 2 |

## 8. Résultats des tests et contrôles

Suites obligatoires : **333/333 réussies**.

| Suite | Résultat |
|---|---:|
| Contract Boundaries A1 | 83/83 |
| Connector Foundation A2 | 24/24 |
| Career Import Pipeline A3 | 17/17 |
| Active Privacy A4 | 44/44 |
| Kelio Referential A5 | 56/56 |
| Document Resolution A6 | 12/12 |
| Career Statement | 16/16 |
| Payslip | 17/17 |
| Employment Contract | 22/22 |
| Kelio Connector | 21/21 |
| Nibelis Connector | 21/21 |

Ensemble Retraite & Pénibilité : **455/455 réussis**.

Suite complète : **1 912 réussites, 128 sous-tests réussis, 3 échecs
historiques** (`DependencyTests::test_import_does_not_load_forbidden_packages`,
`IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`,
`test_integration_failure_preserves_legacy_expert_payload`). Aucun nouvel
échec n’est introduit.

`git diff --check` : réussi.

Syntaxe Python 3.10 : validée sur les 105 modules et les 19 suites Retraite.

## 9. Notes avant / après

| Critère | Avant | Après | Justification synthétique |
|---|---:|---:|---|
| Architecture | 7,3 | 8,7 | Frontières, pipeline et protections actifs ; type d’événement résiduel. |
| Découplage | 6,8 | 8,5 | 0 dépendance contractuelle interdite, 0 cycle. |
| Extensibilité | 7,5 | 8,4 | Fondation et Protocols communs ; façade/versionnement à compléter. |
| Qualité des modèles | 7,0 | 7,3 | Immutabilité forte ; chevauchements toujours présents. |
| Qualité des contrats | 6,8 | 8,8 | 23 Protocols indépendants et vérifiés structurellement. |
| Qualité des connecteurs | 7,2 | 8,5 | Pipeline, privacy et Kelio conformes ; duplication résiduelle. |
| Qualité des tests | 7,6 | 8,8 | 455 cas, tests architecturaux et adversariaux ; charge/version absentes. |
| Confidentialité | 8,1 | 8,4 | Gate actif et fail-closed ; fuite de clé dans diagnostic à corriger. |
| Maintenabilité | 6,7 | 7,8 | Orchestration mutualisée ; surface de modèles et policies élevée. |
| Préparation production | 5,9 | 6,8 | Socle renforcé, mais deux P1 et intégrations réelles volontairement absentes. |

Moyenne : **7,1 → 8,2 / 10**.

## 10. Risques avant données réelles

Les deux P1 doivent être corrigés et couverts par tests de non-régression.
Ensuite restent nécessaires : schémas versionnés, contrôle d’accès, politique
de rétention, journalisation sans contenu, chiffrement, tests de charge,
observabilité et revue de conformité. Aucun score ne suppose ces capacités
déjà présentes.

## 11. Recommandation finale

**READY_WITH_RESTRICTIONS**

Autorisé : poursuite hors ligne, données synthétiques, architecture et tests.

Interdit avant correction : ingestion de document ou donnée réelle, exposition
production et transport externe.

Cet audit n’a modifié aucun fichier Python, test, schéma, référentiel,
connecteur, moteur, policy ou validateur. Aucun commit, push ou merge n’a été
réalisé sur la branche d’audit.
