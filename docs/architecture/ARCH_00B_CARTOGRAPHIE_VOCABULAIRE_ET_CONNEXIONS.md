# LOT ARCH-00B — Cartographie du vocabulaire et des connexions

- Date : 18 juillet 2026
- Dépôt : `C:\tmp\cfdt-nexus`
- Origin : `https://github.com/thierrykrempff-maker/cfdt-nexus.git`
- Branche : `audit-connectors-platform-conformity`
- HEAD : `993c6e6260274737be840d11661e489e7443aecf`
- Recommandation pour ARCH-01 : **GO AVEC RÉSERVES**
- Périmètre : documentation seulement ; aucun contrat runtime, fichier applicatif ou test modifié

## 1. Méthode, périmètre et synthèse

Cette cartographie part des frontières réellement exécutées : `POST /api/analyze`, CLI `assistant_ds_router.py ask`, enrichisseurs Juriste et Paie, orchestrateur, générateur de rapport, dossier salarié synthétique, pipelines CSE Memory/Protection sociale et Connector Platform. Les catalogues et documentations ne sont retenus comme preuve d'une connexion que lorsqu'un transport et un test correspondant existent.

L'inventaire retient **127 orthographes exactes** dans les contrats actifs ou directement préparatoires : **45 termes d'entrée**, **56 termes de sortie** et **26 termes de source, preuve, confiance ou qualité**. Le volume brut de **12 745 entrées** correspond aux occurrences, paramètres, clés et usages techniques recensés dans le code ; il ne représente pas 12 745 concepts métier distincts. Les variantes purement internes à un algorithme et sans portée contractuelle ne sont pas comptées.

Cinq divergences critiques préparent ARCH-01 :

1. une même demande est nommée `query`, `route.query`, `question` ou `main_question`, avec des types et obligations différents ;
2. aucun contrat commun ne sépare faits établis, informations déclarées, hypothèses, scénarios et intentions supposées ;
3. les résultats Juriste, Paie, routeur et dossier salarié ont quatre formes incompatibles ;
4. `confidence` mélange confiance de routage, de métadonnée, de règle et d'analyse, tandis que qualité, pertinence et complétude restent partiellement implicites ;
5. aucune règle commune n'interdit techniquement d'afficher « source consultée » sans preuve d'une lecture ou d'un appel réussi.

Les risques ARCH-00 restent valides : exposition possible du serveur sans authentification et question en argument processus (P0), connecteurs historiques hors plateforme et dictionnaires non versionnés (P1), duplication des modèles documentaires et vocabulaire bilingue (P2). ARCH-01 doit rester un lot de contrats et d'adaptateurs sans changement de comportement.

## 2. Inventaire du vocabulaire d'entrée

Abréviations : **O** obligatoire à la construction ou à la frontière ; **F** facultatif, avec défaut ou tolérance d'absence. Les types sont ceux observés, non les types souhaités.

