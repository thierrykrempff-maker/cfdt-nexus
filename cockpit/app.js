const appState = {
  activeView: "accueil",
  editingCaseId: null,
  cases: [
    {
      id: "DS-2026-001",
      title: "Entretien préalable - salarié A",
      type: "Discipline",
      status: "En cours",
      priority: "Haute",
      date: "2026-07-02",
      notes: "Contestation des faits. Témoins à identifier et convocation à relire.",
      documents: ["Convocation", "Planning 5x8", "Attestations"],
      archived: false,
    },
    {
      id: "DS-2026-002",
      title: "Question prime panier",
      type: "Paie",
      status: "À traiter",
      priority: "Moyenne",
      date: "2026-07-04",
      notes: "Comparer bulletin, accord applicable et règle de paie.",
      documents: ["Bulletin", "Accord interne"],
      archived: false,
    },
    {
      id: "DS-2026-003",
      title: "Signalement chaleur atelier",
      type: "Santé / Sécurité",
      status: "En cours",
      priority: "Haute",
      date: "2026-07-05",
      notes: "Préparer signalement CSSCT et vérifier les mesures de prévention.",
      documents: ["Photos", "Consignes sécurité"],
      archived: false,
    },
    {
      id: "DS-2026-004",
      title: "Demande modèle de courrier",
      type: "Communication",
      status: "Terminé",
      priority: "Basse",
      date: "2026-06-29",
      notes: "Trame remise au salarié pour demande d'explication.",
      documents: ["Modèle courrier"],
      archived: true,
    },
  ],
};

const metrics = [
  { label: "Dossiers actifs", value: "4", detail: "dont 2 prioritaires" },
  { label: "Actions ouvertes", value: "6", detail: "à traiter cette semaine" },
  { label: "Documents prêts", value: "12", detail: "modèles et sources" },
  { label: "Veille à relire", value: "5", detail: "articles en attente" },
];

const priorityActions = [
  { title: "Relire une convocation disciplinaire", detail: "Vérifier délais, assistance et faits reprochés." },
  { title: "Préparer un flash info", detail: "Sujet : prévention chaleur et droits des salariés." },
  { title: "Classer les accords", detail: "Séparer public, privé et confidentiel." },
];

const activities = [
  { title: "Cockpit V2 créé", detail: "Interface de bureau numérique statique." },
  { title: "Routeur d'Intelligence versionné", detail: "Module core disponible dans le dépôt." },
  { title: "Défenseur Syndical V1 ajouté", detail: "Méthode prudente pour dossiers sensibles." },
];

const watchTodayItems = [
  {
    title: "Santé sécurité",
    detail: "Exemple fictif de veille prévention à relire avant exploitation CSSCT.",
    source: "INRS",
    confidence: "Moyen",
  },
  {
    title: "Jurisprudence sociale",
    detail: "Signal fictif : rechercher la décision primaire avant toute analyse.",
    source: "Cour de cassation",
    confidence: "Faible",
  },
  {
    title: "Branche Chimie",
    detail: "Surveiller les évolutions IDCC 44 sur Légifrance et croiser avec les accords locaux.",
    source: "Légifrance",
    confidence: "Fort",
  },
];

const watchSources = [
  { name: "Légifrance", kind: "Source A", detail: "Textes, conventions collectives et jurisprudence." },
  { name: "FCE-CFDT", kind: "Source B", detail: "Positions fédérales Chimie Énergie." },
  { name: "INRS", kind: "Source B", detail: "Prévention, risques chimiques et santé sécurité." },
  { name: "France Chimie", kind: "Source B", detail: "Contexte branche et industrie chimique." },
  { name: "Sources spécialisées", kind: "Source C", detail: "Détection uniquement, source primaire obligatoire." },
];

