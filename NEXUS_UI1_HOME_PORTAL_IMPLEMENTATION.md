# Implémentation UI1

## Réalisation

- remplacement du cockpit en première vue par un portail métier ;
- conservation du cockpit synthétique historique hors du parcours principal ;
- quatre cartes métier et quatre accès secondaires ;
- assistants progressifs propres à chaque espace ;
- contrat structuré envoyé avec la question au endpoint existant ;
- affichage des modes historique et avancé sans mutation de configuration ;
- résultat restructuré et actions de brouillon conservées ;
- mise en page responsive et accessible.
- intégration du logo CFDT INEOS Sarralbe comme ressource JPEG locale, sans URL externe ni encodage base64.

## Choix techniques

HTML, CSS et JavaScript natifs uniquement. Aucune dépendance, aucun framework, aucune API ni aucun stockage n’a été ajouté.

## Sécurité

Le rendu dynamique continue d’utiliser `textContent`. Le portail ne stocke pas les saisies, ne journalise pas leur contenu et n’expose pas de diagnostic interne.
