# A8 — Clôture du diagnostic Privacy Gate

Date : 2026-07-21

Branche : `retirement-penibility-final-closure-audit`

## P1 initial

L’audit de clôture démontrait qu’une clé de mapping sensible pouvait être
reproduite dans un diagnostic. Le chemin était :

1. `PrivacyDetector._walk()` parcourait un mapping ;
2. `child_path = f"{path}.{key}"` conservait la clé réelle ;
3. un `PrivacyFinding` conservait ce chemin ;
4. `RetirementPrivacyGate.sanitize_diagnostic()` concaténait le code et
   `field_path`.

Une clé synthétique au format NIR associée à un type inconnu produisait ainsi
un diagnostic contenant la clé.

## Correction ciblée

Les chemins des mappings et dataclasses utilisent désormais uniquement des
positions techniques neutres :

- `$.entry[index]` pour les mappings ;
- `$.field[index]` pour les dataclasses ;
- les indices historiques des séquences restent inchangés.

Le nom réel du champ continue d’être transmis séparément au détecteur afin de
préserver exactement ses règles de classification. Il n’est jamais placé dans
le chemin exposé.

`sanitize_diagnostic()` n’utilise plus `field_path`. Il produit uniquement :

- le code stable ;
- la catégorie ;
- la sévérité.

Exemple neutre :

```text
PRIVACY_NIR_DETECTED category=NIR severity=CRITICAL
```

Aucune valeur, clé, identité, identifiant RH, NIR, IBAN, RIB, adresse,
coordonnée ou nom de variable sensible n’est rendu.

## Comportement conservé

La détection et les statuts ne changent pas :

- données sûres : `SAFE` ;
- revue nécessaire : `SAFE_WITH_WARNINGS` ;
- donnée interdite : `BLOCKED` ;
- structure non inspectable : `INSPECTION_ERROR`.

Le Privacy Gate reste fail-closed. Aucun connecteur, contrat, pipeline,
référentiel, moteur, règle métier, P2 ou P3 n’est modifié.

## Tests

`tests/test_privacy_gate_no_sensitive_diagnostics.py` couvre :

- NIR, IBAN et RIB ;
- identifiant interne ;
- courriel, téléphone et adresse ;
- clés de mapping sensibles ;
- noms de variables sensibles ;
- défense du formateur contre un `field_path` non fiable ;
- format stable limité au code, à la catégorie et à la sévérité ;
- exceptions fail-closed sans écho ;
- décisions Privacy Gate historiques inchangées.

Résultats :

- nouveaux tests : 21/21 ;
- tests Active Privacy historiques : 44/44 ;
- ensemble Retraite & Pénibilité : 503/503.

## Réaudit ciblé

Le scénario initial a été rejoué. La clé sensible est absente du diagnostic,
de l’exception et de la représentation du constat. Le code
`PRIVACY_UNSUPPORTED_TYPE`, la catégorie et la sévérité restent présents et
le statut demeure `INSPECTION_ERROR`.

P1 restant : **RESOLVED**.

P0 finaux : **0**.

P1 finaux : **0**.

Recommandation finale : **READY**.
