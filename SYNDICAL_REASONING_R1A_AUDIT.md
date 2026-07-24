# LOT R1A — Audit modification du contrat et conditions de travail

## Référence

- Branche : `main`
- SHA audité : `acfb7812d70677a355457a265a144df214f8ca28`
- État de départ : LOT R0 présent dans le working tree, non committé

## Composants R0 réutilisables

- `SyndicalCaseInput` pour les faits, pièces, sources et informations manquantes ;
- `SyndicalReasoningEngine` pour le protocole transversal en 18 étapes ;
- `ActionOption` et `ActionPlanStep` pour les actions graduées ;
- politique de sources pour les accords, Convention Chimie, Code du travail et
  jurisprudence ;
- politique de confiance et de prudence ;
- pont Runtime et son feature flag désactivé par défaut ;
- projections courte et experte du rapport.

## Lacunes métier à couvrir

R0 ne distingue pas finement les formes de changement : horaires, équipe,
poste, qualification, classification, mobilité, suppression de poste,
réorganisation ou rémunération. Il ne fournit pas non plus :

- qualifications concurrentes explicitement justifiées ;
- questions métier priorisées ;
- arguments équilibrés salarié / employeur ;
- preuves classées indispensables, utiles et complémentaires ;
- cinq scénarios comparables.

## Risques de duplication

- recopier le moteur transversal R0 ;
- créer un deuxième modèle de dossier ;
- réimplémenter la hiérarchie des sources ;
- confondre détection d'un indice et qualification certaine ;
- transformer une stratégie progressive en recommandation contentieuse ;
- embarquer une règle juridique ou une jurisprudence non fournie.

## Architecture retenue

Le sous-domaine R1A est ajouté dans `SYNDICAL_REASONING_ENGINE` :

- `contract_change_models.py` : contrats spécialisés ;
- `contract_change_questions.py` : questions priorisées ;
- `contract_change_evidence.py` : preuves classées ;
- `contract_change_arguments.py` : analyses équilibrées ;
- `contract_change_strategies.py` : cinq stratégies ordonnées ;
- `contract_change_engine.py` : projection métier déléguant le socle à R0 ;
- `contract_change_scenarios.py` : cinq cas synthétiques.

Le pont Runtime R0 choisit ce moteur uniquement lorsqu'un indice de changement
contractuel ou organisationnel est détecté. Le même feature flag est conservé.
Hors domaine, le moteur R0 reste utilisé ; flag désactivé ou erreur, le rapport
historique reste inchangé.

## Périmètre exact

Créations :

- sept modules R1A dans `SYNDICAL_REASONING_ENGINE/` ;
- tests ciblés R1A et Runtime ;
- trois livrables R1A.

Modifications :

- façade publique `SYNDICAL_REASONING_ENGINE/__init__.py` ;
- pont `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py`.

Aucun expert, connecteur, corpus, règle paie, composant Core ou interface
visuelle n'est modifié.
