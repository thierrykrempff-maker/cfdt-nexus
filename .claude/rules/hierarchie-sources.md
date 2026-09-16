# Règle — Hiérarchie des sources

Ordre par défaut pour toute question concernant un salarié INEOS Sarralbe :

1. accords d'entreprise INEOS applicables ;
2. Convention collective nationale des industries chimiques (IDCC 44) ;
3. Code du travail ;
4. jurisprudence pertinente ;
5. PV CSE et historique interne lorsqu'ils apportent un élément utile.

Cet ordre est celui déjà défini dans `agents/core/CFDT_NEXUS_CORE_PROMPT_V1.md` et
`agents/core/ROUTEUR_INTELLIGENCE_V1.md`. Cette règle ne fait qu'en rappeler l'application
pratique pour Claude ; la méthode complète de croisement des sources (qualifier les faits,
établir le droit applicable, croiser les sources, construire la défense) est décrite dans
`agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md`, qui prévaut en cas de différence.

## Points de vigilance

- Une jurisprudence ne doit jamais devenir artificiellement la source principale lorsqu'un
  accord, la convention collective ou le Code du travail répond déjà directement à la question.
- Ne jamais citer un article, un accord ou une décision absent des sources réellement
  disponibles dans Nexus (`knowledge-base/`, résultats de connecteurs, documents fournis par
  Thierry).
- Toujours indiquer explicitement quand une couche de sources n'a rien fourni de pertinent,
  plutôt que de passer sous silence l'absence de résultat.
- En cas de contradiction entre deux sources, l'expliquer clairement plutôt que de la résoudre
  silencieusement en faveur d'une seule.
