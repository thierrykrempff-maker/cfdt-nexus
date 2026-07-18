# ARCH-01 — Contrats communs de CFDT Nexus

- Date : 18 juillet 2026
- Branche de travail : `arch-01-common-contracts`
- Version du schéma : `1.0`
- Périmètre : contrats de données additifs, sans migration ni changement de comportement

## 1. Finalité métier

Les contrats communs donnent aux futurs experts et moteurs un langage stable pour distinguer ce que l'utilisateur déclare, ce qui est établi, ce qui reste hypothétique, les scénarios possibles, les informations manquantes, les risques et les sources réellement utilisées.

Ils préparent une analyse syndicale plus défendable : le délégué peut voir pourquoi une conclusion est limitée, quelles pièces demander et quel type de confiance est évalué. Ils ne produisent aucune règle de droit, aucun calcul de paie et aucune stratégie autonome.

## 2. Emplacement et API publique

Le paquet est situé dans `automation/contracts/` :

| Module | Responsabilité |
| --- | --- |
| `enums.py` | petits vocabulaires canoniques |
| `serialization.py` | gel et sérialisation JSON standard |
| `statements.py` | séparation des assertions factuelles |
| `confidence.py` | confiance multidimensionnelle |
| `assessments.py` | informations manquantes et risques |
| `sources.py` | sources et preuves de consultation |
| `requests.py` | demande normalisée d'expert |
| `reports.py` | rapport normalisé d'expert |
| `__init__.py` | imports publics stables |

Les objets publics s'importent directement :

```python
from automation.contracts import ExpertRequest, ExpertReport, SourceEvidence
```

Le paquet utilise uniquement la bibliothèque standard. Il n'importe ni Paie, ni Juriste, ni routeur, ni orchestrateur, ni Connector Platform, ni connecteur officiel.

## 3. Principes structurants

1. Les dataclasses sont `frozen=True`.
2. Les collections contractuelles sont des tuples.
3. Le contexte et les métadonnées sont copiés puis gelés récursivement.
4. Les faits, déclarations, hypothèses, scénarios et intentions supposées portent des catégories distinctes.
5. Une consultation réussie n'existe pas sans `SourceEvidence` valide.
6. `consulted` et `cache_used` sont dérivés du statut de preuve ; ils ne sont jamais des déclarations libres.
7. Une dimension de confiance non évaluée reste absente ou possède `level=None` ; elle ne reçoit jamais `MEDIUM` par défaut.
8. Chaque objet principal porte `schema_version="1.0"`.
9. Les clés inconnues au premier niveau sont rejetées. Les extensions inconnues placées dans `metadata` sont conservées.
10. Les contrats ne contiennent aucune règle métier et n'appellent aucun moteur.

## 4. Objets principaux

### `ExpertRequest`

Demande destinée à un futur expert.

Champs :

- `request_id`, `question_text`, `requested_domain` ;
- `context` ;
- `facts` : uniquement des `Statement(ESTABLISHED_FACT)` ;
- `declared_information` : uniquement des `Statement(DECLARED_INFORMATION)` ;
- `available_evidence_refs` ;
- `missing_information` ;
- `detail_level`, `confidentiality` ;
- `schema_version`, `metadata`.

Une hypothèse ou une intention supposée placée dans `facts` provoque une erreur explicite.

### `ExpertReport`

Résultat normalisé d'un futur expert.

Champs :

- `report_id`, `request_id`, `producer` ;
- `findings`, `conclusions`, `recommendations`, `proposed_actions`, `questions_to_ask` ;
- `missing_information`, `risks` ;
- `sources`, `source_evidence` ;
- `contradictions`, `assumptions`, `scenarios` ;
- `confidence_assessments` ;
- `warnings`, `errors`, `status` ;
- `schema_version`, `metadata`.

`validate_for_request(request)` vérifie que le rapport concerne la bonne requête. Les identifiants de sources et de preuves sont uniques. Toute preuve référence une source du rapport. Une source marquée comme consultée référence une preuve réussie ou un cache explicitement identifié.

### `KnowledgeSource`

Description d'une source, distincte de la preuve qu'elle a été utilisée.

Champs principaux : identité, nom, organisme, catégorie, type, officialité, caractère interne, confidentialité, statut de connexion, référence, dates de publication et d'effet, date de consultation, juridiction, domaines, version, fraîcheur et métadonnées.

`consulted_at` ne peut être renseigné sans `retrieval_evidence_id`, et réciproquement. Le rapport vérifie ensuite l'existence et le statut de cette preuve.

### `SourceEvidence`

Preuve d'une tentative ou d'un accès à une source.

