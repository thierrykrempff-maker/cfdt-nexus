# LOT R1A — Rapport d'implémentation

## Architecture

R1A est une projection métier spécialisée construite sur les contrats R0. Le
moteur `ContractChangeReasoningEngine` détecte les dimensions du changement,
construit plusieurs qualifications provisoires, puis délègue le rapport
transversal au `SyndicalReasoningEngine`.

## Situations couvertes

- modification possible du contrat ;
- modification possible des conditions de travail ;
- changement d'horaires ou de cycle ;
- passage jour vers équipes postées ;
- changement d'équipe ou de poste ;
- qualification et classification ;
- mobilité géographique ;
- suppression de poste ;
- réorganisation ;
- modification liée de la rémunération.

Plusieurs dimensions peuvent coexister. Chaque qualification expose les
informations qui permettraient de la confirmer ou de l'écarter.

## Questions automatiques

Les questions sont ordonnées par priorité et adaptées aux indices détectés :

- contrat et avenant ;
- accord du salarié ;
- durée temporaire ou permanente ;
- clause de mobilité ;
- horaires, cycles, repos et équipes ;
- travail posté prévu ou non ;
- rémunération et primes ;
- missions, qualification et classification ;
- dimension collective et consultation CSE ;
- accords INEOS, Convention Chimie et date d'effet.

Les questions déjà résolues par une pièce connue ne sont pas répétées.

## Stratégies

1. Obtenir toutes les informations.
2. Demander et comparer les documents.
3. Rencontrer la direction.
4. Préparer une intervention CSE.
5. Préparer un recours adapté.

Chaque stratégie fournit objectif, avantages, limites, risques, pièces et
urgence. L'ordre reste progressif ; le recours n'est jamais recommandé
automatiquement en premier.

## Arguments

Deux analyses symétriques sont produites :

- salarié : arguments favorables, points forts et points restant à prouver ;
- employeur : arguments possibles, fondements possibles et démonstrations
  nécessaires.

Les deux positions restent conditionnelles et ne caricaturent aucune partie.

## Preuves

Indispensables selon le cas :

- contrat, avenants et décision écrite ;
- planning avant/après ;
- PV ou information CSE ;
- bulletins de paie.

Utiles :

- fiche de poste ;
- accords d'entreprise ;
- Convention collective Chimie.

Complémentaires :

- organigramme.

## Scénarios synthétiques

- passage jour vers équipe postée ;
- suppression de poste ;
- modification importante des horaires ;
- mutation interne ;
- réorganisation collective.

Chaque scénario produit un profil de dimensions différent.

## Runtime

Le pont R0 conserve `NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED`. Quand R1A est
pertinent, le payload contient `domain_analysis`; sinon le moteur transversal
R0 reste utilisé. Le flag désactivé et les fallbacks conservent le rapport
historique.

## Périmètre

Créés :

- sept modules R1A ;
- trois suites de tests R1A ;
- trois livrables R1A.

Modifiés :

- `SYNDICAL_REASONING_ENGINE/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/syndical_reasoning_runtime.py`

Aucun connecteur, expert, corpus, composant Core ou moteur paie n'est modifié.
