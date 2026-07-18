# LOT ARCH-00 — Audit préparatoire du socle d’intelligence syndicale

- Date : 18 juillet 2026
- Dépôt audité : `C:\tmp\cfdt-nexus`
- Remote : `https://github.com/thierrykrempff-maker/cfdt-nexus.git`
- Branche : `audit-connectors-platform-conformity`
- Révision : `993c6e6260274737be840d11661e489e7443aecf`
- Recommandation : **GO AVEC RÉSERVES**

## 1. Résumé exécutif

CFDT Nexus possède déjà un pipeline exécutable : interface HTTP locale, Assistant DS Router V1.2, sources internes et officielles, orchestrateur Juriste/Paie, générateur de rapport, pipeline de dossiers salariés, CSE Memory Engine, Protection Sociale Engine et Connector Platform.

Le futur Strategic Reasoning Engine ne doit pas être ajouté maintenant. Les contrats sont nombreux mais divergents : dictionnaires libres du routeur et des experts, dataclasses du pipeline salarié, contrats Paie typés, modèles Connector Platform, métadonnées CSE/Protection sociale et schémas JSON. La priorité est de les stabiliser et de poser des adaptateurs rétrocompatibles.

Constats majeurs :

- le point d’entrée principal `POST /api/analyze` exécute réellement routeur → experts → orchestration → rapport ;
- `automation/experts/orchestrator.py` reste de taille contenue, mais mélange déjà agrégation, synthèse métier, position, confiance, documents et questions ;
- Juriste est riche mais monolithique, non typé et très couplé au dictionnaire du routeur ;
- Paie possède le meilleur socle contractuel et de tests pour un pilote ;
- Connector Platform est fail-closed, mais Légifrance, JUDILIBRE, CDTN et la veille historique la contournent encore ;
- CSE Memory et Protection sociale ont des pipelines documentaires parallèles, proches mais non identiques ;
- cinq vocabulaires de confiance/qualité coexistent.

La migration est faisable sans réécriture massive. L’expert pilote recommandé est **Paie**. `KnowledgeGateway` doit être une façade au-dessus de Connector Platform, des adaptateurs historiques et des mémoires documentaires, sans remplacer leurs implémentations.

## 2. État Git

| Élément | Constat |
| --- | --- |
| Chemin absolu | `C:\tmp\cfdt-nexus` |
| Nom du dépôt | `cfdt-nexus` |
| Origin | `https://github.com/thierrykrempff-maker/cfdt-nexus.git` |
| Branche active | `audit-connectors-platform-conformity` |
| HEAD | `993c6e6260274737be840d11661e489e7443aecf` |
| Dernier commit | `Audite la conformité des connecteurs officiels` |
| Working tree initial | propre |
| Écart avec `main` | branche audit en avance de 1 commit, `main` en avance de 0 |
| Écart avec `origin/main` | branche audit en avance de 1 commit, `origin/main` en avance de 0 |
| Suivi | `origin/audit-connectors-platform-conformity` au même commit |

Branches pertinentes : `main`, branches Connector Platform, ANACT/CARSAT/INRS/CNIL/DREETS, CSE Memory, Protection sociale, Paie et dossier salarié. Les branches locales et distantes sont alignées sur leurs travaux spécialisés ; aucun changement de branche, merge, commit ou push n’a été effectué.

Derniers jalons utiles :

| Domaine | Commits/jalons observés |
| --- | --- |
| Connector Platform | `befe70e` socle ; `a61fa6c` DREETS ; `40e01d3` CNIL ; `a98971f` CARSAT ; audit `993c6e6` |
| Paie | `765a4e0` intégration expert ; `7718adf` protocole ; `61004ea` référentiel ; fusion `e6ab1a5` |
| CSE Memory | `795a845` import, puis lots normalisation/métadonnées/chunks |
| Protection sociale | `ebf60e2`, `5d8a91b`, `88badab`, `e1e2733`, `84bc80f` |
| Orchestration/Juriste | intégrés dans le pipeline actuel ; aucune branche récente isolant un contrat expert commun |