const watchReviewItems = [
  { title: "BOSS", detail: "URL à vérifier manuellement avant activation du canal paie." },
  { title: "URSSAF", detail: "Accès automatique instable : ne pas activer sans contrôle humain." },
  { title: "Réseaux sociaux FCE-CFDT", detail: "Capturer les liens exacts depuis le site officiel avant registre." },
  { title: "Village de la Justice", detail: "Source proposée mais à valider avant surveillance." },
];

const watchValidatedItems = [
  { title: "Registre sources V1", detail: "Sources classées par niveau de confiance A / B / C / D." },
  { title: "Canaux de veille V1", detail: "13 canaux prévus : droit, CSE, CSSCT, paie, Chimie, CFDT et industrie." },
  { title: "Règles validation V1", detail: "Publication automatique interdite ; validation Thierry obligatoire." },
];

const libraryDocuments = [
  {
    title: "Convention Chimie - classifications",
    description: "Repère pour classifications, minima et évolution professionnelle.",
    category: "Convention Chimie",
    keywords: ["classification", "minima", "branche"],
    date: "2026-07-01",
    version: "À vérifier",
    level: "Privé",
  },
  {
    title: "Accords INEOS - index",
    description: "Emplacement prévu pour les accords disponibles et validés.",
    category: "Accords INEOS",
    keywords: ["accord", "ineos", "site"],
    date: "2026-07-01",
    version: "Brouillon",
    level: "Confidentiel",
  },
  {
    title: "Règlement intérieur",
    description: "Règles disciplinaires, sécurité et procédure interne.",
    category: "Règlement intérieur",
    keywords: ["discipline", "sécurité", "procédure"],
    date: "2026-07-01",
    version: "À importer",
    level: "Privé",
  },
  {
    title: "Modèle - contestation prudente",
    description: "Courrier factuel distinguant faits, preuves et demandes.",
    category: "Modèles",
    keywords: ["courrier", "contestation", "discipline"],
    date: "2026-07-01",
    version: "V1",
    level: "Public",
  },
  {
    title: "Jurisprudence - discipline",
    description: "Zone prévue pour décisions vérifiées et sourcées.",
    category: "Jurisprudence",
    keywords: ["sanction", "preuve", "entretien"],
    date: "2026-07-01",
    version: "À vérifier",
    level: "Privé",
  },
  {
    title: "Documentation CFDT",
    description: "Repères publics et pédagogiques pour les salariés.",
    category: "Documentation CFDT",
    keywords: ["cfdt", "droits", "salariés"],
    date: "2026-07-01",
    version: "V1",
    level: "Public",
  },
];

const templates = [
  { type: "Article", description: "Structure longue : contexte, analyse, position CFDT, action." },
  { type: "Tract", description: "Message court, direct, imprimable, orienté terrain." },
  { type: "Flash Info", description: "Information rapide et vérifiée pour diffusion régulière." },
  { type: "Courrier", description: "Trame prudente, factuelle et non agressive." },
  { type: "Publication Web", description: "Version SEO, mobile et accessible pour le site." },
];

const integrations = [
  { name: "Google Analytics", metric: "1 248", detail: "visiteurs fictifs", progress: 78 },
  { name: "Search Console", metric: "34", detail: "requêtes fictives", progress: 44 },
  { name: "GitHub", metric: "18", detail: "commits fictifs", progress: 66 },
  { name: "n8n", metric: "5", detail: "workflows prévus", progress: 35 },
];

const settings = [
  { name: "Version", detail: "Cockpit CFDT Nexus V2 statique", status: "Actif" },
  { name: "GitHub", detail: "Prévu pour commits, issues, automatisations et suivi projet.", status: "À connecter" },
  { name: "Hostinger", detail: "Prévu pour statut de déploiement et publication.", status: "À connecter" },
  { name: "Google Analytics", detail: "Prévu pour statistiques du site public.", status: "À connecter" },
  { name: "Google Search Console", detail: "Prévu pour SEO, indexation et requêtes.", status: "À connecter" },
  { name: "Automatisations", detail: "Prévu pour n8n, veille et tâches répétitives.", status: "À concevoir" },
  { name: "Configuration IA", detail: "Prévu pour GPT CFDT Nexus, routeur et agents.", status: "À connecter" },
];

