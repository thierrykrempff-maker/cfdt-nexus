# ARCH-02 — Adaptateurs rétrocompatibles des contrats communs

## 1. Décision d'architecture

ARCH-02 introduit une couche `automation/adapters` séparée des contrats ARCH-01 et des moteurs métier. Cette direction de dépendance est volontaire :

```text
structures historiques Paie
          ↓
automation/adapters/payroll.py → automation/contracts
          ↓
restitution historique compatible
```

Les contrats communs ne connaissent aucun moteur. L'adaptateur peut connaître les contrats et les types historiques Paie indispensables. Aucun appel à l'Expert Paie, calcul, accès réseau, lecture de corpus, sélection de règle, connecteur, routeur ou orchestrateur n'est effectué par l'adaptateur.

Version publique de l'adaptateur : `1.0`.

API publique stable :

- `legacy_payroll_request_to_expert_request` ;
- `expert_request_to_legacy_payroll_request` ;
- `legacy_payroll_result_to_expert_report` ;
- `expert_report_to_legacy_payroll_result` ;
- `legacy_source_to_knowledge_source` ;
- `legacy_evidence_to_source_evidence` ;
- `legacy_missing_information_to_contract` ;
- `legacy_risk_to_risk_assessment` ;
- `legacy_confidence_to_confidence_assessment`.

Les premiers noms courts du pilote restent disponibles comme alias afin de ne pas casser les appels préparatoires.

## 2. Audit ciblé de l'architecture Paie exécutée

### 2.1 Points d'entrée et consommateurs

| Élément | Signature ou forme | Rôle réel | Consommateurs observés |
|---|---|---|---|
| Expert Paie public | `automation.experts.paie.enrich(answer: dict) -> dict` | Enrichit la réponse du routeur sans calculer | `automation.experts.orchestrator.orchestrate`, tests d'intégration Paie, générateur de rapport via le résultat orchestré |
| Applicabilité | `automation.experts.paie.applies(answer)` | Active ou non l'expert à partir de la route et de la question | `paie.enrich` |
| Moteur de règles | `analyze_payroll_query(question, context) -> dict` | Classe le sujet, sélectionne et refuse des règles, collecte les variables | `paie.payroll_rule_analysis` |
| Intégration référentielle | `build_analysis(answer, rule_analysis) -> dict` | Construit `PayrollQuestion`, applique le protocole et rend deux réponses | `paie.enrich` |
| Protocole | `assess(PayrollQuestion) -> ProtocolAssessment` | Détermine pièces, refus et confiance | intégration référentielle et tests |
| Restitution protocole | `render_response(question, assessment, audience) -> dict` | Produit les vues salarié et expert | intégration référentielle |
| Orchestrateur | `orchestrate(answer) -> dict` | Appelle directement `paie.enrich` et conserve son dictionnaire | route locale et génération de rapport |
| Générateur de rapport | dictionnaire `expert_paie` | Lit les clés historiques françaises | `report_generator.py` |

ARCH-02 ne modifie aucun de ces points d'entrée ou consommateurs.

### 2.2 Entrée dictionnaire de `paie.enrich`

Clés effectivement lues, directement ou par les sous-composants :

- `query` : question obligatoire en pratique ;
- `route.domains` : activation et qualification ;
- `sources` et `source_layers` : références locales, sans preuve intrinsèque de lecture ;
- `issues` et `issue_groups` : données, documents et sources regroupés ;
- `context`, `payroll_context`, `payroll_rule_context` : contexte fusionné ;
- `reference_date`, `employee_population`, `employment_category`, `work_schedule`, `site` ;
- `variables` ;
- `documents`, `documents_present`, `pieces_presentes` ;
- `documents_to_request` ;
- `urgent`.

Il n'existe pas aujourd'hui d'identifiant obligatoire de demande dans ce dictionnaire. L'adaptateur conserve `request_id`, `case_id` ou `dossier_id` lorsqu'il existe ; sinon il génère un identifiant déterministe à partir du contenu canonique.

### 2.3 Entrée dataclass du protocole

`PayrollQuestion` est une dataclass gelée contenant :

