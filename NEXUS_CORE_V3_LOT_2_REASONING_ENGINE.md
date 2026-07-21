# Nexus Core V3 — LOT 2 — Reasoning Engine

## Objectif

CORE 2 construit un raisonnement générique à partir des objets de
`NEXUS_CORE`. Il ne répond pas à une question, ne produit aucune conclusion
juridique et n’exécute aucune règle métier. Sa sortie est une trace
structurelle expliquant les faits disponibles, leurs liens, leurs accords,
leurs contradictions et leurs lacunes.

## Architecture

Le sous-paquet `NEXUS_CORE/reasoning/` dépend exclusivement de `NEXUS_CORE` et
de la bibliothèque standard Python 3.10.

- `models.py` : modèles immuables du raisonnement ;
- `facts.py` : projection fidèle Evidence vers Fact ;
- `correlation.py` : liens entre faits du même sujet et du même type ;
- `corroboration.py` : compatibilité entre faits de sources distinctes ;
- `conflicts.py` : détection et explication sans arbitrage ;
- `missing_evidence.py` : vérification d’exigences explicitement injectées ;
- `confidence.py` : confiance technique, documentaire et structurelle ;
- `report.py` : construction et export sûr ;
- `contracts.py` : Protocols d’adaptation ;
- `pipeline.py` : séquence déterministe des sept étapes ;
- `_identity.py` : identifiants stables issus de références techniques.

## Pipeline

1. Evidence → Facts ;
2. Facts → Correlations ;
3. Correlations → Corroborations ;
4. Correlations → Conflicts ;
5. exigences injectées → Missing Evidence ;
6. structure obtenue → Confidence Assessment ;
7. assemblage → Reasoning Report.

Chaque étape est enregistrée dans un `ReasoningStep`. Le pipeline n’ajoute
aucune Evidence, ne fusionne aucun Fact et ne sélectionne aucune alternative.

## Modèles

`Fact` conserve la référence vers l’Evidence d’origine, le sujet, le type de
fait, la même valeur immuable, la période, la provenance, la confiance, la
qualité et le statut de validation. `FactExtractor` produit au maximum un fait
par identifiant Evidence et refuse les collisions incohérentes.

`FactCorrelation` relie au moins deux faits partageant sujet et type. Il ne
contient aucune valeur fusionnée.

`Corroboration` référence des faits compatibles provenant d’au moins deux
sources techniques distinctes. `CorroborationStrength` décrit uniquement le
nombre de sources distinctes : deux, trois ou plusieurs.

`ReasoningConflict` conserve toutes les références concernées et une
`ConflictExplanation` codée. Ses invariants imposent `arbitrated = false` et
`selected_fact = None`.

`MissingEvidence` résulte exclusivement d’une liste de `FactType` requise par
l’appelant. Le moteur distingue absence du type et période non couverte. Il ne
crée jamais la preuve manquante.

`ConfidenceAssessment` conserve une confiance technique. Elle ne représente
ni probabilité juridique, ni chance prud’homale, ni décision.

`ReasoningReport` regroupe faits, corrélations, corroborations, conflits,
preuves manquantes, confiance, étapes et diagnostics techniques.

## Confiance technique

Le score est déterministe et uniquement structurel : moyenne arithmétique de
la confiance technique des faits, du ratio de faits validés et d’un facteur de
complétude diminuant avec les conflits et preuves manquantes. Sans fait, le
score vaut zéro. Une preuve manquante rend le raisonnement `INSUFFICIENT` ; un
conflit le limite. Cette formule ne hiérarchise aucune source et n’a aucune
signification juridique.

## Protocols

- `FactProducer` : transforme des Evidence en `FactCollection` ;
- `ReasoningEngine` : construit un `ReasoningReport` ;
- `ReasoningReporter` : rend un rapport sous une forme transportable.

Les Protocols sont structurels et n’imposent aucune classe métier.

## Confidentialité

Les identifiants dérivés utilisent uniquement des références techniques
pseudonymisées et un condensat SHA-256 tronqué. Les diagnostics sont limités à
un code, une catégorie et une gravité. Les valeurs Fact conservent les objets
Evidence immuables mais restent masquées dans `repr` et dans le JSON sûr. Les
explications de conflit ne contiennent jamais les valeurs comparées.

Aucun nom, NIR, IBAN, RIB, email, téléphone, adresse, clé réelle ou document
réel n’est introduit.

## Sérialisation

`JsonReasoningReporter` réutilise la sérialisation CORE : JSON déterministe,
enums explicites, dates ISO 8601, clés triées, valeurs Evidence masquées et
`schema_version = "1.0"`.

## Dépendances

Sont autorisés : imports relatifs `NEXUS_CORE`, `dataclasses`, `datetime`,
`enum`, `hashlib`, `itertools`, `collections` et `typing`.

Sont interdits : moteurs Paie, Retraite, CSE, CSSCT, Protection Sociale ou
Juriste, `automation`, connecteurs, API, réseau, bases de données, frameworks
web, stockage persistant et imports dynamiques.

## Tests

Sept suites couvrent extraction fidèle, absence d’invention, conservation de
la provenance/période/confiance, corrélations sans fusion, corroborations,
conflits sans arbitrage, preuves manquantes explicites, confiance technique,
rapport complet, JSON sûr, Protocols, frontières d’import, absence de cycle et
Python 3.10.

## Évolutions futures

- CORE 3 construira le Conflict Resolver en consommant les conflits et
  explications de CORE 2, sans modifier le Reasoning Engine ;
- CORE 4 construira l’Orchestrateur Nexus ;
- CORE 5 construira le Cockpit DS.

Ces trois composants, toute IA générative, toute priorité documentaire et
toute décision automatique restent hors du LOT CORE 2.