| Orthographe exacte | Fichier / symbole | Type réel | Producteur → consommateur | O/F | Sens et ambiguïté | Canonique proposé |
| --- | --- | --- | --- | --- | --- | --- |
| `query` | `server.py::do_POST`, `analyze_question`; routeur `ask` | `str` après coercition | HTTP/CLI → routeur, experts | O à l'API logique, F dans le JSON | texte utilisateur ; peut contenir des données sensibles | `question_text` |
| `route.query` | `assistant_ds_router.py::route_query` | `str` | routeur → sélecteurs | O | duplication de `answer.query` | adaptateur vers `question_text` |
| `main_question` | `cases/employee_case.py::EmployeeCase` | `str` | fixture/dossier → pipeline | O | question principale d'un dossier, plus cadrée que `query` | `question_text` + `case_id` |
| `question` | `payroll_reasoning_protocol.py::PayrollQuestion` | `str` | adaptateur Paie → protocole | O | demande Paie ; distincte de `question_type` | `question_text` |
| `description` | `EmployeeCase` | `str` | dossier → pipeline/rapport | O | contexte narratif, potentiellement mêlé aux faits | `request_context.summary` |
| `understanding` | routeur `ask`; `ProtocolAssessment` | `str` ou `Mapping` | routeur/protocole → rapport | O en sortie, dérivé | compréhension calculée, pas une entrée utilisateur | `request_interpretation` |
| `context` | `paie.py::payroll_rule_context` | `dict[str, Any]` | appelant legacy → Paie | F | fourre-tout sans schéma | `request_context.extensions` |
| `payroll_context` | même symbole | `dict[str, Any]` | appelant legacy → Paie | F | alias de contexte Paie | `domain_context.payroll` |
| `payroll_rule_context` | même symbole | `dict[str, Any]` | appelant legacy → moteur règles | F | contexte technique ciblé | `domain_context.payroll.rules` |
| `domains` | routeur `route`; helpers experts | `list[str]` | routeur → experts | O dérivé | domaines détectés, non demandés | `detected_domains` |
| `main_domain` | routeur | `str` | routeur → rapport | O dérivé | domaine prioritaire | `primary_domain` |
| `secondary_domains` | routeur | `list[str]` | routeur → rapport | O dérivé | domaines secondaires | `secondary_domains` |
| `detected_themes` | `EmployeeCase` | `list[str]` | dossier → pipeline | O | thèmes de dossier, voisin de domaines | `detected_domains` ou `topic_tags` selon usage |
| `intents` | routeur | `list[str]` | routeur → plan/expert | O dérivé | actions attendues détectées | `detected_intents` |
| `question_type` | `PayrollQuestion` | `str` | adaptateur → protocole | O | nature de question non bornée | `request_kind` |
| `subject` | `PayrollQuestion` | `str` | adaptateur → règles de preuves | O | sujet Paie technique | `domain_subject` |
| `scope` | `PayrollQuestion` | `QuestionScope` | adaptateur → protocole | O | individuel/collectif | `request_scope` |
| `population` | `PayrollQuestion`, `EmployeeCase` | `str | None` / `str` | dossier/adaptateur → moteurs | O dossier, F Paie | salarié ou groupe ; ne doit pas contenir une identité brute | `affected_population` |
| `employee_population` | `paie.py` | `Any` | payload legacy → contexte Paie | F | alias non typé de population | `affected_population` |
| `employee_information` | `EmployeeCase` | `dict[str, Any]` | dossier → pipeline | F | données du salarié, zone sensible et non structurée | `subject_attributes` expurgés |
| `site` | `paie.py` | `Any` | payload legacy → contexte Paie | F | établissement ou site ; ambigu avec origine web | `establishment_id` |
| `period` | dossier, Paie, documents | `str` / `str | None` | appelant → experts | O dossier, F ailleurs | période métier libre | `analysis_period` |
| `payroll_period` | `PayrollQuestion` | `str | None` | adaptateur → Paie | F | période de paie, sous-ensemble précis | `payroll_period` |
| `reference_date` | `paie.py` | `Any` | payload legacy → règles | F | date d'applicabilité | `as_of_date` |
| `urgent` | dossier, `PayrollQuestion` | `bool` | appelant → pipeline | O dossier, F Paie | urgence déclarée sans échelle | `urgency` |
| `confidentiality` | `EmployeeCase`, `EmployeeDocument` | `ConfidentialityLevel` | dossier → sérialisation/contrôles | F avec défaut | absent de l'API générale ; niveaux internes/restricted/sensitive | `confidentiality_level` |
| `source_limit` | HTTP/CLI | `int` | utilisateur technique → routeur | F, défaut 6 | limite de résultats, pas niveau de détail | `knowledge_limits.max_sources` |
| `response_depth` | routeur | `str` dérivé | routeur → rapport | O dérivé | niveau de réponse calculé | `requested_detail_level` seulement si demandé, sinon `rendering_depth` |
| `available_documents` | `PayrollQuestion` | `frozenset[DocumentCategory]` | adaptateur → protocole | F | catégories disponibles, sans référence aux pièces | `available_evidence_refs` |
| `documents` | `EmployeeCase`; contexte Paie | `list[EmployeeDocument]` / `Any` | dossier/legacy → pipeline | O dossier, F Paie | objets ou valeurs libres selon chemin | `evidence_items` |
| `documents_present` | `paie.py` | `Any` | legacy → Paie | F | alias de pièces disponibles | `available_evidence_refs` |
| `pieces_presentes` | `paie.py` | `Any` | legacy → Paie | F | alias français | `available_evidence_refs` |
| `missing_documents` | `EmployeeCase` | `list[str]` | dossier → pipeline | F | pièces déjà connues comme manquantes | `missing_information` avec type `document` |
| `documents_to_request` | routeur/Paie | `list[str]` | routeur/expert → orchestration | sortie dérivée | action de collecte, pas entrée réelle | `requested_evidence` |
| `assumptions` | `EmployeeCase` | `list[str]` | dossier → pipeline | F | hypothèses déjà formulées ; provenance absente | `assumptions` structurées |
| `missing_information` | `PayrollQuestion` | `tuple[str, ...]` | adaptateur → protocole | F | information manquante générale | `missing_information` |
| `contradictory_documents` | `PayrollQuestion` | `bool` | adaptateur → refus | F | réduit toute contradiction à un booléen | `contradictions` structurées |
| `variables` | Paie | `tuple[str, ...]` ou `dict` | contexte/référentiel → moteur | F | noms ou valeurs selon chemin | `calculation_inputs.variables` |
| `kelio_counters` | `PayrollQuestion` | `tuple[str, ...]` | adaptateur → Paie | F | références de compteurs | `calculation_inputs.time_counters` |
| `nibelis_rubrics` | `PayrollQuestion` | `tuple[str, ...]` | adaptateur → Paie | F | rubriques du SI Paie | `calculation_inputs.payroll_lines` |
| `parameters` | `PayrollQuestion` | `tuple[str, ...]` | adaptateur → Paie | F | paramètres non qualifiés | `calculation_inputs.parameters` |
| `sources` | routeur/Paie | `list[dict]` ou `tuple[str, ...]` | recherche/adaptateur → experts | F | résultat récupéré ou simple libellé | `knowledge_sources` / `source_evidence` |
| `rules` | `PayrollQuestion` | `tuple[str, ...]` | adaptateur → protocole | F | règles disponibles, sans statut | `applicable_rules` |
| `synthetic_only` | dossier/document | `bool` | fixture → garde de pipeline | F avec `True` | nature synthétique, pas confidentialité | `data_classification.synthetic` |
| `privacy_probe` | `EmployeeCase` | `str | None` | test → pipeline | F | sonde de non-divulgation, pas donnée métier | rester extension de test uniquement |

Constat : aucun champ actif ne représente proprement l'établissement, l'auteur d'une déclaration, la provenance d'un fait, le niveau de détail demandé ni la confidentialité de la requête HTTP générale. Ces absences doivent être explicites dans ARCH-01, sans rendre tous les champs obligatoires dès V1.

## 3. Inventaire du vocabulaire de sortie

