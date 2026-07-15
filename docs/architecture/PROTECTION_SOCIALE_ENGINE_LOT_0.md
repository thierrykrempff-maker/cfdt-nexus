# Protection sociale — LOT 0

## Objectif et séparation des domaines

Le domaine Protection sociale fournit un socle documentaire local pour la mutuelle, la prévoyance, le maintien de salaire, la portabilité et les procédures associées. Il est indépendant du CSE Memory Engine et ne modifie aucun moteur juridique, de paie, d’accords ou CSE.

Ce lot crée uniquement un modèle documentaire générique et un audit de métadonnées de fichiers. Il ne réalise aucune extraction de texte, normalisation, indexation ou analyse métier.

## Structure locale et confidentialité

Les originaux sont déposés sous `PROTECTION_SOCIALE_ENGINE/RAW_DOCUMENTS/`, par domaines et sous-catégories. Les rapports vont dans `AUDIT/`; les futurs artefacts utiliseront `PROCESSED/`, `INDEX/` et `GRAPH/`. Ces emplacements, ainsi que `LISEZ_MOI.txt`, sont ignorés par Git. Aucun `.gitkeep` n’est utilisé dans les zones confidentielles.

Les chemins inscrits dans les rapports sont relatifs au corpus. Aucun contenu documentaire, chemin absolu, donnée personnelle ou donnée contractuelle n’est écrit dans le code ou la documentation.

## Modèle documentaire

Le modèle décrit l’identité technique de la source, son empreinte SHA-256, son domaine et sa catégorie, ainsi que des champs facultatifs d’émetteur, fournisseur, contrat, dates et statut. Toute valeur métier inconnue reste `null`. L’identifiant est un UUID v5 stable dérivé du chemin relatif, de l’empreinte et de la version de schéma.

Domaines minimaux : mutuelle, prévoyance, maintien de salaire, portabilité, procédure interne et autre. Catégories minimales : notice, tableau de garanties, cotisations, formulaire, courrier, procédure, contrat, avenant, FAQ, tableau et autre.

## Audit local

L’audit parcourt récursivement les noms et métadonnées techniques sans suivre les liens symboliques. Il calcule les tailles et empreintes binaires, détecte fichiers vides ou illisibles, doublons exacts, chemins longs, noms inhabituels, formats anciens ou inconnus et catégories probables d’après les seuls chemins. Un indice de données personnelles repose exclusivement sur le nom ou le chemin ; il ne confirme jamais la présence de telles données.

```powershell
python -m automation.protection_sociale.audit_corpus
python -m unittest automation.protection_sociale.test_audit_corpus
```

Les rapports locaux sont `PROTECTION_SOCIALE_ENGINE/AUDIT/protection_sociale_audit.json` et `.md`.

## Limites et suites prévues

Ce lot n’utilise ni OCR, ni IA, ni réseau, ni connecteur officiel. Il ne lit pas le contenu logique des documents. Les classifications tirées des chemins sont indicatives.

Les suites prévues sont : LOT 1A import documentaire, LOT 1B normalisation, LOT 1C métadonnées métier, LOT 1D chunks, LOT 2 recherche locale, puis une connexion ultérieure et séparément autorisée aux sources officielles Ameli, Service-Public et textes officiels.
