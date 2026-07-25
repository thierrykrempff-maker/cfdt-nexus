# Audit UI1 — Portail d’accueil CFDT Nexus

## Interface actuelle

L’interface locale reposait sur une page unique combinant un cockpit de démonstration synthétique et un formulaire libre envoyé à `POST /api/analyze`. Le serveur local, sa frontière publique de confidentialité et les restitutions historiques étaient déjà opérationnels.

## Navigation et parcours actuels

Le point d’entrée affichait directement des concepts techniques et un formulaire généraliste. Il n’existait ni orientation par besoin métier, ni parcours progressif, ni distinction visible entre accompagnement salarié, CSE, négociation et paie.

## Composants réutilisables

- serveur HTTP local et endpoint `/api/analyze` ;
- rendu sécurisé par `textContent` ;
- restitution par domaines, sources, constats et documents ;
- génération locale d’une fiche Markdown ;
- cockpit synthétique et ses deux vues ;
- fallback historique lorsque les feature flags sont désactivés ;
- frontière `sanitize_public_payload`.

## Limites et risques

- charge cognitive importante pour un utilisateur non technique ;
- exemples et libellés orientés moteur plutôt qu’usage ;
- contexte insuffisamment structuré avant routage ;
- résultat dense et peu hiérarchisé ;
- risque de régression si les identifiants DOM historiques ou le contrat HTTP étaient supprimés.

## Architecture cible

Le portail ajoute une couche front-end d’orientation : accueil métier → formulaire progressif → requête structurée → endpoint historique → résultat hiérarchisé. Il ne qualifie pas juridiquement, ne choisit aucun moteur avancé et ne persiste aucune saisie.

## Stratégie de compatibilité

Le serveur, l’endpoint, le payload public, le moteur historique, le cockpit synthétique et les contrôles de confidentialité sont conservés. Le contexte UI est ajouté au corps de requête mais le champ `query` reste pleinement compatible avec le routeur historique.