| Famille | Orthographes exactes observées | Producteur / type | Différence de sens | Canonique proposé |
| --- | --- | --- | --- | --- |
| réponse courte | `short_answer`, `response_courte`, `reponse_courte`, `reponse_synthetique_nexus`, `message` | routeur/Juriste/orchestrateur/Paie ; `str` | texte bref à des niveaux différents | `executive_summary` |
| synthèse | `summary`, `synthese`, `synthetic_summary`, `understanding` | dossier/rapport/orchestrateur ; `str` | résumé d'analyse, de document ou compréhension | conserver `summary` avec `summary_kind` |
| rapport | `analysis_report`, `report`, `sections`, `markdown`, `generated_from` | serveur/générateur ; `dict`, `list`, `str` | objet, projection et traçabilité | `expert_report`, `rendered_views`, `generation_trace` |
| analyse | `analysis`, `analyse_metier`, `analyse_par_expertise`, `payroll_rule_analysis`, `payroll_referential_analysis` | experts/orchestrateur | analyses métier et techniques incompatibles | `analyses[]` avec `analysis_kind` |
| constat | `findings`, `points_cles`, `control_points`, `asserted_facts` | routeur/dossier/orchestrateur | observation, contrôle ou fait affirmé | `findings` distinct de `facts` |
| conclusion | `conclusion`, `conclusion_provisoire_juridique`, `can_conclude`, `working_position`, `position_de_travail` | Paie/Juriste/routeur | texte, structure ou booléen | `conclusion`, `conclusion_status`, `working_position` |
| recommandation | `recommended_human_action`, `strategie_action_ordonnee`, `recommandations` implicites | Bible/Juriste | action humaine ou stratégie | `recommendations` puis `actions` |
| action | `next_action`, `action_immediate_recommandee`, `documents_to_request`, `questions_to_ask` | routeur/Juriste | prochaine étape, action ou collecte | `actions`, `requested_evidence`, `questions_to_ask` |
| alerte/avertissement | `warnings`, `limites`, `alertes`, `points_vigilance` | tous composants | qualité technique, limite métier ou vigilance | `warnings`, `limitations`, `risk_assessments` séparés |
| erreur | `error`, `error_code`, `code`, `message`, `engine_available`, `available` | HTTP/connecteurs/Paie | transport, configuration ou indisponibilité | `errors[]` structurées + `component_status` |
| refus | `refusals`, `refusal_reason`, `refusal_reasons`, `can_conclude` | protocole/dossier/référentiel | refus multiple ou motif unique | `refusals[]` avec portée et remédiation |
| risque | `risks`, `controls.risks`, `risques_points_vigilance` | dossier/Paie/Juriste | conséquence ou simple motif de blocage | `risk_assessments[]` |
| source | `sources`, `sources_utilisees`, `regles_ou_sources_disponibles`, `source_layers`, `source_documents` | routeur/experts | objets récupérés ou noms | `knowledge_sources[]` et `source_evidence[]` |
| citation/preuve | `citation`, `cited_rules_or_sources`, `provenance`, `evidence_summary`, `detected_from`, `content_sha256` | plateforme/dossier/mémoires | citation humaine, provenance technique ou empreinte | `citation`, `source_evidence`, `content_fingerprint` |
| jurisprudence | `judilibre_id`, `decision_id`, `official_id`, `jurisprudence_relevance_score` | JUDILIBRE/Juriste | identité, référence et score | `legal_authority` type `case_law` |
| accord/règle | `agreement`, `rule_id`, `selected_rules`, `candidate_rules`, `rejected_rules`, `applicable_rules` | Bible/Paie | document, règle applicable ou candidate | `legal_authorities`, `rule_assessments` |
| calcul | `calculation_ready`, `calcul_detaille`, `variables`, `missing`, `ambiguous` | Paie | capacité, texte de refus, entrées | `calculation_assessment` ; aucun résultat inventé |
| hypothèse/scénario | `assumptions`, `hypotheses`, `scenario`, `scenarios` | dossier/rapport/demo | hypothèse métier ou scénario de test | `assumptions`, `scenarios`; ne pas fusionner |
| contradiction | `contradictory_documents`, `conflicts`, `incoherences`, `contradictions` | Paie/mémoires/dossier | booléen, conflit technique ou métier | `contradictions[]` |
| manquant | `missing_information`, `missing_documents`, `absent_documents`, `indispensable_missing_documents`, `documents_missing`, `missing_data` | Paie/dossier | information, pièce ou entrée de calcul | `missing_information[]` avec `kind` |
| confiance | `confidence`, `niveau_de_confiance`, `confidence_level`, `confidence_score` | routeur/experts/mémoires | quatre objets d'évaluation différents | `confidence_assessments[]` typés |
| complétude | `can_conclude`, `calculation_ready`, `status=partial`, pièces absentes | implicite | possibilité de conclure, pas confiance | `completeness_assessment` |
| qualité | `quality_score`, `quality_level`, `chunk_quality_level`, `metadata_quality_level`, `quality_flags` | mémoires | qualité technique d'extraction/indexation | `quality_assessments[]` |
| pertinence | `_router_score`, `ranking_reasons`, `jurisprudence_relevance_score`, `source_quality_warning` | routeur | classement contextuel et avertissement | `relevance_assessment` |

Deux termes proches ne sont donc pas synonymes : une source peut être officielle et fiable mais peu pertinente ; une extraction peut être techniquement excellente dans un dossier incomplet ; une conclusion juridique peut être solide malgré une forte incertitude stratégique.

