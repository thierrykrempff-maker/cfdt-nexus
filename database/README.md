# Base documentaire privée CFDT Nexus V1

## Objectif

Ce dossier définit l'architecture de la future base documentaire privée de CFDT Nexus.

Il ne contient aucun document réel. Il contient uniquement :

- des schémas de métadonnées ;
- un exemple d'index documentaire fictif ;
- une politique de sécurité documentaire.

## Principe central

Les documents privés restent hors GitHub.

GitHub peut versionner :

- les modèles de données ;
- les règles de sécurité ;
- les index expurgés ;
- les métadonnées non sensibles ;
- les exemples fictifs.

GitHub ne doit jamais contenir :

- accord INEOS réel ;
- PV CSE réel ;
- BDESE ;
- document RH nominatif ;
- dossier salarié ;
- donnée confidentielle ;
- chiffre financier réel non validé pour diffusion.

## Structure

```text
database/
  README.md
  agreements/
    README.md
    agreements-index.schema.json
    search-result.schema.json
    INTEGRATION_CONTRACTS.md
  schema/
    documents.schema.json
    sources.schema.json
    cse.schema.json
  index/
    documents.example.json
  security/
    DOCUMENT_SECURITY_POLICY.md
```

## Métadonnées documentaires V1

Chaque document indexé devra pouvoir porter les métadonnées suivantes :

- `id`
- `titre`
- `categorie`
- `sousCategorie`
- `entreprise`
- `site`
- `date`
- `version`
- `confidentialite`
- `cheminLocalPrive`
- `motsCles`
- `resume`
- `agentsAutorises`
- `dateAjout`
- `derniereVerification`

## Catégories prévues

- convention collective
- accord entreprise
- règlement intérieur
- PV CSE
- jurisprudence
- modèle courrier
- veille juridique
- note personnelle
- document CSSCT
- document paie

## Connexions futures prévues

Cette base documentaire est préparée pour alimenter plus tard :

- Document Intelligence Center ;
- Cycle CSE ;
- Agent Défenseur Syndical ;
- Agent Paie ;
- Agent CSSCT ;
- Agent Convention Chimie ;
- Veille juridique.

## Règle d'usage

Avant toute connexion à une IA, un workflow n8n, un site public ou un export, la confidentialité du document doit être vérifiée.