- `question`, `question_type`, `subject`, `scope` ;
- `population`, `period`, `payroll_period`, `urgent` ;
- `available_documents` ;
- `sources`, `rules`, `variables`, `kelio_counters`, `nibelis_rubrics`, `parameters` ;
- `missing_information`, `contradictory_documents`.

Elle est construite dans `payroll_referential_integration.build_analysis`, puis transmise à `assess` et `render_response`.

### 2.4 Sortie du moteur de règles

`analyze_payroll_query` retourne notamment :

- `catalog`, `query_topics` ;
- `candidate_rules`, `selected_rules`, `rejected_rules`, `historical_rules` ;
- `source_hierarchy` ;
- `variables.required`, `present`, `missing`, `ambiguous` ;
- `documents_present`, `documents_to_request` ;
- `calculation_ready`, `rule_conflict`, `warnings`, `confidence`.

Cette structure reste imbriquée sous `payroll_rule_analysis`. ARCH-02 la conserve dans les métadonnées du rapport ; il ne tente pas de transformer une règle sélectionnée en fait établi.

### 2.5 Sortie de l'intégration référentielle

`build_analysis` expose :

- disponibilité, étapes du protocole, sujet, interruption et refus ;
- confiance et motifs de confiance ;
- documents vérifiés et manquants ;
- réponses salarié et expert ;
- candidats issus des référentiels ;
- drapeaux explicites `calculation_performed=False` et `synthetic_values_used=False` ;
- limites et avertissements.

La structure complète reste sous `payroll_referential_analysis` dans les métadonnées ARCH-01.

### 2.6 Sortie publique de l'Expert Paie

Lorsque l'expert est actif, `paie.enrich` produit les clés :

- `active`, `name`, `objet_du_controle` ;
- `elements_du_bulletin_concernes` ;
- `regles_ou_sources_disponibles` ;
- `donnees_necessaires_au_calcul` ;
- `methode_de_controle`, `anomalies_potentielles` ;
- `calcul_detaille`, `documents_necessaires`, `sources_utilisees` ;
- `niveau_de_confiance`, `limites` ;
- `payroll_rule_analysis`, `payroll_referential_analysis` ;
- `reponse_salarie`, `reponse_expert`.

Lorsqu'il est inactif, la forme minimale est `active`, `name`, `reason`.

Les tests existants figent notamment l'absence de calcul inventé, le filtrage des règles, les demandes de documents, les réponses salarié/expert, le repli sûr et la conservation des clés historiques.

### 2.7 Inventaire typé des champs aux frontières