## 3. Architecture réelle

```text
Navigateur / CLI
  ├─ POST /api/analyze
  │    └─ server.run_router (sous-processus)
  │         └─ assistant_ds_router.ask
  │              ├─ Bible Accords / Nexus Bible Bridge
  │              ├─ Légifrance / JUDILIBRE / CDTN historiques
  │              └─ sélection + normalisation des sources
  │    └─ experts.orchestrator.orchestrate
  │         ├─ juriste_travail.enrich
  │         └─ paie.enrich
  │              ├─ payroll_rule_engine
  │              └─ payroll_referential_integration
  │    └─ report_generator.build_report
  └─ GET /api/employee-case/demo
       └─ EmployeeCasePipeline → ExpertAnalysis synthétiques → rapport dossier

Socles documentaires parallèles
  ├─ CSE Memory : audit → import → normalisation → métadonnées → chunks
  └─ Protection sociale : audit → import → normalisation → métadonnées → chunks

Sources officielles
  ├─ Connector Platform + Official Knowledge
  └─ connecteurs historiques encore appelés directement
```

### Composants et appels réels

| Composant | Fichier / symbole | Entrée | Sortie | Dépendances/appels |
| --- | --- | --- | --- | --- |
| HTTP local | `apps/nexus-local-interface/server.py::NexusHandler` | JSON `{query, source_limit}` | JSON complet ou erreur générique | `run_router`, orchestrateur, générateur |
| Adaptateur HTTP-routeur | `run_router` | question | dictionnaire routeur décodé | sous-processus CLI, timeout 180 s |
| Routeur | `automation/scripts/assistant_ds_router.py::route_query`, `ask` | chaîne, limites | dictionnaire answer | détection domaines/intents, moteurs, recherches, finalisation |
| Normalisation sources | `normalize_source`, `select_final_sources`, `build_source_layers` | résultats hétérogènes | listes de dictionnaires sources | scores contextuels, déduplication, couches |
| Sources internes | `agreements_bible.py`, `nexus_bible_bridge.py` | requête | résultats accords/CSE | index et schémas `database/agreements` |
| Connecteurs historiques | `legifrance_connector.py`, `judilibre_connector.py`, `cdtn_connector.py` | requête/config environnement | sources officielles ou indisponibilité | OAuth/API/cache local selon connecteur |
| Connector Platform | `automation/connector_platform/*` | contrats et contextes | contrats/résultats typés | politiques sécurité, licence, cache, registre, métriques |
| Official Knowledge | `automation/official_knowledge/*` | définitions/catégories | sources, provenance, politiques | registre, catalogue, citation, rétention |
| Orchestrateur | `automation/experts/orchestrator.py::orchestrate` | answer routeur | experts + orchestration | `juriste_travail.enrich`, `paie.enrich` |
| Expert Juriste | `juriste_travail.py::enrich` | dictionnaire answer | dictionnaire expert très riche | sélection sources, modes métier, raisonnement, contentieux |
| Expert Paie | `paie.py::enrich` | dictionnaire answer | dictionnaire expert | moteur de règles et référentiel Paie |
| Protocole Paie | `payroll_reasoning_protocol.py::assess` | `PayrollQuestion` | `ProtocolAssessment` | politique de refus et confiance déterministe |
| Rapport principal | `report_generator.py::build_report` | payload routeur/experts | sections JSON + Markdown | fonctions de projection par expert |
| Dossier salarié | `EmployeeCasePipeline` | `EmployeeCase` | résultat de pipeline/diagnostic | contrôles documentaires et contextes experts |
| Contrat dossier | `employee_case.py` | dataclasses/enums | dictionnaires sérialisables | `EmployeeDocument`, `ExpertAnalysis`, statuts |
| Rapport dossier | `EmployeeCaseReportGenerator.generate` | pipeline + analyses experts | deux vues et sections | agrégation sans calcul/invocation |
| CSE Memory | `automation/cse_memory/*` | documents locaux autorisés | texte, métadonnées, chunks | contrôles de qualité et traçabilité SHA-256 |
| Protection sociale | `automation/protection_sociale/*` | corpus local autorisé | texte, métadonnées, chunks | pipeline parallèle au CSE |
| Interface dossier | `employee_case_demo.py` et API GET | scénario synthétique | payload sérialisable | pipeline et rapport, sans données réelles |

