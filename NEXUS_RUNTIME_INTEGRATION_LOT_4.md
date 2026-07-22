# Runtime Integration LOT 4 — Retraite / Pénibilité

## Architecture avant

Le Runtime local exécutait les experts historiques, le Core V3, les connecteurs officiels et CSE Memory. L'adaptateur Retraite et le socle Retraite existaient, mais aucun chemin utilisateur ne les appelait.

## Architecture après

Le flag `NEXUS_RETIREMENT_RUNTIME_ENABLED`, désactivé par défaut, active un pont indépendant et à échec fermé :

`Question → Router → détection Retraite → rapport prudent Retraite → RetirementAdapter → PipelineExecutor → CommonExpertOrchestrator → rapport enrichi`

Le pont utilise uniquement les modèles et interfaces publics existants. Il ne calcule ni date, ni trimestre, ni pension, ni point C2P. Le socle public demeure `ARCHITECTURE_ONLY` et toute conclusion individuelle reste subordonnée à des données de carrière et à une validation officielle.

## Runtime et appels réels

La détection privilégie les domaines et intentions du routeur, avec une liste fermée de marqueurs explicites. Une demande retenue produit un `RetirementReport` non décisionnel, converti par le `RetirementAdapter` officiel. L'adaptateur est enregistré dans l'`EngineRegistry`, planifié, exécuté par `PipelineExecutor`, puis représenté par une façade technique auprès du `CommonExpertOrchestrator`.

## Diagnostics

La sortie publique est limitée à `retirement_called`, `retirement_runtime_ms`, `retirement_elements_used` et `retirement_fallback`. Les erreurs sont réduites à des codes techniques stables. Aucun message d'exception, chemin, identifiant interne ou contenu documentaire n'est recopié.

## Fallback

Si le domaine, l'adaptateur, le Core ou l'orchestration est indisponible, ou si aucun élément n'est produit, le rapport antérieur est retourné sans copie ni modification. Le diagnostic indique uniquement le code technique du fallback.

## Limitations

Ce LOT est un raccordement Runtime, pas un moteur de calcul. Il n'ajoute aucune règle, source, API, donnée de carrière, preuve ou référentiel. Le résultat indique seulement que le domaine doit être examiné et qu'une vérification officielle reste nécessaire.

## Tests

Les tests couvrent le flag, la détection, l'appel de l'adaptateur Retraite, le passage réel par `PipelineExecutor` et `CommonExpertOrchestrator`, les fallbacks, l'intégration serveur et la confidentialité.
