# Architecture — Assistant final CFDT Nexus

## Modules

- `models.py` : contrats immuables d’entrée, plan, résultats, actions et réponse.
- `normalization.py` : normalisation déterministe.
- `routing.py` : détection contextuelle multi-domaines.
- `planning.py` : ordre stable, moteurs bornés, sources et fallbacks.
- `adapters.py` : conversion explicite des payloads existants.
- `orchestration.py` : appels isolés et résultats partiels.
- `contradictions.py` : politique de prudence et règles bloquantes.
- `sources.py` : déduplication et hiérarchie.
- `questions.py` : fusion et limites 3 critiques/5 prioritaires.
- `synthesis.py` : synthèse structurée unique.
- `actions.py` : brouillons sans envoi.
- `critic.py` : contrôle contradicteur avant publication.
- `privacy.py` : autorisation, anonymisation ou blocage.
- `engine.py` : façade publique.

## Domaines et moteurs

R1A à R2C sont appelés via `syndical_reasoning`. La paie utilise `expert_paie_v2`. Les domaines CSE peuvent ajouter `cse_memory`. La recherche de sources utilise `documentary`. Un moteur n’est appelé qu’une fois et le plan est limité à quatre moteurs par défaut.

## Sources

La priorité générale est : accords INEOS, Convention Chimie, codes, jurisprudence, sources officielles, documents CSE, documents individuels, systèmes factuels, historique CSE, témoignages. Les contenus ne sont jamais inventés.

## Runtime et fallback

`NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED` vaut `false` par défaut. Le Runtime final reçoit le rapport déjà construit. Désactivé ou en erreur, il rend ce même objet. Activé, il ajoute une section bornée et un objet structuré. Les flags spécialisés restent souverains.

## Confidentialité

Le NIR et l’IBAN bloquent la restitution. Email, téléphone, identifiants RH et montant salarial explicite sont neutralisés. Les sorties publiques refusent chemins locaux, identifiants de chunks et identifiants de stockage. Les diagnostics ne contiennent que des codes stables.

## Limites

La détection est déterministe et explicable, sans nouveau moteur NLP. Les actions sont des brouillons. Les qualifications restent hypothétiques tant que les faits et sources ne sont pas vérifiés.
