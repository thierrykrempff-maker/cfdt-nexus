# ARCH-03 — Façades communes des experts

## 1. Périmètre

ARCH-03 ajoute une voie d'appel parallèle `ExpertRequest -> ExpertReport`. Il ne remplace ni
`automation.experts.orchestrator.orchestrate`, ni `automation.experts.paie.enrich`, ni
`automation.experts.juriste_travail.enrich`. Aucun routeur, endpoint, connecteur, corpus ou
consommateur historique n'est modifié. Le registre reçoit un `expert_id` explicite ; il ne choisit
jamais l'expert et ne contient aucune règle de routage métier.

## 2. Cartographie réelle des experts et moteurs

| Identifiant ARCH-03 | Réalité exécutable observée | État | Compatibilité ARCH-01 |
|---|---|---|---|
| `paie` | `automation.experts.paie.enrich(answer)` | `AVAILABLE` | complète par les adaptateurs ARCH-02 |
| `juriste_travail` | `automation.experts.juriste_travail.enrich(answer)` | `PARTIAL` | entrée et sortie dictionnaires, aucun adaptateur ARCH-01 validé |
| `cse_memory` | import, normalisation, métadonnées et découpage documentaire | `NOT_READY` | mémoire documentaire, pas d'expert autonome |
| `protection_sociale` | import, normalisation, métadonnées et découpage documentaire | `NOT_READY` | pipeline documentaire, pas d'expert autonome |
| `local_law` | règles, applicabilité, comparaison et garde de raisonnement | `NOT_READY` | composant d'appui, pas de point d'entrée expert |
| `sante_securite` | aucun expert autonome trouvé | `NOT_READY` | le thème CSSCT/sécurité est traité dans Juriste Travail |

L'orchestrateur réellement consommé par l'interface locale appelle uniquement Juriste Travail et
Paie. Aucun autre expert n'est appelé par `automation.experts.orchestrator.orchestrate`.

## 3. Points d'entrée historiques

### Paie

- entrée publique : `enrich(answer: dict[str, Any]) -> dict[str, Any]` ;
- activation : domaines du routeur, mots-clés et classification du moteur de règles ;
- dépendances : `experts.utils`, puis, lorsqu'ils sont importables,
  `payroll_rule_engine` et `payroll_referential_integration` ;
- effets de bord propres au point d'entrée : aucun écrit et aucun appel réseau observé ;
- erreurs : les intégrations optionnelles disposent de replis prudents ; les erreurs de
  programmation non déclarées ne sont pas silencieusement absorbées par ARCH-03 ;
- refus : `active=False` hors périmètre ;
- sources : libellés dérivés de `answer["sources"]`, sans preuve inventée ;
- confiance : chaîne historique, généralement `faible`, `moyen` ou valeur normalisée par
  l'intégration des référentiels ;
- risques et informations manquantes : dictionnaires et listes historiques, convertis par ARCH-02 ;
- consommateurs : `automation.experts.orchestrator`, générateur de rapport, interface locale et
  tests/intégrations Paie.

### Juriste Travail

- entrée publique : `enrich(answer: dict[str, Any]) -> dict[str, Any]` ;
- sortie : rapport juridique historique riche, non contractuel ;
- dépendances : utilitaires locaux et données déjà préparées dans `answer` ;
- effets de bord et réseau propres : aucun observé ;
- refus : `active=False` hors périmètre ;
- sources : sélection à partir des sources déjà fournies par le routeur ;
- confiance : valeur historique de `answer["confidence"]` ;
- risques : `risques_points_vigilance` textuels ;
- consommateurs : orchestrateur actuel, générateur de rapport et interface locale ;
- réserve : l'adapter maintenant obligerait à définir la sémantique des règles, conclusions,
  sources et risques juridiques. ARCH-03 ne fabrique pas cette conversion.

### CSE Memory, Protection sociale et Local Law

CSE Memory et Protection sociale lisent et, selon leur mode, écrivent des artefacts documentaires.
Leurs fonctions `run_*` ne sont pas des analyses expertes d'une question. Local Law expose des
fonctions spécialisées (`assess_applicability`, `compare`, `evaluate_local_law_check`) mais aucun
agrégat `ExpertRequest -> rapport`. Les présenter comme experts autonomes serait trompeur.

