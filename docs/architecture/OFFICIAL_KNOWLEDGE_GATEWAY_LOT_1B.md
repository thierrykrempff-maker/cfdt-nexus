# Official Knowledge Gateway — LOT 1B — politique documentaire commune

## Architecture

Le LOT 1B fournit une politique pure et commune à tous les futurs connecteurs officiels. Il sépare modèles documentaires, capacités de licence, citation, indexation, cache, conservation, rafraîchissement et version. Aucun module ne transporte, télécharge, synchronise ou lit un document réel.

Une décision suit l’ordre suivant : provenance obligatoire, plafond imposé par la licence, niveau d’indexation déclaré par le connecteur, cache et rétention. Une règle plus permissive ne peut jamais dépasser les capacités de licence.

## Licences

La matrice couvre Licence Ouverte, CC BY, CC BY-SA, CC BY-ND, CC BY-NC, CC BY-NC-SA, CC BY-NC-ND, domaine public et inconnue. Elle définit texte intégral, cache, permanence, indexation, métadonnées, extraits, longueur maximale, citation, attribution, transformation, redistribution et revue juridique.

Les licences ND interdisent toute transformation et l’indexation plein texte dans la politique commune; les extraits sont plafonnés et soumis à revue. Les variantes NC interdisent par défaut la redistribution et le stockage permanent. Une licence inconnue est fail-closed : métadonnées seulement, sans cache, texte intégral ni extrait.

## Indexation

Chaque connecteur doit déclarer exactement un niveau : `NONE`, `METADATA_ONLY`, `EXCERPTS`, `FULLTEXT_ALLOWED` ou `INTERNE_ONLY`. `FULLTEXT_ALLOWED` n’autorise réellement le plein texte que si la licence le permet. `INTERNE_ONLY` refuse toute source externe.

## Citations

Les réponses peuvent reposer sur métadonnées, extrait, document interne ou plusieurs sources. Chaque source conserve titre, URI canonique, provenance, licence, autorité, date de récupération, version et caractère interne. Un extrait est refusé s’il est interdit ou trop long. L’identifiant de citation est déterministe.

## Cache

Les modes sont interdit, temporaire et permanent. Le temporaire exige une durée positive; le permanent exige une licence autorisant le stockage permanent. La politique prévoit validation, ETag, Last-Modified, expiration et purge. Les calculs sont locaux et n’effectuent aucune requête.

## Rafraîchissement

Les modes sont manuel, journalier, hebdomadaire, mensuel, jamais et sur événement. Le module calcule seulement échéance et décision; il n’attend pas et ne déclenche aucun transport.

## Versions

La comparaison utilise SHA-256 et identifiant de version déterministe. Elle distingue contenu inchangé, nouvelle version, version courante et historique. La provenance et l’empreinte relient chaque état.

## Conservation et suppression

Les journaux de synchronisation, provenances et empreintes sont toujours protégés. Un contenu en cache ne peut être supprimé que si la suppression est explicitement activée et si sa durée de conservation est expirée. La politique n’exécute aucune suppression physique.

## Confidentialité et limites

Tous les tests sont synthétiques. Aucun document interne ou officiel réel n’est lu ou écrit. Aucun connecteur n’est activé et le garde réseau du LOT 0 demeure inchangé. La matrice est volontairement prudente; toute condition particulière d’une source ou d’un document peut imposer une restriction supplémentaire et une revue juridique.
