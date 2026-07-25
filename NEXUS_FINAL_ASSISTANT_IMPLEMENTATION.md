# Implémentation — Assistant final CFDT Nexus

## Réalisation

Une nouvelle couche `NEXUS_FINAL_ASSISTANT` orchestre les moteurs existants sans modifier leurs contrats. Le modèle d’entrée couvre contexte, rôle, faits, documents, période, urgence, sortie attendue, détail, moteurs autorisés, données interdites, confidentialité et historique.

Le routage fournit score, déclencheurs, indices contraires, confiance, rôle, moteur et raison. Le plan fixe domaine principal, compléments, ordre, sources, questions critiques, données manquantes, calculs, exclusions, arrêt, fallback et mode de réponse.

L’orchestrateur isole chaque exception et conserve les résultats partiels. Les adaptateurs convertissent les payloads en un résultat commun. Les questions et sources sont dédupliquées. Les contradictions sont visibles et résolues par la prudence. La synthèse sépare compréhension, qualifications, manques, sources, arguments, risques, actions et limites.

Le générateur produit uniquement des brouillons marqués « Brouillon à relire et adapter. ». Le contradicteur contrôle les affirmations fortes et peut bloquer la publication. Le filtre de confidentialité précède la restitution.

## Runtime et interface

Le serveur local appelle la nouvelle intégration après les enrichissements historiques. Le rapport conserve toutes ses sections puis reçoit, lorsque le flag est actif, une section `nexus_final_assistant` et des champs structurés utilisables par l’interface générique existante.

## Hors périmètre respecté

Aucun moteur métier, connecteur, corpus, règle de paie, document réel, envoi automatique ou conclusion juridique automatique n’a été ajouté.
