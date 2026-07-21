# Audit transversal — Expert Retraite & Pénibilité

Date de l'audit : 2026-07-21

Branche auditée : `retirement-penibility-lot-13-nibelis-connector`

Périmètre : LOTS 1 à 13, y compris les huit fichiers non suivis du LOT 13.
Exclusions : `RETIREMENT_PENIBILITY_CONFIDENTIAL_MEMORY_LOT_0.md` et `RETIREMENT_PENIBILITY_CONFIDENTIAL_MEMORY_LOT_0_MATRIX.json`.

## Synthèse exécutive

L'architecture fournit une chaîne métier lisible et largement déterministe : fondation, chronologie, preuves, connaissance documentaire, raisonnement, droits potentiels, import, reconstruction puis cinq connecteurs spécialisés. Les modèles sont immuables, les responsabilités sont généralement réparties par module, les traitements sont hors ligne et aucun cycle d'import n'a été détecté.

L'ensemble n'est toutefois pas prêt pour une mise en production avec des données réelles. Les contrats importent parfois leurs implémentations, les connecteurs contournent la validation du Career Import Engine avant reconstruction, et le rapprochement de reconstruction ne distingue pas suffisamment les types sémantiques des enregistrements génériques. Les contrôles de confidentialité sont surtout déclaratifs et doivent devenir des contrôles d'entrée effectifs avant tout connecteur réel.

Verdict : **architecture exploitable pour poursuivre le prototypage, avec refactorings P1 requis avant l'intégration de données ou de transports réels**.

## Méthode et métriques

L'audit a combiné inventaire des modules, analyse AST des classes, interfaces et imports, recherche statique des capacités réseau et d'accès aux fichiers, comparaison des contrats/connecteurs/policies/validateurs/rapports, et lecture des flux Import → Reconstruction.

| Mesure | Résultat |
|---|---:|
| Fichiers audités | 106 |
| Modules métier | 93 |
| Fichiers de tests | 13 |
| Types de modèles | 277 |
| Dataclasses immuables | 217 |
| Énumérations | 59 |
| Protocol de référentiel placé dans un module de modèles | 1 |
| Modules de contrat | 15 |
| Interfaces `Protocol` publiques | 14 |
| Méthodes portées par ces interfaces | 84 |
| Connecteurs | 5 |
| Convertisseurs | 5 |
| Policies | 12 |
| Validateurs | 8 |
| Modules de rapport | 11 |
| Structures de rapport | 13 |
| Fonctions de test | 183 |
| Cas exécutés par les 13 suites Retraite & Pénibilité | 219 |
| Cycles d'import détectés | 0 |

Le nombre de modèles inclut les dataclasses, énumérations et le protocol de lookup déclarés dans les quatorze modules `*_models.py`. Le nombre de tests distingue les fonctions sources des cas réellement collectés/exécutés par pytest.

## Architecture globale et couches

### Chaîne observée

1. `retirement_*` définit la fondation et les politiques générales.
2. `career_timeline_*` représente la chronologie structurée.
3. `career_evidence_*` qualifie les preuves et leurs relations.
4. `document_*` sélectionne les versions et règles documentaires applicables.
5. `rule_reasoning_*` évalue des règles structurées sans calcul de retraite.
6. `potential_rights_*` qualifie des pistes et la maturité documentaire.
7. `career_import_*` valide et normalise les métadonnées importées.
8. `career_reconstruction_*` rapproche les sources et produit des propositions soumises à validation humaine.
9. Les cinq connecteurs convertissent leurs métadonnées vers `ImportBatch` et préparent une reconstruction.

### Points conformes

- Aucun cycle d'import n'a été détecté dans les 93 modules.
- Les moteurs ne dépendent pas des connecteurs.
- Les connecteurs convergent vers les modèles publics de Career Import et Career Reconstruction.
- Les modèles sont immuables et les sorties sont déterministes.
- Les règles de non-calcul, non-décision et validation humaine sont présentes dans les couches concernées.
- Aucun transport, stockage persistant ou lecture de document n'est présent dans le périmètre.

### Écart de couche

Huit modules de contrat importent des implémentations concrètes ou leurs auxiliaires : Career Evidence, Career Import, Career Reconstruction, Career Statement, Document Knowledge, Employment Contract, Potential Rights et Rule Reasoning. Les ports devraient rester orientés vers les modèles et abstractions, tandis qu'un module de façade ou de composition devrait exposer les implémentations.

Cette inversion ne crée pas encore de cycle, mais elle fragilise le découplage et rend les contrats moins réutilisables.

## Interfaces publiques