Points d’entrée : HTTP local, CLI `assistant_ds_router.py` (`ask`, `route`, `diagnose`, `run-scenarios`), scripts de connecteurs et scripts de validation. Aucun framework web externe n’est requis.

## 4. Pipeline réel

### Question générale

1. `NexusHandler.do_POST` valide le chemin et décode le JSON.
2. `analyze_question` refuse une question vide.
3. `run_router` transmet la question en argument CLI au routeur.
4. `route_query` produit domaines, intentions, moteur principal, moteurs sélectionnés, décisions et confiance.
5. `ask` appelle Bible Accords/bridge et, si disponibles, Légifrance, JUDILIBRE et CDTN.
6. Chaque résultat est normalisé puis filtré par pertinence et couche de source.
7. `finalize_answer` produit sources, constats, documents, questions, position, prochaine action, confiance et alertes.
8. `orchestrate` appelle toujours les deux enrichisseurs ; chacun décide s’il est actif.
9. L’orchestrateur calcule la synthèse, la position, les analyses par expertise, les pièces, questions, limites et la confiance la plus basse.
10. `build_report` transforme le payload en rapport structuré.
11. Le serveur renvoie l’ensemble avec `Cache-Control: no-store`.

### Dossier salarié

Le chemin de démonstration ne passe pas par le routeur : fixture synthétique → `EmployeeCasePipeline` → contextes par thème → diagnostics/contradictions/statuts → analyses synthétiques → générateur de rapport → vue salarié et vue expert.

### CSE Memory et Protection sociale

Les deux moteurs s’arrêtent aujourd’hui aux chunks techniques : inventaire sécurisé, import, extraction/normalisation, métadonnées avec preuve, qualité et chunking. Ils ne sont pas activés comme experts par l’orchestrateur principal.

## 5. Inventaire des contrats

| Contrat actuel | Forme | Champs saillants |
| --- | --- | --- |
| Routeur `answer` | `dict[str, Any]` | `query`, `understanding`, `route`, `execution_plan`, `sources`, `source_layers`, `findings`, `documents_to_request`, `questions_to_ask`, `working_position`, `next_action`, `confidence`, `warnings`, audits connecteurs |
| Juriste | dictionnaire | activation, modes, faits, règles, application, conclusion, argumentation, sources, pièces, risques, actions, confiance, limites |
| Paie | dictionnaire | objet, rubriques, règles/sources, données de calcul, méthode, anomalies, documents, analyses règle/référentiel, confiance, limites |
| `PayrollQuestion` | dataclass | question/type/sujet/périmètre/population/période/documents/sources/règles/variables/compteurs/rubriques/paramètres/manquants/contradiction |
| `ProtocolAssessment` | dataclass | étapes, compréhension, documents, retrieval, contrôles, manquants, confiance, refus, conclusion possible |
| `EmployeeCase` | dataclass | question, faits, période, population, thèmes, urgence, documents, manquants, hypothèses, confidentialité, historique |
| `ExpertAnalysis` | dataclass | expert, statut, résumé, constats, sources, documents, contrôles, risques, confiance, refus, limites, faits affirmés |
| `ConnectorContract` | dataclass | metadata, state, capabilities, document policy, licence, security, enabled |
| `OperationResult` | dataclass | succès, code, message, nombre de documents |
| `SourceDefinition` | dataclass | source/publisher/type/domaines/autorité/politiques/licence/activation/statut/version |
| CSE/PS metadata | dataclasses | valeur, score/niveau de confiance, preuves, conflits, qualité, versions |
| Chunks CSE/PS | dataclasses | identités, offsets/locators, qualité, flags, warnings, liens et empreintes |
| Schémas JSON | JSON Schema | accords, sources, paie, compteurs, rubriques, paramètres, veille |

