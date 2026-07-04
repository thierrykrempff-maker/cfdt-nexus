# Audit V1 - CFDT Nexus

Date : 1er juillet 2026
Rôle : Architecte logiciel / CTO
Périmètre audité : dépôt `cfdt-nexus`, architecture documentaire, agents, cockpit, base documentaire, workflows, sécurité, tests et gouvernance.

## Synthèse exécutive

CFDT Nexus dispose déjà d'une base architecturale saine pour un projet encore jeune. Le dépôt montre une intention claire : séparer les agents, la base documentaire, les applications, le cockpit, les workflows, les tests, la configuration et la documentation.

Le point fort principal est la vision produit : CFDT Nexus n'est pas traité comme un simple chatbot, mais comme une future plateforme de travail syndical. C'est le bon angle.

Le point faible principal est que l'architecture est encore majoritairement déclarative : beaucoup de dossiers, peu de contrats techniques, peu de conventions de données, aucun test automatisé, aucune stratégie d'exécution applicative, aucune vraie séparation runtime entre espace privé et futur chatbot public.

Le projet est bien posé pour une phase de cadrage. Il n'est pas encore prêt pour une extension fonctionnelle rapide sans consolidation.

## 1. Points forts de l'architecture

### Vision produit claire

Le projet est aligné sur une vision ambitieuse : assistant privé, chatbot public, base documentaire, agents spécialisés, workflows, site, veille et automatisations.

Cette vision est correctement inscrite dans :

- `README.md`
- `ROADMAP.md`
- `docs/architecture/ARCHITECTURE_GLOBALE_V1.md`
- `docs/decisions/ADR-0001-architecture-initiale.md`
- `cockpit/README.md`

### Séparation initiale des responsabilités

L'arborescence distingue déjà :

- `agents/` pour les rôles IA ;
- `knowledge-base/` pour les sources ;
- `apps/` pour les futures interfaces ;
- `cockpit/` pour l'interface privée actuelle ;
- `workflows/` pour n8n, GitHub et veille ;
- `automation/` pour scripts et jobs ;
- `tests/` pour les futurs contrôles ;
- `config/` pour les environnements et schémas.

C'est une bonne base pour éviter un dépôt désordonné.

### Culture de documentation déjà présente

Le projet possède :

- une roadmap ;
- un changelog ;
- un ADR ;
- une documentation d'architecture ;
- une documentation sécurité ;
- des README de domaine.

Pour un projet IA, c'est un vrai avantage. Beaucoup de projets IA commencent par du code et rattrapent la documentation trop tard.

### Agents versionnés

Les modules importants ne restent pas dans les conversations. Ils sont versionnés :

- `agents/core/CFDT_NEXUS_CORE_PROMPT_V1.md`
- `agents/core/ROUTEUR_INTELLIGENCE_V1.md`
- `agents/defenseur/DEFENSEUR_SYNDICAL_V1.md`

C'est une bonne pratique structurante.

### Cockpit V2 cohérent avec la vision

Le cockpit est encore statique, mais il matérialise la vision :

- dossiers salariés ;
- assistant IA simulé ;
- bibliothèque ;
- communication ;
- veille ;
- statistiques ;
- paramètres ;
- niveaux documentaires public / privé / confidentiel.

Il donne une direction produit concrète.

### Sécurité identifiée tôt

Le projet documente déjà les notions de :

- validation humaine ;
- confidentialité ;
- séparation public / privé ;
- documents confidentiels non chargés automatiquement.

C'est indispensable vu les sujets : discipline, santé, paie, conflits, documents internes.

## 2. Points faibles

### Architecture encore déclarative

L'architecture est bien décrite, mais elle n'est pas encore exécutable.

Exemples :

- `apps/` est vide ;
- `automation/` est vide ;
- `workflows/` ne contient pas de workflow exploitable ;
- `config/` ne contient pas encore de schéma ;
- `tests/` ne contient aucun test ;
- `knowledge-base/` ne contient aucune source réelle ni modèle de métadonnées.

La structure est correcte, mais elle doit maintenant être rendue opérationnelle.

### Pas de contrat de données

Le cockpit manipule localement des objets `cases`, `libraryDocuments`, `settings`, etc., mais aucun schéma officiel n'existe.

Il manque :

- schéma `case`;
- schéma `document`;
- schéma `agent`;
- schéma `workflow`;
- schéma `source`;
- schéma `prompt`;
- schéma `user`.

Sans contrats de données, chaque future connexion risque de réinventer ses propres formats.