Les quatorze interfaces `Protocol` couvrent 84 méthodes. Les cinq connecteurs exposent tous six opérations conceptuellement homogènes : création vide, validation, conversion vers `ImportBatch`, extraction métier, préparation de reconstruction et rapport.

Écarts d'homogénéité :

- l'ordre des méthodes varie entre Career Statement, Nibelis et les autres connecteurs ;
- les cinq implémentations omettent l'annotation de retour de `convert_to_import_batch`, alors que les protocols annoncent `ImportBatch` ;
- `generate_import_report` renvoie en réalité un rapport propre au connecteur et non un `ImportReport` du Career Import Engine ;
- le `__init__.py` public expose essentiellement la fondation LOT 1 et ne définit pas de façade versionnée pour les LOTS ultérieurs ;
- les contrats qui réexportent leurs implémentations rendent ambiguë la frontière entre port et façade.

## Modèles

Les 277 types donnent une couverture documentaire riche, mais leur volume crée une surface de maintenance importante.

Chevauchements principaux :

- `CareerPeriod`, `NightWorkPeriod`, `FiveShiftPeriod` et `ExposurePeriod` existent dans la fondation et dans la Timeline avec des structures distinctes ;
- chaque connecteur redéfinit ses variantes de `Confidence`, `Status`, `ReportView`, `Metadata`, `Issue`, `Warning`, `Validation`, `Import`, `Summary` et `Report` ;
- Career Import, Reconstruction et Timeline représentent parfois le même fait sous trois formes successives sans schéma de correspondance central et versionné ;
- `NibelisReferentialLookup` est une interface mais réside dans `nibelis_models.py`, contrairement aux autres ports placés dans des contrats.

Ces formes distinctes restent justifiables aux frontières, mais leurs invariants communs devraient être explicités par de petits protocoles ou modèles partagés stables, sans créer une super-classe métier générique.

## Comparaison des connecteurs

| Connecteur | Entrée | Extraction | Référentiel | Sortie commune | État |
|---|---|---|---|---|---|
| Career Statement | relevé synthétique | métadonnées de relevé | types internes | `ImportBatch` + proposition | cohérent |
| Payslip | bulletin synthétique | paie structurée | compatibilité déclarative Kelio/Nibelis | `ImportBatch` + proposition | cohérent, référentiels non injectés |
| Employment Contract | contrat synthétique | contrat/classification/horaire | types internes | `ImportBatch` + proposition | cohérent |
| Kelio | export synthétique | temps de travail | compatibilité seulement déclarée | `ImportBatch` + proposition | intégration référentielle insuffisante |
| Nibelis | export synthétique | paie et paramètres | lookup injecté obligatoire | `ImportBatch` + proposition | modèle de référence le plus robuste |

Les cinq architectures sont proches et testables hors ligne. Nibelis améliore le modèle avec un lookup injecté et un refus fermé lorsque les identifiants de référentiel ne peuvent pas être validés. Kelio déclare une compatibilité référentielle, mais ne possède pas d'interface comparable : ses horaires et compteurs restent des chaînes propres au connecteur. Payslip déclare aussi une compatibilité sans projection explicite vers ces référentiels.

La duplication entre les cinq ensembles `connector/contract/converter/models/policy/report/validator` est forte. La factorisation recommandée porte uniquement sur les invariants techniques (validation de provenance, contrôles de sécurité, construction de rapports et orchestration), pas sur les modèles métier propres à chaque source.

## Cohérence Import, Reconstruction, Timeline et Evidence

Le flux de types est cohérent en intention :

`Connector metadata → ImportBatch → Career Import → Reconstruction → Timeline/Evidence proposals`

Deux écarts doivent être traités avant production :

1. Les méthodes `prepare_reconstruction()` des connecteurs construisent un `ImportBatch` puis l'ajoutent directement au `CareerReconstructionEngine`. Elles n'appellent pas `CareerImportEngine.validate_batch()`, `normalize_batch()` ni `detect_conflicts()`. Un lot invalide au sens de Career Import peut donc atteindre la reconstruction.
2. `CareerReconstructionEngine.build_candidates()` groupe les éléments par classe Python. Tous les `ImportedCareerRecord` sont alors comparés ensemble, tandis que `CareerReconstructionMatcher` n'utilise pas `career_event_type` parmi ses critères comparables. Deux événements métier différents issus du même document peuvent être considérés comme `SAME_SOURCE_REFERENCE` et devenir fusionnables.