| Champ historique | Type réel | Présence | Défaut actuel | Origine | Destination | Incompatibilité ou perte | Conversion ARCH-02 |
|---|---|---|---|---|---|---|---|
| `query` | `str` | obligatoire pour une demande utile | chaîne vide tolérée par certains composants | routeur/réponse locale | `ExpertRequest.question_text` | ARCH-01 refuse le vide | validation non vide |
| `request_id`, `case_id`, `dossier_id` | scalaire textuel | optionnelle | absent | producteur amont | `request_id` | Paie n'impose aucun identifiant | conservation prioritaire, sinon empreinte stable |
| `route.domains` | liste de chaînes | optionnelle | liste vide | routeur | métadonnées legacy | pas de champ ARCH-01 équivalent | conservation structurée |
| contextes Paie | dictionnaire | optionnelle | `{}` | routeur, appelant, moteur | `ExpertRequest.context` | trois clés d'enveloppe concurrentes | fusion ordonnée et copie |
| `facts` | chaîne, objet ou liste | optionnelle | vide | appelant futur/legacy | `facts` | qualification rarement présente aujourd'hui | seulement fait explicitement déclaré comme tel |
| `declarations` | chaîne, objet ou liste | optionnelle | vide | appelant futur/legacy | `declared_information` | aucune clé publique actuelle garantie | déclaration conservée, jamais promue |
| hypothèses, intentions, scénarios | chaîne, objet ou liste | optionnelle | vide | extensions legacy | métadonnées de requête | aucun champ direct dans `ExpertRequest` | conservation par catégorie et restitution |
| `sources` | liste de chaînes ou dictionnaires | optionnelle | vide | routeur et recherche locale | références et `KnowledgeSource` | ne prouve pas une lecture | aucune `SourceEvidence` sans trace complète |
| `missing_information` | chaîne, objet ou liste | optionnelle | vide | protocole ou appelant | `MissingInformation[]` | chaînes peu structurées | enrichissement prudent et original conservé |
| `PayrollQuestion.scope` | `QuestionScope` | obligatoire dans la dataclass | aucun | intégration référentielle | contexte ARCH-01 | enum historique | valeur textuelle et original conservés |
| documents et référentiels | tuples, frozenset et enums | optionnelle | collections vides | protocole Paie | contexte et métadonnées | pas de contrats dédiés ARCH-01 | copie JSON déterministe |
| `active` | `bool` | obligatoire dans la sortie publique | `False` hors périmètre | `paie.enrich` | statut de rapport | correspondance non bijective | `False` devient `REFUSED`, erreurs deviennent `FAILED` |
| objet et éléments du contrôle | chaîne et listes | présents si actif | listes générées | Expert Paie | `findings` | ce ne sont pas des faits établis | constats de périmètre seulement |
| méthode et recommandations | listes de chaînes | présentes si actif | listes générées | Expert Paie | `recommendations` | catégories historiques partiellement confondues | mapping seulement des clés explicites |
| anomalies potentielles | liste de chaînes | présente si actif | liste générée | Expert Paie | `assumptions` | aucun niveau de risque | hypothèses uniquement |
| documents/données nécessaires | listes de chaînes | présentes si actif | listes générées | Expert Paie | `MissingInformation[]` | addressee et criticité absents | défaut documenté, original conservé |
| `niveau_de_confiance` | chaîne ou futur dictionnaire | présente si actif | faible, moyen ou valeur protocole | Expert Paie/intégration | évaluations de confiance | valeur globale historique | conversion prudente et dimensions séparées si disponibles |
| limites, erreurs et refus | listes ou objets | optionnelle | vide/repli sûr | expert, protocole, intégration | warnings, errors, status | sémantiques distinctes | aucune promotion en conclusion |
| analyses règle/référentiel | dictionnaires imbriqués | optionnelle | repli ou `None` | sous-moteurs Paie | métadonnées legacy | pas d'équivalent direct complet | conservation intégrale, aucun recalcul |
| champ inconnu | valeur JSON | optionnelle | sans objet | extension historique | métadonnées structurées | non convertible | enregistrement individuel avec statut et avertissement |

## 3. Correspondance ancien vers nouveau

### 3.1 Requête

| Structure historique | Contrat ARCH-01 | Règle |
|---|---|---|
| `request_id`, `case_id`, `dossier_id` | `ExpertRequest.request_id` | priorité dans cet ordre ; sinon empreinte SHA-256 stable |
| `query` ou `question` | `question_text` | texte non vide obligatoire |
| `domain` | `requested_domain` | défaut prudent `paie` |
| contextes Paie et champs de contexte directs | `context` | fusion déterministe, copie sans mutation |
| `facts`, `established_facts` | `facts` | uniquement `ESTABLISHED_FACT` explicite |
| `declarations`, `declared_information` | `declared_information` | toujours `DECLARED_INFORMATION`, jamais promu en fait |
| `hypotheses`, `assumptions` | `metadata.legacy_categories.assumptions` | `ExpertRequest` ne possède pas ce champ |
| `assumed_intentions` | `metadata.legacy_categories.assumed_intentions` | séparation conservée |
| `scenarios` | `metadata.legacy_categories.scenarios` | séparation conservée |
| `missing_information` | `MissingInformation[]` | chaînes ou objets structurés ; niveau par défaut `MEDIUM` documenté pour une information manquante |
| noms ou objets `sources` | `available_evidence_refs` et source convertible séparément | un nom n'est jamais une preuve |
| champs inconnus | `metadata.legacy.unknown_fields` | aucune suppression silencieuse |
| structure complète | `metadata.legacy.original` | permet restitution et audit |

### 3.2 Rapport

