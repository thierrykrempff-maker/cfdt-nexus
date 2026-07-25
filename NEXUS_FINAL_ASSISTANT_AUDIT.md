# Audit transversal — Assistant final CFDT Nexus

## Référence

- SHA audité : `8f1fa63afc39c3628983971a6d0cffa020f7c4ae`
- Pipeline utilisateur réel : interface locale → `assistant_ds_router.py` → orchestrateur historique → enrichissements Core/connecteurs/CSE/Retraite/Protection sociale/Syndical Reasoning → rapport.
- Les moteurs spécialisés sont protégés par des feature flags désactivés par défaut.

## Pipeline actuel

Le serveur applique des enrichissements successifs. Chaque Runtime possède son propre contrat, son diagnostic et son mapper. Le Syndical Reasoning Runtime articule R0 à R2C, tandis qu’Expert Paie V2 dispose d’un Runtime séparé. Le rapport final reste historiquement assemblé par mutations successives.

## Écarts observés

- formats de sortie hétérogènes entre moteurs historiques et récents ;
- sélection répartie entre routeur, Runtime et moteurs spécialisés ;
- risques de doublons dans les questions, sources et recommandations ;
- contradictions non rapprochées transversalement ;
- traces techniques distinctes ;
- absence d’un contrat final commun pour les faits, hypothèses, risques, actions et limites ;
- risque de sur-sollicitation sans limite commune du nombre de moteurs ;
- confidentialité contrôlée aux frontières publiques, mais sans gate métier commun avant la synthèse.

## Compatibilités retenues

- les contrats métier existants ne sont pas modifiés ;
- les sorties existantes passent par des adaptateurs explicites ;
- le Syndical Reasoning Runtime reste la façade de R0–R2C ;
- Expert Paie V2 reste conditionné par son propre flag ;
- le rapport historique est conservé par identité lorsque l’Assistant Final est désactivé ou échoue ;
- CSE Memory et la recherche documentaire ne transmettent que des métadonnées bornées.

## Pipeline cible

Question → normalisation → contrôle de confidentialité → détection multi-domaines → plan borné → runtimes existants → adaptation commune → contradictions → sources/questions → synthèse → actions brouillons → contradicteur → restitution publique.

Cette couche ne crée aucune règle métier, aucun connecteur et aucun calcul.