const selectors = {
  navItems: document.querySelectorAll("[data-nav-target]"),
  views: document.querySelectorAll(".view"),
  sidebar: document.querySelector(".sidebar"),
  menuToggle: document.querySelector(".menu-toggle"),
  todayLabel: document.querySelector("#today-label"),
  homeMetrics: document.querySelector("#home-metrics"),
  priorityActions: document.querySelector("#priority-actions"),
  activityList: document.querySelector("#activity-list"),
  caseForm: document.querySelector("#case-form"),
  caseReset: document.querySelector("#case-reset"),
  caseFormTitle: document.querySelector("#case-form-title"),
  caseList: document.querySelector("#case-list"),
  caseCount: document.querySelector("#case-count"),
  caseSearch: document.querySelector("#case-search"),
  caseStatusFilter: document.querySelector("#case-status-filter"),
  casePriorityFilter: document.querySelector("#case-priority-filter"),
  chatForm: document.querySelector("#chat-form"),
  chatInput: document.querySelector("#chat-input"),
  chatLog: document.querySelector("#chat-log"),
  presetButtons: document.querySelectorAll("[data-preset]"),
  librarySearch: document.querySelector("#library-search"),
  libraryCategoryFilter: document.querySelector("#library-category-filter"),
  resourceGrid: document.querySelector("#resource-grid"),
  templateGrid: document.querySelector("#template-grid"),
  contentForm: document.querySelector("#content-form"),
  generatedOutput: document.querySelector("#generated-output"),
  integrationGrid: document.querySelector("#integration-grid"),
  settingsList: document.querySelector("#settings-list"),
  globalSearch: document.querySelector("#global-search"),
  watchSourceCount: document.querySelector("#watch-source-count"),
  watchReviewCount: document.querySelector("#watch-review-count"),
  watchTodayList: document.querySelector("#watch-today-list"),
  watchSourcesList: document.querySelector("#watch-sources-list"),
  watchReviewList: document.querySelector("#watch-review-list"),
  watchValidatedList: document.querySelector("#watch-validated-list"),
};

const formatDate = (value) =>
  new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(value));

const getPriorityClass = (priority) => {
  if (priority === "Haute") return "priority-high";
  if (priority === "Moyenne") return "priority-medium";
  return "priority-low";
};

// Point d'extension futur : remplacer ce state local par une API sécurisée.
const renderHome = () => {
  selectors.todayLabel.textContent = new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date());

  selectors.homeMetrics.innerHTML = metrics
    .map((metric) => `<article class="metric-card"><span>${metric.label}</span><strong>${metric.value}</strong><small>${metric.detail}</small></article>`)
    .join("");

  selectors.priorityActions.innerHTML = priorityActions
    .map((item) => `<article class="task-item"><strong>${item.title}</strong><span>${item.detail}</span></article>`)
    .join("");

  selectors.activityList.innerHTML = activities
    .map((item) => `<article class="activity-item"><strong>${item.title}</strong><span>${item.detail}</span></article>`)
    .join("");
};

const showView = (targetId) => {
  appState.activeView = targetId;

  selectors.views.forEach((view) => {
    view.classList.toggle("view--active", view.id === targetId);
  });

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("nav-item--active", item.dataset.navTarget === targetId);
  });

  selectors.sidebar.classList.remove("sidebar--open");
  selectors.menuToggle?.setAttribute("aria-expanded", "false");
};