## 4. Concepts stratégiques obligatoires

| Concept | Définition et critère d'utilisation | Exemple synthétique | Erreurs à éviter | Futur champ |
| --- | --- | --- | --- | --- |
| Fait | élément corroboré par une pièce ou une source vérifiable ; citer la preuve | « Le planning synthétique indique une prise de poste à 8 h. » | déduire l'intention ; omettre la preuve | `facts[]` |
| Information déclarée | élément fourni par l'utilisateur, non encore corroboré | « Le salarié déclare avoir repris à 8 h. » | l'étiqueter comme fait | `declared_information[]` |
| Hypothèse | explication plausible nécessitant vérification | « Une mauvaise rubrique pourrait expliquer l'écart. » | conclure ou calculer à partir d'elle | `assumptions[]` |
| Scénario | évolution possible ou réaction conditionnelle | « Si la direction maintient le projet, demander l'étude d'impact. » | présenter une probabilité comme certitude | `scenarios[]` |
| Intention supposée | attribution prudente et explicitement non établie d'un objectif à un acteur | « Il est possible, sans preuve, que la mesure vise une réorganisation. » | psychologiser ou accuser | `assumed_intentions[]` avec garde sensible |
| Information manquante | donnée nécessaire pour vérifier, qualifier ou conclure | « Bulletin de la période concernée. » | confondre absence dans Nexus et inexistence | `missing_information[]` |
| Contradiction | incompatibilité localisée entre deux assertions, sources ou résultats | « Planning et relevé horaire indiquent des fins différentes. » | résoudre silencieusement | `contradictions[]` |
| Risque | conséquence potentielle qualifiée par domaine, gravité et horizon | « Risque financier de rappel de salaire. » | confondre risque et fait acquis | `risk_assessments[]` |
| Action | mesure concrète, assignable et ordonnée | « Obtenir le relevé Kelio avant le contrôle du bulletin. » | recommander une action hors preuve | `actions[]` |
| Question à poser | demande ciblée à un acteur pour lever une incertitude | « Quelle règle locale justifie ce taux ? » | question suggestive présentée comme preuve | `questions_to_ask[]` |

Chaque entrée future doit porter au minimum un identifiant, un texte, une provenance, un statut de vérification et, lorsque pertinent, les identifiants des preuves ou contradictions liées.

## 5. Statut vérifié des sources et connexions

Les statuts ci-dessous sont exclusifs et décrivent l'état au HEAD audité.

| Source / socle | Statut | Preuves code et tests | Chemin exécutable et limites |
| --- | --- | --- | --- |
| Connector Platform | `OPERATIONAL` | `automation/connector_platform/*`; tests modèles, contrats, politiques, registre | socle fail-closed exécutable et testé ; ne connecte aucune source à lui seul |
| Légifrance / PISTE | `PARTIAL` | `scripts/legifrance_connector.py`, `assistant_ds_router.py::ask`, `test_legifrance_fallback.py` | vrai OAuth/HTTP et appel routeur si configuré ; test ciblé utilise un faux connecteur, pas de preuve réseau reproductible ni migration plateforme |
| JUDILIBRE / PISTE | `PARTIAL` | `scripts/judilibre_connector.py`, appel routeur | vrai OAuth/HTTP exécutable si configuré ; aucun test transport dédié trouvé, hors plateforme |
| Code du travail numérique | `PARTIAL` | `pratique_officielle_connector.py`, ancien `cdtn_connector.py`, routeur, `test_pratique_officielle_connector.py` | `/api/presearch` exécuté par le client et normalisé ; prototype, corps complet non récupéré, deux implémentations, hors plateforme |
| Accords et documents INEOS / Bible Accords | `LOCAL_CORPUS_ONLY` | `agreements_bible.py`, `nexus_bible_bridge.py`, schémas/index `database/agreements`, scénarios routeur | recherche locale active ; dépend du corpus présent et autorisé, aucun document confidentiel réel admis dans Git |
| Référentiels Paie | `LOCAL_CORPUS_ONLY` | `automation/payroll/*`, `database/payroll/*`, tests Paie | règles et référentiels locaux actifs ; exemples synthétiques, refus de calcul incomplet |
| CSE Memory | `LOCAL_CORPUS_ONLY` | `automation/cse_memory/*`, tests import/normalisation/métadonnées/chunks | pipeline local testé jusqu'aux chunks ; pas expert autonome ni connexion externe |
| Protection Sociale Engine | `LOCAL_CORPUS_ONLY` | `automation/protection_sociale/*`, tests synthétiques | pipeline local mutuelle/prévoyance/notices/garanties ; pas expert orchestré ni source externe |
| Mutuelle | `LOCAL_CORPUS_ONLY` | règles de chemins et métadonnées Protection sociale | ingestion de corpus local autorisé seulement ; aucun organisme/API connecté |
| Prévoyance | `LOCAL_CORPUS_ONLY` | mêmes modules et fixtures synthétiques | ingestion locale seulement ; aucune notice réelle dans Git |
| Notices et tableaux de garanties | `LOCAL_CORPUS_ONLY` | classificateur/importeur Protection sociale | formats locaux pris en charge ; qualité et confidentialité à contrôler avant exposition |
| ANACT / ARACT | `PARTIAL` | `official_knowledge/connectors/anact/*`; tests sitemap, métadonnées, classification | transports HTTPS bornés exécutables sur construction explicite ; façade reste `architecture_only`, désactivée et non intégrée au routeur |
| CNIL | `SCAFFOLD_ONLY` | catalogue, modèles, plateforme et tests CNIL | `discover`/`fetch`/`sync` lèvent `CNIL_CONNECTOR_NETWORK_NOT_IMPLEMENTED` |
| DREETS Grand Est | `SCAFFOLD_ONLY` | catalogue, revue d'accès, plateforme et tests | opérations réseau explicitement bloquées ; métadonnées/politiques seulement |
| CARSAT | `SCAFFOLD_ONLY` | `connectors/carsat/*` et tests | `ARCHITECTURE_ONLY`, capacité manuelle, statistiques nulles, réseau non implémenté |
| INRS | `SCAFFOLD_ONLY` | `connectors/inrs/*` et tests | catalogue/contrat seulement ; aucun transport, cache ou synchronisation |
| CNAM / Assurance Maladie – Risques professionnels | `PLANNED` | mentions de registre/veille et rapprochement CARSAT/ameli | aucun connecteur CNAM autonome ni chemin d'appel trouvé |
| Corpus CSSCT dédié | `PLANNED` | domaines/schémas/routeur/Bible CSE existants | logique thématique présente, mais pas de corpus CSSCT gouverné et exposé comme source autonome |
| Service-Public.fr via CDTN | `PARTIAL` | source autorisée dans `pratique_officielle_connector.py` | uniquement métadonnées remontées par `/api/presearch`, pas connecteur séparé |
| Veille contextuelle officielle et syndicale | `PLANNED` | registre et documentation de veille | sources nommées/configurées mais pas de pipeline plateforme prouvé au runtime principal |

