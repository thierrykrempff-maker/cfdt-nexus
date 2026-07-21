# A4 — Confidentialité active Retraite & Pénibilité

## Anomalie initiale

Les lots précédents déclaraient des interdictions de confidentialité dans les
policies et contrats, mais leur exécution n'était pas centralisée. Les
validateurs refusaient déjà les sources non synthétiques, l'absence de
provenance, un salarié Kelio non anonymisé et les rubriques Nibelis sans
référentiel. Ces contrôles devaient être conservés, mais ils ne détectaient pas
uniformément un NIR, un IBAN, un RIB ou des coordonnées personnelles injectés
dans un champ libre.

## Cartographie avant correction

| Couche | Protection existante | Limite avant A4 |
|---|---|---|
| Career Statement | policy sans identité, validateur `synthetic_only` | contenu de champs non inspecté |
| Payslip | anonymisation et source synthétique | motifs bancaires ou personnels non détectés |
| Employment Contract | policy sans identité, source synthétique | champs libres non inspectés |
| Kelio | salarié anonymisé obligatoire | identifiant réel simulé possible hors champ contrôlé |
| Nibelis | source synthétique et référentiel fail-closed | identifiant ou donnée bancaire libre non détecté |
| Career Import | provenance structurelle et batch synthétique | aucune détection active de motifs sensibles |
| Career Reconstruction | batch validé A3 | confiance dans le batch sans seconde inspection |
| Timeline / Evidence | policies prudentes et données synthétiques | appels directs possibles |
| Potential Rights | sortie prudente et sans attribution de droit | contexte direct non inspecté |
| Rapports | listes de marqueurs textuels dans certains builders | blocage tardif et incomplet |

## Chemins de fuite potentiels corrigés

- conversion d'une source valide structurellement mais contenant un motif
  sensible ;
- génération d'un rapport de connecteur depuis cette même source ;
- appel direct de `CareerImportEngine` sans passer par le pipeline A3 ;
- construction manuelle d'un batch validé avant reconstruction ;
- appels directs aux couches Timeline, Evidence et Potential Rights ;
- message d'erreur recopiant la valeur ayant déclenché le contrôle.

## Architecture du Privacy Gate

Le flux protégé est :

`Source synthétique → Validation connecteur → Privacy Gate → Career Import → Career Reconstruction → Timeline → Evidence → Potential Rights`

Trois modules suffisent :

- `privacy_models.py` : décisions et constats immuables sans valeur inspectée ;
- `privacy_detector.py` : inspection récursive déterministe et contextuelle ;
- `privacy_gate.py` : façade fail-closed, statuts et diagnostics sûrs.

Le contrôle principal se situe dans `ConnectorFoundation` et
`CareerImportPipeline`. Une défense en profondeur protège également
`CareerImportEngine`, `CareerReconstructionEngine`, `CareerTimelineEngine`,
`CareerEvidenceEngine` et `PotentialRightsEngine`.

## Catégories et statuts

Les catégories critiques couvrent : NIR, IBAN, RIB structuré, identifiant
interne non synthétique, identité directe dans un champ explicitement
personnel, courriel, téléphone, adresse postale personnelle, document ou
chemin réel, source réelle ou de production et inspection impossible.

Les statuts sont :

- `SAFE` : aucune anomalie ;
- `SAFE_WITH_WARNINGS` : revue manuelle non bloquante ;
- `BLOCKED` : violation critique, aucun traitement métier ;
- `INSPECTION_ERROR` : structure inconnue, cycle ou Privacy Gate absent.

## Stratégie anti-faux-positifs

Les contrôles combinent le nom logique du champ, le type de la valeur, un
motif suffisamment structuré et le contexte synthétique. Un numéro quelconque
n'est pas sensible par défaut. Les années, dates, coefficients, montants,
durées, compteurs, numéros de rubriques et identifiants explicitement
synthétiques restent autorisés. Les adresses et identités directes ne sont
bloquées que dans des champs sémantiquement personnels. Les RIB exigent leurs
quatre blocs structurés.

## Fail-closed et diagnostics

L'absence de Privacy Gate, un type inconnu, une clé de mapping non textuelle,
un cycle ou une erreur d'inspection produisent `INSPECTION_ERROR`. Une
violation critique produit `BLOCKED`. Dans les deux cas, aucun import, aucune
reconstruction et aucun rapport métier ne sont produits.

Un constat ne contient que catégorie, sévérité, chemin logique, code,
explication générique et action requise. Aucune valeur complète ou masquée
n'est conservée. Un diagnostic prend la forme
`PRIVACY_NIR_DETECTED at $.records[0].metadata.identifier` et ne reproduit
jamais la valeur détectée. Aucun contenu brut n'est journalisé.

## Compatibilité conservée

Les signatures métier des cinq connecteurs, le pipeline A3, la fondation A2,
les frontières A1, les conversions et rapports sûrs sont conservés. Le
fail-closed Nibelis et l'anonymisation Kelio restent actifs. Aucune règle
juridique et aucun calcul de retraite ne sont ajoutés.

## Limites et hors périmètre

A4 ne constitue pas une conformité RGPD complète. Il ne traite ni contrôle
d'accès, authentification, hébergement, stockage chiffré, rapprochement métier
sensible, référentiel Kelio, normalisation des rapports, façade publique,
API, OCR, PDF, connexion Kelio/Nibelis, CNAV, CARSAT ou France Travail. Les
détecteurs restent volontairement prudents et centrés sur les structures
synthétiques du moteur.
