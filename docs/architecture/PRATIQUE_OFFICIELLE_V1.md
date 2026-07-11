# Couche pratique officielle V1 - etude et prototype

## Objectif

Ajouter, a terme, une couche d'explication pratique officielle dans Nexus, sans
remplacer les couches juridiques existantes :

- accords INEOS ;
- convention collective chimie ;
- Code du travail via Legifrance ;
- jurisprudence via JUDILIBRE.

La couche cible doit utiliser `source_layer: pratique_officielle`.

## Sources etudiees

### Code du travail numerique

Source officielle du ministere du Travail, developpee dans l'ecosysteme
SocialGouv. Le service fournit des reponses accessibles, des contenus
personnalises selon la convention collective, des simulateurs et des modeles.

Acces repere :

- site public : `https://code.travail.gouv.fr` ;
- endpoint JSON public de recherche courte : `https://code.travail.gouv.fr/api/presearch?q=...` ;
- depot open source : `https://github.com/SocialGouv/code-du-travail-numerique`.

Le endpoint `/api/presearch` retourne notamment :

- `title` ;
- `description` ;
- `source` ;
- `slug` ;
- `cdtnId` ;
- `url` quand il existe ;
- `breadcrumbs` ;
- une definition de glossaire quand le terme est reconnu.

Limite constatee : cet endpoint ne retourne pas le corps complet des fiches.
Il donne une couche de recherche et de resume, utile pour orienter Nexus, mais
pas suffisante seule pour citer un contenu detaille.

### Sources pratiques remontees par presearch

Sources retenues pour le prototype :

- `fiches_service_public` : fiches Service-Public.fr ;
- `fiches_ministere_travail` : fiches du ministere du Travail republiees dans le Code du travail numerique ;
- `contributions` : reponses pratiques Code du travail numerique ;
- `themes` : navigation officielle par theme, utile pour orienter mais moins probante qu'une fiche.

### Donnees structurees SocialGouv

Le depot SocialGouv contient le frontend, les modules API internes et le package
`code-du-travail-modeles`, qui implemente des modeles Publicodes pour certains
simulateurs et conventions collectives. Ces modeles sont utiles pour une future
couche de simulateurs, mais ils ne remplacent pas les sources juridiques Nexus.

## Licence et reutilisation

Le site Code du travail numerique indique que, sauf mention contraire de tiers,
ses contenus sont proposes sous Licence Ouverte Etalab 2.0.

Contraintes pratiques a respecter :

- mentionner la source ;
- mentionner l'URL et, si disponible, la date de mise a jour ;
- ne pas laisser croire que Nexus est cautionne par l'administration ;
- distinguer clairement cette couche d'aide pratique des sources juridiquement opposables.

Le code du depot SocialGouv est publie sous licence Apache-2.0.

## Prototype cree

Fichier :

- `automation/scripts/pratique_officielle_connector.py`

Comportement :

- appelle uniquement `GET https://code.travail.gouv.fr/api/presearch?q=...` ;
- ne demande aucun secret ;
- ne scrape pas les pages HTML ;
- filtre les sources pratiques officielles ;
- normalise les resultats avec `source_layer: pratique_officielle` ;
- stocke le cache dans `local-index/pratique-officielle/`, deja ignore par Git.

Champs normalises :

- `title` ;
- `theme` ;
- `summary` ;
- `contenu_utile` ;
- `source_officielle` ;
- `updated_at` si disponible ;
- `official_id` / `reference` ;
- `url` ;
- `source_layer: pratique_officielle`.

## Resultats des 4 themes

### Astreinte et repos

Qualite : bonne.

Contenus retrouves :

- theme Code du travail numerique sur les astreintes ;
- fiche Service-Public.fr "Astreinte dans le secteur prive" ;
- fiche Service-Public.fr sur les heures d'equivalence ;
- fiches ministere du Travail sur la duree legale du travail.

### Heures supplementaires

Qualite : bonne.

Contenus retrouves :

- contribution Code du travail numerique sur majoration et repos compensateur ;
- fiches ministere du Travail sur la duree legale du travail ;
- resultats pratiques relies a la paie et au temps de travail.

### Travail du dimanche

Qualite : moyenne a bonne.

Contenus retrouves :

- fiche Service-Public.fr sur le travail du dimanche ;
- resultats sur repos compensateur, repos hebdomadaire et majorations selon le contexte.

Point de vigilance : il faut croiser avec les accords INEOS, la convention
collective, le Code du travail et les derogations applicables.

### Classification professionnelle

Qualite : faible a moyenne.

Contenus retrouves :

- fiches Service-Public.fr sur la consultation et le role d'une convention collective ;
- reponse pratique sur le salaire minimum et les accords collectifs ;
- peu de contenu directement centre sur la contestation de classification au regard des fonctions reelles.

Point de vigilance : pour Nexus, ce theme doit rester principalement porte par
les accords, la convention collective, le Code du travail si utile et la
jurisprudence.

## Architecture recommandee

Flux cible apres validation :

```text
question utilisateur
-> routeur Nexus
-> accords INEOS
-> convention collective chimie
-> Code du travail Legifrance
-> jurisprudence JUDILIBRE
-> pratique_officielle Code du travail numerique
-> synthese Nexus
```

La couche pratique officielle doit etre appelee apres les sources juridiques, ou
en parallele mais affichee separement. Elle doit servir a reformuler et orienter,
pas a trancher seule.

## Recommandation GO / NO-GO

GO pour une integration V1 limitee, avec garde-fous.

Conditions avant integration moteur :

- afficher cette couche dans une section separee ;
- limiter a 1 ou 2 contenus pratiques maximum ;
- toujours conserver les sources juridiques au-dessus ;
- signaler que le contenu pratique aide a comprendre mais ne remplace pas les textes applicables ;
- conserver le warning lorsque seul un resume `/api/presearch` est disponible ;
- ne pas scraper les pages HTML.