## 4. Architecture de la couche de façades

Le paquet `automation.expert_facades` contient :

- `base.py` : contrat abstrait, version d'API et rapports d'erreur ;
- `registry.py` : déclarations, statuts et résolution explicite ;
- `payroll.py` : seule façade opérationnelle de ce lot ;
- `__init__.py` : API publique stable ;
- `test_facades.py` : contrôles synthétiques ARCH-03.

La couche dépend vers le bas des contrats, adaptateurs et du seul expert historique nécessaire.
Elle n'est importée par aucun consommateur historique.

## 5. Interface commune

```python
class ExpertFacade:
    expert_id: str
    capabilities: tuple[str, ...]
    facade_version: str

    def execute(self, request: ExpertRequest) -> ExpertReport:
        ...
```

`execute` vérifie le type, capture un instantané sérialisé pour contrôler l'absence de mutation,
valide l'association du rapport à la requête et ajoute `api_version`, `facade_version`, `expert_id`
et les capacités dans les métadonnées. Les identifiants et rapports d'erreur sont déterministes.

## 6. Registre

`ExpertFacadeRegistry` permet `register`, `declare`, `get`, `resolve`, `registrations`,
`list_capabilities` et `execute`. Les doublons lèvent `DuplicateExpertError`; une recherche inconnue
lève `UnknownExpertError`; une résolution indisponible lève `FacadeUnavailableError`.

`execute(expert_id, request)` n'infère rien : l'appelant donne l'identifiant exact. Pour un identifiant
inconnu, indisponible ou désactivé, il renvoie un `ExpertReport` structuré. Les quatre états sont :

- `AVAILABLE` : façade exécutable ;
- `PARTIAL` : moteur réel, migration contractuelle incomplète ;
- `NOT_READY` : aucun point d'entrée expert compatible ;
- `DISABLED` : entrée volontairement neutralisée.

## 7. Façade Paie

`PayrollFacade` suit exactement cette chaîne :

1. reçoit un `ExpertRequest` ARCH-01 ;
2. appelle `expert_request_to_legacy_payroll` d'ARCH-02 ;
3. ajoute seulement le domaine historique Paie quand aucun résultat de routage n'est présent ;
4. appelle `automation.experts.paie.enrich` ;
5. exige une sortie de type mapping ;
6. appelle `legacy_payroll_report_to_expert_report` d'ARCH-02 ;
7. conserve la trace des formats, version d'adaptateur et catégories de la requête dans les
   métadonnées contractuelles.

Aucune règle de conversion ARCH-02 n'est recopiée. L'exécuteur peut être injecté uniquement pour
tester synthétiquement refus, sources et sorties mal formées. Les capacités annoncées couvrent le
contrôle Paie, les heures supplémentaires, l'astreinte, les congés payés, le maintien de salaire,
les jours fériés et le repos compensateur.

## 8. État des autres experts

Juriste Travail reste `PARTIAL`, sans fausse façade : son entrée réelle est connue mais son mapping
vers `ExpertReport` doit faire l'objet d'un lot de migration métier validé après Paie. CSE Memory,
Protection sociale, Local Law et Santé-sécurité restent `NOT_READY` pour les raisons factuelles du
tableau. Aucun de ces états n'empêche les usages historiques.

## 9. Gestion des erreurs

| Cas | Politique |
|---|---|
| objet qui n'est pas `ExpertRequest` | rapport `FAILED`, code `INVALID_REQUEST` |
| expert inconnu | rapport `FAILED`, code `UNKNOWN_EXPERT` via `registry.execute` |
| expert indisponible | rapport `FAILED`, code `EXPERT_NOT_READY` |
| expert désactivé | rapport `REFUSED`, code `EXPERT_DISABLED` |
| refus métier historique explicite | rapport `REFUSED`, code `LEGACY_BUSINESS_REFUSAL` |
| sortie Paie non mapping ou non adaptable | rapport `FAILED`, code `MALFORMED_LEGACY_OUTPUT` |
| données insuffisantes | informations manquantes et statut prudent fournis par ARCH-02 |
| exception de programmation inattendue | propagée, jamais transformée silencieusement |

