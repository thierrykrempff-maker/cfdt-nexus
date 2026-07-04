# Règles de validation de veille V1

## Principe

La veille CFDT Nexus sert à détecter, comprendre et préparer. Elle ne publie rien automatiquement.

Chaque élément collecté doit être classé en brouillon jusqu'à validation humaine.

## Parcours obligatoire

1. Détection
   - identifier la source ;
   - relever le titre ;
   - relever l'URL ;
   - relever la date de publication ;
   - relever le canal de veille concerné.

2. Qualification
   - vérifier le niveau de confiance de la source ;
   - vérifier si la source est primaire, institutionnelle, experte, secondaire ou sociale ;
   - identifier le thème principal ;
   - identifier les agents concernés.

3. Vérification
   - rechercher la source primaire si la source est secondaire ;
   - vérifier les dates d'entrée en vigueur ;
   - vérifier si la règle est nationale, conventionnelle ou locale ;
   - vérifier si un accord INEOS privé peut modifier ou compléter l'analyse.

4. Synthèse
   - produire une version courte ;
   - distinguer les faits, les sources, l'analyse et les points à vérifier ;
   - proposer une action concrète.

5. Validation
   - garder le statut `a_verifier` tant qu'une source primaire manque ;
   - passer en `pret_pour_relecture` seulement après vérification suffisante ;
   - publier uniquement après validation explicite de Thierry.

## Niveaux de confiance

- `fort` : source A ou B, date vérifiée, champ d'application clair.
- `moyen` : source fiable mais contexte incomplet ou texte primaire à confirmer.
- `faible` : signal social, article secondaire, information partielle ou accès limité.

## Interdictions

- Pas de scraping agressif.
- Pas de contournement de protection technique.
- Pas de reprise intégrale d'article protégé.
- Pas de publication automatique sur le site public.
- Pas de citation d'un accord INEOS privé dans un contenu public sans validation.
- Pas de données nominatives dans les exemples, fixtures ou bulletins.

## Règles par type de source

### Source primaire

Peut fonder une analyse si le champ d'application est clair.

### Source institutionnelle

Peut expliquer ou contextualiser, mais doit être croisée si un dossier individuel est sensible.

### Source CFDT

Peut fonder une position syndicale ou une communication CFDT, mais pas une règle juridique.

### Source spécialisée

Sert à détecter et préparer. La source primaire doit être retrouvée.

### Réseau social

Sert uniquement de signal faible. Une publication sociale ne suffit jamais.

## Statuts de traitement

- `detecte`
- `a_verifier`
- `source_primaire_recherchee`
- `analyse_preparee`
- `pret_pour_relecture`
- `valide`
- `rejete`
- `archive`

