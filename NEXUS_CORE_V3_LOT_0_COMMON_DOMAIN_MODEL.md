# Nexus Core V3 — LOT 0 — Modèle métier commun

## Objectif

CORE 0 définit un langage métier commun, neutre et minimal pour les domaines
de CFDT Nexus. Il fournit des objets de transport et des contrats d’adaptation
sans exécuter de règle métier et sans importer les moteurs existants.

## Périmètre

Le lot couvre les identités techniques pseudonymisées, personnes et emplois,
périodes, documents, provenance, confiance technique, qualité des preuves,
Evidence, findings, conflits, recommandations, requêtes multidomaines,
résultats de domaines, rapports par références, confidentialité et
sérialisation déterministe.

## Non-objectifs

CORE 0 ne fournit ni orchestrateur, ni routeur, ni stockage, ni API, ni
interface, ni authentification, ni graphe complet, ni résolveur de conflits.
Il n’implémente aucune règle juridique, paie, retraite, CSE, CSSCT ou
protection sociale. Aucun modèle historique n’est déplacé, remplacé ou migré.

## Emplacement et architecture

Le noyau est placé dans `NEXUS_CORE/`, paquet racine autonome au même niveau
que les domaines existants. Ce choix rend sa frontière visible et évite de le
rattacher à `automation`, aux connecteurs ou à un moteur particulier.

Les modules sont spécialisés :

- `identifiers.py` : identifiants techniques sans donnée personnelle ;
- `entities.py` et `periods.py` : références pseudonymisées et temps civil ;
- `documents.py` et `provenance.py` : références documentaires et traçabilité ;
- `quality.py` : confiance technique, qualité et validation ;
- `values.py` et `evidence.py` : valeurs typées extensibles et preuves ;
- `findings.py`, `conflicts.py`, `recommendations.py` : constats neutres ;
- `analysis.py` : requêtes, résultats et rapports multidomaines ;
- `contracts.py` : Protocols d’adaptation ;
- `privacy.py` et `serialization.py` : labels, redaction et JSON stable.

Les modèles sont principalement des dataclasses gelées avec slots. La
composition est utilisée à la place de l’héritage métier.

## Dépendances

### Autorisées

Uniquement la bibliothèque standard Python 3.10 : `dataclasses`, `datetime`,
`decimal`, `enum`, `json`, `re` et `typing`, ainsi que les imports relatifs
internes à `NEXUS_CORE`.

### Interdites

- tous les moteurs existants ;
- `automation` et la Connector Platform ;
- les connecteurs officiels ;
- les frameworks web et les API ;
- les clients réseau ;
- les imports dynamiques ;
- les bases de données et caches.

Le graphe d’import interne fait l’objet d’un test d’absence de cycle.

## Modèles communs

Les identités (`EntityId`, `CorrelationId`, `AnalysisId`, `DocumentId`,
`EvidenceId`, `FindingId`) encapsulent uniquement des clés techniques. Les
références de personne ne proposent aucun champ nom, prénom, NIR, adresse,
email ou téléphone.

`Period` expose seulement l’ouverture, la fermeture, le chevauchement et le
containment calendaires. Ces méthodes ne portent aucune inférence juridique.

`DocumentReference` décrit un document par son type, sa source et ses
métadonnées. `MEDICAL_OR_HEALTH_DOCUMENT` est un type descriptif : le noyau ne
stocke ni donnée médicale ni contenu documentaire.

`Evidence` conserve systématiquement sujet, type de fait, valeur typée,
période, document, provenance, confiance technique, qualité, validation,
producteur, métadonnées et date de création. Les valeurs admises sont des
dataclasses explicites : texte, nombre, booléen, temps, référence d’entité ou
extension structurée. Aucun `Any` libre n’est utilisé.

Un `EvidenceConflict` conserve toutes les références concernées et ne possède
aucun champ de valeur sélectionnée. Les findings et recommandations utilisent
des codes techniques ; ils ne portent aucune conclusion juridique.

## Contrats d’adaptation

Les Protocols `EvidenceProducer`, `FindingProducer`,
`RecommendationProducer`, `DomainAnalyzer` et `DomainResultAdapter`
permettront à chaque moteur de construire progressivement des résultats CORE.
Ils n’imposent aucune classe de base et n’importent aucun moteur.

`DomainAnalysisResult` conserve les preuves, constats, conflits,
recommandations, diagnostics et métadonnées d’un seul domaine.
`AnalysisReport` n’agrège que des identifiants et des références de résultats ;
il ne fusionne pas les réponses.

## Confidentialité

- `PersonReference` exige une identité pseudonymisée ;
- les formats manifestement personnels sont refusés dans les identifiants ;
- `ConfidentialityLevel`, `DataSensitivity` et `RedactionStatus` étiquettent
  les données sans définir une politique RGPD globale ;
- `MetadataEntry` masque toujours sa valeur dans `repr` ;
- les valeurs Evidence masquent leur contenu dans `repr` et dans la
  sérialisation sûre par défaut ;
- `Diagnostic` n’accepte que code, catégorie, gravité et référence technique ;
- aucune donnée réelle ou confidentielle n’est incluse dans le lot.

## Sérialisation

`to_primitive()` et `to_json()` produisent une représentation stable : enums
par valeur publique, dates ISO 8601, décimaux sous forme textuelle, ordre JSON
trié et absence de représentation mémoire Python. Les métadonnées sensibles
sont remplacées par `<redacted>` par défaut. Les objets de premier niveau
portent `schema_version = "1.0"` pour préparer une évolution additive.

La sérialisation sans redaction existe uniquement comme primitive explicite
pour des adaptateurs contrôlés ; la valeur par défaut reste sûre.

## Stratégie d’extension

Les nouveaux domaines ajoutent leurs modèles propres hors du noyau et les
convertissent via les Protocols. Une valeur métier spécifique utilise
`CustomEvidenceValue` avec un code de type et des `MetadataEntry` typées.
L’ajout d’un domaine à `DomainSelection` ou d’un type documentaire constitue
une évolution additive versionnée ; aucune logique du domaine ne doit entrer
dans CORE.

## Migration progressive

1. conserver chaque moteur et son API publique ;
2. créer un adaptateur externe au noyau ;
3. mapper ses sorties vers `DomainAnalysisResult` ;
4. vérifier provenance, période, confiance et confidentialité ;
5. exposer des références dans `AnalysisReport` ;
6. migrer consommateur par consommateur sans suppression historique.

CORE 0 ne réalise aucune de ces migrations.

## Tests

Quatre suites dédiées couvrent les modèles, contrats, sérialisation et
frontières architecturales. Elles vérifient notamment pseudonymisation,
périodes, Evidence typée, conflits sans arbitrage, multidomaine, JSON stable,
redaction, absence de dépendance moteur, absence de réseau, absence d’import
dynamique, absence de cycle et grammaire Python 3.10.

## Risques

- multiplier prématurément les types communs ;
- confondre confiance technique et valeur juridique ;
- laisser un adaptateur contourner la redaction ;
- introduire une dépendance inverse depuis CORE ;
- transformer `CustomEvidenceValue` en conteneur universel non typé.

Ces risques sont contenus par le périmètre minimal, les Protocols et les tests
statiques.

## Étapes suivantes proposées

- CORE 1 : schémas de compatibilité et adaptateurs pilotes, sans orchestration ;
- CORE 2 : registre de schémas et validations inter-domaines ;
- CORE 3 : graphe Evidence commun ;
- lot ultérieur distinct : résolution de conflits ;
- lot ultérieur distinct : orchestrateur Nexus V3.
