# A6 — Rapprochement documentaire de carrière

## Anomalie corrigée

Avant A6, le merger de Career Reconstruction traitait les enregistrements
compatibles dans leur ordre d'arrivée. Les types documentaires, la confiance,
la provenance et la complétude de période étaient conservés mais n'influaient
pas sur la proposition de rapprochement.

## Stratégie centralisée

`DocumentResolutionStrategy`, exclusivement utilisée par Career
Reconstruction, applique l'ordre suivant :

1. contrat de travail ou avenant ;
2. relevé de carrière ;
3. bulletin de paie ;
4. export Kelio ;
5. autres preuves.

À type documentaire égal, la confiance départage les sources (`HIGH`,
`MEDIUM`, `LOW`, `UNKNOWN`), puis la complétude de la période couverte et enfin
une clé stable issue de la provenance. Aucun connecteur ne contient cette
logique.

## Fusion prudente

La valeur de la source prioritaire devient la valeur proposée dans
`merged_values`. Toute valeur différente reste simultanément visible dans
`alternative_values` et produit un conflit exigeant une validation humaine.
`resolution_order` expose l'ordre déterministe appliqué.

Toutes les provenances et tous les niveaux de confiance restent attachés à la
fusion. Aucune source n'est supprimée, aucun document n'est déclaré vrai et
aucune priorité ne crée un droit, un calcul de retraite ou une décision
automatique.

## Compatibilité

Le pipeline A3 reste l'unique entrée de reconstruction. Le Privacy Gate A4
reste actif avant tout traitement. Le référentiel Kelio A5, la fondation A2 et
les frontières A1 sont inchangés. Aucun connecteur n'est modifié.

## Limites

La stratégie classe uniquement des métadonnées déjà validées. Elle ne lit pas
de document, ne compare pas de texte, n'interprète aucune règle juridique et
ne calcule ni retraite, ni pénibilité, ni droit potentiel.
