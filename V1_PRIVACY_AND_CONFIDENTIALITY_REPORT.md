# Rapport confidentialité et données — CFDT Nexus V1

## Verdict

Aucun constat `BLOCKING` après durcissement du LOT 4.

| Niveau | Constat | Traitement |
|---|---|---|
| HIGH | Une exception serveur pouvait être journalisée avec son message complet. | Journal limité au type d'exception ; réponse publique générique. |
| MEDIUM | Les secrets de connecteurs dépendent d'une configuration locale. | Fichier sous `local-index/`, ignoré par Git ; valeurs jamais affichées. |
| MEDIUM | Les exports peuvent contenir les faits fournis par l'utilisateur. | Export volontaire et limité à la synthèse publique ; avertissement utilisateur. |
| LOW | Les corpus locaux nécessitent une sauvegarde opérateur. | Absence de stockage serveur annoncée et procédure documentée. |
| INFORMATIONAL | Le navigateur ne persiste pas automatiquement les dossiers. | Aucun usage de `localStorage` ou `sessionStorage`. |

## Contrôles

- secrets et tokens absents des fichiers suivis du LOT ;
- aucun chemin utilisateur dans les réponses et captures de release ;
- aucun diagnostic Runtime dans `analysis_report` public ;
- aucun contenu documentaire intégral ajouté à Git ;
- isolation vérifiée entre analyses successives ;
- erreurs HTTP sans trace Python ni message d'exception ;
- serveur lié à `127.0.0.1` ;
- export et impression déclenchés explicitement ;
- `local-index/` reste ignoré.

Les captures de la baseline sont synthétiques et anonymisées. Les documents locaux
réels ont été testés sur place sans être copiés dans les livrables.
