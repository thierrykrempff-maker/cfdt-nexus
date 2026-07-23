# CFDT Nexus — Correctif P0-1 Confidentialité Runtime

## Périmètre

- Branche : `nexus-v1-stabilization-p0-confidentiality`
- Parent : `8287b848552acefaabf43ffbb92ea9602f36cae4`
- Objet unique : empêcher la publication des identifiants et références techniques du Runtime.
- Moteurs, règles, connecteurs, routage et corpus : inchangés.

## Cause exacte

Le Runtime construisait un payload interne complet, puis le serveur HTTP publiait ce
même objet sans frontière de confidentialité dédiée. Les sources normalisées par le
routeur contenaient notamment leur identifiant de chunk. Le générateur de rapport
réutilisait également des noms de modules dans le flux d'exécution. Enfin, le
frontend affichait explicitement l'identifiant de chunk parmi les métadonnées de
source.

Propagation observée :

1. le routeur crée les sources et leurs références techniques ;
2. les adaptateurs, le Core, `PipelineExecutor` et `CommonExpertOrchestrator`
   utilisent ces références en interne ;
3. le serveur assemblait le payload interne ;
4. la route publique `/api/analyze` renvoyait ce payload directement ;
5. l'interface rendait certaines références techniques.

Le chiffre historique de 71 chemins Windows a aussi révélé un défaut du détecteur
de campagne : son expression régulière interprétait la séquence `s:/` d'une URL
HTTPS comme un lecteur Windows. Cette catégorie était donc un faux positif de
mesure. La fuite des identifiants de chunks, elle, était réelle et suffisait à
classer les 100 scénarios en P0.

## Correction appliquée

Une frontière publique unique, `sanitize_public_payload`, produit une copie
assainie du résultat final. Le payload interne n'est pas modifié et reste disponible
pour les diagnostics internes.

La frontière publique :

- retire les identifiants de chunk, stockage, exécution, preuve et classement ;
- retire les chemins locaux et empreintes techniques ;
- retire les diagnostics Runtime du payload public ;
- remplace les chemins de modules du flux par des libellés métier ;
- conserve les titres, extraits métier, références officielles et URL publiques ;
- traite récursivement la réponse, le rapport et les objets destinés à l'export.

La route HTTP utilise exclusivement cette frontière. Le frontend ne rend plus les
identifiants de chunks. Le runner de campagne appelle le même point d'entrée public
et son détecteur distingue désormais une URL HTTPS d'un chemin local.

## Contrôles automatiques

Les tests synthétiques couvrent :

- chemins locaux de différents systèmes ;
- identifiants de chunk et de stockage ;
- UUID, empreintes longues et identifiants Runtime ;
- références de modules et noms internes de corpus ;
- conservation des libellés métier et URL officielles ;
- absence de mutation du payload interne ;
- application de la frontière par le serveur ;
- absence de rendu d'un identifiant de chunk dans le frontend.

## Campagne des 100 scénarios

| Mesure | Avant | Après |
|---|---:|---:|
| Scénarios exécutés | 100 | 100 |
| Succès techniques | 100 | 100 |
| Échecs techniques | 0 | 0 |
| Scénarios avec fuite publique | 100 | 0 |
| P0 Confidentialité | 100 | 0 |
| Réponses brutes conservées | 0 | 0 |

La campagne finale a terminé 100 scénarios sur 100. Aucun motif interdit n'a été
détecté dans les payloads publics observés.

Les métriques de cette campagne sont : moyenne 4 577,29 ms, médiane 2 747 ms,
P95 12 794 ms et maximum 27 488 ms. Ce lot ne cherche pas à modifier les
performances.

## Résultats des tests

- Confidentialité publique et runner : 7 réussites.
- Tests Runtime : 86 réussites, 661 désélectionnés.
- Validation d'architecture : 12 réussites.
- Interface HTTP réelle : réussie.
- Suite complète : 2 204 réussites, 128 sous-tests réussis et les 3 échecs
  historiques déjà qualifiés.
- Nouvel échec : aucun.

Les trois anomalies historiques sont :

- `DependencyTests::test_import_does_not_load_forbidden_packages` ;
- `IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages` ;
- `test_integration_failure_preserves_legacy_expert_payload`.

## Conclusion

Le P0-1 Confidentialité Runtime est résolu sur la frontière utilisateur :
**100 P0 avant, 0 P0 après**. Les informations techniques restent utilisables en
interne, mais ne sont plus envoyées au frontend, au rapport utilisateur ou aux
exports publics.