La frontière est intentionnelle : `LegacyBusinessRefusal` et `MalformedLegacyOutput` sont des
erreurs de frontière attendues. `RuntimeError`, `AssertionError`, erreur d'import ou autre défaut non
classé reste visible pour correction. Les exceptions `BaseException` ne sont jamais capturées.

## 10. Gestion des sources

La façade ne consulte aucune source et n'importe aucun connecteur. ARCH-02 produit une
`KnowledgeSource` sans `SourceEvidence` quand aucune preuve de consultation n'existe. Une
`SourceEvidence` n'est conservée que si la sortie historique fournit une preuve structurée et un
statut de consultation réussi ou de cache. Une simple référence ou un libellé ne devient jamais une
preuve.

## 11. Gestion de la confiance

Les niveaux historiques sont convertis par ARCH-02 en `ConfidenceAssessment`. Une confiance faible
reste `LOW`; une valeur inconnue reste explicitement non connue. ARCH-03 ne relève jamais un niveau,
ne calcule aucun score et ne déduit aucune confiance de la présence d'une façade.

## 12. Gestion des risques

Les risques structurés présents dans la sortie historique sont convertis par ARCH-02 et conservés.
ARCH-03 n'invente ni probabilité, ni impact, ni criticité. Les textes de prudence historiques restent
des avertissements lorsqu'ils ne satisfont pas le contrat `RiskAssessment`.

## 13. Rétrocompatibilité

Le chemin existant reste : interface locale → routeur → orchestrateur historique → `enrich` Paie et
Juriste. Le chemin ARCH-03 est parallèle et n'a aucun appelant de production. Les formats historiques
sont préservés par les métadonnées ARCH-02 et les métadonnées de façade. Aucun endpoint, test
historique, routeur, orchestrateur ou module expert n'est modifié.

## 14. Dépendances interdites

Le paquet ne dépend directement ni du routeur, ni de l'orchestrateur, ni de l'interface web, ni de
Connector Platform, ni des connecteurs officiels, ni de CSE Memory, ni de Protection sociale, ni des
corpus. Les tests analysent les imports et interdisent aussi `assistant_ds_router` et
`experts.orchestrator`. Aucun appel réseau n'est ajouté.

## 15. Limites connues

- seule Paie est exécutable par la nouvelle API ;
- le domaine Paie est fourni au format historique lorsque le futur appel commun n'a pas de route ;
- la qualité du rapport reste limitée par la sortie de `paie.enrich` et ses sources en entrée ;
- le registre n'offre aucune sélection par question ou capacité ;
- Juriste Travail exige encore une validation métier de son mapping ;
- les pipelines documentaires ne sont pas promus en experts ;
- aucune disponibilité de connecteur n'est simulée.

## 16. Points d'intégration ARCH-04

ARCH-04 pourra construire un orchestrateur minimal au-dessus de `ExpertFacadeRegistry`, choisir
explicitement des experts selon une politique séparée, appeler `registry.execute` et agréger des
`ExpertReport`. Il devra respecter les statuts, conserver les refus et ne jamais interpréter
`NOT_READY` comme un résultat métier. Il ne devra pas modifier les façades pour introduire du routage.

## 17. Critères d'acceptation

- API publique versionnée et importable ;
- Paie utilise ARCH-01, ARCH-02 et le vrai `paie.enrich` ;
- aucune mutation de requête ni collection partagée ;
- registre déterministe avec quatre statuts et rejet des doublons ;
- erreurs de frontière structurées, erreurs de programmation visibles ;
- sources consultées et non consultées distinguées ;
- données synthétiques uniquement dans les tests ;
- aucun appel réseau, connecteur, corpus ou consommateur historique modifié ;
- suites ARCH-01, ARCH-02, ARCH-03 et non-régression réussies ;
- aucun commit, push ou début d'ARCH-04 dans ce lot.
