# Revue d'architecture et d'intégration Nexus V2

## Périmètre

Cette revue couvre les lots V2-1A à V2-2C au commit parent
`09fb2f5aa2a0362f9801ce0f11bd68a657d09184` :

- Document Intelligence Center ;
- ingestion metadata-only ;
- API de navigation documentaire ;
- CSE Knowledge Engine ;
- CSE Decision & Action Tracker ;
- CSE Meeting Preparation Engine.

La revue porte sur le code réellement présent. Elle n'introduit ni réseau, ni
LLM, ni recherche sémantique, ni modification du Runtime, du Core, des
connecteurs, des experts ou des corpus.

## Architecture observée

Le flux complet est le suivant :

```text
Métadonnées documentaires injectées
  -> DocumentIngestionService
  -> DocumentGraph / MetadataIndex
  -> DocumentNavigationService
  -> CSEKnowledgeEngine
  -> CSEDecisionTracker
  -> CSEMeetingPreparationEngine
  -> dossier de préparation metadata-only
```

Le graphe de dépendances entre paquets est acyclique :

```text
DOCUMENT_INTELLIGENCE_CENTER
  <- CSE_KNOWLEDGE_ENGINE
  <- CSE_DECISION_TRACKER
  <- CSE_MEETING_ENGINE

CSE_DECISION_TRACKER
  <- CSE_MEETING_ENGINE

CSE_KNOWLEDGE_ENGINE
  <- CSE_MEETING_ENGINE
```

Les dépendances transversales utilisent les façades publiques des paquets.
La couche documentaire ne dépend d'aucune couche métier. Aucun paquet examiné
ne dépend du Runtime, de Nexus Core, d'un expert historique ou d'une
bibliothèque réseau.

## API publiques recensées

### Document Intelligence Center

La façade publique expose les modèles documentaires, le graphe, l'ingestion,
l'index metadata-only, le versioning, la navigation, les contrats de recherche
et les contrôles de métadonnées sûres. Les services structurants sont
`DocumentIngestionService`, `DocumentNavigationService`, `DocumentGraph` et
`MetadataIndex`.

### CSE Knowledge Engine

La façade expose `CSEKnowledgeEngine`, son contrat public, ses requêtes,
rapports, synthèses, éléments d'ordre du jour et sujets récurrents. La fonction
de normalisation partagée par les couches CSE est désormais exposée par la
façade publique.

### CSE Decision & Action Tracker

La façade expose le moteur, son contrat, les requêtes, éléments suivis,
statistiques, rapports, statuts et éléments d'ordre du jour.

### CSE Meeting Preparation Engine

La façade expose le moteur, son contrat, la requête de préparation, le dossier,
les références documentaires projetées, les indicateurs et les éléments
d'ordre du jour.

Les contrats publics sont sérialisables de façon déterministe. Les modèles
publics concernés sont immuables. La syntaxe reste compatible Python 3.10.

## Duplications examinées

- Les champs de requête `subject`, période et instance sont répétés entre
  couches. Cette répétition matérialise les frontières de chaque API et évite
  un couplage à un modèle de requête central.
- `NavigationDocument`, `CSEKnowledgeItem`, `TrackedCSEItem` et
  `PreparationDocumentReference` sont des projections différentes d'un même
  document. Elles limitent volontairement les données exposées à chaque
  couche ; leur fusion augmenterait le couplage sans bénéfice mesurable.
- `MetadataStatus` décrit l'état documentaire, alors que `TrackingStatus`
  décrit le cycle métier d'une décision ou d'une action. Les vocabulaires
  restent distincts, avec une conversion explicite.
- Les validations défensives de métadonnées sont répétées aux frontières du
  Tracker et du Meeting Engine. Cette redondance est conservée pour revalider
  les métadonnées héritées avant exposition.
- Les méthodes `to_dict()` et `to_json()` sont répétitives, mais une classe de
  base commune imposerait une dépendance transversale inutile.

## Anomalies démontrées et corrections minimales

### V2-REV-001 — Imports internes entre paquets — P1 résolu

Le test d'architecture a détecté huit imports directs vers des sous-modules
d'autres paquets V2. Ces imports contournaient les contrats publics.