const getFilteredCases = () => {
  const query = selectors.caseSearch.value.trim().toLowerCase();
  const status = selectors.caseStatusFilter.value;
  const priority = selectors.casePriorityFilter.value;

  return appState.cases.filter((item) => {
    const searchable = [item.id, item.title, item.type, item.status, item.priority, item.notes, item.documents.join(" ")].join(" ").toLowerCase();
    const matchesQuery = !query || searchable.includes(query);
    const displayedStatus = item.archived ? "Archivé" : item.status;
    const matchesStatus = status === "Tous" || displayedStatus === status;
    const matchesPriority = priority === "Toutes" || item.priority === priority;
    return matchesQuery && matchesStatus && matchesPriority;
  });
};

const renderCases = () => {
  const cases = getFilteredCases();
  selectors.caseCount.textContent = `${cases.length} dossier${cases.length > 1 ? "s" : ""}`;

  if (!cases.length) {
    selectors.caseList.innerHTML = `<article class="case-card"><p>Aucun dossier ne correspond aux filtres.</p></article>`;
    return;
  }

  selectors.caseList.innerHTML = cases
    .map(
      (item) => `
        <article class="case-card">
          <div class="case-card__top">
            <div>
              <span class="case-chip">${item.id}</span>
              <h3>${item.title}</h3>
            </div>
            <span class="case-chip ${getPriorityClass(item.priority)}">${item.priority}</span>
          </div>
          <p>${item.notes || "Aucune note renseignée."}</p>
          <div class="case-card__meta">
            <span class="case-chip">${item.type}</span>
            <span class="case-chip">${item.archived ? "Archivé" : item.status}</span>
            <span class="case-chip">${formatDate(item.date)}</span>
            <span class="case-chip">${item.documents.length} document${item.documents.length > 1 ? "s" : ""}</span>
          </div>
          <div class="case-card__footer">
            <small>Documents : ${item.documents.join(", ") || "à compléter"}</small>
            <div class="case-card__actions">
              <button type="button" data-edit-case="${item.id}">Modifier</button>
              <button type="button" data-archive-case="${item.id}">${item.archived ? "Restaurer" : "Archiver"}</button>
            </div>
          </div>
        </article>
      `
    )
    .join("");
};

const resetCaseForm = () => {
  appState.editingCaseId = null;
  selectors.caseForm.reset();
  selectors.caseForm.caseId.value = "";
  selectors.caseForm.date.value = new Date().toISOString().slice(0, 10);
  selectors.caseFormTitle.textContent = "Créer un dossier";
};

const submitCase = (event) => {
  event.preventDefault();
  const formData = new FormData(selectors.caseForm);
  const documents = formData
    .get("documents")
    .toString()
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const payload = {
    id: formData.get("caseId").toString() || `DS-2026-${String(appState.cases.length + 1).padStart(3, "0")}`,
    title: formData.get("title").toString().trim(),
    type: formData.get("type").toString(),
    status: formData.get("status").toString(),
    priority: formData.get("priority").toString(),
    date: formData.get("date").toString(),
    notes: formData.get("notes").toString().trim(),
    documents,
    archived: false,
  };

  const existingIndex = appState.cases.findIndex((item) => item.id === payload.id);
  if (existingIndex >= 0) {
    payload.archived = appState.cases[existingIndex].archived;
    appState.cases.splice(existingIndex, 1, payload);
  } else {
    appState.cases.unshift(payload);
  }

  resetCaseForm();
  renderCases();
};