Autre limite : `CareerImportEngine.prepare_timeline_records()` ignore silencieusement les `career_event_type` absents de `CareerEventType`. Plusieurs types spécifiques produits par les connecteurs (rubriques Nibelis, paramètres, contributions, amendements, absences ou compteurs) n'ont donc pas de projection Timeline. La Reconstruction les conserve, mais la divergence entre les deux chemins n'est pas documentée par une matrice de compatibilité.

## Policies

Les douze policies sont cohérentes sur les invariants essentiels : immutabilité, provenance, absence d'invention, absence de correction automatique, conservation des contradictions, non-décision, non-calcul et revue humaine.

Aucune contradiction directe n'a été trouvée. Les mêmes règles sont toutefois répétées sous des identifiants différents (`provenance`, `provenance_required`, `provenance_is_mandatory`, `immutable`, `immutable_originals`, etc.). Une taxonomie commune des invariants, consommée par les policies spécialisées, réduirait le risque de divergence future.

## Validateurs

Les huit validateurs vérifient des structures injectées : identifiants, dates, périodes, doublons, cohérence locale, provenance et caractère synthétique. Les cinq validateurs de connecteur répètent des contrôles très proches.

Limites :

- l'indicateur `synthetic_only` est déclaré par l'appelant et n'est pas corroboré par un filtrage profond des champs ;
- les règles de rejet de NIR, IBAN, noms réels, chemins locaux ou autres identifiants sensibles ne sont pas centralisées dans un validateur d'entrée réutilisable ;
- la validation d'un connecteur et celle du Career Import Engine ne sont pas chaînées avant reconstruction ;
- aucune validation de version de schéma n'est présente sur les échanges inter-couches.

## Rapports Employee View / Expert View

Les rapports de Reasoning, Potential Rights, Reconstruction et des connecteurs séparent correctement les informations destinées au salarié et à l'expert. Les vues salarié privilégient périodes, éléments reconnus, manques et prochaines étapes ; les vues expert ajoutent provenance, conflits, classifications, paramètres et préparation d'import.

Écarts :

- les structures de rapport ont des champs et vocabulaires différents alors que plusieurs concepts sont communs ;
- `TimelineReport` et `RetirementReport` n'utilisent pas le même mécanisme explicite Employee/Expert View ;
- le nom `generate_import_report` masque le fait que le rapport est propre au connecteur ;
- aucune politique transversale exécutable ne garantit que les champs réservés à l'expert restent absents de la vue salarié.

## Confidentialité et sécurité

Constats conformes :

- aucun import de client HTTP, `urllib`, `ssl`, `socket`, scraper ou parseur de document ;
- aucun appel réseau, téléchargement, OCR, lecture PDF/HTML ou accès à un fichier réel ;
- aucune persistance, cache documentaire ou variable globale contenant des données métier ;
- aucun secret, jeton, NIR, IBAN, identité réelle ou document réel détecté dans le périmètre audité ;
- les données de test sont synthétiques et les modèles sont immuables ;
- les deux fichiers confidentiels LOT 0 ont été exclus et laissés intacts.

Risque restant : la confidentialité est essentiellement garantie par contrat, données synthétiques de test et booléen `synthetic_only`. Avant données réelles, il faut une frontière d'ingestion dédiée avec minimisation, classification, validation, journalisation sans contenu, politique de rétention et tests adversariaux.

## Référentiels

- Career fournit les types communs d'import et reconstruction ; il n'existe pas de taxonomie centrale des `career_event_type` réellement acceptés de bout en bout.
- Nibelis réutilise les identifiants d'un référentiel injecté, refuse les identifiants inconnus et n'embarque pas de taxonomie dupliquée : approche conforme.
- Kelio expose seulement un indicateur de compatibilité ; aucun port de lookup, identifiant référentiel obligatoire ou validation injectée équivalente n'est présent.
- Payslip annonce des compatibilités Kelio/Nibelis, mais sans adaptateur formel ni matrice de projection.

La prochaine étape devrait définir des ports de référentiel génériques orientés identifiants, puis des adaptateurs Kelio/Nibelis spécialisés, sans déplacer leurs règles métier dans le moteur Retraite.

## Tests et couverture

Les treize suites contiennent 183 fonctions et représentent 219 cas exécutés. Le dernier contrôle fonctionnel établi sur l'état audité a validé les 219/219 cas Retraite & Pénibilité. La suite complète associée a produit 1 676 réussites et 128 sous-tests réussis, avec uniquement les trois anomalies historiques déjà qualifiées dans le dépôt.

Points forts : contrats, immutabilité, déterminisme, vues de rapport, refus des données non synthétiques, absence de réseau, conversions et propositions de reconstruction sont largement couverts.

