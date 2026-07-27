# Baseline Nexus — cas métier réels anonymisés

Cette baseline mesure le comportement existant de Nexus. Aucun moteur n'a été modifié pour améliorer les réponses.

- Cas exécutés : 6
- Score moyen : 32.67/100
- Cas réussis : 0
- Cas en échec : 6

## Limites de cette mesure

- L'Assistant Final était désactivé pendant les six exécutions.
- La baseline porte principalement sur le moteur historique et son orchestration.
- La Bible Accords locale était indisponible ou vide.
- La disponibilité des sources officielles a varié selon les cas.
- Les scores ne représentent pas la performance maximale possible de toute l'architecture Nexus dans une autre configuration.

## Scores

| Cas | Faits | Questions | Sources | Texte/faits | Stratégie | Contradictoire | Sans invention | Pratique | Total | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| REAL-01-INSULTING_EMAILS_ALCOHOL | 8/20 | 4/10 | 6/15 | 4/15 | 5/15 | 4/10 | 5/10 | 2/5 | **38/100** | ÉCHEC |
| REAL-02-SMOKING_BREAKS_SEVESO_BADGE | 5/20 | 4/10 | 5/15 | 3/15 | 3/15 | 2/10 | 3/10 | 2/5 | **27/100** | ÉCHEC |
| REAL-03-TAG_INSTALLATION | 9/20 | 6/10 | 7/15 | 5/15 | 10/15 | 6/10 | 4/10 | 3/5 | **50/100** | ÉCHEC |
| REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY | 12/20 | 9/10 | 2/15 | 3/15 | 9/15 | 5/10 | 3/10 | 4/5 | **47/100** | ÉCHEC |
| REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE | 7/20 | 3/10 | 3/15 | 2/15 | 2/15 | 2/10 | 2/10 | 1/5 | **22/100** | ÉCHEC |
| REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED | 4/20 | 2/10 | 1/15 | 1/15 | 1/15 | 1/10 | 1/10 | 1/5 | **12/100** | ÉCHEC |

## REAL-01-INSULTING_EMAILS_ALCOHOL — Courriels insultants reconnus et consommation d'alcool alléguée

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **38/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité de correction : Très haute — préserver le fait disciplinaire principal et traiter l'alcool comme contexte distinct.

### Réussites

- Reconnaissance des faits et proportionnalité ne sont pas totalement ignorées.
- Le statut du destinataire ne conduit pas à une affirmation expresse de discrimination ou d'entrave.
- Une jurisprudence sur deux sanctions pour les mêmes faits est remontée, mais elle n'est pas intégrée au raisonnement du cas.

### Erreurs

- Le grief est classé comme alcool ou stupéfiants au lieu de courriels insultants.
- La mutation et le suivi relatif à l'alcool ne sont pas qualifiés.
- L'absence de lien entre les courriels et le mandat n'est pas réellement analysée.
- Le contrôle postérieur de l'issue connue montre que l'éventail proposé ne couvre pas correctement la mutation ni la confidentialité du suivi.

### Sources hors sujet

- Cass. soc., 18 mars 2009, 07-44.185 est utilisée sans établir de mise à pied conservatoire comparable dans les faits initiaux.
- Les moyens syndicaux et crédits d'heures sont recherchés sans lien factuel avec le contenu des courriels.

### Faits inventés

- Faits présentés comme répétés.
- Geste commis sous le coup de l'énervement.
- Absence de personne nommément visée.
- Réparation, nettoyage ou suppression rapide.

### Questions essentielles absentes

- Termes exacts, nombre, dates, destinataires et diffusion des courriels.
- Lien réel ou absence de lien avec le mandat.
- Nature contractuelle et disciplinaire d'une éventuelle mutation.
- Cumul de mesures pour les mêmes faits.
- Nature, auteur et confidentialité d'un éventuel suivi relatif à l'alcool.

### Stratégies irréalistes

