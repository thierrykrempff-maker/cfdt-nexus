# Politique de sécurité documentaire CFDT Nexus V1

## Objectif

Cette politique fixe les règles de base pour protéger les documents privés utilisés par CFDT Nexus.

Le dépôt GitHub doit rester un espace de versionnage technique et méthodologique. Il ne doit pas devenir un espace de stockage documentaire confidentiel.

## Règles obligatoires

1. Aucun accord réel dans GitHub.
2. Aucun PV CSE réel dans GitHub.
3. Aucune BDESE dans GitHub.
4. Aucune donnée nominative dans GitHub.
5. Les documents privés restent sur le PC ou cloud privé de Thierry.
6. Seuls les index et métadonnées expurgées peuvent être versionnés.
7. Toute publication vers le site public nécessite une validation humaine.
8. Aucun PDF OCRisé réel ne doit être ajouté à GitHub.
9. Aucun texte OCR réel ne doit être ajouté à GitHub.

## Niveaux de confidentialité

### Public

Document déjà public ou source officielle accessible publiquement.

Utilisation possible :

- indexation ;
- résumé ;
- citation courte avec source ;
- utilisation par agents publics si validé.

### Interne

Document utile au travail CFDT mais non destiné à publication directe.

Utilisation possible :

- assistant privé ;
- préparation de dossier ;
- synthèse interne ;
- analyse avec validation humaine.

Interdiction :

- publication automatique ;
- accès chatbot public ;
- export sans relecture.

### Confidentiel

Document sensible : PV CSE, élément social, situation individuelle, donnée économique non publique, document d'entreprise ou donnée personnelle.

Utilisation possible uniquement avec validation explicite.

Interdiction :

- stockage dans GitHub ;
- publication ;
- accès chatbot public ;
- chargement automatique non contrôlé ;
- partage sans autorisation.

## Métadonnées autorisées dans GitHub

Les métadonnées versionnées doivent rester expurgées.

Autorisé :

- identifiant ;
- titre non sensible ;
- catégorie ;
- niveau de confidentialité ;
- mots-clés génériques ;
- résumé non confidentiel ;
- agents autorisés ;
- dates de suivi ;
- chemin privé indicatif non exploitable publiquement.

Interdit :

- nom de salarié ;
- matricule ;
- donnée médicale ;
- sanction disciplinaire identifiable ;
- contenu de PV réel ;
- montant confidentiel ;
- extrait d'accord non public ;
- lien public vers document privé.

## Connexions futures

Toute connexion future doit respecter cette politique :

- Document Intelligence Center : accès par métadonnées, puis chargement contrôlé.
- Cycle CSE : aucun PV réel dans GitHub, seulement références expurgées.
- Agent Défenseur Syndical : pas de dossier salarié réel dans GitHub.
- Agent Paie : pas de bulletin nominatif dans GitHub.
- Agent CSSCT : prudence renforcée sur santé, sécurité et données personnelles.
- Agent Convention Chimie : privilégier les sources publiques ou validées.
- Veille juridique : sources officielles ou liens publics uniquement.

## OCR local

L'OCR des accords et documents privés doit rester strictement local.

Interdit :

- API OCR cloud ;
- envoi vers OpenAI, Google, Microsoft, AWS ou autre service externe ;
- stockage de PDF OCRisé réel dans GitHub ;
- stockage de texte OCR réel dans GitHub ;
- stockage de rapport OCR privé dans GitHub.

Autorisé uniquement en local :

- copie de travail temporaire ;
- PDF OCRisé privé ;
- pages texte OCR privées ;
- rapport OCR privé ;
- statut OCR privé.

Emplacement local prévu :

```text
local-index/agreements/ocr/
```

Ce dossier doit rester ignoré par Git.

## Rapports d'integration locale

Les analyses generees par la connexion Bible Accords, Document Intelligence Center et Cycle CSE restent strictement locales.

Emplacement local prevu :

```text
local-index/agreements/integration/
```

Interdit dans GitHub :

- rapport d'analyse CSE reel ;
- rapport d'analyse documentaire reel ;
- scenario contenant un nom de document prive ;
- extrait d'accord, de reglement interieur ou de document interne ;
- chemin absolu vers un corpus prive.

Ces rapports peuvent servir a preparer une reunion, une question ou une analyse, mais ils necessitent toujours une validation humaine avant toute utilisation externe.

## Validation humaine

Avant diffusion, Thierry ou une personne habilitée doit vérifier :

- le niveau de confidentialité ;
- l'absence de donnée nominative ;
- l'absence d'information interne non validée ;
- la conformité au ton CFDT ;
- la destination du contenu : privé, adhérents, salariés, public.

## Règle d'arrêt

En cas de doute sur la confidentialité, ne pas publier, ne pas exporter et ne pas ajouter dans GitHub.