Aucun modèle Pydantic n’est utilisé. Les tuples sont fréquents dans les contrats Paie et `ExpertAnalysis`. Les payloads HTTP sont des JSON non validés par schéma runtime.

### Champs métier couverts

- question/contexte/domaine : présents partout, noms divergents ;
- faits/hypothèses/manquants : explicites dans dossiers et Juriste, partiels dans le routeur ;
- sources/références juridiques : riches mais hétérogènes ;
- confiance : cinq familles d’échelles ;
- alertes/risques/recommandations/actions : présents, sans type commun ;
- erreurs/refus/diagnostics : structurés dans Paie et dossiers, partiels dans le routeur, absents comme contrat commun ;
- confidentialité : dataclass dossier, politiques documentaires et chemins locaux, mais pas dans la requête routeur générale.

## 6. Divergences entre moteurs

| Moteur | Divergence principale |
| --- | --- |
| Juriste | dictionnaire français très large ; confiance héritée du routeur ; contradictions déjà traitées dans le même module |
| Paie | dictionnaire legacy + sous-contrats typés anglais ; confiance parfois `faible/moyen`, parfois uppercase |
| CSE Memory | métadonnées/chunks seulement ; `confidence_level` lowercase et preuves techniques |
| Protection sociale | modèle voisin du CSE mais noms différents (`source`, `confidence_score`, `is_indexable`) |
| Connector Platform | statut/capacités/licence/sécurité, pas de `KnowledgeSource` de consommation expert |
| Official Knowledge | `SourceDefinition` décrit une source, pas un résultat récupéré |
| Dossier salarié | `ExpertAnalysis` est le meilleur embryon de rapport commun, mais `confidence` reste une chaîne |
| Orchestrateur | suppose les clés spécifiques Juriste/Paie et ne consomme aucun protocole commun |

## 7. Audit de la confiance et de la qualité

| Échelle | Producteur/consommateur | Sens |
| --- | --- | --- |
| `faible`, `moyen`, `fort`, `a verifier` | routeur, experts, orchestrateur | confiance globale legacy |
| `UNKNOWN`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH` | protocole Paie, pipeline/rapport salarié | confiance métier typée, sans `VERY_LOW` |
| `very_low`, `low`, `medium`, `high`, `very_high` | métadonnées CSE et Protection sociale | confiance dans une métadonnée, seuils 0/.25/.50/.75/.90 |
| score `0..1` | métadonnées | intensité de preuve |
| `unusable`, `poor`, `acceptable`, `good`, `excellent` | textes, métadonnées et chunks | qualité technique, pas confiance métier |
| `A/B/C/D` | registre des sources | niveau de confiance institutionnelle/contextuelle |
| `faible/moyenne/forte` | registre veille | valeur de détection/analyse |
| statuts connecteurs | Connector Platform/Official Knowledge | état opérationnel, pas confiance |

Correspondance proposée :

| Héritage | Cible | Conservation obligatoire |
| --- | --- | --- |
| `faible`, `low`, `LOW` | `LOW` | valeur brute et justification |
| `moyen`, `medium`, `MEDIUM` | `MEDIUM` | valeur brute |
| `fort`, `high`, `HIGH` | `HIGH` | valeur brute |
| `very_high`, `VERY_HIGH` | `VERY_HIGH` | score et preuves |
| `very_low` | `VERY_LOW` | score et preuves |
| `a verifier`, `UNKNOWN` | ne pas convertir silencieusement | `known=false`, valeur brute ; `VERY_LOW` seulement si le contrat impose une valeur et avec drapeau explicite |

Les niveaux de qualité, la classe A-D d’une source et les statuts ne doivent jamais être convertis en `ConfidenceLevel`.

## 8. Audit des sources

### Internes

Bible Accords, index des accords, référentiels Paie synthétiques, corpus CSE/Protection sociale hors Git, méthodologies et base privée exemple. Les politiques interdisent les documents réels/confidentiels dans Git.

### Officielles

Légifrance et JUDILIBRE sont opérationnels historiquement via PISTE ; CDTN fournit la pratique officielle. ANACT est le connecteur plateforme le plus complet. CNIL, DREETS, CARSAT et INRS sont principalement des contrats/catalogues fail-closed sans transport de production.

### Réglementaires/techniques

CNIL, CARSAT, INRS, ANACT, Assurance Maladie/ameli sont enregistrés ou préparés. Aucun connecteur CNAM distinct n’a été identifié.

### Contextuelles

Veille multi-source, France Chimie, CFDT/FCE, publications spécialisées et réseaux sociaux. Le registre porte autorité, preuve, valeur d’analyse et règle de vérification.

### `KnowledgeGateway`

Faisable comme façade additive :

```text
Experts/SRE → KnowledgeGateway → Connector Platform
                            ├── adaptateurs connecteurs historiques
                            ├── Bible Accords
                            ├── CSE Memory
                            └── Protection sociale