- Stratégie de tag non ciblé appliquée à des courriels adressés à un collègue.
- Piste de formation, habilitation et mode opératoire sans fait technique.

### Répétitions importantes

- Questions générales sur les faits, la preuve et la proportionnalité répétées entre routeur, dossier disciplinaire et Expert Juriste.

## REAL-02-SMOKING_BREAKS_SEVESO_BADGE — Pauses cigarettes et utilisation d'un badgeage de sécurité Seveso

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **27/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité de correction : Critique — distinguer immédiatement le fait reconnu de la licéité et de la finalité de la preuve.

### Réussites

- La procédure disciplinaire et la proportionnalité sont mentionnées.
- Nexus ne traite pas l'issue négociée connue comme un fait initial.

### Erreurs

- Les pauses reconnues ne sont pas extraites.
- La finalité du tourniquet, le RGPD, la CNIL, l'information des salariés et la consultation du CSE sont absents.
- Le contrôle postérieur de l'issue connue montre que mise à pied, arrêt maladie, menace de licenciement et consentement à la rupture ne font pas partie des options analysées.

### Sources hors sujet

- Les seules sources portent sur la définition et l'information de la sanction, sans cadre du badgeage ni des pauses.

### Faits inventés

- Projet d'accord ou d'avenant.
- Réduction du repos à neuf heures.
- Erreur de manipulation et défaut de formation.
- Problème d'heures supplémentaires et de majorations.

### Questions essentielles absentes

- Finalité déclarée du tourniquet et information des salariés.
- Consultation du CSE et registre du traitement.
- Règles, durées et tolérances de pauses.
- Chronologie des mesures et risque de double sanction.
- Arrêt maladie traité séparément.
- Consentement libre à une éventuelle rupture conventionnelle.

### Stratégies irréalistes

- Stratégie d'injure ou d'attribution d'un acte appliquée à des pauses reconnues.
- Conclusion sur une perte de repos sans lien avec les faits.

### Répétitions importantes

- Questions de paie, compteurs et majorations répétées dans plusieurs blocs.

## REAL-03-TAG_INSTALLATION — Tag grossier sur une installation dans un contexte de souffrance au travail

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **50/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité de correction : Critique — fiabiliser l'extraction avant l'agrégation et empêcher les domaines secondaires de remplacer le dossier principal.

### Réussites

- La reconnaissance, l'absence de personne identifiée, le contexte et la proportionnalité alimentent une stratégie réaliste.
- La réponse évite une conclusion automatique de faute grave.
- Les sources réellement indisponibles sont signalées.

### Erreurs

- Le tag grossier est classé comme menace ou violence.
- Le fait est présenté comme répété alors que ce point est manquant.
- La réponse principale bascule sur un contrôle paie sans rapport direct.
- Le contrôle postérieur de l'issue connue confirme que lettre de recadrage et nettoyage figuraient parmi les options réalistes, sans justifier les inventions factuelles.

### Sources hors sujet

- Aucune source citée n'est manifestement fausse, mais les blocs paie sont hors sujet et dominent la restitution.

### Faits inventés

- Menace ou violence alléguée.
- Faits répétés.
- Absence de dommage matériel durable indiquée, alors que le dommage est seulement inconnu.

### Questions essentielles absentes

- Phrase complète, support et visibilité.
- Effaçabilité, dommage, nettoyage, ordre, durée et badgeage.
- Faits précis de souffrance et signalements antérieurs.
- Caractère isolé ou répété posé comme question plutôt que déduit.

### Stratégies irréalistes

- Qualification de menace malgré la contestation explicite de toute menace.
- Contrôle de paie générique substitué à la synthèse disciplinaire.

### Répétitions importantes

- Procédure, preuve et proportionnalité reviennent dans plusieurs sections.
- Questions et documents de paie sont répétés entre routeur, orchestration et rapport.

## REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY — Passage non volontaire d'horaires de jour à des horaires postés au laboratoire

