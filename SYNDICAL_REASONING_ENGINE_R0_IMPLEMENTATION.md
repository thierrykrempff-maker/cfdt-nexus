# LOT R0 — Rapport d'implémentation

## Architecture créée

Le lot ajoute un domaine autonome `SYNDICAL_REASONING_ENGINE` composé de
contrats immuables, d'un protocole en 18 étapes, d'une politique de sources,
d'une politique de prudence, d'un générateur d'options progressives et d'un
moteur d'assemblage.

## Contrats ajoutés

- `SyndicalCaseInput`
- `CaseFact`
- `AvailablePiece`
- `SourceReference`
- `SourceAssessment`
- `SourceContradiction`
- `ActionOption`
- `ActionPlanStep`
- `SyndicalReasoningReport`
- niveaux de confiance, urgence, vérification et confidentialité.

## Étapes du protocole

Le protocole couvre explicitement les 18 étapes exigées, de la reformulation
neutre jusqu'à la conclusion prudente. La liste ordonnée est incluse dans
chaque rapport pour rendre l'exécution observable et testable.

## Scénario de référence

Le scénario laboratoire / passage en équipe postée est entièrement synthétique.
Il couvre contrat, horaires, travail posté, paie, santé-sécurité, consultation
CSE, sources applicables, preuves, urgence et stratégie graduée. Le rapport ne
conclut jamais automatiquement à la légalité ou à l'illégalité.

## Intégration Runtime

Le pont optionnel :

- réutilise la route existante ;
- construit un dossier incomplet sans inventer de fait ;
- adapte uniquement les métadonnées HTTPS déjà présentes ;
- appelle le moteur ;
- ajoute une section courte au rapport ;
- préserve l'objet historique à l'identique si le flag est désactivé,
  non applicable ou en fallback.

Le comportement historique reste le comportement par défaut.

## Fichiers créés

- paquet `SYNDICAL_REASONING_ENGINE/` ;
- `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py` ;
- cinq fichiers de tests ciblés ;
- quatre documents R0.

## Fichiers modifiés

- `NEXUS_RUNTIME_INTEGRATION/config.py`
- `NEXUS_RUNTIME_INTEGRATION/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/report_mapper.py`
- `apps/nexus-local-interface/server.py`

## Limites et reports

Les lots futurs pourront connecter des contrats métiers supplémentaires,
enrichir les relations de contradiction, fournir des modèles de documents et
ajouter des stratégies spécialisées. R0 n'ajoute aucune recherche, règle
juridique, règle paie, source, connecteur ou document.