| Structure historique | Contrat ARCH-01 | Règle |
|---|---|---|
| `report_id` | `report_id` | conservé ou généré par empreinte stable |
| `request_id` ou argument explicite | `request_id` | obligatoire pour la traçabilité |
| `name` | `producer` | défaut `Expert Paie V0` |
| `objet_du_controle`, éléments concernés | `findings` | constats de périmètre, pas faits juridiques |
| `conclusions` | `conclusions` | uniquement si la structure historique en fournit |
| `methode_de_controle`, `recommendations` | `recommendations` | pas de calcul ajouté |
| `proposed_actions` | `proposed_actions` | copie explicite |
| `questions_to_ask` | `questions_to_ask` | copie explicite |
| `donnees_necessaires_au_calcul` ou `missing_information` | `MissingInformation[]` | aucune donnée réelle ajoutée |
| risques structurés | `RiskAssessment[]` | description, impact et niveau explicites obligatoires |
| risque texte libre | non converti | erreur compréhensible : classement interdit sans structure |
| `anomalies_potentielles`, `hypotheses` | `assumptions` | `ASSUMPTION`, jamais fait établi |
| `scenarios` | `scenarios` | `SCENARIO` |
| `niveau_de_confiance` scalaire | `ConfidenceAssessment(EXPERT_ANALYSIS_CONFIDENCE)` | conversion prudente d'une seule dimension |
| confiance structurée | plusieurs `ConfidenceAssessment` | factuelle, juridique, documentaire et couverture restent distinctes lorsque disponibles ; calcul et doublons sans équivalent restent en métadonnées |
| source sans trace | `KnowledgeSource` | `NOT_INVESTIGATED`, sans date ni preuve |
| source avec trace valide | `KnowledgeSource` + `SourceEvidence` | preuve structurée, réussie ou issue du cache, horodatée |
| limites et avertissements | `warnings` | conservation sans promotion en conclusion |
| erreurs | `errors`, statut `FAILED` | explicite |
| sections règle/référentiel/réponses | `metadata.legacy_sections` | conservation intégrale |
| champs inconnus et original | métadonnées structurées | conservation intégrale |

## 4. Correspondance nouveau vers ancien

| Contrat ARCH-01 | Format historique restitué |
|---|---|
| `ExpertRequest.request_id` | `request_id` |
| `question_text` | `query` |
| `requested_domain` | `domain` |
| `context` | `context` |
| faits et déclarations | `facts`, `declarations` avec leur type explicite |
| catégories sans champ de requête ARCH-01 | `hypotheses`, `assumed_intentions`, `scenarios` depuis les métadonnées |
| informations manquantes | `missing_information` structuré |
| références disponibles | `available_evidence_refs` |
| rapport actif | `active=True`, sauf statut `REFUSED` ou `FAILED` |
| findings | `objet_du_controle` et `elements_du_bulletin_concernes` |
| recommandations | `methode_de_controle` |
| sources et preuves | `sources`, `source_evidence` distincts |
| confiance | `niveau_de_confiance` ; valeur brute si inconnue |
| avertissements | `limites` |
| structure originale | base de restitution ; les champs inconnus restent présents |

Une clé technique `_nexus_arch02` contient la version d'adaptateur et le contrat sérialisé. Le code Paie actuel ignore les clés inconnues, ce qui rend cette enveloppe rétrocompatible. Elle permet un aller-retour nouveau → ancien → nouveau sans perte lorsque le payload n'est pas altéré entre les deux conversions.

## 5. Règles de conversion

### 5.1 Identifiants

Un identifiant historique est prioritaire. En son absence, l'adaptateur calcule une empreinte SHA-256 sur une représentation JSON canonique. Il n'utilise ni compteur global, ni UUID aléatoire, ni horloge. Deux conversions identiques produisent donc les mêmes identifiants.

### 5.2 Immutabilité et absence d'effet de bord

Les entrées sont copiées récursivement. Les contrats ARCH-01 figent ensuite leurs collections. Les conversions inverses rendent de nouveaux dictionnaires. Aucun objet d'entrée n'est muté.

### 5.3 Confiance

Une valeur globale scalaire est convertie uniquement vers `EXPERT_ANALYSIS_CONFIDENCE`. Elle ne renseigne ni fiabilité d'une source, ni solidité juridique, ni complétude du dossier. Une valeur inconnue conserve sa valeur brute et un niveau `None`. Aucun niveau inconnu n'est transformé en `MEDIUM`.

