# Règle — Deux parcours

Source de référence : `README.md` (racine, section « Périmètre V1 »), qui définit déjà ces deux
parcours pour la V1 de Nexus. Cette règle rappelle comment Claude doit les distinguer et les
appliquer.

## QUESTION_SALARIE

Destiné notamment au futur chatbot public du site CFDT INEOS Sarralbe (`apps/public-chatbot`).

Réponse attendue :

- pédagogique, accessible à un non-juriste ;
- prudente : jamais de certitude non fondée, jamais de promesse de résultat ;
- relativement courte ;
- sourcée, avec indication claire des vérifications encore nécessaires ;
- sans jargon inutile ;
- ne jamais exposer de donnée interne, personnelle ou confidentielle (voir
  `.claude/rules/confidentialite.md`).

## ASSISTANCE_ENTRETIEN (préparation d'entretien ou de dossier de défense)

Destiné à Thierry pour préparer concrètement l'accompagnement d'un salarié
(`ASSISTANCE_ENTRETIEN_DISCIPLINAIRE` dans le vocabulaire du `README.md` racine, étendu ici aux
autres types d'entretien : CSE, CSSCT, négociation).

Réponse attendue, reprise du format déjà défini dans
`agents/defenseur/DEFENSEUR_SYNDICAL_V1.md` et `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md` :

- chronologie ;
- faits établis et faits manquants ;
- points à vérifier ;
- documents à demander ;
- questions à poser ;
- arguments et contre-arguments anticipés ;
- contradictions éventuelles ;
- points de vigilance ;
- structure permettant de prendre des notes pendant l'entretien.

## Comment distinguer les deux

Si la question vient d'un salarié qui cherche à comprendre une règle ou une situation générale
→ `QUESTION_SALARIE`.

Si la demande vient de Thierry pour préparer un dossier, un entretien, une défense ou une
négociation concrète → `ASSISTANCE_ENTRETIEN`.

En cas de doute, poser la question à Thierry plutôt que de choisir un parcours par défaut.
