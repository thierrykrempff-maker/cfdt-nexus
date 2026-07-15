# Cockpit V3 connecte au pipeline dossier salarie - LOT 5C

## Architecture reelle avant modification

Le depot contient deux interfaces distinctes :

- `cockpit/` : maquette V2 statique historique, sans backend ;
- `apps/nexus-local-interface/` : interface locale V2.2 effectivement connectee a Nexus.

Le LOT 5C enrichit uniquement `apps/nexus-local-interface/`. Cette application utilise la bibliotheque standard Python :
`ThreadingHTTPServer` sert `index.html`, `styles.css` et `app.js`. Avant LOT 5C, elle exposait `GET /health` et
`POST /api/analyze`, appelait le routeur local, l'orchestrateur puis `automation/experts/report_generator.py`.

Aucune seconde application n'est creee et la maquette `cockpit/` reste inchangee.

## Endpoint LOT 5C

```text
GET /api/employee-case/scenarios
GET /api/employee-case/demo?scenario=<identifiant>
```

Le premier endpoint retourne les demonstrations autorisees. Le second charge une fixture controlee, execute
`EmployeeCasePipeline`, injecte deux analyses expertes synthetiques, puis appelle `EmployeeCaseReportGenerator`.

La reponse contient le dossier, les 12 statuts, la completude, les contextes experts, les themes analyses/bloques, les
contradictions, le diagnostic, `employee_view`, `expert_view` et les metadonnees. Ces structures proviennent directement
des LOTS 5A et 5B.

## Flux

```text
fixture synthetique autorisee
-> pipeline LOT 5A
-> analyses expertes synthetiques injectees
-> rapport LOT 5B
-> adaptateur employee_case_demo.py
-> endpoint local
-> Cockpit V3
```

Le taux global de completude est calcule cote backend a partir des scores documentaires du pipeline. Il est accompagne
d'un avertissement indiquant qu'il ne mesure ni succes ni conformite juridique.

## Scenarios disponibles

- heures supplementaires complet ;
- astreinte incomplete ;
- maladie avec pieces contradictoires ;
- classification sans fiche de poste ;
- conges payes complet.

Le scenario contenant la sonde sensible est exclu de `SCENARIOS` et ne peut pas etre selectionne dans l'interface.

## Ecran

Le panneau dossier affiche : en-tete, confidentialite, confiance, 12 etapes, completude, documents, diagnostic,
themes bloques, contradictions et rapport. Les statuts combinent libelle, symbole et couleur.

Deux boutons accessibles au clavier basculent entre :

- la vue salarie, rendue uniquement depuis `employee_view` ;
- la vue expert, rendue uniquement depuis `expert_view`.

Le frontend affiche les donnees recues. Il ne contient ni matrice documentaire, ni calcul de confiance, ni regle de
contradiction, ni lecture de referentiel.

## Erreurs

Le serveur distingue scenario absent, inconnu, refuse et erreur interne. Le frontend affiche explicitement endpoint
indisponible, JSON invalide, erreur de chargement et liste de scenarios indisponible. Aucun repli par de fausses donnees
n'est utilise.

## Confidentialite et securite

- fixtures synthetiques uniquement ;
- aucun chemin de fichier accepte depuis le navigateur ;
- aucun import de document ;
- aucune API externe ;
- aucun stockage navigateur permanent ;
- aucun champ de valeur de parametre expose ;
- rendu par `textContent` et creation DOM, sans HTML issu du rapport ;
- en-tetes `no-store` et politique CSP existante conserves.

## Limites V3

- aucun document reel, OCR ou PDF ;
- aucune persistance ;
- analyses expertes de demonstration injectees ;
- aucun calcul de paie ou avis juridique ;
- aucun export supplementaire ;
- aucun framework frontend ou backend.

Une version future pourra accepter un import documentaire prealablement anonymise, apres definition d'un stockage local
securise, d'un contrat d'authentification et de controles de confidentialite specifiques. Ces fonctions ne sont pas
activees par LOT 5C.