Champs : `evidence_id`, `source_id`, `access_mode`, `consultation_status`, `occurred_at`, `exact_reference`, `excerpt_or_fingerprint`, `access_result`, `error`, version et métadonnées.

Statuts :

- `NOT_ATTEMPTED` : aucune tentative ;
- `PLANNED` : accès futur seulement ;
- `SUCCEEDED` : accès réel réussi ;
- `FAILED` : tentative en échec avec erreur explicite ;
- `CACHE_HIT` : utilisation d'un contenu précédemment récupéré, jamais présentée comme consultation directe du jour.

`SUCCEEDED` et `CACHE_HIT` exigent un horodatage avec fuseau, une référence exacte et un résultat d'accès. `FAILED` exige une erreur.

### `MissingInformation`

Information ou pièce nécessaire mais absente : identifiant, description, raison, criticité, destinataire, question suggérée, caractère bloquant, domaine, version et métadonnées.

### `RiskAssessment`

Risque juridique, social, financier, opérationnel ou stratégique : identifiant, type, description, niveau, probabilité facultative entre 0 et 1, impact, horizon, preuves, actions de réduction, domaine, version et métadonnées.

Niveaux : `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Un risque `CRITICAL` sans description ou impact est invalide. Tous les risques doivent rester motivés ; un risque n'est pas un fait établi.

### `ConfidenceAssessment`

Une instance évalue une seule dimension. Un rapport ne peut porter qu'une instance par dimension.

Dimensions :

- `SOURCE_RELIABILITY` ;
- `EXTRACTION_CONFIDENCE` ;
- `QUESTION_RELEVANCE` ;
- `CASE_COMPLETENESS` ;
- `EXPERT_ANALYSIS_CONFIDENCE` ;
- `LEGAL_SOLIDITY` ;
- `STRATEGIC_UNCERTAINTY`.

Niveaux : `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`. Le score facultatif est borné entre 0 et 1. Si `level=None`, `known` vaut `False` et aucun score n'est autorisé. Pour `STRATEGIC_UNCERTAINTY`, un niveau élevé signifie une forte incertitude, pas une forte confiance.

## 5. Objets et enums complémentaires

`Statement` porte un identifiant, un texte, une catégorie, des références de preuves et des métadonnées. `StatementKind` sépare :

- `ESTABLISHED_FACT` ;
- `DECLARED_INFORMATION` ;
- `ASSUMPTION` ;
- `SCENARIO` ;
- `ASSUMED_INTENTION`.

Les autres enums sont limités aux statuts réellement nécessaires : confidentialité, rapport, connexion, consultation, catégorie de source, criticité, niveau et dimension de confiance.

## 6. Règles de validation

- identifiants, question et libellés structurants non vides ;
- valeurs d'enum explicites ;
- rapport lié à la bonne requête ;
- faits et déclarations strictement séparés ;
- hypothèses et scénarios strictement séparés dans le rapport ;
- intention supposée interdite dans les faits ;
- preuve réussie ou issue du cache impossible sans horodatage, référence et résultat ;
- horodatages de consultation obligatoirement munis d'un fuseau ;
- preuve en échec munie d'une erreur ;
- source consultée liée à une preuve cohérente du rapport ;
- probabilité et scores dans `[0, 1]` ;
- au plus une confiance par dimension ;
- risque `CRITICAL` avec description et impact ;
- métadonnées et contexte exclusivement JSON compatibles ;
- clés de métadonnées obligatoirement textuelles ;
- clés inconnues hors `metadata` refusées.

Les erreurs utilisent `ValueError` pour une valeur incohérente et `TypeError` pour un type incompatible, avec le champ concerné dans le message.

## 7. Sérialisation et désérialisation

Chaque objet principal expose :

```python
payload = contract.to_dict()
restored = type(contract).from_dict(payload)
```

Règles :

- dictionnaires, listes, scalaires JSON et valeurs nulles seulement ;
- enums sérialisés par leur valeur canonique ;
- tuples sérialisés en listes JSON ;
- dates et horodatages en ISO-8601 ;
- fuseau conservé pour les horodatages ;
- champs facultatifs conservés avec `null` ou une collection vide stable ;
- métadonnées inconnues conservées intégralement ;
- champs inconnus au premier niveau rejetés pour détecter une dérive de version.

Le gel récursif empêche qu'une liste ou un dictionnaire fourni par l'appelant soit modifié après construction du contrat.

## 8. Exemple synthétique

Scénario : un salarié fictif déclare des heures supplémentaires non payées, sans bulletin ni relevé horaire.

```python
from automation.contracts import (
    ConfidenceAssessment, ConfidenceDimension, ConfidenceLevel,
    CriticalityLevel, ExpertReport, ExpertRequest, MissingInformation,
    ReportStatus, RiskAssessment, Statement, StatementKind,
)