- Parcours : `QUESTION_SALARIE`
- Score : **47/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité de correction : Haute — conserver la bonne trame de questions mais supprimer toute mémoire factuelle ou contamination inter-scénario.

### Réussites

- Les questions prioritaires essentielles sont presque toutes présentes.
- Aucun travail de nuit n'est affirmé comme un fait ; les horaires exacts sont demandés.
- Nexus déconseille un refus immédiat non préparé.

### Erreurs

- Des faits historiques d'un autre dossier jour-vers-poste sont injectés dans cette fixture.
- Aucune source réelle ne permet la comparaison demandée.
- Classification, équipements techniques et repos de neuf heures contaminent le rapport.
- La salariée partie en pleurs n'est pas intégrée aux faits ou à la stratégie de santé.

### Sources hors sujet

- Aucune source n'est retenue ; les thèmes classification et équipements techniques apparaissent sans source ni lien avec case_input.

### Faits inventés

- Remplacement d'un salarié démissionnaire.
- Réduction possible de l'équipe de jour.
- Rémunération supérieure ou prime de poste.
- Réduction du repos à neuf heures.
- Locaux SNCC/PROVOX, analyseurs et stock de pièces critiques.

### Questions essentielles absentes

- Les pleurs et les besoins immédiats de soutien ou de prévention.
- Confirmation explicite que seuls matin et après-midi sont annoncés.

### Stratégies irréalistes

- Analyse de classification et de maintenance technique mêlée à la défense du changement d'horaires.

### Répétitions importantes

- Les listes de documents et questions sont dupliquées dans la méthode salarié et l'orchestration.

## REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE — Refus d'heures déclarées pour assister à une réunion CSSCT

- Parcours : `QUESTION_SALARIE`
- Score : **22/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`, `INCOMPLETE_CASE_OVERCLAIM`
- Priorité de correction : Critique — respecter le parcours explicite et bloquer toute conclusion tant que le récit incomplet n'est pas clarifié.

### Réussites

- La réponse courte indique qu'une conclusion automatique est impossible.
- La distinction entre mandat, convocation et nature de la réunion apparaît brièvement.

### Erreurs

- Le mot convocation vers une CSSCT déclenche à tort le parcours disciplinaire malgré le parcours QUESTION_SALARIE demandé.
- Le caractère incomplet et la fin manquante ne sont pas signalés.
- Le rapport conclut à une position défavorable sur une réduction du repos inexistante.

### Sources hors sujet

- Article général sur le temps de travail effectif sans source spécifique CSSCT ou délégation.

### Faits inventés

- Réunion pendant un repos.
- Régime 5x8.
- Réduction du repos à neuf heures.
- Projet d'accord ou d'avenant.
- Faute disciplinaire et erreur de manipulation.

### Questions essentielles absentes

- Quelle est la fin manquante du récit ?
- L'élu est-il membre de la CSSCT et officiellement convoqué ?
- Réunion pendant travail ou repos ?
- Temps de réunion ou crédit d'heures ?
- Canal prévu par quel texte ?
- Empêchement effectif et retenue de salaire ?

### Stratégies irréalistes

- Défense disciplinaire sur attribution, personne visée et antécédents.
- Négociation d'un projet réduisant le repos.

### Répétitions importantes

- Questions de paie et de procédure disciplinaire répétées sans lien avec le mandat.

## REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED — Disparition alléguée d'une règle des 10 % après modification de la période de congés

- Parcours : `QUESTION_SALARIE`
- Score : **12/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`, `INCOMPLETE_CASE_OVERCLAIM`, `TEN_PERCENT_RULE_NOT_CLARIFIED`
- Priorité de correction : Critique — imposer la clarification sémantique avant tout routage juridique ou paie.

### Réussites

- Nexus indique qu'aucune source locale suffisante ne permet de conclure.
- Aucun calcul chiffré n'est effectué.

### Erreurs

