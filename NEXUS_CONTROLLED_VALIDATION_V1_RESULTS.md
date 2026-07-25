# Résultats — Validation contrôlée CFDT Nexus V1

Campagne exclusivement synthétique, locale, déterministe et sans réseau.

- Dossiers : 34
- Score moyen : 100.0/100
- Score minimum : 100/100
- Dossiers sous 80 : 0
- Dossiers sous 70 : 0
- Incidents de confidentialité : 0
- Calculs interdits : 0
- Erreurs de routage : 0
- Contradictions non résolues : 0
- Fallbacks contrôlés : 1
- Verdict : **PRÊT POUR ACTIVATION CONTRÔLÉE**

## Résultats par dossier

| Dossier | Score | Domaine | Fallback | Acceptable |
|---|---:|---|---|---|
| CV-R1A-01 | 100 | contract_conditions | non | oui |
| CV-R1A-02 | 100 | contract_conditions | non | oui |
| CV-R1A-03 | 100 | contract_conditions | non | oui |
| CV-R1B-01 | 100 | discipline | non | oui |
| CV-R1B-02 | 100 | discipline | non | oui |
| CV-R1B-03 | 100 | discipline | non | oui |
| CV-R1C-01 | 100 | working_time | non | oui |
| CV-R1C-02 | 100 | working_time | non | oui |
| CV-R1C-03 | 100 | working_time | non | oui |
| CV-R1C-04 | 100 | working_time | non | oui |
| CV-R1D-01 | 100 | discrimination_harassment | non | oui |
| CV-R1D-02 | 100 | discrimination_harassment | non | oui |
| CV-R1D-03 | 100 | discrimination_harassment | non | oui |
| CV-R1D-04 | 100 | discrimination_harassment | non | oui |
| CV-R1E-01 | 100 | health_absence | non | oui |
| CV-R1E-02 | 100 | health_absence | non | oui |
| CV-R1E-03 | 100 | health_absence | non | oui |
| CV-R1E-04 | 100 | health_absence | non | oui |
| CV-R2A-01 | 100 | cse_consultation | non | oui |
| CV-R2A-02 | 100 | cse_consultation | non | oui |
| CV-R2A-03 | 100 | cse_consultation | non | oui |
| CV-R2B-01 | 100 | cse_operation | non | oui |
| CV-R2B-02 | 100 | cse_operation | non | oui |
| CV-R2B-03 | 100 | cse_operation | non | oui |
| CV-R2C-01 | 100 | cse_alerts | non | oui |
| CV-R2C-02 | 100 | cse_alerts | non | oui |
| CV-R2C-03 | 100 | cse_alerts | non | oui |
| CV-PAY-01 | 100 | payroll | non | oui |
| CV-PAY-02 | 100 | payroll | non | oui |
| CV-PAY-03 | 100 | payroll | non | oui |
| CV-TR-01 | 100 | cse_consultation | non | oui |
| CV-TR-02 | 100 | cse_consultation | oui | oui |
| CV-TR-03 | 100 | documentary | non | oui |
| CV-TR-04 | 100 | discipline | non | oui |

## Validation technique

- Trois anomalies historiques ciblées : 3/3 réussites.
- Routeur historique : 13 réussites.
- Orchestrateur commun : 14 réussites.
- Syndical Reasoning R0–R2C : 362 réussites.
- Expert Paie V2 : 46 réussites.
- Assistant Final : 62 réussites.
- Runtime : 186 réussites.
- CSE Memory : 78 réussites.
- Interface et HTTP synthétiques : 20 réussites.
- Validation contrôlée : 43 réussites, dont 14 contrôles dédiés supplémentaires de confidentialité.
- Répertoire `tests/` : 1 512 réussites.
- Suite complète : 2 992 réussites et 128 sous-tests.
- Nouvel échec : aucun.

## Corrections et limites

Les trois anomalies historiques sont corrigées : deux contrôles d’import sont désormais réellement isolés et l’intégration Paie utilise une identité de module canonique. Les moteurs optionnels ne sont plus chargés avant activation explicite.

Le script HTTP autonome historique reçoit toujours un statut 200 puis rencontre sa précondition `answer["sources"]` quand le corpus local de classification n’est pas installé. La campagne HTTP synthétique complète est verte ; corriger le corpus réel serait hors du périmètre de ce lot.
