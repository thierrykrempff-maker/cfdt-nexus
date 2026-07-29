# Rapport de préparation de la release CFDT Nexus V1

## 1. Verdict provisoire

`READY_WITH_LIMITATIONS`

## 2. SHA audité

`77341831b1b16e4bcec5ee5c44995c0cca893594`

## 3. Périmètre V1

La V1 garantit `QUESTION_SALARIE`, `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`, la
comparaison sources–faits lorsque les sources existent, et un mode dégradé honnête.
Elle reste locale, assistée et soumise à validation humaine.

## 4. Résultats fonctionnels

Le parcours navigateur réel a été validé depuis le portail jusqu'à la restitution :
choix du parcours, formulaire progressif, appel HTTP, synthèse, analyse détaillée
repliée, copie et export volontaire. Le correctif de sortie ajoute explicitement la
racine du dépôt au `PYTHONPATH` du sous-processus routeur.

## 5. Résultats des 11 cas

- parcours corrects : 11/11 ;
- faits principaux corrects : 11/11 ;
- score moyen : 85,36/100 ;
- cas complets au-dessus de 75 : 8/9 ;
- source inventée : 0 ;
- contamination : 0 ;
- REAL-05 et REAL-06 : suspendus ;
- REAL-09 : 74/100, procédure interne applicable absente ;
- taille moyenne : 29 891,55 octets ;
- taille maximale : 39 595 octets.

## 6. Sources et connecteurs

Les accords INEOS et la CCNIC locale ont été retrouvés dans l'environnement
autorisé. Les connecteurs externes restent dépendants de la configuration et de la
disponibilité. Les connecteurs avancés restent désactivés par défaut et aucun
connecteur indisponible n'est simulé.

## 7. Tests

La suite obligatoire V1 réussit à 100 % :

- LOT 1 élargi : 84/84 ;
- sélection des connecteurs : 11/11 ;
- LOT 2 et LOT 3 : 34/34 ;
- contrats release, confidentialité et E2E : 13/13 ;
- cockpit salarié ciblé : 16/16 ;
- suite complète officielle : 3 203/3 203 en 520,60 secondes.

Les trois tests de formats facultatifs réussissent dans l'environnement audité.
Leurs décorateurs les marquent `SKIPPED` lorsqu'une dépendance manque.
`pip check` ne signale aucune dépendance cassée. Les dix fichiers Python modifiés
ou créés passent l'analyse syntaxique avec la grammaire Python 3.10 ; l'exécution
complète a été réalisée avec Python 3.12.13, seul interpréteur disponible.

## 8. Installation

`requirements.txt` décrit le cœur et les validations reproductibles.
`requirements-optional.txt` décrit les formats PDF/PPTX/XLSX facultatifs. Aucune
installation silencieuse n'est réalisée.

## 9. Lancement

Le lanceur Windows accepte le mode dégradé, contrôle Python, charge éventuellement
une configuration locale ignorée par Git et ouvre automatiquement le navigateur.
Le test indépendant a retourné `/health` 200, la version 1.0.0, chargé le logo
local, puis libéré le port 8765 sans processus orphelin.

## 10. Interface

Les parcours sont distincts, la synthèse est prioritaire, l'analyse détaillée est
fermée par défaut et le rendu 390 px ne provoque aucun débordement horizontal.

## 11. Export

Copie, impression et téléchargement sont limités à la synthèse publique. La version
1.0.0 est incluse. Les diagnostics détaillés et sources rejetées ne sont pas
exportés.

## 12. Confidentialité

Aucun constat bloquant. Les erreurs publiques sont génériques, les sessions sont
isolées, les secrets restent locaux et ignorés, et aucun chemin utilisateur ne
figure dans les captures de release.

## 13. Dépendances

Les dépendances obligatoires et facultatives sont séparées. Leur disponibilité est
exposée dans `/health` sans les importer ni les installer.

## 14. Documentation

README, guide utilisateur, guide technique, limites connues, audit initial,
rapport confidentialité et changelog 1.0.0 sont fournis.

## 15. Limites connues

REAL-09, disponibilité variable des sources externes, connecteurs
metadata-only/architecture-only, absence de calcul paie fiable, mode local et
absence de persistance serveur.

## 16. Anomalies corrigées

- version produit contradictoire ;
- absence de manifeste de dépendances ;
- formats facultatifs comptés comme échecs ;
- lancement impossible sans secrets externes ;
- absence de lanceur d'arrêt ;
- sous-processus routeur incapable d'importer les paquets à partir d'un lancement
  Windows propre ;
- erreur HTTP interne susceptible de journaliser un message détaillé ;
- impression absente ;
- incohérence temporaire HTML/JavaScript pouvant bloquer le rendu lors d'un cache
  navigateur ancien.

## 17. Anomalies restantes

Aucune anomalie bloquante connue. Les limites fonctionnelles documentées restent
volontaires et visibles.

## 18. Risques

La qualité des sources externes et des corpus locaux dépend de leur configuration,
de leur fraîcheur et de leur champ d'application. La validation humaine demeure
obligatoire. Une exécution native sur Python 3.10 reste recommandée avant diffusion
sur un poste qui utiliserait précisément cette version.

## 19. Décision

`READY_WITH_LIMITATIONS`

Le tag `v1.0.0` ne doit être créé qu'après approbation formelle.