Aucune source externe n'est classée `OPERATIONAL` : les connecteurs historiques sont exécutables, mais leur activation dépend de l'environnement et leur transport n'est pas couvert de bout en bout par un test reproductible hors réseau. Cette prudence évite de confondre « code capable d'appeler » et « connexion stabilisée ».

## 6. Vocabulaire canonique de `KnowledgeSource` (sans code)

| Besoin | Champ canonique proposé | Règle |
| --- | --- | --- |
| identité | `source_id`, `display_name`, `publisher` | identifiant stable, nom humain, organisme distincts |
| nature | `source_type`, `source_category` | API, page, document, corpus ; officiel/interne/réglementaire/contextuel séparés |
| connexion | `connection_status` | état technique réel, jamais dérivé d'un catalogue |
| statut institutionnel | `is_official`, `is_internal` | booléens indépendants |
| protection | `confidentiality_level` | public/interne/restreint/sensible avec politique d'accès |
| dates | `retrieved_at`, `published_at`, `effective_from`, `effective_to` | consultation, publication et effet ne sont pas interchangeables |
| champ | `jurisdiction`, `domains` | ressort et domaines multiples |
| référence | `canonical_uri`, `external_reference` | URL validée ou référence non URL |
| contenu | `extracted_content`, `citation` | extrait borné distinct de la citation affichable |
| évaluations | `relevance_assessment`, `source_reliability_assessment`, `freshness_assessment` | trois notions séparées |
| preuve | `retrieval_evidence_id` | référence obligatoire pour affirmer une consultation |
| échec | `connection_error` | code, catégorie, message expurgé, caractère transitoire |
| versions | `source_version`, `connector_version`, `schema_version` | version de contenu, transport et contrat distinctes |
| héritage | `native_payload_ref` | conserve la donnée legacy sans la confondre avec le canonique |

### Garde anti-fausse-consultation

`consulted` ne doit pas être un booléen libre. Il doit être **dérivé** d'une `SourceEvidence` avec `retrieval_status=SUCCEEDED`, `operation_id`, `connector_id`, `requested_at`, `completed_at`, `request_fingerprint`, `response_status`, `retrieved_at` et une empreinte ou référence du contenu obtenu. Les états minimaux sont `NOT_ATTEMPTED`, `PLANNED`, `SUCCEEDED`, `FAILED`, `CACHE_HIT`. `CACHE_HIT` doit afficher « consultée depuis le cache » avec date d'origine, jamais « consultée aujourd'hui ». Catalogue, fixture et configuration ne créent aucune preuve d'interrogation.

## 7. Séparation des notions de confiance

| Notion | Définition | Producteurs → consommateurs | Échelles existantes | Cible recommandée | Confusion à éviter |
| --- | --- | --- | --- | --- | --- |
| fiabilité de source | autorité et stabilité de la source | registre/humain → gateway/expert | A/B/C/D, `authority_level` | score borné + niveau + justification | officiel ≠ pertinent |
| confiance d'extraction | fidélité du texte/métadonnée extrait | pipeline documentaire → index/gateway | `0..1`, `very_low..very_high` | même score + preuves techniques | extraction ≠ vérité métier |
| pertinence | adéquation à la question | routeur/retriever → expert | `_router_score`, scores spécialisés | score `0..1` + raisons | rang ≠ autorité |
| complétude du dossier | couverture des faits/pièces nécessaires | expert/protocole → orchestrateur | booléens et listes de manquants | score de couverture + manquants bloquants | complétude ≠ confiance |
| confiance d'analyse | robustesse du raisonnement expert | expert → rapport/orchestrateur | `faible/moyen/fort`, uppercase | cinq niveaux + facteurs + valeur brute | minimum lexical ≠ agrégation valide |
| solidité juridique | stabilité de la conclusion au regard des textes, faits et jurisprudence | Juriste/humain → délégué | partiellement textuelle | niveau + autorités + réserves + validation humaine | certitude juridique ≠ stratégie |
| incertitude stratégique | variabilité des réactions et scénarios | futur SRE/humain → délégué | absente | faible/moyenne/forte incertitude + scénarios | ne jamais inventer une intention |
| qualité technique | lisibilité/indexabilité/cohérence du document | CSE/PS → index | `unusable..excellent` | conserver cette échelle séparée | qualité ≠ confiance |

