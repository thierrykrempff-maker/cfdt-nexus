# Audit R1D — Discrimination, harcèlement et égalité de traitement

## Socle réutilisé

R1D réutilise sans modification les entrées `SyndicalCaseInput`, le rapport transverse R0, les niveaux de confiance et d'urgence, la politique de prudence, la hiérarchie des sources et le pont Runtime fail-safe. Comme R1A, R1B et R1C, il produit une projection métier immuable au-dessus du rapport R0.

Les spécialisations existantes restent responsables de leurs objets : R1A des modifications contractuelles, R1B des mesures disciplinaires et R1C du temps de travail. R1D n'effectue aucun calcul de paie et ne pose aucun diagnostic médical.

## Frontières de qualification

| Notion | Frontière retenue |
|---|---|
| Conflit professionnel | Désaccord ou tension sans répétition ni indice suffisant d'une atteinte interdite. |
| Pouvoir de direction | Décision de gestion pouvant être objectivement justifiée, à examiner contradictoirement. |
| Management inadapté | Pratique inadéquate sans que les critères d'un harcèlement soient automatiquement réunis. |
| Harcèlement moral possible | Agissements et répétition à documenter, avec effets déclarés analysés sans diagnostic. |
| Harcèlement sexuel possible | Propos ou comportements sexuels/sexistes, répétition ou pression grave à vérifier. |
| Agissement sexiste | Comportement lié au sexe sans présumer une sollicitation sexuelle. |
| Discrimination possible | Mesure défavorable, critère protégé potentiel et lien causal restant à examiner. |
| Différence objectivement justifiée | Écart compatible avec une raison vérifiable étrangère à un critère protégé. |
| Représailles possibles | Mesure postérieure à un signalement ou témoignage, sans causalité présumée. |
| Atteinte syndicale possible | Traitement défavorable lié potentiellement à l'activité ou au mandat syndical. |

## Risques maîtrisés

- Un fait isolé ne devient pas automatiquement du harcèlement moral.
- Une différence de traitement ne devient pas automatiquement une discrimination.
- Les comparateurs conservent leurs différences objectives et leurs limites.
- Les conséquences de santé restent déclaratives ; aucune maladie n'est déduite.
- L'urgence humaine est traitée avant la qualification juridique.
- Les preuves ne peuvent être recherchées ou conservées que licitement.
- Les sorties emploient des formulations prudentes et des hypothèses concurrentes.

## Extensions nécessaires

Une chronologie factuelle, des critères protégés, des mesures défavorables, des comparateurs, des hypothèses concurrentes, une argumentation contradictoire, un questionnement priorisé, des preuves licites et cinq niveaux de stratégie sont ajoutés dans des modules R1D isolés. Le Runtime sélectionne R1D seulement sur un domaine explicite ou une combinaison contextuelle suffisante.