### Pas de stratégie d'identité et d'accès

Le projet prévoit :

- assistant privé ;
- chatbot public ;
- données publiques ;
- données privées ;
- données confidentielles.

Mais il manque une architecture d'authentification et d'autorisation.

Question non résolue : qui peut accéder à quoi, dans quel contexte, avec quelle trace ?

### Confusion future possible entre `site/`, `apps/` et `cockpit/`

Le dépôt contient :

- `site/` ;
- `apps/`;
- `cockpit/`.

Le cockpit est en réalité une application. À terme, il faudra décider s'il doit rester à la racine ou migrer vers `apps/private-assistant/` ou `apps/cockpit/`.

Le maintien de `cockpit/` à la racine est acceptable à court terme, mais pas optimal à long terme si plusieurs applications apparaissent.

### Pas de stratégie technique applicative

Le cockpit est en HTML/CSS/JS natif. C'est pertinent pour prototyper vite.

Mais pour une application durable, il faudra trancher :

- rester en vanilla JS modulaire ;
- passer à un framework ;
- isoler une couche services ;
- définir un modèle de build ;
- définir une stratégie de tests UI.

Aujourd'hui, la trajectoire technique du front n'est pas décidée.

### Pas de test automatisé

Le dossier `tests/` existe, mais il est vide.

Le projet n'a pas encore :

- test de prompt ;
- test agent ;
- test de règles de sécurité ;
- test UI ;
- test accessibilité ;
- test de non-régression ;
- test de schéma.

Pour un projet qui touchera à des sujets sensibles, c'est un manque prioritaire.

### Sécurité encore conceptuelle

La sécurité est documentée, mais non implémentée.

Il manque :

- modèle de classification ;
- règles de stockage ;
- politique de rétention ;
- chiffrement ou stratégie de secret ;
- matrice d'accès ;
- règles d'audit ;
- procédure d'incident ;
- séparation entre données réelles et données de démonstration.

### Documentation métier incomplète

Seul l'agent Défenseur Syndical est réellement détaillé.

Les autres agents sont encore vides :

- conseiller salarié ;
- juriste ;
- convention chimie ;
- accords INEOS ;
- paie ;
- CSSCT ;
- communication ;
- rédacteur CFDT ;
- site-web-codex ;
- veille.

Le routeur existe, mais il ne peut pas encore router vers des modules suffisamment décrits.

## 3. Risques futurs

### Risque de dette fonctionnelle

Le cockpit peut rapidement devenir une grande page monolithique si les prochaines fonctionnalités sont ajoutées directement dans `index.html` et `app.js`.

Risque : complexité croissante, difficile à tester et à maintenir.

### Risque de fuite de données

Le projet va manipuler des informations sensibles. Si les niveaux public / privé / confidentiel ne deviennent pas des règles techniques, le risque augmentera fortement.

Le plus gros risque n'est pas technique : c'est une mauvaise classification d'un document ou une publication non validée.

### Risque de mélange public / privé

Le futur chatbot public ne doit jamais accéder aux mêmes sources que l'assistant privé.

Si cette séparation est seulement documentaire, elle ne suffira pas.

### Risque d'agents trop autonomes

Le Routeur indique que l'utilisateur ne doit pas savoir quels modules ont été utilisés. C'est utile côté expérience, mais cela peut réduire la traçabilité.

Il faudra prévoir un mode interne où Thierry peut voir :

- sources consultées ;
- agents sollicités ;
- niveau de confiance ;
- points à vérifier ;
- limites.

### Risque juridique

Les agents juridiques peuvent donner l'impression de produire une analyse fiable. Le projet doit verrouiller :

- sources à jour ;
- vérification humaine ;
- formulation prudente ;
- absence de promesse ;
- distinction entre information et conseil juridique.

### Risque de sur-architecture

Le dépôt contient déjà beaucoup de dossiers. Si certains restent vides longtemps, l'architecture peut devenir intimidante et moins utile.

La structure est pertinente, mais elle doit maintenant être remplie par ordre de priorité.

### Risque de dépendance aux conversations

La règle de versionner les spécifications est bonne. Il faut l'appliquer systématiquement aux futurs prompts, workflows et décisions. Sinon, les décisions importantes resteront dispersées dans les échanges.

## 4. Dossiers inutiles ou prématurés

Ces dossiers ne sont pas mauvais, mais ils sont prématurés tant qu'ils ne contiennent pas de contenu exploitable :