Zones insuffisamment testées :

- aucun test de bout en bout ne chaîne connecteur → validation Career Import → normalisation → conflits → reconstruction → timeline/evidence → reasoning → potential rights ;
- absence de test démontrant qu'un lot invalide est bloqué avant reconstruction ;
- absence de test empêchant le rapprochement de deux `ImportedCareerRecord` de types métier différents ;
- couverture faible des entrées sensibles mal étiquetées `synthetic_only=True` ;
- absence de tests de compatibilité/versionnement des contrats inter-couches ;
- absence de property-based testing, volumétrie et mesures de performance ;
- absence d'un seuil de couverture instrumenté.

## Anomalies par priorité

### P0 — 0

Aucune architecture incorrecte bloquante, dépendance circulaire, violation active de confidentialité ou fuite de données n'a été constatée dans l'état audité.

### P1 — 6

1. **Inversion contrat/implémentation** : huit contrats importent des moteurs, connecteurs ou auxiliaires concrets.
2. **Contournement du Career Import Engine** : les connecteurs alimentent la reconstruction sans validation, normalisation ni détection de conflits au niveau Import.
3. **Rapprochement sémantiquement trop large** : les `ImportedCareerRecord` de types d'événement différents peuvent être comparés et proposés à la fusion.
4. **Duplication des connecteurs** : orchestration, sécurité, policies, validation et rapports sont recopiés dans cinq piles proches.
5. **Contrôle de confidentialité trop déclaratif** : `synthetic_only` ne suffit pas à détecter une donnée réelle injectée par erreur.
6. **Référentiel Kelio incomplet** : compatibilité déclarée sans lookup injecté ni validation d'identifiants, contrairement à Nibelis.

### P2 — 7

1. Collisions et chevauchements de modèles entre Foundation, Timeline, Import, Reconstruction et connecteurs.
2. Ordre des méthodes et annotations de retour non totalement homogènes dans les cinq connecteurs.
3. Taxonomie de policy dupliquée avec des identifiants différents pour les mêmes invariants.
4. Structures Employee/Expert View cohérentes sur le fond mais non normalisées transversalement.
5. Façade publique `__init__.py` limitée à la fondation et non versionnée pour les LOTS ultérieurs.
6. Couverture insuffisante des scénarios inter-couches, adversariaux, volumétriques et de versionnement.
7. Ambiguïté du nom `generate_import_report`, qui produit un rapport de connecteur plutôt qu'un rapport Career Import.

## Évaluation

| Critère | Note / 10 | Justification |
|---|---:|---|
| Architecture | 7,3 | Chaîne lisible et modulaire ; inversions dans les contrats et flux Import contourné. |
| Découplage | 6,8 | Pas de cycle et moteurs indépendants des connecteurs ; ports parfois couplés aux implémentations. |
| Extensibilité | 7,5 | Ajout d'un connecteur prévisible ; duplication et taxonomies non versionnées augmentent le coût. |
| Qualité des modèles | 7,0 | Immutabilité et expressivité fortes ; 277 types et plusieurs chevauchements. |
| Qualité des contrats | 6,8 | Protocols riches et explicites ; frontières port/façade imparfaites. |
| Qualité des connecteurs | 7,2 | Hors ligne, déterministes et homogènes ; validation Import et référentiel Kelio incomplets. |
| Qualité des tests | 7,6 | 219 cas métier ciblés et suite complète stable ; manque de tests inter-couches et adversariaux. |
| Confidentialité | 8,1 | Aucune donnée réelle ni I/O ; contrôles d'entrée encore déclaratifs. |
| Maintenabilité | 6,7 | Nommage clair par domaine ; duplication et volume de modèles élevés. |
| Préparation production | 5,9 | Bon prototype sécurisé hors ligne ; ingestion réelle, versionnement, observabilité et tests de charge absents. |

Moyenne indicative : **7,1 / 10**.

## Conclusion générale

Les LOTS 1 à 13 forment un socle cohérent, traçable et prudent, adapté à la poursuite du développement hors ligne. Aucun P0 n'empêche la conservation de l'architecture actuelle. Avant l'ouverture aux documents et connecteurs réels, les six P1 doivent toutefois être traités en priorité : restaurer l'indépendance des contrats, imposer le passage par Career Import, rendre le matching sensible au type métier, factoriser les invariants techniques des connecteurs, installer une vraie frontière de confidentialité et aligner Kelio sur l'approche référentielle injectée de Nibelis.

L'audit n'a modifié aucun fichier métier. Aucun commit, aucun push et aucune fusion n'ont été réalisés.
