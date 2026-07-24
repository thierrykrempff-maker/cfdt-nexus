# LOT R1B — Audit préalable

## Référence

- Branche auditée : `main`
- SHA audité : `acfb7812d70677a355457a265a144df214f8ca28`
- Socles examinés : Syndical Reasoning Engine R0 et extension R1A
- État Git : R0 et R1A présents dans le working tree, sans commit

## Composants réutilisables

Le moteur R0 fournit déjà les contrats transverses nécessaires :

- `SyndicalCaseInput` pour les faits déclarés ou établis, les pièces, les sources,
  l'urgence et les informations manquantes ;
- `SyndicalReasoningReport` pour le rapport transverse, la prudence, les limites
  et la hiérarchie des sources ;
- `SyndicalReasoningEngine` pour produire le rapport de base sans conclure
  automatiquement ;
- la politique de sources, le protocole, la prudence et les stratégies générales ;
- le pont Runtime fail-safe et son feature flag existant.

R1A fournit des projections spécialisées réutilisables :

- `PrioritizedQuestion` pour ordonner les questions et expliciter leur objectif ;
- `EvidencePriority` et `EvidenceRequirement` pour classer les preuves ;
- `PositionAnalysis` pour séparer les argumentations contradictoires ;
- le principe d'une analyse spécialisée contenant le rapport R0 complet ;
- la sélection Runtime conditionnelle et le champ générique `domain_analysis`.

## Écarts à couvrir

R0 et R1A ne modélisent pas encore :

- les mesures et qualifications disciplinaires concurrentes ;
- les étapes et délais d'une procédure disciplinaire ;
- l'insuffisance professionnelle ou de résultats, qui ne doivent pas être
  confondues automatiquement avec une faute ;
- l'abandon de poste et le refus d'une modification contractuelle ;
- la protection particulière des représentants du personnel ;
- les questions, preuves et stratégies propres à ces situations.

## Architecture retenue

R1B sera une extension additive du paquet `SYNDICAL_REASONING_ENGINE`.

Les modèles disciplinaires référenceront directement les contrats génériques de
R1A (`PrioritizedQuestion`, `EvidenceRequirement`, `PositionAnalysis`) au lieu de
les dupliquer. Le moteur spécialisé :

1. recevra un `SyndicalCaseInput` ;
2. conservera le rapport transverse R0 ;
3. détectera des indices, jamais une vérité juridique ;
4. conservera plusieurs qualifications provisoires lorsque les informations sont
   insuffisantes ;
5. produira questions, positions contradictoires, preuves et stratégies ;
6. ajoutera une analyse spécifique de la protection, sans conclusion automatique.

Le Runtime utilisera le même feature flag que R0. La priorité spécialisée sera :

1. R1B si un domaine disciplinaire est détecté ;
2. R1A si une modification du contrat ou des conditions de travail est détectée ;
3. R0 dans les autres situations syndicales.

Cette priorité évite qu'un refus de modification contractuelle soit traité
uniquement comme un dossier R1A alors que la question porte sur une sanction.

## Prévention des duplications

- aucune nouvelle classe générique de question, preuve ou position ;
- aucune nouvelle politique transverse de sources ou de confidentialité ;
- aucune copie du pont Runtime ;
- aucune règle dans le serveur ou le mapper de rapport ;
- aucune conclusion sur la justification ou la légalité de la sanction ;
- aucune donnée documentaire complète, aucun réseau et aucun connecteur.

## Périmètre prévu

Créations fonctionnelles limitées à des modules R1B dédiés :

- modèles et qualifications disciplinaires ;
- détection et moteur spécialisé ;
- questions, preuves, argumentations et stratégies ;
- sept scénarios entièrement synthétiques ;
- tests unitaires et Runtime.

Modifications prévues :

- façade publique `SYNDICAL_REASONING_ENGINE/__init__.py` ;
- sélection spécialisée dans
  `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py`.

Les contrats R0/R1A, le feature flag, les connecteurs, le Core, les experts,
CSSCT et la Paie V2 restent inchangés.
