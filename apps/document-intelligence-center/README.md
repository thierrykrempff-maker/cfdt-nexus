# Document Intelligence Center - Connexion Bible Accords V1

## Objectif

Le Document Intelligence Center prépare l'analyse locale d'un document privé ou d'un projet présenté à Thierry.

Dans cette V1, il ne contient pas encore d'interface complète. Il s'appuie sur le service local :

```text
automation/scripts/nexus_bible_bridge.py
```

Ce service appelle réellement le moteur de recherche de la Bible Accords Sarralbe dans :

```text
automation/scripts/agreements_bible.py
```

Le scoring Bible Accords reste la référence unique.

## Flux

```text
Document local
        ↓
Extraction locale du texte
        ↓
Détection du sujet
        ↓
Génération de requêtes métier
        ↓
Bible Accords Sarralbe
        ↓
Sources document + page + article
        ↓
Analyse comparative
        ↓
Questions / relances / documents manquants
```

## Commandes locales

Diagnostic :

```powershell
python automation/scripts/nexus_bible_bridge.py diagnose
```

Analyser un document local :

```powershell
python automation/scripts/nexus_bible_bridge.py analyze-document --path "C:\chemin\document.pdf"
```

Analyser un point CSE fictif ou préparatoire :

```powershell
python automation/scripts/nexus_bible_bridge.py analyze-cse --subject "La direction souhaite modifier le repos entre deux postes pour les salariés en 5x8."
```

Tester les scénarios V1 :

```powershell
python automation/scripts/nexus_bible_bridge.py run-scenarios
```

## Sortie documentaire

Chaque analyse produit localement :

- sujet principal ;
- ce que le document semble vouloir modifier ou présenter ;
- textes locaux potentiellement concernés ;
- sources avec document, page, article si disponible, score et niveau de confiance ;
- points de comparaison ;
- points à vérifier.

Les rapports privés sont écrits dans :

```text
local-index/agreements/integration/
```

Ce dossier est ignoré par Git.

## Principe de prudence

L'analyse automatique constitue une aide à la préparation. Vérifier les textes cités, leur date, leur champ d'application et leur articulation avec les normes supérieures avant toute position définitive en CSE, CSSCT ou négociation.

Ne jamais interpréter l'absence de résultat comme l'absence de droit.

## Limites V1

Non connecté dans ce sprint :

- Code du travail externe ;
- jurisprudence ;
- API cloud ;
- modèle IA externe ;
- PV CSE réels ;
- BDESE réelle.