declaration = Statement(
    "DECL_OVERTIME_SYN",
    "Le salarié fictif déclare des heures supplémentaires non payées.",
    StatementKind.DECLARED_INFORMATION,
)

missing_payslip = MissingInformation(
    "MISS_PAYSLIP_SYN",
    "Bulletin de la période.",
    "Nécessaire pour contrôler les rubriques.",
    CriticalityLevel.HIGH,
    "salarié",
    "Pouvez-vous fournir le bulletin fictif ?",
    True,
    "paie",
)

request = ExpertRequest(
    "REQ_OVERTIME_SYN",
    "Quelles vérifications mener ?",
    "paie",
    facts=(),
    declared_information=(declaration,),
    missing_information=(missing_payslip,),
    metadata={"synthetic_only": True},
)

report = ExpertReport(
    "REPORT_OVERTIME_SYN",
    request.request_id,
    "synthetic_contract_example",
    conclusions=("Le non-paiement n'est pas établi.",),
    questions_to_ask=("Quels horaires sont déclarés ?",),
    missing_information=request.missing_information,
    risks=(RiskAssessment(
        "RISK_OVERTIME_SYN", "financial",
        "Écart de rémunération à vérifier.", CriticalityLevel.MEDIUM,
        None, "Rappel éventuel à qualifier.", "court terme", domain="paie",
    ),),
    confidence_assessments=(ConfidenceAssessment(
        "CONF_COMPLETENESS_SYN", ConfidenceDimension.CASE_COMPLETENESS,
        ConfidenceLevel.VERY_LOW, 0.1,
        "Aucun bulletin ni relevé horaire.",
    ),),
    status=ReportStatus.PARTIAL,
    metadata={"synthetic_only": True},
)
report.validate_for_request(request)
```

La déclaration ne devient jamais un fait. Le résultat expose les pièces manquantes, une question, un risque et une complétude très faible.

## 9. Rétrocompatibilité et ARCH-02

ARCH-01 n'altère aucun dictionnaire legacy. ARCH-02 devra ajouter des adaptateurs aux frontières, sous tests de non-régression :

```text
dict legacy -> validation/normalisation -> contrat commun
contrat commun -> projection -> mêmes clés et valeurs legacy
```

Stratégie prévue :

1. capturer des fixtures synthétiques représentatives des payloads actuels ;
2. créer un adaptateur par frontière, sans importer les moteurs dans le paquet de contrats ;
3. conserver les clés non mappées sous une extension `metadata.legacy` ;
4. comparer les sorties legacy avant/après ;
5. activer les nouveaux chemins derrière un mécanisme réversible ;
6. migrer Paie seul comme expert pilote après validation des adaptateurs ;
7. ne migrer Juriste et les autres domaines qu'après retour du pilote.

Aucun adaptateur métier complet n'est inclus dans ce lot.

## 10. Limites du lot

- aucun expert, connecteur, routeur ou orchestrateur n'utilise encore ces contrats ;
- aucun `KnowledgeGateway` n'est créé ;
- aucune source n'est interrogée ;
- aucun résultat utilisateur ne change ;
- aucune agrégation de confiance n'est définie ;
- aucune règle de droit, de paie ou de stratégie n'est ajoutée ;
- aucune persistance, authentification ou politique d'accès n'est implémentée ;
- les adaptateurs legacy relèvent d'ARCH-02.

Le Strategic Reasoning Engine reste hors périmètre. Il ne pourra être envisagé qu'après stabilisation des contrats, adaptateurs, connecteurs officiels, accès aux corpus internes et migration du pilote Paie.

## Limite connue du contrôle de confidentialité

Le validateur de confidentialité Paie actuel peut assimiler certains mots majuscules de 8 ou 11 caractères à des codes BIC. Les 35 alertes observées sur les fichiers ARCH-01 ont été vérifiées : elles sont toutes des faux positifs, portant notamment sur `CRITICAL`, `INTERNAL`, `OFFICIAL` et `SCENARIO`. Aucun code BIC réel ni renseignement bancaire réel n'est présent dans le lot.

La correction du validateur relève d'un lot technique séparé. ARCH-01 n'ajoute aucune exception générale destinée à désactiver ou contourner ce contrôle.

## 11. Bénéfice concret pour le délégué syndical

Le socle permet à terme de présenter une analyse où chaque élément est qualifié : déclaration, fait établi, hypothèse ou scénario. Les pièces manquantes deviennent des questions actionnables, les risques restent motivés, une source n'est dite consultée qu'avec une preuve et la confiance explique séparément fiabilité, pertinence, complétude et solidité. Le délégué peut ainsi construire un dossier plus clair sans recevoir une certitude artificielle.
