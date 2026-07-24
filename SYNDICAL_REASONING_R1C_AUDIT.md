# LOT R1C — Audit préalable

## Référence

- Branche auditée : `syndical-reasoning-r1c-working-time`
- SHA de départ : `af9ef9be31677b3beef450c83df479e32319cdcb`
- État initial : dépôt propre, R0, R1A et R1B fusionnés dans `main`
- Runtime : feature flag syndical unique, désactivé par défaut et fail-safe

## Composants réutilisables

Le socle R0 apporte déjà :

- `SyndicalCaseInput`, ses faits typés, ses pièces metadata-only, ses sources,
  son urgence et sa confidentialité ;
- `SyndicalReasoningReport`, le protocole en dix-huit étapes, la prudence, la
  confiance et la hiérarchie des sources ;
- la séparation entre faits déclarés, faits établis et hypothèses ;
- le pont Runtime et son fallback historique.

R1A apporte les priorités de preuves, les positions contradictoires et le
principe d'une spécialisation qui conserve le rapport R0. R1B confirme la
sélection spécialisée progressive et la conservation de plusieurs
qualifications provisoires.

La politique de sources R0 est directement réutilisable. R1C doit seulement
décrire les catégories supplémentaires des pièces opérationnelles : planning,
cycle, badgeages, Kelio, feuille d'intervention et bulletin Nibelis.

## Extensions nécessaires

R1C requiert des contrats immuables propres au temps de travail :

- situations proches mais distinctes ;
- organisation, horaires théoriques, déclarés et constatés ;
- astreintes, interventions, pauses et repos ;
- hypothèses de qualification prudentes ;
- comparaisons documentaires structurées ;
- incidences potentielles sur la rémunération ;
- questions en quatre niveaux ;
- preuves indiquant ce qu'elles démontrent et ne démontrent pas seules ;
- stratégies en cinq niveaux ;
- articulation explicite R1A/R1B/R1C.

## Frontière avec Expert Paie

Trois responsabilités sont strictement séparées.

1. **Raisonnement syndical sur le temps de travail** : qualifier prudemment
   horaires, pauses, repos, astreintes, interventions, cycles et organisation à
   partir de faits et pièces incomplets.
2. **Incidence potentielle sur la rémunération** : signaler qu'une majoration,
   une prime, une indemnité, un compteur ou une régularisation pourrait être
   concerné, avec un niveau de confiance et les données nécessaires.
3. **Calcul réel de paie** : appliquer des assiettes, taux, montants, règles de
   cumul ou formules. Cette responsabilité reste entièrement hors R1C et relève
   de l'Expert Paie lorsque ses propres conditions sont réunies.

R1C n'importe, n'appelle et ne modifie aucun module de l'Expert Paie. Les
mentions Kelio et Nibelis sont exclusivement des métadonnées de pièces à
rapprocher. Une absence de rubrique ou un écart de compteur est une anomalie à
vérifier, jamais la preuve définitive d'une erreur de paie.

## Risques identifiés et réponses

- **Duplication avec R0** : le rapport, la prudence, les sources et la
  confidentialité restent délégués à R0.
- **Duplication avec R1A/R1B** : une politique d'articulation désigne un domaine
  principal et des compléments ; elle interdit deux conclusions spécialisées
  concurrentes.
- **Confusion horaire/contrat** : une modification imposée ou un passage de jour
  en poste garde R1A comme domaine principal ; R1C décrit seulement les effets
  temporels et les contreparties possibles.
- **Confusion refus/sanction** : une sanction ou une procédure disciplinaire
  garde R1B comme domaine principal ; R1C fournit le contexte d'horaires.
- **Réponse trop affirmative** : chaque qualification contient faits favorables,
  fragilités, informations manquantes, sources, confiance et conséquences
  possibles. Aucune violation n'est certaine sur un récit seul.
- **Calcul implicite** : aucun champ monétaire, taux, formule ou total calculé
  n'est prévu dans les modèles.
- **Données sensibles** : scénarios anonymes et synthétiques, aucune pièce réelle,
  aucun contenu de bulletin, planning, Kelio ou Nibelis.

## Architecture retenue

R1C sera une extension additive de `SYNDICAL_REASONING_ENGINE`, sans dépendance
vers le Runtime ni vers Expert Paie. Le Runtime importera uniquement sa façade
publique et appliquera la priorité :

1. R1B principal si une procédure disciplinaire est détectée ;
2. R1A principal si une modification contractuelle ou organisationnelle est
   détectée ;
3. R1C principal pour une question autonome de temps, repos, compteur ou
   contrepartie ;
4. R0 sinon.

R1C pourra être ajouté comme analyse complémentaire aux deux premiers cas. Le
feature flag existant restera l'unique commande d'activation.