```

Il doit normaliser recherche, résultat, provenance, citation, fraîcheur, confidentialité et erreurs, tout en conservant le payload natif. Il ne doit ni réimplémenter les transports ni supprimer Connector Platform.

## 9. Audit de l’orchestrateur

Le risque de God Object est **P1 en croissance**, pas encore P0. `orchestrate` coordonne seulement deux experts, mais le module contient déjà des synthèses métier codées par domaine.

| Responsabilité | État actuel | Cible |
| --- | --- | --- |
| Routage | routeur séparé, bon découpage | rester hors orchestrateur |
| Planification | implicite, deux appels fixes | futur SRE après contrats |
| Activation experts | `applies` dans chaque expert | registre/dispatcher commun |
| Agrégation | orchestrateur | peut rester temporairement |
| Contradictions | Juriste + dossier salarié | service séparé plus tard |
| Confiance | minimum d’une liste legacy | évaluateur commun |
| Qualité | tests/pipelines documentaires | futur Quality Engine |
| Réponse finale | orchestrateur + report generator | conserver le générateur séparé |
| Stratégie contradictoire | déjà mêlée au Juriste | extraire seulement au dernier lot |

Pendant la transition, l’orchestrateur peut garder dispatch, collecte et agrégation. Les phrases métier, le calcul de confiance et les règles de contradiction doivent sortir progressivement.

## 10. Futurs contrats communs

### `ExpertRequest`

Réutiliser `PayrollQuestion` et la vue expurgée d’`EmployeeCase` : `request_id`, version, question, domaine, contexte, période, population, faits, hypothèses, manquants, références de documents, sources disponibles, confidentialité, expert demandé et identifiant de corrélation.

Adaptateurs : answer routeur → request ; dossier → request expurgée ; CSE/PS query → request. Risque principal : injecter une question sensible dans les arguments processus ou un expert hors périmètre.

### `ExpertReport`

Étendre `ExpertAnalysis` : identifiants/version/statut, résumé, faits, hypothèses, constats, sources et références juridiques structurées, manquants, alertes, risques, recommandations, actions, confiance structurée, diagnostics, erreurs, refus, limites et horodatage.

Les dictionnaires Juriste/Paie doivent d’abord être enveloppés, pas réécrits.

### `KnowledgeSource`

Composer `SourceDefinition`, provenance Official Knowledge et sources normalisées du routeur : identifiant, type interne/officiel/réglementaire/contextuel, autorité, titre, URI canonique, connecteur, version/dates, citation, empreinte, licence, confidentialité, fraîcheur, statut de vérification, pertinence et référence au payload natif.

### `ConfidenceLevel`

Enum cible exact : `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`, accompagné de `score`, `rationale`, `factors`, `raw_value`, `producer` et `known`.

## 11. Rétrocompatibilité

1. Versionner les contrats sans modifier les dictionnaires existants.
2. Ajouter des adaptateurs aux frontières routeur/expert/orchestrateur.
3. Capturer des golden fixtures synthétiques sur les scénarios actuels.
4. Préserver toutes les clés legacy dans `extensions.legacy`.
5. Garder `orchestrate(answer)` et `build_report(payload)` comme façades publiques.
6. Activer chaque nouveau chemin par feature flag.
7. Comparer ancien/nouveau rapport avant bascule.
8. Ne migrer qu’un expert à la fois.

## 12. Expert pilote

| Critère | Juriste | Paie |
| --- | --- | --- |
| Taille/couplage | plus de 2 300 lignes, dictionnaire routeur, sources et stratégie | module plus petit, sous-systèmes séparés |
| Contrat typé | absent | `PayrollQuestion`, `ProtocolAssessment`, enums/refus |
| Tests dédiés | aucun fichier Juriste isolé | 5 suites payroll + 2 suites intégration expert |
| Sortie | très large, redondante, modes multiples | périmètre de contrôle/refus explicite |
| Risque | élevé | moyen |
| Valeur pilote | forte mais trop complexe | excellente pour request/report/confiance/refus |

**Choix : Paie.** Le pilote doit adapter le protocole existant et conserver `paie.enrich`; aucun calcul réel ne doit être ajouté.

## 13. Lots suivants

### ARCH-01 — Contrats V1

- Objectif : schémas `ExpertRequest`, `ExpertReport`, `KnowledgeSource`, `ConfidenceLevel`.
- Fichiers probables : `automation/contracts/`, schémas JSON, tests.
- Tests : validation, sérialisation, valeurs inconnues, confidentialité.
- Acceptation : aucune modification comportementale.
- Risque/rollback : surspécification ; package supprimable.

### ARCH-02 — Adaptateurs legacy

- Objectif : envelopper answer, Juriste, Paie et `ExpertAnalysis`.
- Tests : golden fixtures des scénarios routeur et dossier.
- Acceptation : rapports actuels inchangés.
- Dépendance : ARCH-01 ; rollback par feature flag.

### ARCH-03 — `KnowledgeGateway`

- Objectif : façade au-dessus de Connector Platform et adaptateurs historiques.
- Tests : connecteur désactivé, timeout, source interne, provenance, confidentialité.
- Acceptation : aucune source sans statut/citation ; aucun transport dupliqué.
- Rollback : appels actuels conservés.

### ARCH-04 — Confiance commune

- Objectif : normaliser sans confondre qualité/autorité/statut.
- Tests : toutes les échelles, `UNKNOWN`, score et justification conservés.
- Acceptation : aucune perte de valeur brute.
- Dépendances : ARCH-01/02.

### ARCH-05 — Paie pilote

- Objectif : `ExpertRequest → ExpertReport` via le protocole existant.
- Tests : suites Paie actuelles, refus, pièces manquantes, contradictions, non-calcul.
- Acceptation : sortie legacy stable et rapport commun valide.
- Rollback : `paie.enrich` direct.

### ARCH-06 — Juriste

- Objectif : adapter puis découpler Juriste, sans réécriture globale.
- Tests à créer : modes défense/négociation/CSE, sources absentes, jurisprudence, contradictions.
- Acceptation : aucune conclusion non sourcée, toutes limites conservées.
- Dépendances : gateway et pilote validé.

### ARCH-07 — CSE Memory et Protection sociale

- Objectif : exposer leurs chunks comme `KnowledgeSource`, puis ajouter un expert par sous-lot.
- Tests : provenance, confidentialité, qualité insuffisante, conflits métadonnées.
- Acceptation : pipelines documentaires inchangés.

### ARCH-08 — Strategic Reasoning Engine

- Objectif : planifier experts normalisés et agréger leurs rapports.
- Tests : expert indisponible, partiel, timeout, multi-domaines, contradiction.
- Acceptation : aucune règle métier dans le planner ; fallback legacy.

### ARCH-09 — Quality Engine

- Objectif : évaluer couverture, provenance, cohérence et limites séparément de la confiance.
- Tests : source absente, fait non sourcé, rapport incomplet, conflit.
- Rollback : mode observation.

### ARCH-10 — Contradicteur stratégique

- Objectif : extraire la logique contradictoire du Juriste après stabilisation.
- Tests : désaccord conservé, hypothèse adverse, validation humaine.
- Rollback : désactivation complète.

## 14. Risques

### P0 — avant usage réel sensible

1. Le serveur peut être lié à une adresse non locale via `--host` sans authentification ; interdire ce mode avant données réelles.
2. La question complète est transmise en argument de processus, potentiellement visible dans la liste des processus.
3. CSE/Protection sociale et dossier salarié doivent rester synthétiques/expurgés tant que contrôle d’accès, chiffrement, rétention et audit ne sont pas opérationnels.

### P1

1. Légifrance, JUDILIBRE, ancien CDTN et veille contournent Connector Platform.
2. Jetons OAuth et caches historiques locaux en clair, bien qu’ignorés par Git.
3. Dictionnaires non versionnés entre routeur, experts et orchestrateur.
4. Juriste monolithique et logique contradictoire prématurément intégrée.
5. Confiance agrégée par minimum lexical sans facteurs communs.
6. Tests d’interface complets très lents et dépendants des replis connecteurs.

### P2

1. Duplication CSE/Protection sociale avec noms et seuils légèrement différents.
2. Vocabulaire bilingue et échelles de statuts nombreuses.
3. Deux implémentations CDTN concurrentes.
4. Aucun test Juriste isolé ni test JUDILIBRE transport dédié.

## 15. Tests exécutés

| Suite | Résultat |
| --- | --- |
| `assistant_ds_router.py run-scenarios` | **OK** : 26 routages + 11 scénarios `ask` |
| Dossiers + Connector Platform + CSE Memory + Experts + Paie + Protection sociale | **OK** : 241 tests |
| Official Knowledge et connecteurs plateforme | **OK** : 452 tests |
| Fallback Légifrance | **OK** |
| Pratique officielle | **OK** |
| Cockpit dossier salarié | **OK** : 16 contrôles affichés |
| Interface principale complète | **INCOMPLET — timeout 120 s** après 11 réponses HTTP 200 ; aucun échec fonctionnel observé avant interruption |

Les messages PDF invalides pendant les tests CSE/Protection sociale proviennent de fixtures négatives attendues ; la suite se termine `OK`. Aucun test réseau réel n’a été volontairement lancé. Les suites Juriste isolée et JUDILIBRE transport n’existent pas.

## 16. Recommandation finale

### GO AVEC RÉSERVES

Conditions : traiter les P0 avant données réelles, stabiliser les contrats, conserver les adaptateurs legacy, migrer Paie seul, puis Juriste et les mémoires. Le Strategic Reasoning Engine vient seulement après validation des experts normalisés ; le Quality Engine ensuite ; le contradicteur en dernier.

Séquence exacte :

`ARCH-01 Contrats` → `ARCH-02 Adaptateurs` → `ARCH-03 KnowledgeGateway` → `ARCH-04 Confiance` → `ARCH-05 Paie` → `ARCH-06 Juriste` → `ARCH-07 CSE/Protection sociale` → `ARCH-08 Strategic Reasoning Engine` → `ARCH-09 Quality Engine` → `ARCH-10 Contradicteur`.