- `apps/admin/`
- `apps/public-chatbot/`
- `automation/jobs/`
- `automation/scripts/`
- `config/environments/`
- `config/schemas/`
- `site/public/`
- `site/src/`
- `tests/workflows/`
- `tests/site/`

Recommandation : les garder uniquement si une roadmap les alimente rapidement. Sinon, ils deviennent du bruit architectural.

Le dossier `cockpit/` à la racine est acceptable maintenant, mais il pourrait être mieux placé à terme dans :

```text
apps/cockpit/
```

ou :

```text
apps/private-assistant/
```

Ce déplacement ne doit pas être fait immédiatement si le cockpit est encore en phase de prototypage.

## 5. Dossiers manquants

### `schemas/` applicatif ou `config/schemas/` à remplir

Le dossier existe, mais il manque les schémas.

À créer en priorité :

- `config/schemas/case.schema.json`
- `config/schemas/document.schema.json`
- `config/schemas/agent.schema.json`
- `config/schemas/workflow.schema.json`

### `docs/product/`

Il manque une zone produit claire pour :

- personas ;
- parcours utilisateur ;
- backlog fonctionnel ;
- règles UX ;
- priorisation.

Actuellement, la vision produit est dispersée entre README, ROADMAP et cockpit.

### `docs/privacy/` ou extension de `docs/security/`

Le sujet RGPD / données personnelles mérite une section propre.

À documenter :

- données traitées ;
- finalités ;
- durée de conservation ;
- droits des personnes ;
- règles d'anonymisation ;
- export / suppression.

### `docs/api/`

Avant de connecter n8n, GPT, GitHub, Analytics ou Hostinger, il faudra documenter les contrats d'intégration.

### `tests/security/`

Les tests de sécurité méritent un dossier dédié.

Exemples :

- vérifier qu'un agent ne sort pas de données confidentielles ;
- vérifier qu'un contenu public ne référence pas une source privée ;
- vérifier qu'une publication nécessite validation.

### `fixtures/` ou `tests/fixtures/`

Les données fictives utilisées dans le cockpit devraient à terme sortir de `app.js` et être stockées comme fixtures.

Exemple :

```text
tests/fixtures/cases.demo.json
tests/fixtures/documents.demo.json
```

## 6. Améliorations prioritaires

### Priorité 1 - Définir les modèles de données

Avant d'ajouter des fonctions, définir les schémas :

- dossier salarié ;
- document ;
- source ;
- agent ;
- conversation ;
- workflow ;
- tâche.

Sans cela, les futures connexions backend/n8n/GPT seront fragiles.

### Priorité 2 - Formaliser la sécurité documentaire

Créer une matrice :

| Niveau | Accès assistant privé | Accès chatbot public | Chargement automatique | Validation |
|---|---|---|---|---|
| Public | oui | oui | possible | standard |
| Privé | oui | non | contrôlé | Thierry |
| Confidentiel | non par défaut | non | interdit | explicite |

### Priorité 3 - Créer les premiers tests

Commencer par les tests les plus utiles :

- le cockpit charge sans erreur JS ;
- les sections principales existent ;
- aucun module sensible ne promet une victoire ;
- le Défenseur Syndical contient les garde-fous ;
- le Routeur impose questions manquantes et niveau de confiance.

### Priorité 4 - Décider la stratégie front-end

Deux options raisonnables :

1. Continuer en vanilla JS modulaire.
2. Migrer le cockpit vers une app structurée.

Pour l'instant, je recommande de rester en vanilla JS mais de découper en modules avant toute nouvelle fonctionnalité.

Exemple cible :

```text
cockpit/
  index.html
  styles.css
  app.js
  data/
  modules/
  services/
  components/
```

### Priorité 5 - Documenter le flux IA

Il manque une architecture d'exécution :

- qui appelle le Routeur ;
- comment le Routeur sélectionne les agents ;
- comment les sources sont récupérées ;
- comment le niveau de confiance est affiché ;
- comment Thierry valide avant action.

### Priorité 6 - Remplir les agents vides

Les prochains agents à créer :

1. Juriste V1
2. Convention Chimie V1
3. Accords INEOS V1
4. CSSCT V1
5. Communication / Rédacteur CFDT V1

## 7. Erreurs d'architecture éventuelles

### Cockpit placé hors de `apps/`

Ce n'est pas bloquant, mais ce n'est pas parfaitement aligné avec l'architecture cible.

Le cockpit est une application. À terme, il devrait probablement vivre dans `apps/cockpit/` ou `apps/private-assistant/`.