ARCH-01 peut recommander une échelle commune de présentation `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`, mais chaque évaluation doit garder `assessment_kind`, `score`, `rationale`, `factors`, `raw_value`, `producer` et `known`. `UNKNOWN` est un état d'absence d'évaluation, pas un niveau faible.

## 8. Glossaire canonique

| Canonique | Définition | Anciens termes | À conserver / à déprécier | Domaine | Priorité / rupture |
| --- | --- | --- | --- | --- | --- |
| `ExpertRequest` | demande versionnée remise à un expert | answer, query, PayrollQuestion | conserver façades ; déprécier payload libre | transversal | P0 / élevée |
| `question_text` | texte original de la demande | query, question, main_question | conserver adaptateurs | demande | P0 / moyenne |
| `request_context` | contexte structuré non conclusif | context, description | conserver extensions | demande | P1 / moyenne |
| `detected_domains` | domaines inférés | domains, detected_themes | conserver codes existants | routage | P1 / faible |
| `detected_intents` | intentions de traitement | intents | conserver | routage | P1 / faible |
| `affected_population` | personne ou groupe concerné, expurgé | population, employee_population | déprécier alias | demande | P1 / moyenne |
| `evidence_items` | pièces ou références disponibles | documents, pieces_presentes | déprécier listes libres | preuve | P0 / élevée |
| `declared_information` | assertion utilisateur non corroborée | faits implicites | nouveau, sans supprimer legacy | stratégie | P0 / moyenne |
| `facts` | assertions corroborées | asserted_facts, findings | ne pas fusionner avec findings | stratégie | P0 / élevée |
| `assumptions` | hypothèses explicites | hypotheses | conserver, structurer | stratégie | P0 / moyenne |
| `scenarios` | évolutions conditionnelles | scenario | conserver terme de démo en extension | stratégie | P1 / faible |
| `assumed_intentions` | intentions non établies et sensibles | aucune structure | nouveau avec garde | stratégie | P0 / faible |
| `missing_information` | données/pièces nécessaires absentes | missing_*, absent_* | déprécier variantes après adaptateurs | complétude | P0 / moyenne |
| `contradictions` | incompatibilités explicites | conflicts, incoherences, booléen | conserver payload brut | qualité métier | P0 / moyenne |
| `ExpertReport` | sortie versionnée d'un expert | dict Juriste/Paie, ExpertAnalysis | envelopper avant migration | résultat | P0 / élevée |
| `findings` | constats analytiques, non forcément faits | points_cles | conserver findings | résultat | P1 / moyenne |
| `conclusion` | position motivée et bornée | working_position, conclusion_* | garder position legacy | résultat | P0 / élevée |
| `recommendations` | orientations motivées | stratégie/action mélangées | distinguer des actions | résultat | P1 / moyenne |
| `actions` | mesures concrètes | next_action, action_immediate_* | adaptateurs | résultat | P1 / moyenne |
| `questions_to_ask` | questions de collecte/contradiction | questions_utiles | conserver | résultat | P1 / faible |
| `risk_assessments` | risques typés et évalués | risks, vigilance | déprécier listes libres | risque | P0 / moyenne |
| `KnowledgeSource` | identité et politique d'une source | SourceDefinition, sources dict | composer, ne pas remplacer plateforme | source | P0 / élevée |
| `SourceEvidence` | preuve d'appel/lecture et résultat | provenance, audit rows | nouveau mécanisme obligatoire | preuve | P0 / moyenne |
| `citation` | référence affichable vérifiable | cited_rules_or_sources | structurer progressivement | preuve | P1 / moyenne |
| `source_reliability` | confiance propre à la source | authority_level, A-D | conserver brut | confiance | P0 / moyenne |
| `extraction_confidence` | confiance technique d'extraction | confidence_score metadata | conserver | confiance | P0 / faible |
| `relevance_assessment` | adéquation question/source | router score | ne pas exposer `_router_score` | pertinence | P0 / faible |
| `completeness_assessment` | couverture du dossier | can_conclude, missing | nouveau | complétude | P0 / moyenne |
| `analysis_confidence` | confiance du raisonnement | niveau_de_confiance | garder valeur brute | confiance | P0 / moyenne |
| `quality_assessment` | qualité technique | quality_level | conserver séparé | qualité | P0 / faible |
| `confidentiality_level` | politique de diffusion | confidentiality | étendre à requêtes/sources/rapports | sécurité | P0 / élevée |
| `errors` | échecs techniques structurés | error, warnings | ne pas transformer en limite métier | erreur | P1 / moyenne |
| `refusals` | impossibilités motivées de conclure/agir | refusal_reason(s) | conserver motifs legacy | refus | P0 / moyenne |
| `limitations` | limites visibles de l'analyse | limites, warnings | séparer des erreurs | résultat | P0 / moyenne |
| `memory_corpus` | mémoire documentaire interrogeable | CSE Memory, Protection sociale | conserver noms produits | mémoire | P1 / faible |

## 9. Règles futures de langage Nexus

