# Official Knowledge Gateway — LOT 1C — Catalogue priorisé

## Objet et garde-fous

Ce lot crée un catalogue descriptif unique de 53 sources et une feuille de route. Une présence au catalogue ne vaut ni autorisation d’accès, ni validation de licence, ni activation de connecteur. Toutes les entrées sont désactivées, en revue d’accès et de licence, sans mode d’accès autorisé. Aucun transport, téléchargement, scraping, contenu officiel ou CSSCT n’est créé.

La priorité Nexus exprime un ordre de consultation général. Elle ne remplace jamais le champ d’application ni l’autorité juridique. Le score de développement mesure l’intérêt de construire un connecteur; il ne mesure pas l’autorité du contenu.

## Audit du registre existant

Le registre opérationnel contenait 15 entrées : CNIL, INRS, ANACT, Ameli, Service-Public, URSSAF, Assurance retraite, Agirc-Arrco, Légifrance, JUDILIBRE, Code du travail numérique et quatre sources logiques du droit local. Légifrance, JUDILIBRE et Code du travail numérique correspondent à des connecteurs historiques hors du package Gateway. La CNIL reste une architecture sans réseau. Les identifiants spécialisés `service_public_local_law` et `dreets_grand_est_local_law` recouvrent partiellement des éditeurs plus larges; le catalogue conserve ces dépendances sans les confondre avec une source générale. Aucun statut existant n’autorise le réseau.

Les lacunes principales étaient DREAL/ICPE, INERIS/AIDA/ARIA, ECHA/GESTIS, autorités européennes, branche chimique, formation, protection sociale étendue et position institutionnelle de l’éditeur.

## Catalogue complet par importance

| Priorité | Sources cataloguées |
|---|---|
| `PRIORITY_0` | `ineos_internal_sources`, `alsace_moselle_local_law`, `alsace_moselle_health_regime` |
| `PRIORITY_1` | `legifrance`, `ccn_chimie`, `judilibre`, `eur_lex`, `cjeu`, `conseil_constitutionnel`, `conseil_etat`, `icpe_legal_sources` |
| `PRIORITY_2` | `dreets_grand_est`, `dreets_national`, `inspection_travail`, `ministere_travail`, `bulletin_officiel_travail`, `cnil`, `dreal_grand_est`, `dreal_national`, `edpb`, `eu_ai_act`, `ministere_transition_ecologique` |
| `PRIORITY_3` | `inrs`, `ineris`, `aida`, `aria`, `georisques`, `anact`, `assurance_maladie_risques_professionnels`, `anssi`, `echa`, `sante_publique_france`, `anses`, `base_icpe`, `oppbtp` |
| `PRIORITY_4` | `code_travail_numerique`, `service_public`, `ameli`, `assurance_maladie`, `urssaf`, `assurance_retraite`, `agirc_arrco`, `caf`, `france_competences`, `france_travail`, `rncp`, `cybermalveillance`, `data_gouv_fr`, `api_entreprise` |
| `PRIORITY_5` | `france_chimie`, `observatoire_chimie`, `opco_2i` |
| `PRIORITY_6` | `gestis` |

Les entrées internes et les textes applicables sont consultés en premier, sous réserve de leur champ. Une source technique de priorité inférieure peut être la meilleure référence factuelle sur une substance ou un risque précis.

## Classement d’autorité

- Normes et versions officielles : Légifrance, CCN Chimie publiée, EUR-Lex et prescriptions ICPE exactes, après contrôle de version et de champ.
- Jurisprudence : JUDILIBRE, CJUE, Conseil constitutionnel et Conseil d’État.
- Autorités et guides : DREETS, DREAL, ministères, CNIL et EDPB; un guide n’est jamais une loi.
- Prévention et références techniques : INRS, INERIS, AIDA, ARIA, ANACT, ANSES, ECHA, Géorisques et GESTIS selon la nature exacte du document.
- Informations pratiques et opérateurs : Code du travail numérique, Service-Public, Ameli, URSSAF, caisses de retraite et CAF.
- Informations institutionnelles : France Chimie, observatoire, OPCO et organismes de branche; leur position doit rester visible.

## Scores de développement

La fonction additionne huit critères bornés : autorité 25, utilité salarié 15, utilité représentants 15, Seveso 20, territoire 10, qualité 5, faisabilité 5 et licence 5. Les scores prioritaires calculés sont : Légifrance 81, DREAL Grand Est 76, INRS 75, DREETS Grand Est 73, AIDA 71, ECHA 70, INERIS 65, ARIA 61, France Chimie 37 et GESTIS 37.

DREAL obtient un score très élevé pour INEOS Sarralbe sans devenir une source primaire pour tout sujet. France Chimie reste utile mais de faible autorité. Légifrance conserve l’autorité maximale même si son connecteur historique existe.

## Vagues recommandées

- `WAVE_0` : Légifrance, JUDILIBRE, Code du travail numérique, étude CNIL et socle droit local.
- `WAVE_1` : DREAL Grand Est, INRS, DREETS Grand Est, AIDA, INERIS puis ARIA. Cet ordre prépare les connaissances nécessaires à un futur domaine CSSCT sans commencer ce domaine.
- `WAVE_2` : ANACT, Ameli, Assurance Maladie Risques professionnels, URSSAF et Service-Public.
- `WAVE_3` : ECHA, Géorisques, ANSSI, France Chimie, Observatoire et OPCO 2i.
- `WAVE_4` : Assurance retraite, Agirc-Arrco, France Compétences, CAF et GESTIS, puis compléments validés.

Le prochain lot recommandé est une étude d’accès séparée pour DREAL Grand Est ou INRS, précédée d’une validation explicite des licences, conditions d’usage, cache, citations et périmètre documentaire. Aucun connecteur n’est développé ici.

## INEOS Sarralbe et futur CSSCT

Le contexte chimique, Seveso et mosellan augmente la pertinence de DREAL Grand Est, ICPE/arrêtés, INRS, INERIS, AIDA, ARIA et ECHA. Une communication générale ne devient pas une prescription du site. Un retour d’accident ARIA n’est pas une preuve juridique. AIDA doit distinguer texte normatif et outil documentaire. GESTIS complète ECHA et INRS sans prévaloir sur le droit français ou européen applicable.

## France Chimie

France Chimie est une fédération d’employeurs, classée `employer_side_institution`, `institutional_information` et `PRIORITY_5`. Elle n’est ni une loi ni une source neutre. Toute citation doit identifier l’éditeur et sa position. Les données factuelles de branche doivent être séparées des positions patronales. Cette source ne prévaut jamais sur la loi, la CCN, un accord INEOS ou la jurisprudence.

## Relations et confusions à éviter

DREETS et DREAL Grand Est sont des instances régionales de leurs portails nationaux. Service-Public et Code du travail numérique expliquent pratiquement les textes Légifrance. AIDA documente la réglementation ICPE; ARIA documente les retours d’expérience. Légifrance porte les versions officielles des textes. France Chimie exprime une position patronale sur la branche. GESTIS complète ECHA. Aucune relation ne dit qu’une source institutionnelle remplace une norme juridique; les cycles `supersedes` sont interdits.

Les risques majeurs sont la confusion priorité/autorité, guide/loi, donnée technique/prescription, information pratique/texte opposable, donnée de branche/position patronale et score de développement/validité juridique.
