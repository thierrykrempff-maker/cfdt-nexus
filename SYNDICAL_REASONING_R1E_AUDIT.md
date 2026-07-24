# Audit R1E — Maladie, absences et protection sociale

## Composants réutilisés

R1E compose le moteur prudent R0, ses niveaux de confiance et d'urgence, sa hiérarchie de sources et le pont Runtime fail-safe. Les types CPAM, URSSAF et Agirc-Arrco sont déjà reconnus par la politique de sources. Le corpus Protection Sociale et ses recherches restent indépendants et metadata-only.

## Frontières

1. Le moteur structure une qualification juridique ou administrative provisoire ; il ne rend aucune décision.
2. Un fait déclaré reste distinct d'un document ou d'une décision.
3. Les données de santé sont limitées à l'existence d'un arrêt, d'une restriction ou d'un avis minimal.
4. Le service paie traite les rubriques ; R1E ne calcule aucun montant.
5. La CPAM instruit et décide le caractère professionnel et les prestations relevant de sa compétence.
6. Le médecin du travail rend les avis de santé au travail ; R1E ne les interprète pas médicalement.
7. L'employeur organise la reprise, l'aménagement et le reclassement dans son champ de responsabilité.
8. La mutuelle, la prévoyance ou l'assureur appliquent leurs garanties après instruction ; aucune prise en charge n'est promise.

## Risques maîtrisés

- Pas de diagnostic, de pathologie ou de traitement détaillé.
- Pas d'anticipation d'une reconnaissance CPAM.
- Pas de calcul de paie, d'IJSS ou d'indemnisation.
- Comparaisons documentaires limitées à des métadonnées.
- Acteur compétent indiqué pour chaque hypothèse et stratégie.
- Urgence humaine, médicale, financière, contractuelle, administrative ou contentieuse séparée.
- R1A à R1D restent propriétaires de leurs qualifications.