Correction : export de `is_pseudonymous_id`, `validate_safe_metadata` et
`normalize_label` par les façades publiques, puis remplacement des imports
internes par des imports depuis les paquets racines.

### V2-REV-002 — Vocabulaire de statut incomplet — P1 résolu

Le scénario d'intégration d'une décision clôturée échouait avant même
l'ingestion : le statut documentaire public ne pouvait pas représenter
`OPEN`, `IN_PROGRESS`, `CLOSED` ou `CANCELLED`, alors que les moteurs aval les
interprètent explicitement.

Correction : ajout rétrocompatible de ces quatre valeurs à `MetadataStatus`.
Les valeurs documentaires historiques restent inchangées.

### V2-REV-003 — Résultat dépendant de l'ordre d'insertion — P1 résolu

Le test exécutant le même lot dans l'ordre normal puis inversé produisait deux
résultats différents. La clé de déduplication omettait le statut : deux
décisions de même date, famille et nature, mais d'états différents, entraient
en collision.

Correction : ajout du statut à la clé de déduplication. La correction est
locale, metadata-only et ne modifie pas les identifiants documentaires.

## Limitation connue

### V2-REV-004 — Granularité restante de la déduplication — P2

Conformément au choix V2-1B, le titre ne participe pas à la clé de
déduplication. Deux sources distinctes ayant exactement le même type, la même
date, la même famille, la même nature, la même version et le même statut
peuvent encore être rapprochées. Les identifiants stables et l'ingestion
contrôlée réduisent ce risque. Une évolution ne doit être envisagée qu'avec un
cas métier démontré et une règle d'identité documentée.

## Confidentialité

La chaîne reste metadata-only. Les tests vérifient le rejet d'une métadonnée
héritée contenant un chemin local avant son exposition. Les sorties ne
contiennent ni texte intégral, PDF, HTML, chunks, chemins locaux, données
personnelles, secrets ou contenu brut de corpus. Chaque couche aval revalide
les projections qu'elle expose.

## Déterminisme

Les tests couvrent :

- deux exécutions identiques donnant exactement le même JSON ;
- l'invariance du résultat à l'ordre d'insertion ;
- l'absence d'horloge implicite, d'UUID aléatoire et de variable
  d'environnement non injectée ;
- le tri stable des collections ;
- le comportement sûr d'un document orphelin.

Les dates métier sont fournies explicitement par les requêtes et métadonnées.

## Scénarios d'intégration

Le test transversal construit le graphe exclusivement à partir de métadonnées
synthétiques, puis traverse toutes les couches. Il vérifie :

1. la présence d'une décision ouverte dans le dossier ;
2. l'ajout à l'ordre du jour d'un engagement arrivé à échéance ;
3. l'exclusion d'une décision clôturée des décisions ouvertes ;
4. la détection d'un sujet récurrent ;
5. le rapprochement explicite d'un accord et d'un PV ;
6. le comptage d'une consultation en cours ;
7. le rejet d'une métadonnée interdite ;
8. la stabilité de la sérialisation ;
9. l'invariance à l'ordre d'insertion ;
10. la tolérance aux documents orphelins.

Quatre contrôles d'architecture complètent ces scénarios : API publiques,
frontières documentaires, imports interdits et sources de non-déterminisme.

## Résultats des validations

- Tests V2 ciblés : 155 réussites.
- Tests d'intégration ajoutés : 14 réussites.
- Suite complète : 2 433 réussites et 128 sous-tests réussis.
- Échecs : uniquement les trois anomalies historiques déjà qualifiées
  (isolation des imports Adapter et Contracts, conservation du payload Expert
  Paie en échec d'intégration).
- Syntaxe Python 3.10 : 30 fichiers V2 et d'intégration analysés avec succès.
- Matrice JSON : valide.
- `git diff --check` : réussi.
- Imports réseau, Runtime, Core et experts : aucun.
- Horloge implicite, UUID aléatoire et environnement non injecté : aucun.

## Recommandation

**READY WITH KNOWN LIMITATIONS**

Les anomalies P1 démontrées sont corrigées et couvertes par des tests de
non-régression. Aucun P0 ni P1 ouvert ne subsiste dans le périmètre examiné.
La limitation P2 sur la granularité de déduplication est documentée et ne
bloque pas une future campagne de fusion.