### Données de démonstration codées dans `app.js`

Pour une V2 statique, c'est acceptable.

Mais il faudra rapidement sortir les données de démonstration dans des fichiers JSON. Sinon, l'application sera difficile à connecter à une vraie base.

### Routeur trop opaque

La spécification dit que l'utilisateur ne doit jamais savoir quels modules ont été utilisés.

Pour un utilisateur final, c'est correct. Pour Thierry en mode pilotage, il faut un mode transparence. Sinon, impossible d'auditer la réponse IA.

### `.gitkeep` nombreux

Les `.gitkeep` sont utiles pour poser l'architecture. Mais trop de dossiers vides peuvent donner une impression de maturité artificielle.

Il faut maintenant remplacer progressivement les `.gitkeep` par des README, schémas ou specs réels.

### Absence de stratégie de versionnage des agents

Les fichiers utilisent `V1`, mais il manque une règle :

- quand incrémenter V2 ;
- comment déprécier V1 ;
- comment lier agents, prompts et tests ;
- comment documenter les changements.

## 8. Bonnes pratiques non encore appliquées

### Tests automatisés

Aucun test réel n'est encore versionné.

### Lint / format

Pas de règle de formatage.

### CI GitHub

Pas de workflow GitHub Actions. La raison actuelle est connue : manque de scope `workflow` sur le token utilisé. Il faudra l'ajouter plus tard.

### Schémas de données

Pas de JSON Schema ou équivalent.

### ADR systématiques

Un ADR existe. Il faut continuer pour les choix importants :

- choix front-end ;
- stratégie de base documentaire ;
- séparation public / privé ;
- choix n8n ;
- choix hébergement ;
- stratégie IA.

### Gestion des secrets

Pas encore de stratégie :

- où stocker les clés ;
- comment les nommer ;
- comment éviter leur commit ;
- comment gérer dev / prod.

### Observabilité

Pas encore de logs, erreurs, indicateurs, traces, historique d'action.

### Accessibilité formalisée

Le cockpit est visuellement structuré, mais il manque une checklist accessibilité versionnée.

### Gouvernance produit

Pas encore de backlog structuré, critères d'acceptation, priorisation ou définition de "terminé".

## 9. Recommandations avant d'ajouter de nouvelles fonctionnalités

Avant toute nouvelle fonctionnalité métier, je recommande :

1. Créer les schémas de données V1.
2. Extraire les données fictives du cockpit vers `cockpit/data/*.json`.
3. Découper `cockpit/app.js` en modules.
4. Créer une première suite de tests cockpit.
5. Créer une première suite de tests agents/prompts.
6. Documenter la séparation public / privé / confidentiel comme règle technique.
7. Créer `docs/product/` avec personas, parcours et backlog.
8. Créer `docs/privacy/` ou renforcer `docs/security/` pour RGPD et données sensibles.
9. Créer les agents métier manquants dans l'ordre de valeur.
10. Définir comment le Routeur sera exécuté concrètement.

Ordre recommandé :

```text
1. Schémas
2. Sécurité documentaire
3. Tests minimaux
4. Modularisation cockpit
5. Agents métier prioritaires
6. Workflows n8n
7. Connexion IA
8. Connexion données réelles
```

## 10. Note CTO

Note actuelle : **72 / 100**

### Pourquoi pas plus haut

- Pas de tests.
- Pas de schémas.
- Pas de sécurité implémentée.
- Pas de backend ni stratégie d'exécution.
- Beaucoup de dossiers encore vides.
- Cockpit encore monolithique.
- Données de démonstration codées dans le JS.

### Pourquoi la note est déjà bonne

- Vision très claire.
- Architecture initiale pertinente.
- Documentation supérieure à la moyenne pour un projet naissant.
- Séparation public / privé déjà identifiée.
- Agents critiques déjà versionnés.
- Cockpit V2 crédible pour valider le produit.
- Bonne discipline de commit et versionnage.

## Conclusion CTO

CFDT Nexus est à un bon niveau pour une phase de fondation. Le projet a une direction, une architecture et une première interface crédible.

La priorité n'est pas d'ajouter de nouvelles pages ou de nouveaux boutons. La priorité est de transformer cette architecture en socle robuste :

- schémas ;
- sécurité ;
- tests ;
- modularisation ;
- règles de gouvernance ;
- agents métier complétés.

Si ces fondations sont posées maintenant, CFDT Nexus pourra évoluer plusieurs années sans se transformer en prototype difficile à maintenir.