1. Nexus ne présente jamais une hypothèse comme un fait.
2. Nexus ne présente jamais une source comme consultée sans `SourceEvidence` réussie.
3. Une absence de résultat n'est pas une absence de droit, de preuve ou de risque.
4. La confiance ne remplace jamais la complétude.
5. Une source officielle peut être peu pertinente pour la question.
6. Une source interne peut être déterminante tout en restant confidentielle.
7. CSE Memory est une mémoire documentaire, pas un expert autonome.
8. Un connecteur fournit des connaissances ; il ne décide pas seul de la réponse.
9. Un expert analyse son domaine et n'invente pas le résultat d'un autre expert.
10. Le Strategic Reasoning Engine coordonnera des rapports stabilisés sans produire lui-même droit, paie ou faits.
11. Le futur contradicteur attaque les raisonnements et leurs preuves, jamais une intention inventée de la direction.
12. Toute limite importante est visible dans la réponse finale.
13. Une information utilisateur non corroborée reste étiquetée `DECLARED`.
14. Toute contradiction non résolue reste visible et liée aux assertions concernées.
15. `UNKNOWN`, échec technique et absence de résultat ne sont jamais convertis silencieusement en confiance faible.

## 10. Objets minimaux recommandés pour ARCH-01

### `ExpertRequest`

- Objectif : fournir une demande stable et expurgée à un expert.
- Minimaux : `request_id`, `schema_version`, `question_text`, `requested_expert`, `detected_domains`, `detected_intents`, `request_scope`, `confidentiality_level`, `correlation_id`.
- Facultatifs : contexte, période, population, établissement, déclarations, faits déjà corroborés, hypothèses, pièces, manquants, urgence, niveau de détail, extensions legacy.
- Compatibilité : adaptateurs depuis `answer`, `PayrollQuestion` et `EmployeeCase`; conserver `orchestrate(answer)`.
- Risques : surspécification, fuite de contexte, conversion implicite déclaration→fait.
- Bénéfice : aucun domaine utile oublié et collecte plus claire des pièces manquantes.

### `ExpertReport`

- Objectif : envelopper une analyse d'expert sans réécrire Juriste/Paie.
- Minimaux : identifiants/version, expert, statut, résumé, findings, conclusion, sources, manquants, risques, confiance d'analyse, limites, génération.
- Facultatifs : faits, déclarations, hypothèses, scénarios, contradictions, recommandations, actions, questions, erreurs, refus, extensions legacy.
- Adaptateurs : dict Juriste, dict Paie, `ExpertAnalysis`.
- Risques : perdre des clés riches ou faire croire qu'une liste legacy est structurée.
- Bénéfice : dossier défendable et comparable entre experts.

### `KnowledgeSource`

- Objectif : décrire une source et ses politiques, sans prétendre qu'elle a été consultée.
- Minimaux : identité, organisme, type/catégorie, statut connexion, officialité/internalité, confidentialité, juridiction, domaines, version schéma.
- Facultatifs : URI, dates, licence, fraîcheur, fiabilité, politique documentaire, payload natif.
- Adaptateurs : `SourceDefinition`, sources routeur, modèles ANACT/CNIL/DREETS/CARSAT/INRS, mémoires locales.
- Risque : remplacer Connector Platform au lieu de la compléter.
- Bénéfice : savoir quelle source est disponible, autorisée et adaptée.

### `SourceEvidence`

- Objectif : prouver une tentative et son résultat.
- Minimaux : `evidence_id`, `source_id`, `operation_id`, `retrieval_status`, `requested_at`, `connector_id`, `connector_version`, `request_fingerprint`.
- Facultatifs : fin, HTTP/statut natif, empreinte contenu, citation, cache, erreur expurgée, fraîcheur.
- Adaptateurs : `ProvenanceRecord`, audits Légifrance/JUDILIBRE, diagnostics ANACT.
- Risque : fabriquer une preuve depuis une fixture/catalogue.
- Bénéfice : le délégué sait exactement ce qui a été consulté.

### `MissingInformation`

- Objectif : qualifier ce qui manque et pourquoi.
- Minimaux : identifiant, `kind`, description, caractère bloquant, demandé à, raison.
- Facultatifs : échéance, action liée, expert, priorité, pièce attendue.
- Adaptateurs : toutes les variantes `missing_*`, `absent_*`, `documents_to_request`.
- Bénéfice : liste de collecte directement exploitable.

### `RiskAssessment`

- Objectif : distinguer conséquences juridiques, sociales, financières, opérationnelles et stratégiques.
- Minimaux : identifiant, catégorie, description, gravité, probabilité connue/inconnue, horizon, preuves, responsable d'évaluation.
- Facultatifs : mesures, signaux, scénario lié, réversibilité.
- Adaptateurs : risques Juriste, dossier et refus Paie sans convertir automatiquement un refus en risque.
- Bénéfice : priorisation transparente des actions syndicales.

### `ConfidenceAssessment`

- Objectif : porter une évaluation typée, motivée et traçable.
- Minimaux : `assessment_kind`, niveau, `known`, producteur, justification, valeur brute.
- Facultatifs : score, facteurs, preuves, date, méthode/version.
- Adaptateurs : cinq familles d'échelles existantes ; aucune conversion de qualité/statut.
- Bénéfice : voir pourquoi une conclusion est solide ou fragile.

## 11. Registre des connexions restantes