- La règle des 10 % est assimilée directement à l'indemnité légale du dixième.
- Le parcours QUESTION_SALARIE demandé est remplacé par le parcours disciplinaire parce que le texte contient « faute de connaître ».
- Le caractère unresolved n'est pas affiché.
- Le rapport conclut malgré tout à une position défavorable sur une réduction du repos inexistante.

### Sources hors sujet

- Aucune source affichée ; les règles paie listées dans l'Expert Paie concernent plusieurs thèmes 5x8 et jours fériés étrangers à la clarification préalable.

### Faits inventés

- Application de la règle légale du dixième.
- Existence d'un grief disciplinaire.
- Réduction du repos à neuf heures.
- Projet d'accord à négocier.
- Éléments propres aux salariés postés.

### Questions essentielles absentes

- Que signifie exactement la règle des 10 % ?
- Dixième légal, quota d'absence, report ou règle locale de pose ?
- Quelle était sa source ?
- Quel accord a modifié la période ?
- Perte financière ou changement d'organisation ?

### Stratégies irréalistes

- Contrôle de l'assiette du dixième avant définition de la règle.
- Défense disciplinaire et négociation d'une réduction du repos.

### Répétitions importantes

- Questions de paie et discipline répétées dans le routeur, l'orchestration et les experts.

## Synthèse transversale

### Erreurs récurrentes de compréhension

- Le moteur choisit un mot secondaire comme fait principal : alcool, convocation, nettoyage, dixième ou faute dans une locution.
- Les faits reconnus, contestés et explicitement inconnus sont parfois remplacés par des valeurs booléennes affirmatives.
- Des éléments d'autres scénarios apparaissent dans les réponses : repos à neuf heures, démission, réduction d'équipe, SNCC/PROVOX.

### Fausses pistes récurrentes

- Erreur de manipulation, formation, habilitation et modes opératoires dans des dossiers non techniques.
- Paie, compteurs, majorations et bulletins dès qu'un temps ou une rémunération potentielle est mentionné.
- Projet d'accord et réduction du repos à neuf heures appliqués à plusieurs cas individuels.
- Discipline déclenchée par « convocation » CSSCT ou « faute de connaître ».

### Sélection documentaire

- La Bible Accords est indisponible ou vide pendant toute la baseline.
- Les sources locales attendues ne sont donc pas comparées aux faits.
- Des listes génériques de documents de paie ou de classification remplacent les pièces propres au dossier.

### Jurisprudence

- Les décisions Judilibre retenues sont procédurales ou lexicalement proches mais rarement comparées aux faits précis.
- Aucune jurisprudence factuellement comparable n'est fournie pour pauses/badgeage, tag ou changement d'horaires.
- L'absence de jurisprudence est parfois correctement signalée.

### Stratégie

- Des stratégies spécialisées sont appliquées au mauvais type de fait.
- La bonne stratégie disciplinaire du tag est masquée par l'agrégation paie.
- Les cas incomplets reçoivent des conclusions ou positions défavorables au lieu d'un arrêt sur clarification.

### Interface et restitution

- La vue principale agrège findings, questions et experts hors sujet alors qu'un sous-dossier métier peut être meilleur.
- Les réponses brutes publiques font entre 127 et 391 Ko, avec répétitions importantes.
- Le statut final assistant est DISABLED pour les six cas ; la baseline mesure donc le moteur historique et son orchestration actuelle.

### Familles les plus faibles

- Ambiguïté lexicale préalable : règle des 10 %.
- Mandat/CSSCT avec récit incomplet.
- Preuve numérique/RGPD dans un dossier disciplinaire.
- Extraction disciplinaire lorsque plusieurs thèmes coexistent.

### Trois corrections prioritaires maximales

- Fiabiliser l'extraction et le routage sur le fait principal, avec respect du parcours explicite et arrêt obligatoire sur ambiguïté bloquante.
- Empêcher toute contamination inter-scénario et toute agrégation d'un domaine secondaire qui remplace le dossier principal.
- Sélectionner questions, documents et sources par comparaison factuelle, puis dédupliquer la restitution visible.
