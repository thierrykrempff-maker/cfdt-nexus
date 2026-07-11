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

Autre limite V1 : `/api/presearch` est une recherche courte. Nexus ne doit donc
pas presenter ces resultats comme une source juridique complete ou opposable.

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
- mentionner la licence : Licence Ouverte Etalab 2.0 ;
- mentionner l'attribution : Code du travail numerique - ministere du Travail ;
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
- valide le domaine avant tout appel reseau ;
- accepte en production uniquement l'URL de base exacte `https://code.travail.gouv.fr` ;
- rejette les identifiants, mots de passe, ports explicites, chemins, query strings et fragments ;
- rejette les domaines ressemblants comme `code.travail.gouv.fr.example.com`, `evil-code.travail.gouv.fr` ou `code-travail.gouv.fr` ;
- accepte `localhost` / `127.0.0.1` / `::1` uniquement avec le mode de test explicite `allow_local_test_base_url` ;
- rejette tous les autres hotes locaux, prives ou arbitraires ;
- rejette toute URL arbitraire sans normaliser de source `pratique_officielle` ;
- limite la reponse HTTP a 1 000 000 octets pendant la lecture, avant parsing JSON ;
- filtre les sources pratiques officielles ;
- normalise les resultats avec `source_layer: pratique_officielle` ;
- stocke le cache dans `local-index/pratique-officielle/`, deja ignore par Git.

Cache :

- une entree expiree est ignoree ;
- un JSON corrompu est ignore sans interrompre la recherche ;
- une structure non objet, incomplete ou inattendue est ignoree ;
- un dossier de cache inaccessible ne doit pas faire echouer une reponse reseau valide ;
- l'ecriture se fait via fichier temporaire puis remplacement atomique lorsque possible ;
- si l'ecriture echoue, Nexus conserve le resultat reseau mais ajoute un warning.

Champs normalises :

- `title` ;
- `theme` ;
- `summary` ;
- `contenu_utile` ;
- `source_officielle` ;
- `updated_at` si disponible ;
- `official_id` / `reference` ;
- `url` ;
- `license` ;
- `attribution` ;
- `official_disclaimer` ;
- `source_layer: pratique_officielle`.

Champs fixes ajoutes aux resultats V1 :

- `license: Licence Ouverte Etalab 2.0` ;
- `attribution: Code du travail numerique - ministere du Travail` ;
- `official_disclaimer: Nexus n'est pas cautionne par l'administration.`

## Statut du composant

Statut actuel : prototype securise et teste, non integre au routeur Nexus.

Le connecteur peut etre execute localement et teste sans reseau reel via le
fichier de tests dedie. Il ne doit pas etre branche au moteur tant que les
garde-fous d'affichage et de hierarchie des sources ne sont pas valides.

Tests couverts :

- normalisation d'un resultat valide ;
- conservation de `source_layer: pratique_officielle` ;
- presence de `license` et `attribution` ;
- rejet d'une source inconnue ;
- reponse vide ;
- JSON invalide ;
- erreur reseau ;
- timeout simule ;
- cache miss, cache hit, cache expire et cache corrompu ;
- cache contenant une structure invalide ou incomplete ;
- cache inaccessible et echec d'ecriture ;
- domaine officiel accepte ;
- domaine non autorise rejete ;
- localhost, 127.0.0.1 et ::1 acceptes uniquement en mode test explicite ;
- HTTP 400, 404, 500, timeout et erreur reseau ;
- Content-Length trop grand, Content-Length mensonger, absence de Content-Length et taille exacte ;
- reponse trop volumineuse rejetee.

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
