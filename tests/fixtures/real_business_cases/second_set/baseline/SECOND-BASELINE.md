# Seconde baseline Nexus — cas métier réels anonymisés

Cette mesure utilise le moteur Nexus existant, sans modification de moteur, routeur, connecteur, runtime ou interface.

- Cas exécutés : 5
- Score moyen du second lot : **25.2/100**
- Baseline initiale : **32.67/100**
- Écart : **-7.47 points**
- Cas réussis : 0
- Cas en échec : 5

## Limites

- Les réponses mesurent la configuration locale disponible lors de l'exécution.
- Les sources locales ou officielles indisponibles sont une limite de mesure.
- Les références non vérifiables du récit source sont isolées dans `legal-references-to-verify.json` et ne servent pas d'autorité.
- Ni `evaluation_expectations` ni `evaluation_only` n'ont été transmis à Nexus.

## Scores

| Cas | Faits | Questions | Sources | Texte/faits | Stratégie | Contradictoire | Sans invention | Pratique | Total | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE | 4/20 | 2/10 | 1/15 | 1/15 | 2/15 | 2/10 | 3/10 | 1/5 | **16/100** | ÉCHEC |
| REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL | 8/20 | 2/10 | 5/15 | 3/15 | 3/15 | 3/10 | 3/10 | 1/5 | **28/100** | ÉCHEC |
| REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE | 3/20 | 2/10 | 1/15 | 1/15 | 2/15 | 2/10 | 3/10 | 1/5 | **15/100** | ÉCHEC |
| REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION | 10/20 | 4/10 | 2/15 | 2/15 | 4/15 | 3/10 | 3/10 | 2/5 | **30/100** | ÉCHEC |
| REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT | 9/20 | 3/10 | 6/15 | 4/15 | 5/15 | 4/10 | 4/10 | 2/5 | **37/100** | ÉCHEC |

## REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE — EPI indisponible ou inadapté lors d'une opération sur acide sulfurique

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **16/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité : Très haute — extraire le risque, l'EPI manquant ou inadapté et les responsabilités avant tout domaine secondaire.

### Réussites

- Le besoin de vérifier le DUERP, les incidents et les preuves est évoqué.

### Erreurs

- Contamination par un scénario de classification professionnelle.
- Le risque chimique, les EPI disponibles et le comportement du salarié ne sont pas restitués.

### Questions essentielles absentes

- Consigne EPI exacte.
- Disponibilité et adaptation des protections.
- Possibilité d'arrêt, urgence et signalement préalable.

## REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL — Refus d'un passage temporaire de jour vers un cycle 3x8

- Parcours : `QUESTION_SALARIE`
- Score : **28/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité : Très haute — empêcher la contamination et comparer clause, cycle, vie familiale, besoin temporaire et alternatives.

### Réussites

- Le parcours QUESTION_SALARIE est respecté.
- Le thème modification du contrat est détecté.

### Erreurs

- Contamination majeure par un scénario technique SNCC/PROVOX.
- La clause et l'atteinte familiale ne structurent pas l'analyse.

### Questions essentielles absentes

- Texte exact de la clause.
- Horaires de nuit et délai de prévenance.
- Garde alternée et alternatives recherchées.

## REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE — Erreur de fabrication et procédure informatique potentiellement obsolète

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **15/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité : Très haute — préserver le fait technique et distinguer erreur, faute, insuffisance et défaillance documentaire.

### Réussites

- La nécessité de recueillir les preuves de la direction est rappelée.

### Erreurs

- Le fait de fabrication disparaît entièrement.
- Contamination par la classification et la carrière.

### Questions essentielles absentes

- Version exacte de la recette sur le terminal.
- Horodatage de publication et de consultation.
- Formation, contrôle croisé et causalité.

## REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION — Contrôle d'alcoolémie positif sur un poste à risque

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **30/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité : Haute — conserver la bonne catégorie mais extraire la procédure, la fiabilité, le risque concret et les alternatives.

### Réussites

- La catégorie disciplinaire principale est détectée.
- La réponse ne promet pas que l'ancienneté exclut la faute grave.

### Erreurs

- Les garanties spécifiques du contrôle ne sont pas analysées.
- Contamination par un scénario technique de climatisation et d'analyseurs.

### Questions essentielles absentes

- Unité, heure, matériel et calibration.
- Contre-expertise réellement accessible.
- Prise effective du chariot et mise en sécurité.

## REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT — Insultes envers un supérieur dans un contexte de fatigue et de surcharge

- Parcours : `ASSISTANCE_ENTRETIEN_DISCIPLINAIRE`
- Score : **37/100**
- Règles éliminatoires : `FACTUAL_MISUNDERSTANDING`, `PRIMARY_FACT_CONTRADICTION`, `INVENTED_AUTHORITY_OR_EVIDENCE`, `FORBIDDEN_FALSE_LEAD`
- Priorité : Très haute — distinguer insulte de menace et préserver la cible, puis comparer les repos au planning.

### Réussites

- La fatigue est traitée comme contexte allégué, non comme excuse automatique.
- Deux articles officiels sur les repos sont retrouvés.

### Erreurs

- Insultes requalifiées en menace ou violence.
- Superviseur remplacé par un collègue.
- Contamination par le scénario SNCC/PROVOX.

### Questions essentielles absentes

- Mots exacts et menace éventuelle.
- Remarque du superviseur et témoins.
- Planning, repos, excuses et antécédents.

## Synthèse transversale

- Les cinq cas échouent au verrou de compréhension factuelle.
- Les réponses disciplinaires génériques perdent les faits techniques spécifiques.
- Des contaminations récurrentes par la classification professionnelle et le scénario SNCC/PROVOX apparaissent.
- Le parcours demandé est respecté, mais cela ne suffit pas à préserver le dossier.
- Les sources officielles pertinentes restent rares et sont peu comparées aux faits.
- La priorité demeure l'isolation du scénario, l'extraction du fait principal et la sélection factuelle des questions et sources.