| Priorité | Source/corpus | État réel | Architecture existante | Travail restant / dépendances | Risque | Lot probable |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Légifrance | `PARTIAL` | connecteur historique + routeur | adapter à Connector Platform, tests transport simulé, preuve d'appel, secrets sûrs | P1 élevé | ARCH-02/03 |
| 2 | JUDILIBRE | `PARTIAL` | connecteur historique + routeur | tests dédiés, adaptateur plateforme, provenance/citation | P1 élevé | ARCH-02/03 |
| 3 | CDTN | `PARTIAL` | deux clients historiques | choisir façade conservant compatibilité, test endpoint simulé, preuve cache | P1 | ARCH-02/03 |
| 4 | ANACT | `PARTIAL` | transports bornés + façade désactivée | revue licence, activation contrôlée, intégration registre/gateway | P1 | ARCH-03 |
| 5 | CNIL | `SCAFFOLD_ONLY` | contrat/catalogue plateforme | transport ciblé après revue accès/licence | P1 | connecteur officiel dédié |
| 6 | DREETS Grand Est | `SCAFFOLD_ONLY` | revue d'accès + contrat | transport métadonnées ciblées, tests et preuve | P1 | connecteur officiel dédié |
| 7 | CARSAT | `SCAFFOLD_ONLY` | LOT 0 plateforme | valider source régionale/nationale, accès, licence, transport | P1 | connecteur officiel dédié |
| 8 | INRS | `SCAFFOLD_ONLY` | LOT 0 plateforme | revue licence et transport officiel borné | P1 | connecteur officiel dédié |
| 9 | CNAM/Assurance Maladie RP | `PLANNED` | mentions/registre seulement | clarifier périmètre distinct de CARSAT/ameli, source officielle, contrat | P1 | connecteur officiel futur |
| 10 | Accords/documents INEOS | `LOCAL_CORPUS_ONLY` | Bible Accords/index | gouvernance, contrôle d'accès, chiffrement, rétention, preuve de lecture | P0 données | ARCH-03/07 |
| 11 | CSE Memory | `LOCAL_CORPUS_ONLY` | pipeline chunks | exposer via gateway, ACL, recherche, provenance ; rester mémoire | P0 données | ARCH-07 |
| 12 | Protection sociale | `LOCAL_CORPUS_ONLY` | pipeline chunks | gateway, ACL, recherche, provenance, validation humaine | P0 données | ARCH-07 |
| 13 | Mutuelle/prévoyance/garanties | `LOCAL_CORPUS_ONLY` | sous-corpus Protection sociale | sources réelles hors Git, droits d'accès, versions/date d'effet | P0 données | ARCH-07 |
| 14 | Corpus CSSCT | `PLANNED` | routage et schémas | gouvernance corpus, ingestion, source evidence, expertise dédiée ultérieure | P1 | ARCH-07 puis expert |
| 15 | Paie | `LOCAL_CORPUS_ONLY` | moteur/référentiel/protocole testé | pilote contrats communs, adaptateurs, golden tests | P1 | ARCH-05 |
| 16 | Veille contextuelle | `PLANNED` | registre/documentation | transports, fréquence, qualification, séparation source/alerte | P2 | après sources officielles |

Ordre obligatoire : stabiliser Connector Platform et les sources officielles ; intégrer les corpus internes sous contrôle ; migrer Paie puis les autres experts ; construire ensuite les compétences supérieures ; introduire le Strategic Reasoning Engine seulement après validation des contrats et du pilote Paie ; ajouter Quality Engine, puis le contradicteur.

## 12. Séquence proposée après validation

`ARCH-01 Contrats communs` → `ARCH-02 Adaptateurs legacy` → `ARCH-03 KnowledgeGateway et preuves de consultation` → `ARCH-04 Évaluations confiance/pertinence/complétude` → `ARCH-05 Expert pilote Paie` → `ARCH-06 Juriste` → `ARCH-07 Mémoires CSE/Protection sociale et corpus internes` → `ARCH-08 Strategic Reasoning Engine` → `ARCH-09 Quality Engine` → `ARCH-10 Contradicteur stratégique`.

ARCH-01 est autorisable avec réserves si : les contrats restent additifs et versionnés, les valeurs legacy sont conservées, `SourceEvidence` empêche les fausses consultations, et aucun moteur n'est migré dans ce lot.

## 13. Vérifications exécutées

| Contrôle | Résultat |
| --- | --- |
| identité Git et working tree | conforme ; seul ARCH-00 était non suivi au départ |
| lecture ARCH-00 | effectuée, constats importants revérifiés dans le code |
| chemins cités | présents au HEAD audité |
| références runtime | vérifiées avec `rg` sur frontières, producteurs, consommateurs et tests |
| statuts connecteurs | cohérents avec transports, drapeaux `architecture_only`, exceptions et tests |
| tests `automation` explicites | **729 tests, OK**, 3,004 s |
| fallback Légifrance | **OK** |
| pratique officielle CDTN | **OK** |
| avertissements PDF | fixtures négatives synthétiques attendues, suite globale OK |
| test réseau réel | non exécuté |

## 14. Recommandation finale

### GO AVEC RÉSERVES pour ARCH-01

Le langage commun est suffisamment défini pour créer des contrats V1 additifs. Les réserves portent sur la séparation stricte des notions stratégiques, la preuve de consultation des sources, la conservation des payloads legacy et la confidentialité. Paie reste l'expert pilote recommandé grâce à `PayrollQuestion`, `ProtocolAssessment`, ses refus déterministes et sa couverture de tests.

Bénéfice concret attendu : le délégué syndical obtient progressivement une analyse qui distingue ce qui est prouvé, déclaré, supposé ou manquant ; sait quelles sources ont réellement été consultées ; voit les contradictions et risques ; et dispose d'actions/questions ordonnées avec un niveau de solidité explicable.