Lorsqu'une structure historique fournit plusieurs dimensions, l'adaptateur conserve séparément :

- factuelle → `EXPERT_ANALYSIS_CONFIDENCE` ;
- juridique → `LEGAL_SOLIDITY` ;
- documentaire → `SOURCE_RELIABILITY` ;
- couverture → `CASE_COMPLETENESS`.

La confiance de calcul n'a pas d'équivalent fidèle dans ARCH-01 et reste en métadonnées avec avertissement. Une confiance globale en doublon d'une confiance factuelle reste également en métadonnées afin de respecter l'unicité des dimensions.

### 5.4 Risques

Un risque doit être structuré et posséder un niveau explicite. Un niveau manquant n'est jamais remplacé par `MEDIUM`. `CRITICAL` exige une description et un impact non vides, comme l'impose ARCH-01. Les anomalies potentielles textuelles restent des hypothèses et non des risques classés.

### 5.5 Sources et preuves

Un nom de document, une couche de source ou une liste de sources produit uniquement un `KnowledgeSource` non consulté. La source reçoit `NOT_INVESTIGATED` et `consultation_not_demonstrated=true`.

Une preuve exige une structure `consultation_evidence` comprenant :

- `status` égal à `SUCCEEDED` ou `CACHE_HIT` ;
- `occurred_at` ISO-8601 avec fuseau ;
- `exact_reference` ;
- `access_result` ;
- `excerpt_or_fingerprint` ou `verifiable_trace` constituant la trace vérifiable.

Les drapeaux historiques `consulted=true` ou `consulted_at` sans cette structure sont refusés. L'adaptateur n'invente jamais une consultation.

### 5.6 Champs inconnus

Chaque conversion conserve :

- le type d'origine ;
- le nom et la version de l'adaptateur ;
- la structure originale JSON ;
- les champs non reconnus séparément ;
- les sections historiques imbriquées importantes.

Chaque champ sans équivalent possède un enregistrement individuel contenant au minimum :

- `legacy_type` ;
- `legacy_field` ;
- `legacy_value` ;
- `adapter_version` ;
- `conversion_status` ;
- `conversion_warning`.

La traçabilité globale ajoute l'identifiant d'origine, la liste des champs convertis, la liste des champs non convertis et les avertissements de conversion.

Aucune date de conversion n'est ajoutée : elle rendrait la fonction non déterministe et n'est pas pertinente sans événement de persistance.

## 6. Pertes potentielles et ambiguïtés

| Ambiguïté | Traitement ARCH-02 |
|---|---|
| La requête ARCH-01 ne porte pas hypothèses, intentions ou scénarios | conservation séparée dans les métadonnées, restitution inverse |
| La sortie Paie ne distingue pas toujours conclusion, recommandation et limite | seules les clés explicitement nommées sont mappées ; les autres restent dans l'original |
| `anomalies_potentielles` n'a pas de niveau de risque | conversion en hypothèses, jamais en risque classé |
| `sources_utilisees` peut être un simple libellé | source non consultée, aucune preuve |
| La confiance historique est globale | une seule dimension d'analyse, sans extrapolation |
| Certains payloads n'ont pas d'identifiant | empreinte stable du contenu, donc changement si le contenu change |
| Un risque libre n'a pas de niveau, impact ou horizon fiable | refus de conversion, aucun défaut silencieux |
| Les réponses salarié et expert sont des dictionnaires spécifiques | conservation complète dans `metadata.legacy_sections` |
| Le format historique peut accepter des extensions | original et inconnus conservés ; la clé de pont est ignorée par Paie |

## 7. Stratégie de rétrocompatibilité

1. Les points d'entrée existants ne sont pas modifiés.
2. Les adaptateurs sont appelables explicitement par de futurs pilotes et tests.
3. La restitution historique conserve les clés inconnues et l'original.
4. Les tests Paie existants sont relancés avec leurs fonctions `run_all()` réelles.
5. La façade n'est pas activée et aucun consommateur ne reçoit encore un contrat commun.
6. Toute activation future devra être derrière une frontière réversible et comparer les sorties historiques avant/après.

## 8. Façade pilote

