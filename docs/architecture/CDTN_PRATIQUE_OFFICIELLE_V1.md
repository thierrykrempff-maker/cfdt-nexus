# CDTN pratique officielle V1

## Objectif

Ajouter une couche `source_layer: pratique_officielle` fondee sur le Code du
travail numerique pour expliquer les regles en langage clair.

Cette couche ne remplace jamais :

- les accords INEOS ;
- la convention collective chimie ;
- les articles Code du travail recuperes par Legifrance ;
- la jurisprudence recuperee par JUDILIBRE.

## Endpoint etudie

Endpoint public teste :

```text
GET https://code.travail.gouv.fr/api/presearch?q=<question>
```

Parametre confirme :

- `q` obligatoire.

Sans `q`, l'endpoint repond `400` avec le message :

```json
{"message":"Query parameter 'q' is required."}
```

Authentification :

- aucune.

Limite observee :

- 8 resultats maximum ;
- pas de parametre public stable observe pour demander plus de resultats ;
- pas de corps complet de fiche dans la reponse.

## Structure des donnees

Reponse top-level observee :

- `results` ;
- `class` ;
- parfois `definition`.

Champs de resultat observes :

- `_score` ;
- `title` ;
- `description` ;
- `source` ;
- `slug` ;
- `cdtnId` ;
- `url` quand la source externe le fournit ;
- `breadcrumbs` ;
- `algo` ;
- parfois `class`.

Types de contenus utiles pour Nexus :

- `fiches_service_public` ;
- `fiches_ministere_travail` ;
- `contributions` ;
- `infographies`.

Types utiles seulement pour orienter :

- `themes` ;
- `outils` ;
- `modeles_de_courriers`.

## Contenu complet

Le prototype ne recupere pas le contenu complet des pages. L'acces public
teste `https://code.travail.gouv.fr/api/items?source=...&slug=...` renvoie
`404`.

Le code source public du site montre que `/api/presearch` appelle le controleur
de recherche et retourne les documents courts de recherche. Le module interne
`items` existe dans le code applicatif, mais aucune route publique stable
`/api/items` n'est exposee.

Conclusion technique :

- GO pour titre, resume court, URL, identifiant et source officielle ;
- NO-GO pour pretendre fournir le corps complet d'une fiche CDTN sans autre API
  publique documentee ;
- pas de scraping HTML.

## Connecteur cree

Fichier :

- `automation/scripts/cdtn_connector.py`

Cache :

- `local-index/cdtn/`
- deja ignore par Git via `local-index/`.

Commandes principales :

```powershell
python -B automation/scripts/cdtn_connector.py diagnose --format text
python -B automation/scripts/cdtn_connector.py search --query "astreinte repos" --format json
python -B automation/scripts/cdtn_connector.py run-scenarios --limit 4 --format text
```

Champs normalises :

- `title` ;
- `theme` ;
- `summary` ;
- `explanation` ;
- `contenu_utile` ;
- `content_type` ;
- `source_officielle` ;
- `url_or_id` ;
- `updated_at` si fourni ;
- `retrieved_at` ;
- `source_layer: pratique_officielle`.

Chaque source contient aussi :

- `full_content_available: false` ;
- `content_access: presearch_description_only` ;
- un avertissement indiquant que le corps complet n'est pas recupere.

## Resultats des themes prioritaires

### Astreinte et repos

Qualite : bonne.

Resultats pertinents :

- Service-Public.fr, astreinte dans le secteur prive ;
- contenus sur heures supplementaires, repos compensateur, dimanche et temps de
  travail effectif.

### Heures supplementaires

Qualite : bonne.

Resultats pertinents :

- contribution CDTN sur majorations et repos compensateur ;
- fiches Ministere du Travail ;
- fiche Service-Public.fr.

### Travail du dimanche

Qualite : bonne.

Resultats pertinents :

- contribution CDTN sur contrepartie du travail du dimanche ;
- fiche Service-Public.fr ;
- contenus sur repos compensateur.

### Prime et remuneration

Qualite : bonne pour une premiere explication.

Resultats pertinents :

- fiche Service-Public.fr salaire, primes et avantages ;
- fiches Ministere du Travail sur bulletin de paie et contestation ;
- contribution salaire minimum.

### Classification professionnelle

Qualite : moyenne.

Les resultats aident surtout a expliquer le role de la convention collective et
du salaire minimum. Ils ne couvrent pas assez directement la contestation de la
classification au regard des fonctions reellement exercees.

### CSE et temps de reunion

Qualite : moyenne.

Les resultats expliquent le CSE et ses reunions, mais ne traitent pas assez
precisement le cas du temps de reunion pendant un repos. Nexus doit continuer a
s'appuyer d'abord sur Code du travail et jurisprudence.

## Recommandation

GO pour un branchement ulterieur limite, avec garde-fous :

- afficher la couche dans une section separee ;
- limiter a 1 ou 2 contenus pratiques ;
- conserver les sources juridiques au-dessus ;
- afficher l'avertissement `presearch_description_only` ;
- ne jamais utiliser cette couche pour trancher seule ;
- ne pas scraper le site.