const handleCaseActions = (event) => {
  const editId = event.target.dataset.editCase;
  const archiveId = event.target.dataset.archiveCase;

  if (editId) {
    const item = appState.cases.find((caseItem) => caseItem.id === editId);
    if (!item) return;
    appState.editingCaseId = editId;
    selectors.caseForm.caseId.value = item.id;
    selectors.caseForm.title.value = item.title;
    selectors.caseForm.type.value = item.type;
    selectors.caseForm.status.value = item.status;
    selectors.caseForm.priority.value = item.priority;
    selectors.caseForm.date.value = item.date;
    selectors.caseForm.notes.value = item.notes;
    selectors.caseForm.documents.value = item.documents.join(", ");
    selectors.caseFormTitle.textContent = `Modifier ${item.id}`;
    selectors.caseForm.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (archiveId) {
    const item = appState.cases.find((caseItem) => caseItem.id === archiveId);
    if (!item) return;
    item.archived = !item.archived;
    renderCases();
  }
};

const renderLibrary = () => {
  const query = selectors.librarySearch.value.trim().toLowerCase();
  const category = selectors.libraryCategoryFilter.value;

  const filtered = libraryDocuments.filter((item) => {
    const searchable = [item.title, item.description, item.category, item.keywords.join(" "), item.version, item.level].join(" ").toLowerCase();
    return (!query || searchable.includes(query)) && (category === "Toutes" || item.category === category);
  });

  selectors.resourceGrid.innerHTML = filtered
    .map((item) => {
      const levelClass = item.level === "Confidentiel" ? "level-confidential" : item.level === "Privé" ? "level-private" : "";
      return `
        <article class="resource-card">
          <span class="resource-tag">${item.category}</span>
          <h3>${item.title}</h3>
          <p>${item.description}</p>
          <div class="resource-card__meta">
            <span class="level-badge ${levelClass}">${item.level}</span>
            <span class="level-badge">${item.version}</span>
            <span class="level-badge">${formatDate(item.date)}</span>
          </div>
          <small>Mots-clés : ${item.keywords.join(", ")}</small>
        </article>
      `;
    })
    .join("");
};

const renderWatch = () => {
  selectors.watchSourceCount.textContent = String(watchSources.length);
  selectors.watchReviewCount.textContent = String(watchReviewItems.length);

  selectors.watchTodayList.innerHTML = watchTodayItems
    .map(
      (item) => `
        <article class="watch-item">
          <span class="badge">${item.source}</span>
          <h4>${item.title}</h4>
          <p>${item.detail}</p>
          <small>Confiance : ${item.confidence}</small>
        </article>
      `
    )
    .join("");

  selectors.watchSourcesList.innerHTML = watchSources
    .map(
      (item) => `
        <article class="watch-item">
          <span class="badge">${item.kind}</span>
          <h4>${item.name}</h4>
          <p>${item.detail}</p>
        </article>
      `
    )
    .join("");

  selectors.watchReviewList.innerHTML = watchReviewItems
    .map(
      (item) => `
        <article class="watch-item watch-item--warning">
          <span class="badge">À vérifier</span>
          <h4>${item.title}</h4>
          <p>${item.detail}</p>
        </article>
      `
    )
    .join("");

  selectors.watchValidatedList.innerHTML = watchValidatedItems
    .map(
      (item) => `
        <article class="watch-item watch-item--valid">
          <span class="badge">Validé</span>
          <h4>${item.title}</h4>
          <p>${item.detail}</p>
        </article>
      `
    )
    .join("");
};

const renderTemplates = () => {
  selectors.templateGrid.innerHTML = templates
    .map(
      (item) => `
        <article class="template-card">
          <h3>${item.type}</h3>
          <p>${item.description}</p>
          <button type="button" data-template-type="${item.type}">Utiliser ce modèle</button>
        </article>
      `
    )
    .join("");
};

const generateContent = (event) => {
  event.preventDefault();
  const data = new FormData(selectors.contentForm);
  const type = data.get("contentType").toString();
  const topic = data.get("topic").toString().trim() || "sujet à préciser";
  const audience = data.get("audience").toString().trim() || "salariés concernés";

  selectors.generatedOutput.value = [
    `${type} - ${topic}`,
    "",
    `Public : ${audience}`,
    "",
    "1. Contexte",
    "2. Ce qu'il faut comprendre",
    "3. Position CFDT",
    "4. Points utiles aux salariés",
    "5. Action proposée / contact",
    "",
    "À vérifier avant diffusion : faits, sources, confidentialité, ton et validation Thierry.",
  ].join("\n");
};

const renderIntegrations = () => {
  selectors.integrationGrid.innerHTML = integrations
    .map(
      (item) => `
        <article class="integration-card">
          <span>${item.name}</span>
          <strong>${item.metric}</strong>
          <small>${item.detail}</small>
          <div class="progress"><span style="width: ${item.progress}%"></span></div>
          <span class="badge">Données fictives</span>
        </article>
      `
    )
    .join("");
};

const renderSettings = () => {
  selectors.settingsList.innerHTML = settings
    .map(
      (item) => `
        <article class="settings-row">
          <div>
            <strong>${item.name}</strong>
            <small>${item.detail}</small>
          </div>
          <span class="badge">${item.status}</span>
        </article>
      `
    )
    .join("");
};

const addMessage = (content, type = "assistant") => {
  const message = document.createElement("div");
  message.className = `message message--${type}`;
  message.textContent = content;
  selectors.chatLog.appendChild(message);
  selectors.chatLog.scrollTop = selectors.chatLog.scrollHeight;
};

// Simulation V2 : ce bloc sera remplacé par l'appel au GPT CFDT Nexus.
const simulateAssistant = (message) => {
  const normalized = message.toLowerCase();

  if (normalized.includes("codex") || normalized.includes("site")) {
    return "Réponse simulée : je préparerais un prompt Codex avec objectif, fichiers ciblés, contraintes, vérifications et commit attendu.";
  }

  if (normalized.includes("cse") || normalized.includes("nao")) {
    return "Réponse simulée : je structurerais la préparation avec contexte, questions, pièces à demander, arguments CFDT et points à valider.";
  }

  if (normalized.includes("article") || normalized.includes("tract") || normalized.includes("flash")) {
    return "Réponse simulée : je proposerais un contenu clair avec titre, résumé, message principal, preuves à vérifier et version courte.";
  }

  return "Réponse simulée : je commence par qualifier la situation, poser les questions manquantes, puis distinguer faits, preuves, textes, analyse et stratégie prudente.";
};

const handleChatSubmit = (event) => {
  event.preventDefault();
  const message = selectors.chatInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  selectors.chatInput.value = "";
  setTimeout(() => addMessage(simulateAssistant(message)), 250);
};

const initializeEvents = () => {
  selectors.navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const target = item.dataset.navTarget;
      if (target) showView(target);

      if (item.dataset.preset) {
        selectors.chatInput.value = item.dataset.preset;
      }
    });
  });

  selectors.menuToggle.addEventListener("click", () => {
    const isOpen = !selectors.sidebar.classList.contains("sidebar--open");
    selectors.sidebar.classList.toggle("sidebar--open", isOpen);
    selectors.menuToggle.setAttribute("aria-expanded", String(isOpen));
  });

  selectors.caseForm.addEventListener("submit", submitCase);
  selectors.caseReset.addEventListener("click", resetCaseForm);
  selectors.caseList.addEventListener("click", handleCaseActions);
  selectors.caseSearch.addEventListener("input", renderCases);
  selectors.caseStatusFilter.addEventListener("change", renderCases);
  selectors.casePriorityFilter.addEventListener("change", renderCases);
  selectors.librarySearch.addEventListener("input", renderLibrary);
  selectors.libraryCategoryFilter.addEventListener("change", renderLibrary);
  selectors.contentForm.addEventListener("submit", generateContent);
  selectors.chatForm.addEventListener("submit", handleChatSubmit);

  selectors.presetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      selectors.chatInput.value = button.dataset.preset;
      showView("assistant");
      selectors.chatInput.focus();
    });
  });

  selectors.templateGrid.addEventListener("click", (event) => {
    const templateType = event.target.dataset.templateType;
    if (!templateType) return;
    selectors.contentForm.contentType.value = templateType;
    selectors.contentForm.topic.focus();
  });
};

const init = () => {
  resetCaseForm();
  renderHome();
  renderCases();
  renderLibrary();
  renderWatch();
  renderTemplates();
  renderIntegrations();
  renderSettings();
  initializeEvents();
};

init();