Aucune façade expérimentale n'est créée dans ce lot. Le point public actuel `orchestrator.orchestrate` appelle directement `paie.enrich`, et le générateur de rapport dépend de sa forme exacte. Ajouter maintenant une façade qui appelle l'expert créerait un second chemin d'exécution sans consommateur et augmenterait le risque de divergence.

Point d'intégration futur prévu : une façade distincte, après validation du présent lot, pourra recevoir `ExpertRequest`, appeler successivement `expert_request_to_legacy_payroll`, `paie.enrich`, puis `legacy_payroll_report_to_expert_report`. Elle ne devra remplacer le chemin actuel qu'après comparaison de non-régression et mécanisme de désactivation.

## 9. Tests synthétiques

La suite `automation.adapters.test_payroll` couvre 55 contrôles : conversions minimales et complètes, validations, catégories, sources, preuves, confiance multidimensionnelle, quatre niveaux de risque, métadonnées, déterminisme, immutabilité, collections non partagées, dépendances, API publique et aller-retour. Elle inclut six scénarios sans donnée réelle :

- heures supplémentaires ;
- astreinte ;
- congés payés ;
- maintien de salaire ;
- jour férié ;
- repos compensateur.

## 10. Confidentialité

Les fixtures ARCH-02 utilisent uniquement des identifiants et contenus explicitement synthétiques. Aucun nom réel, matricule, IBAN, BIC réel, secret, jeton, clé privée ou chemin privé n'est ajouté. Le validateur BIC n'est pas modifié. Ses faux positifs éventuels sur des mots techniques en majuscules doivent rester distingués d'une donnée bancaire réelle.

## 11. Plan de migration future

1. Valider et figer les adaptateurs ARCH-02.
2. Ajouter des tests de projection autour d'un échantillon synthétique plus large des payloads Paie.
3. Créer la façade pilote réversible sans modifier les consommateurs.
4. Exécuter en double lecture : sortie historique de référence et contrat adapté, sans changer la réponse utilisateur.
5. Comparer les écarts et enrichir les mappings explicites.
6. Basculer un seul consommateur Paie après validation humaine.
7. Stabiliser le pilote avant toute migration Juriste ou autre domaine.
8. Intégrer les connecteurs officiels dans Connector Platform et sécuriser les corpus internes selon la feuille de route validée.
9. N'envisager le Strategic Reasoning Engine qu'après la migration du pilote et la stabilisation des contrats.

## 12. Limites du lot

- aucune migration complète de l'Expert Paie ;
- aucune modification de `paie.py`, du moteur de règles, du protocole ou de l'intégration référentielle ;
- aucun changement du routeur, de l'orchestrateur, de l'interface HTTP ou du site ;
- aucun connecteur ou corpus consulté ;
- aucun calcul de paie ;
- aucune façade activée ;
- aucun changement de comportement utilisateur ;
- aucun Strategic Reasoning Engine, Quality Engine ou contradicteur ;
- aucune correction ou exception du validateur BIC.

## 13. Critères d'acceptation ARCH-02

ARCH-02 est acceptable si les conditions suivantes sont simultanément satisfaites :

1. la couche réside hors de `automation/contracts` et n'altère aucun contrat ARCH-01 ;
2. l'API publique versionnée expose les neuf conversions prévues ;
3. les requêtes et rapports minimaux et complets sont convertis ;
4. les aller-retour conservent les données utiles et les extensions historiques ;
5. chaque donnée non convertible possède une trace structurée complète ;
6. aucune déclaration, hypothèse, intention ou scénario n'est promu en fait ;
7. aucun risque inconnu n'est classé par défaut et les quatre niveaux explicites sont testés ;
8. une confiance inconnue reste inconnue et les dimensions disponibles restent séparées ;
9. aucune preuve de source n'est créée sans référence, résultat, horodatage avec fuseau et trace vérifiable ;
10. les conversions sont déterministes, sans mutation ni collection partagée ;
11. aucun appel réseau ou import interdit n'est introduit ;
12. les tests ARCH-01, ARCH-02 et toutes les non-régressions demandées réussissent ;
13. aucun fichier applicatif existant ni consommateur n'est modifié ;
14. aucune façade n'est activée avant ARCH-03 ;
15. aucun commit, push ou merge n'est effectué avant validation.
