const form = document.getElementById("questionForm");
const queryInput = document.getElementById("questionInput");
const sourceLimitInput = document.getElementById("sourceLimitInput");
const statusPill = document.getElementById("statusPill");
const emptyState = document.getElementById("emptyState");
const resultContent = document.getElementById("resultContent");
const resultQuestion = document.getElementById("resultQuestion");
const confidenceValue = document.getElementById("confidenceValue");
const shortAnswer = document.getElementById("shortAnswer");
const workingPosition = document.getElementById("workingPosition");
const sourcesList = document.getElementById("sourcesList");
const findingsList = document.getElementById("findingsList");
const documentsList = document.getElementById("documentsList");
const questionsList = document.getElementById("questionsList");
const warningsList = document.getElementById("warningsList");
const domainsList = document.getElementById("domainsList");
const expertsList = document.getElementById("expertsList");
const issueGroupsPanel = document.getElementById("issueGroupsPanel");
const issueGroups = document.getElementById("issueGroups");
const expertPanel = document.getElementById("expertPanel");
const expertContent = document.getElementById("expertContent");
const expertConfidence = document.getElementById("expertConfidence");
const generateReportButton = document.getElementById("generateReportButton");
const copyReportButton = document.getElementById("copyReportButton");
const downloadReportButton = document.getElementById("downloadReportButton");
const reportOutput = document.getElementById("reportOutput");
const caseScenarioSelect = document.getElementById("caseScenarioSelect");
const loadCaseButton = document.getElementById("loadCaseButton");
const caseError = document.getElementById("caseError");
const caseContent = document.getElementById("caseContent");
const caseHeaderTitle = document.getElementById("caseHeaderTitle");
const caseHeaderMeta = document.getElementById("caseHeaderMeta");
const caseStatus = document.getElementById("caseStatus");
const caseConfidentiality = document.getElementById("caseConfidentiality");
const caseConfidence = document.getElementById("caseConfidence");
const pipelineSteps = document.getElementById("pipelineSteps");
const completenessRate = document.getElementById("completenessRate");
const completenessNotice = document.getElementById("completenessNotice");
const documentSummary = document.getElementById("documentSummary");
const caseDiagnosticSummary = document.getElementById("caseDiagnosticSummary");
const employeeViewButton = document.getElementById("employeeViewButton");
const expertViewButton = document.getElementById("expertViewButton");
const caseViewDescription = document.getElementById("caseViewDescription");
const caseReportView = document.getElementById("caseReportView");
const homeView = document.getElementById("homeView");
const wizardView = document.getElementById("wizardView");
const resultView = document.getElementById("resultView");
const analysisState = document.getElementById("analysisState");
const settingsButton = document.getElementById("settingsButton");
const settingsPanel = document.getElementById("settingsPanel");
const closeSettingsButton = document.getElementById("closeSettingsButton");
const runtimeStatus = document.getElementById("runtimeStatus");
const runtimeStatusLabel = document.getElementById("runtimeStatusLabel");
const assistantStatusValue = document.getElementById("assistantStatusValue");
const payrollStatusValue = document.getElementById("payrollStatusValue");
const wizardWorkspaceLabel = document.getElementById("wizardWorkspaceLabel");
const wizardTitle = document.getElementById("wizardTitle");
const wizardDescription = document.getElementById("wizardDescription");
const wizardProgress = document.getElementById("wizardProgress");
const situationChoices = document.getElementById("situationChoices");
const contextFields = document.getElementById("contextFields");
const documentChoices = document.getElementById("documentChoices");
const outcomeChoices = document.getElementById("outcomeChoices");
const previousStepButton = document.getElementById("previousStepButton");
const nextStepButton = document.getElementById("nextStepButton");
const analyzeButton = document.getElementById("analyzeButton");
const wizardError = document.getElementById("wizardError");
const confidentialityLevel = document.getElementById("confidentialityLevel");
const payrollWarning = document.getElementById("payrollWarning");
const resultModeNotice = document.getElementById("resultModeNotice");
const editInformationButton = document.getElementById("editInformationButton");
const addDocumentButton = document.getElementById("addDocumentButton");
const newAnalysisButton = document.getElementById("newAnalysisButton");
const secondaryMessage = document.getElementById("secondaryMessage");
const disciplinaryPanel = document.getElementById("disciplinaryPanel");
const disciplinaryContent = document.getElementById("disciplinaryContent");
const generalFollowupGrid = document.getElementById("generalFollowupGrid");
const employeeInterview = document.getElementById("employeeInterview");
const interviewSaveActions = document.getElementById("interviewSaveActions");
const downloadInterviewButton = document.getElementById("downloadInterviewButton");
const interviewSaveStatus = document.getElementById("interviewSaveStatus");

let currentPayload = null;
let currentReportMarkdown = "";
let currentCasePayload = null;
let currentCaseView = "employee";
let currentWorkspace = null;
let currentEmployeePath = null;
let currentWizardStep = 1;
let selectedSituation = "";
let selectedOutcome = "";
let sessionHistoryCount = 0;

const ANALYZE_TIMEOUT_MS = 190000;
const SERVER_UNAVAILABLE_MESSAGE =
  "Le serveur Nexus local ne répond pas. Relancez start-nexus-local.bat puis ouvrez http://127.0.0.1:8765/";
const ANALYZE_TIMEOUT_MESSAGE =
  "Le délai d’analyse est dépassé. Vérifiez que le serveur Nexus est toujours actif puis réessayez.";
const INVALID_SERVER_RESPONSE_MESSAGE =
  "Le serveur Nexus a renvoyé une réponse invalide";

class NexusRequestError extends Error {
  constructor(kind, message, status = null) {
    super(message);
    this.name = "NexusRequestError";
    this.kind = kind;
    this.status = status;
  }
}

function parseNexusResponse(rawBody) {
  try {
    return JSON.parse(rawBody);
  } catch (_error) {
    return null;
  }
}

function httpErrorMessage(response, payload) {
  const serverMessage =
    payload && typeof payload.error === "string" ? payload.error.trim() : "";
  const fallback =
    response.status >= 500
      ? "Une erreur interne Nexus est survenue."
      : "La requête a été refusée par le serveur Nexus.";
  return `Erreur HTTP ${response.status} — ${serverMessage || fallback}`;
}

async function requestNexusAnalysis(requestPayload, timeoutMs = ANALYZE_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  let response;

  try {
    response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload),
      signal: controller.signal
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new NexusRequestError("timeout", ANALYZE_TIMEOUT_MESSAGE);
    }
    throw new NexusRequestError("network", SERVER_UNAVAILABLE_MESSAGE);
  } finally {
    window.clearTimeout(timeoutId);
  }

  let rawBody;
  try {
    rawBody = await response.text();
  } catch (_error) {
    throw new NexusRequestError("network", SERVER_UNAVAILABLE_MESSAGE);
  }
  const payload = parseNexusResponse(rawBody);

  if (!response.ok) {
    throw new NexusRequestError(
      "http",
      httpErrorMessage(response, payload),
      response.status
    );
  }
  if (!payload) {
    throw new NexusRequestError("invalid_json", INVALID_SERVER_RESPONSE_MESSAGE);
  }
  if (!payload.ok) {
    const businessMessage =
      typeof payload.error === "string" && payload.error.trim()
        ? payload.error.trim()
        : "Nexus n’a pas pu traiter cette analyse.";
    throw new NexusRequestError("business", businessMessage);
  }
  return payload;
}

const examples = [
  "classification",
  "Un salarie en 5x8 peut-il assister a une reunion du CSE pendant son repos, et comment ce temps doit-il etre traite ?",
  "Un salarie d'astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste : quels sont ses droits en matiere de repos et comment l'intervention doit-elle apparaitre sur la paie ?",
  "Je pense qu'il manque des heures de nuit et une majoration dimanche sur mon bulletin. Que faut-il controler ?"
];

queryInput.value = "";

const workspaceDefinitions = {
  employee: {
    label: "Questions salariés",
    title: "Analyser une situation salarié",
    description: "Décrivez les faits utiles sans qualifier vous-même la situation juridiquement.",
    situations: [
      ["changement-poste", "Changement de poste"],
      ["horaires", "Horaires"],
      ["discipline", "Discipline"],
      ["temps-travail", "Temps de travail"],
      ["paie", "Paie"],
      ["discrimination", "Harcèlement ou discrimination"],
      ["maladie", "Maladie ou absence"],
      ["accident-travail", "Accident du travail"],
      ["inaptitude", "Inaptitude"],
      ["autre", "Autre question individuelle"]
    ],
    documents: ["Contrat", "Avenant", "Fiche de poste", "Planning", "Bulletin de paie", "Courrier", "Convocation", "Accord", "Document administratif minimal", "Autre"],
    outcomes: ["Comprendre la situation", "Préparer un entretien", "Préparer un courrier", "Identifier les preuves", "Préparer une contestation", "Vérifier la paie", "Autre"],
    context: "employee"
  },
  cse: {
    label: "CSE",
    title: "Préparer une action CSE",
    description: "Précisez le sujet collectif, le calendrier et les documents déjà reçus.",
    situations: [
      ["reunion", "Préparer une réunion"],
      ["ordre-du-jour", "Ordre du jour"],
      ["consultation", "Consultation"],
      ["reorganisation", "Réorganisation"],
      ["documents", "Demander des documents"],
      ["avis", "Préparer un avis"],
      ["resolution", "Préparer une résolution"],
      ["engagement", "Suivre un engagement"],
      ["alerte", "Étudier une alerte"],
      ["expertise", "Préparer une expertise"],
      ["ancien-pv", "Rechercher un ancien PV"],
      ["autre", "Autre besoin CSE"]
    ],
    documents: ["Projet de la direction", "Ordre du jour", "Documents reçus", "Ancien PV", "Accord", "Courrier", "Données économiques agrégées", "Autre"],
    outcomes: ["Poser des questions", "Demander des documents", "Préparer un avis", "Préparer une résolution", "Analyser une consultation", "Rechercher un précédent", "Préparer une action collective"],
    context: "cse"
  },
  negotiation: {
    label: "Négociations et accords",
    title: "Préparer une négociation",
    description: "Nexus recherche d’abord les accords et sources disponibles avant de mobiliser d’autres outils.",
    situations: [
      ["rechercher-clause", "Rechercher une clause"],
      ["analyser-accord", "Analyser un accord"],
      ["comparer-accords", "Comparer des accords"],
      ["preparer-negociation", "Préparer une négociation"],
      ["projet-accord", "Analyser un projet d’accord"],
      ["revendications", "Préparer des revendications"],
      ["engagement", "Suivre un engagement"]
    ],
    documents: ["Accord actuel", "Projet de la direction", "Anciennes versions", "PV ou compte rendu", "Convention collective", "Aucun document", "Autre"],
    outcomes: ["Comprendre les règles existantes", "Comparer les positions", "Construire des revendications", "Préparer la réunion paritaire", "Identifier les points de vigilance"],
    context: "negotiation"
  },
  payroll: {
    label: "Paie et rémunération",
    title: "Analyser une situation de paie",
    description: "Décrivez l’écart observé. Aucun taux ni calcul ne sera inventé.",
    situations: [
      ["heures-supplementaires", "Heures supplémentaires"],
      ["nuit", "Travail de nuit"],
      ["dimanche", "Dimanche"],
      ["jour-ferie", "Jour férié"],
      ["prime-poste", "Prime de poste"],
      ["astreinte", "Astreinte"],
      ["intervention", "Intervention"],
      ["conges-rtt", "Congés ou RTT"],
      ["maladie", "Maladie"],
      ["ijss", "IJSS"],
      ["subrogation", "Subrogation"],
      ["prevoyance", "Prévoyance"],
      ["autre", "Autre anomalie de paie"]
    ],
    documents: ["Planning", "Kelio", "Nibelis", "Bulletin", "Accord", "Feuille d’intervention", "Décompte IJSS", "Autre"],
    outcomes: ["Comprendre", "Vérifier un écart", "Préparer une question paie", "Demander une correction", "Préparer une régularisation"],
    context: "payroll"
  }
};

const employeePathDefinitions = {
  QUESTION_SALARIE: {
    label: "Questions salariés",
    title: "Poser une question salarié",
    description: "Obtenez une première analyse pédagogique avant de préciser les documents utiles.",
    situations: workspaceDefinitions.employee.situations.filter(([value]) => value !== "discipline"),
    outcomes: ["Comprendre la situation", "Connaître mes droits", "Préparer un courrier", "Identifier les preuves", "Vérifier la paie", "Autre"]
  },
  ASSISTANCE_ENTRETIEN_DISCIPLINAIRE: {
    label: "Assistance entretien disciplinaire",
    title: "Préparer un entretien disciplinaire",
    description: "Construisez un dossier syndical approfondi avant, pendant et après l’entretien, sans présumer les faits ni l’issue.",
    situations: [
      ["entretien-prealable", "Entretien préalable"],
      ["avertissement", "Avertissement"],
      ["blame", "Blâme"],
      ["mise-a-pied", "Mise à pied"],
      ["licenciement", "Licenciement disciplinaire"],
      ["faute", "Faute ou faits reprochés"],
      ["insubordination", "Insubordination"],
      ["incident-securite", "Incident de sécurité"],
      ["autre-discipline", "Autre procédure disciplinaire"]
    ],
    outcomes: ["Préparer la défense", "Préparer l’entretien", "Contrôler la procédure", "Identifier les preuves", "Préparer la suite"]
  }
};

const employeeInterviewSections = [
  {
    title: "1. Demande et faits",
    principle: "Recueillir les faits sans les qualifier juridiquement.",
    questions: [
      ["employeeRequest", "Que demande précisément le salarié aujourd’hui ?", "textarea"],
      ["factsCertain", "Quels faits le salarié présente-t-il comme certains ?", "textarea"],
      ["factsUncertain", "Quels points sont supposés, contestés ou encore inconnus ?", "textarea"],
      ["eventTimeline", "Quelles sont les dates et étapes importantes ?", "textarea"]
    ]
  },
  {
    title: "2. Situation contractuelle",
    principle: "Comparer la situation réelle avec le contrat et ses avenants.",
    questions: [
      ["currentJob", "Quel est le poste, le service et la qualification actuels ?", "text"],
      ["contractTerms", "Que prévoient le contrat et les avenants sur le poste, le lieu et les horaires ?", "textarea"],
      ["proposedChange", "Quel changement exact l’employeur veut-il appliquer ?", "textarea"],
      ["temporaryOrPermanent", "Le changement est-il temporaire ou définitif ?", "select", [["", "Non précisé"], ["temporary", "Temporaire"], ["permanent", "Définitif"], ["disputed", "Information contestée"]]]
    ]
  },
  {
    title: "3. Décision de l’employeur",
    principle: "Identifier le fondement, le calendrier et la marge de choix réelle.",
    questions: [
      ["employerReason", "Quel motif l’employeur donne-t-il ?", "textarea"],
      ["writtenDecision", "La décision ou proposition a-t-elle été remise par écrit ?", "select", [["", "Non précisé"], ["yes", "Oui"], ["no", "Non"]]],
      ["effectiveDate", "Quelle date d’application a été annoncée ?", "date"],
      ["employeeChoice", "Le salarié peut-il réellement accepter ou refuser ?", "textarea"],
      ["volunteersSought", "Des volontaires ou solutions alternatives ont-ils été recherchés ?", "textarea"]
    ]
  },
  {
    title: "4. Horaires et conséquences",
    principle: "Mesurer concrètement le changement et ses effets.",
    questions: [
      ["currentSchedule", "Quels sont les horaires actuels exacts ?", "text"],
      ["futureSchedule", "Quels seraient les horaires et le cycle exacts ?", "textarea"],
      ["weekendsHolidaysNights", "Y aurait-il des nuits, week-ends ou jours fériés ?", "textarea"],
      ["personalConsequences", "Quelles seraient les conséquences sur la santé, le transport ou la vie personnelle et familiale ?", "textarea"],
      ["payConsequences", "Quelles conséquences salariales sont annoncées ?", "textarea"]
    ]
  },
  {
    title: "5. Dimension collective et preuves",
    principle: "Rechercher les règles locales, les précédents et les éléments vérifiables.",
    questions: [
      ["teamImpact", "Quels seraient les effectifs et la charge de travail avant et après ?", "textarea"],
      ["otherEmployees", "D’autres salariés sont-ils concernés ou dans une situation comparable ?", "textarea"],
      ["cseInformation", "Le CSE ou la CSSCT ont-ils été informés ou consultés ?", "textarea"],
      ["localPrecedents", "Existe-t-il des précédents, engagements ou débats connus dans les PV CSE ?", "textarea"],
      ["supportingEvidence", "Quels écrits, plannings, courriels ou témoignages confirment les faits ?", "textarea"]
    ]
  },
  {
    title: "6. Position du salarié",
    principle: "Construire une action adaptée sans présumer la conclusion juridique.",
    questions: [
      ["employeePosition", "Quelle est la position actuelle du salarié ?", "textarea"],
      ["urgentRisk", "Existe-t-il une urgence, une échéance ou un risque disciplinaire ?", "textarea"],
      ["desiredSolution", "Quelle solution souhaite prioritairement le salarié ?", "textarea"]
    ]
  }
];

function workspaceDefinition(workspace) {
  const definition = workspaceDefinitions[workspace];
  if (workspace !== "employee") return definition;
  const pathDefinition = employeePathDefinitions[currentEmployeePath] || employeePathDefinitions.QUESTION_SALARIE;
  return { ...definition, ...pathDefinition };
}

function setStatus(text, level) {
  statusPill.textContent = text;
  if (level) {
    statusPill.dataset.level = level;
  } else {
    delete statusPill.dataset.level;
  }
}

function setConfidence(element, value) {
  element.textContent = value || "-";
  if (value) {
    element.dataset.level = value;
  } else {
    delete element.dataset.level;
  }
}

function sourceLine(source) {
  if (typeof source === "string") return source;
  const parts = [source.document || "Document local"];
  if (source.page) parts.push(`page ${source.page}`);
  const article = source.article || source.article_or_section;
  if (article) parts.push(article);
  if (source.source_layer_label) parts.push(source.source_layer_label);
  if (source.official_id) parts.push(source.official_id);
  if (source.etat) parts.push(`etat ${source.etat}`);
  if (source.is_in_force !== undefined && source.is_in_force !== null) {
    parts.push(`en vigueur ${source.is_in_force ? "oui" : "non"}`);
  }
  if (source.source_quality_warning) parts.push(source.source_quality_warning);
  const line = parts.join(" | ");
  return source.excerpt ? `${line} | extrait: ${source.excerpt}` : line;
}

function fillList(element, values, formatter = (item) => item) {
  element.textContent = "";
  const items = values && values.length ? values : ["A completer apres lecture des sources locales."];
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = formatter(item);
    element.appendChild(li);
  }
}

function fillInlineList(element, values) {
  element.textContent = "";
  const items = values && values.length ? values : ["Aucun"];
  for (const item of items) {
    const span = document.createElement("span");
    span.textContent = item;
    element.appendChild(span);
  }
}

function renderIssueGroups(groups) {
  issueGroups.textContent = "";
  if (!groups || !groups.length) {
    issueGroupsPanel.hidden = true;
    return;
  }
  issueGroupsPanel.hidden = false;
  for (const group of groups) {
    const section = document.createElement("section");
    section.className = "issue-group";
    const title = document.createElement("h4");
    title.textContent = group.name || group.id || "Enjeu";
    section.appendChild(title);

    const findings = document.createElement("ul");
    fillList(findings, group.findings || []);
    section.appendChild(findings);
    issueGroups.appendChild(section);
  }
}

function renderDisciplinaryAssistance(dossier) {
  disciplinaryContent.textContent = "";
  disciplinaryPanel.hidden = !dossier;
  generalFollowupGrid.hidden = Boolean(dossier);
  if (!dossier) return;
  const labels = {
    A_qualification: "A. Qualification de la situation",
    B_timeline: "B. Chronologie",
    C_procedure_control: "C. Contrôle de la procédure",
    D_facts_analysis: "D. Analyse des faits",
    E_interview_preparation: "E. Préparation de l’entretien",
    F_during_interview: "F. Fiche pendant l’entretien",
    G_after_interview: "G. Après l’entretien"
  };
  for (const [key, title] of Object.entries(labels)) {
    const value = dossier[key];
    const section = document.createElement("section");
    section.className = "disciplinary-section";
    const heading = document.createElement("h3");
    heading.textContent = title;
    section.appendChild(heading);
    if (Array.isArray(value)) {
      const list = document.createElement("ul");
      value.forEach((item) => {
        const row = document.createElement("li");
        row.textContent = String(item);
        list.appendChild(row);
      });
      section.appendChild(list);
    } else {
      Object.entries(value || {}).forEach(([name, item]) => {
        const row = document.createElement("p");
        const headingLabel = document.createElement("strong");
        headingLabel.textContent = `${name.replaceAll("_", " ")} : `;
        row.appendChild(headingLabel);
        row.appendChild(document.createTextNode(
          Array.isArray(item)
            ? item.map((entry) => typeof entry === "object" ? entry.document || JSON.stringify(entry) : entry).join(" · ") || "À compléter"
            : String(item ?? "À vérifier")
        ));
        section.appendChild(row);
      });
    }
    disciplinaryContent.appendChild(section);
  }
}

function sourceLayerFallback(sources) {
  const labels = {
    accord_entreprise: "Accords d'entreprise",
    convention_collective: "Convention collective",
    code_travail: "Code du travail",
    jurisprudence: "Jurisprudence",
    prudhommes: "Prud'hommes",
    pratique: "Points pratiques",
    autre: "Autres sources"
  };
  const absent = {
    code_travail: "Code du travail absent: connecteur Legifrance non configure ou aucune source remontee.",
    jurisprudence: "Jurisprudence absente du socle documentaire local actuel.",
    prudhommes: "Decisions prud'homales absentes du socle documentaire local actuel.",
    pratique: "Aucune fiche pratique distincte indexee dans le socle documentaire local actuel."
  };
  const order = Object.keys(labels);
  return order.map((id) => {
    const layerSources = (sources || []).filter((source) => (source.source_layer || "autre") === id);
    return {
      id,
      label: labels[id],
      status: layerSources.length ? "present" : "absent",
      absent_message: absent[id] || "Aucune source de ce niveau n'a ete remontee par Nexus.",
      sources: layerSources
    };
  });
}

function renderSources(element, answer, orchestration) {
  element.textContent = "";
  const layers = answer.source_layers || orchestration.source_layers || sourceLayerFallback(answer.sources || []);
  for (const layer of layers) {
    const section = document.createElement("section");
    section.className = `source-layer source-layer-${layer.status || "absent"}`;
    const heading = document.createElement("h4");
    heading.textContent = layer.label || layer.id || "Source";
    section.appendChild(heading);

    const sources = layer.sources || [];
    if (!sources.length) {
      const empty = document.createElement("p");
      empty.className = "source-absent";
      empty.textContent = layer.absent_message || "Aucune source de ce niveau n'a ete remontee par Nexus.";
      section.appendChild(empty);
      element.appendChild(section);
      continue;
    }

    for (const source of sources) {
      const item = document.createElement("article");
      item.className = "source-item";
      const title = document.createElement("strong");
      title.textContent = source.document || "Document local";
      item.appendChild(title);

      const meta = document.createElement("p");
      meta.className = "source-meta";
      const metaParts = [];
      if (source.page) metaParts.push(`page ${source.page}`);
      const article = source.article || source.article_or_section;
      if (article) metaParts.push(article);
      if (source.source_layer_label) metaParts.push(source.source_layer_label);
      if (source.official_id) metaParts.push(source.official_id);
      if (source.etat) metaParts.push(`etat ${source.etat}`);
      if (source.is_in_force !== undefined && source.is_in_force !== null) {
        metaParts.push(`en vigueur ${source.is_in_force ? "oui" : "non"}`);
      }
      if (source.version_start_date || source.version_end_date || source.date_debut || source.date_fin) {
        const start = source.version_start_date || source.date_debut || "?";
        const end = source.version_end_date || source.date_fin || "?";
        metaParts.push(`version ${start} -> ${end}`);
      }
      if (source.retrieved_at) metaParts.push(`recupere ${source.retrieved_at}`);
      meta.textContent = metaParts.join(" | ") || "Localisation a verifier";
      item.appendChild(meta);

      if (source.excerpt) {
        const excerpt = document.createElement("p");
        excerpt.className = "source-excerpt";
        excerpt.textContent = source.excerpt;
        item.appendChild(excerpt);
      }

      if (source.source_quality_warning) {
        const warning = document.createElement("p");
        warning.className = "source-warning";
        warning.textContent = source.source_quality_warning;
        item.appendChild(warning);
      }

      section.appendChild(item);
    }
    element.appendChild(section);
  }
}

function expertBlock(title, values) {
  const block = document.createElement("div");
  block.className = "expert-block";
  const heading = document.createElement("strong");
  heading.textContent = title;
  block.appendChild(heading);
  if (Array.isArray(values)) {
    const list = document.createElement("ul");
    fillList(list, values);
    block.appendChild(list);
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = values || "A completer.";
    block.appendChild(paragraph);
  }
  return block;
}

function renderExpertCard(title, expert, sections) {
  if (!expert || !expert.active) return;
  const card = document.createElement("section");
  card.className = "expert-card";
  const heading = document.createElement("h4");
  heading.textContent = title;
  card.appendChild(heading);
  for (const section of sections) {
    card.appendChild(expertBlock(section.title, expert[section.key]));
  }
  expertContent.appendChild(card);
}

function renderExperts(payload) {
  expertContent.textContent = "";
  const orchestration = payload.orchestration || {};
  const hasExpert = Boolean(
    (payload.expert_juriste && payload.expert_juriste.active) ||
    (payload.expert_paie && payload.expert_paie.active)
  );
  if (!hasExpert) {
    expertPanel.hidden = true;
    return;
  }
  expertPanel.hidden = false;
  setConfidence(expertConfidence, orchestration.niveau_de_confiance);

  renderExpertCard("Juriste droit du travail", payload.expert_juriste, [
    { title: "Reponse courte", key: "response_courte" },
    { title: "Qualification juridique", key: "qualification_juridique_situation" },
    { title: "Ce qui est etabli", key: "ce_qui_est_etabli_par_sources" },
    { title: "Ce qui depend des textes ou faits manquants", key: "ce_qui_depend_accord_statut_element_manquant" },
    { title: "Analyse et raisonnement", key: "analyse_et_raisonnement" },
    { title: "Risques et vigilance", key: "risques_points_vigilance" },
    { title: "Position de travail", key: "position_de_travail_proposee" },
    { title: "Questions direction", key: "questions_a_poser_direction" },
    { title: "Limites", key: "limites" }
  ]);

  renderExpertCard("Paie", payload.expert_paie, [
    { title: "Objet du controle", key: "objet_du_controle" },
    { title: "Elements du bulletin", key: "elements_du_bulletin_concernes" },
    { title: "Regles ou sources disponibles", key: "regles_ou_sources_disponibles" },
    { title: "Donnees necessaires au calcul", key: "donnees_necessaires_au_calcul" },
    { title: "Methode de controle", key: "methode_de_controle" },
    { title: "Anomalies potentielles", key: "anomalies_potentielles" },
    { title: "Calcul detaille", key: "calcul_detaille" },
    { title: "Documents necessaires", key: "documents_necessaires" },
    { title: "Limites", key: "limites" }
  ]);
}

function resetReportState(message = "Lance une analyse Nexus, puis genere la fiche de travail a partir du resultat reel.") {
  currentReportMarkdown = "";
  reportOutput.textContent = message;
  generateReportButton.disabled = !currentPayload?.analysis_report;
  copyReportButton.disabled = true;
  downloadReportButton.disabled = true;
}

function reportFileName(report) {
  const slug = String(report?.title || "rapport-analyse-nexus")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return `${slug || "rapport-analyse-nexus"}.md`;
}

function reportBlock(title, values) {
  const section = document.createElement("section");
  section.className = "report-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  section.appendChild(heading);
  const items = Array.isArray(values) && values.length ? values : ["Aucun element distinct remonte par l'analyse Nexus a ce stade."];
  if (items.length === 1) {
    const paragraph = document.createElement("p");
    paragraph.textContent = items[0];
    section.appendChild(paragraph);
  } else {
    const list = document.createElement("ul");
    fillList(list, items);
    section.appendChild(list);
  }
  return section;
}

function renderReport() {
  const report = currentPayload?.analysis_report;
  if (!report) {
    resetReportState("Aucun rapport Nexus n'est disponible pour cette analyse.");
    return;
  }
  currentReportMarkdown = report.markdown || "";
  reportOutput.textContent = "";

  const meta = document.createElement("div");
  meta.className = "report-meta";
  const version = document.createElement("span");
  version.textContent = `Rapport V${report.version || "2.2"}`;
  const title = document.createElement("strong");
  title.textContent = report.title || "Rapport Nexus";
  meta.appendChild(version);
  meta.appendChild(title);
  reportOutput.appendChild(meta);

  const flow = document.createElement("p");
  flow.className = "report-flow";
  flow.textContent = `Flux reel : ${(report.generated_from || []).join(" -> ")}`;
  reportOutput.appendChild(flow);

  for (const item of report.sections || []) {
    reportOutput.appendChild(reportBlock(item.title, item.items));
  }

  const juristeSections = report.expert_sections?.juriste || [];
  if (juristeSections.length) {
    reportOutput.appendChild(reportBlock("Analyse Juriste reelle", juristeSections.map((item) => `${item.title}: ${(item.items || []).join(" / ")}`)));
  }

  const paieSections = report.expert_sections?.paie || [];
  if (paieSections.length) {
    reportOutput.appendChild(reportBlock("Analyse Paie reelle", paieSections.map((item) => `${item.title}: ${(item.items || []).join(" / ")}`)));
  }

  copyReportButton.disabled = !currentReportMarkdown;
  downloadReportButton.disabled = !currentReportMarkdown;
}

async function copyReport() {
  if (!currentReportMarkdown) return;
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(currentReportMarkdown);
    setStatus("Rapport copie", currentPayload?.orchestration?.niveau_de_confiance);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = currentReportMarkdown;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
  setStatus("Rapport copie", currentPayload?.orchestration?.niveau_de_confiance);
}

function downloadReport() {
  if (!currentReportMarkdown) return;
  const blob = new Blob([currentReportMarkdown], { type: "text/markdown;charset=utf-8" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = reportFileName(currentPayload?.analysis_report);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 500);
  setStatus("Rapport telecharge", currentPayload?.orchestration?.niveau_de_confiance);
}

function renderResult(payload) {
  currentPayload = payload;
  const answer = payload.answer;
  const orchestration = payload.orchestration || {};
  const finalAssistant = payload.final_assistant_runtime?.assistant || null;
  const finalSummary = finalAssistant?.summary || {};
  const finalTrace = finalAssistant?.trace || {};
  emptyState.hidden = true;
  resultContent.hidden = false;
  resultQuestion.textContent = currentWorkspace
    ? queryInput.value.trim()
    : orchestration.question_posee || answer.query;
  setConfidence(confidenceValue, finalAssistant?.confidence || orchestration.niveau_de_confiance || answer.confidence);
  const finalDomains = finalAssistant
    ? [finalAssistant.primary_domain, ...(finalAssistant.complementary_domains || [])]
    : null;
  fillInlineList(domainsList, finalDomains || orchestration.domaines_detectes || answer.route.domains || []);
  fillInlineList(expertsList, finalTrace.engines_called || orchestration.experts_mobilises || []);
  shortAnswer.textContent = orchestration.reponse_synthetique_nexus || answer.short_answer || "A completer.";
  workingPosition.textContent = orchestration.position_de_travail || answer.working_position || "A completer.";
  renderSources(sourcesList, answer, orchestration);
  fillList(findingsList, answer.findings || []);
  fillList(documentsList, finalSummary.documents_or_actions || orchestration.documents_necessaires || answer.documents_to_request || []);
  fillList(
    questionsList,
    finalAssistant?.questions?.map((item) => `${item.priority}: ${item.text}`) ||
      orchestration.questions_utiles ||
      answer.questions_to_ask ||
      []
  );
  fillList(
    warningsList,
    finalAssistant
      ? [
          ...(finalSummary.limits || []),
          ...(finalAssistant.warnings || []),
          `Assistant final: ${payload.final_assistant_runtime.mode}`
        ]
      : orchestration.limites || answer.warnings || []
  );
  renderIssueGroups(answer.issue_groups || []);
  renderDisciplinaryAssistance(answer.disciplinary_assistance || null);
  renderExperts(payload);
  const expertMode = document.querySelector('input[name="responseMode"]:checked')?.value === "EXPERT";
  expertPanel.hidden = !expertMode;
  const finalEnabled = payload.final_assistant_runtime?.mode !== "DISABLED";
  runtimeStatus.dataset.advanced = String(finalEnabled);
  runtimeStatusLabel.textContent = finalEnabled ? "Assistant avancé activé" : "Mode historique";
  assistantStatusValue.textContent = finalEnabled ? "Assistant avancé activé" : "Moteur historique";
  const paieV2Used = Boolean(
    payload.final_assistant_runtime?.diagnostics?.engines_used?.includes("expert_paie_v2")
  );
  payrollStatusValue.textContent = paieV2Used ? "Contrôle avancé mobilisé" : "Analyse prudente";
  resultModeNotice.textContent = finalEnabled
    ? "L’Assistant avancé a enrichi cette analyse."
    : "Analyse avancée non activée : Nexus utilise le moteur historique.";
  analysisState.hidden = true;
  wizardView.hidden = true;
  homeView.hidden = true;
  resultView.hidden = false;
  sessionHistoryCount += 1;
  resetReportState();
  resultView.focus?.();
}

function renderError(message) {
  currentPayload = null;
  resetReportState();
  emptyState.hidden = false;
  resultContent.hidden = true;
  emptyState.innerHTML = "";
  const title = document.createElement("h2");
  title.textContent = "Analyse impossible";
  const text = document.createElement("p");
  text.className = "error-text";
  text.textContent = message;
  emptyState.appendChild(title);
  emptyState.appendChild(text);
}

function showOnly(view) {
  homeView.hidden = view !== "home";
  wizardView.hidden = view !== "wizard";
  resultView.hidden = view !== "result";
  analysisState.hidden = view !== "loading";
  if (view === "home") {
    document.getElementById("homeTitle").focus?.();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function createChoiceButton(value, label, selected, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "choice-button";
  button.dataset.value = value;
  button.setAttribute("aria-pressed", String(selected));
  button.textContent = label;
  button.addEventListener("click", () => handler(value));
  return button;
}

function renderSituationChoices(definition) {
  situationChoices.textContent = "";
  for (const [value, label] of definition.situations) {
    situationChoices.appendChild(
      createChoiceButton(value, label, selectedSituation === value, (nextValue) => {
        selectedSituation = nextValue;
        renderSituationChoices(definition);
        wizardError.hidden = true;
      })
    );
  }
}

function renderOutcomeChoices(definition) {
  outcomeChoices.textContent = "";
  for (const label of definition.outcomes) {
    outcomeChoices.appendChild(
      createChoiceButton(label, label, selectedOutcome === label, (nextValue) => {
        selectedOutcome = nextValue;
        renderOutcomeChoices(definition);
        wizardError.hidden = true;
      })
    );
  }
}

function addField(container, id, label, type = "text", options = []) {
  const wrapper = document.createElement("div");
  wrapper.className = `field-control${type === "checkbox" ? " checkbox-control" : ""}`;
  const fieldLabel = document.createElement("label");
  fieldLabel.htmlFor = id;
  fieldLabel.textContent = label;
  const input = type === "select" ? document.createElement("select") : document.createElement("input");
  input.id = id;
  input.name = id;
  if (type === "checkbox") {
    input.type = "checkbox";
    wrapper.appendChild(input);
    wrapper.appendChild(fieldLabel);
  } else {
    if (type !== "select") input.type = type;
    if (type === "select") {
      for (const [value, text] of options) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = text;
        input.appendChild(option);
      }
    }
    wrapper.appendChild(fieldLabel);
    wrapper.appendChild(input);
  }
  container.appendChild(wrapper);
}

function renderEmployeeInterview() {
  employeeInterview.textContent = "";
  const enabled = currentWorkspace === "employee" && currentEmployeePath === "QUESTION_SALARIE";
  employeeInterview.hidden = !enabled;
  interviewSaveActions.hidden = !enabled;
  if (!enabled) return;

  for (const section of employeeInterviewSections) {
    const fieldset = document.createElement("fieldset");
    fieldset.className = "interview-section";
    const legend = document.createElement("legend");
    legend.textContent = section.title;
    const principle = document.createElement("p");
    principle.className = "interview-principle";
    principle.textContent = `Principe appliqué : ${section.principle}`;
    fieldset.appendChild(legend);
    fieldset.appendChild(principle);
    for (const [id, label, type, options = []] of section.questions) {
      const wrapper = document.createElement("div");
      wrapper.className = "interview-question";
      const fieldLabel = document.createElement("label");
      fieldLabel.htmlFor = id;
      fieldLabel.textContent = label;
      let field;
      if (type === "textarea") {
        field = document.createElement("textarea");
        field.rows = 3;
        field.maxLength = 2000;
      } else if (type === "select") {
        field = document.createElement("select");
        for (const [value, text] of options) {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = text;
          field.appendChild(option);
        }
      } else {
        field = document.createElement("input");
        field.type = type;
      }
      field.id = id;
      field.name = id;
      field.dataset.interviewAnswer = "true";
      wrapper.appendChild(fieldLabel);
      wrapper.appendChild(field);
      fieldset.appendChild(wrapper);
    }
    employeeInterview.appendChild(fieldset);
  }
}

function renderContextFields(definition) {
  contextFields.textContent = "";
  renderEmployeeInterview();
  if (definition.context === "employee") {
    addField(contextFields, "startDate", "Date de début", "date");
    addField(contextFields, "eventFrequency", "Événement", "select", [["", "Non précisé"], ["ponctuel", "Ponctuel"], ["recurrent", "Récurrent"]]);
    addField(contextFields, "stillEmployed", "Salarié encore en poste", "checkbox");
    addField(contextFields, "procedureOngoing", "Procédure en cours", "checkbox");
    addField(contextFields, "urgentSituation", "Situation urgente", "checkbox");
    addField(contextFields, "knownDeadline", "Échéance connue", "date");
  } else if (definition.context === "cse") {
    addField(contextFields, "employeeCount", "Nombre approximatif de salariés", "number");
    addField(contextFields, "services", "Services concernés");
    addField(contextFields, "decisionAnnounced", "Décision déjà annoncée", "checkbox");
    addField(contextFields, "implementationStarted", "Mise en œuvre commencée", "checkbox");
    addField(contextFields, "meetingPlanned", "Réunion prévue", "checkbox");
    addField(contextFields, "meetingDate", "Date de réunion", "date");
  } else if (definition.context === "negotiation") {
    addField(contextFields, "negotiationTheme", "Thème", "select", [
      ["remuneration", "Rémunération"], ["classification", "Classification"], ["temps-travail", "Temps de travail"],
      ["primes", "Primes"], ["egalite", "Égalité professionnelle"], ["droit-syndical", "Droit syndical"],
      ["emploi", "Emploi"], ["formation", "Formation"], ["protection-sociale", "Protection sociale"], ["autre", "Autre"]
    ]);
    addField(contextFields, "meetingDate", "Date de réunion éventuelle", "date");
    addField(contextFields, "directionProject", "Projet de la direction disponible", "checkbox");
    addField(contextFields, "previousVersions", "Anciennes versions disponibles", "checkbox");
  } else {
    addField(contextFields, "payrollMonth", "Mois concerné", "month");
    addField(contextFields, "periodDetails", "Période précise si connue");
    addField(contextFields, "recurringGap", "Écart récurrent", "checkbox");
    addField(contextFields, "alreadyReported", "Anomalie déjà signalée", "checkbox");
  }
}

function getInterviewAnswers() {
  const answers = {};
  employeeInterview.querySelectorAll("[data-interview-answer]").forEach((field) => {
    if (field.value.trim()) answers[field.name] = field.value.trim();
  });
  return answers;
}

function interviewQuestionLabel(id) {
  for (const section of employeeInterviewSections) {
    const question = section.questions.find(([questionId]) => questionId === id);
    if (question) return question[1];
  }
  return id;
}

function downloadInterview() {
  const answers = getInterviewAnswers();
  const dossier = {
    format: "CFDT Nexus - questionnaire salarié",
    version: 1,
    exported_at: new Date().toISOString(),
    confidentiality_notice: "Document local à conserver et transmettre avec prudence.",
    situation_type: selectedSituation || null,
    initial_question: queryInput.value.trim() || null,
    answers: Object.fromEntries(
      Object.entries(answers).map(([id, answer]) => [
        id,
        { question: interviewQuestionLabel(id), answer }
      ])
    )
  };
  const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `questionnaire-salarie-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  interviewSaveStatus.textContent = `${Object.keys(answers).length} réponse(s) enregistrée(s) dans le fichier local.`;
}

function renderDocumentChoices(definition) {
  documentChoices.textContent = "";
  definition.documents.forEach((label, index) => {
    const item = document.createElement("label");
    item.className = "checkbox-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "availableDocument";
    input.value = label;
    input.id = `availableDocument${index}`;
    item.appendChild(input);
    item.appendChild(document.createTextNode(label));
    documentChoices.appendChild(item);
  });
}

function renderWizardProgress() {
  const labels = ["Besoin", "Description", "Repères", "Éléments", "Résultat"];
  wizardProgress.textContent = "";
  labels.forEach((label, index) => {
    const item = document.createElement("li");
    const step = index + 1;
    item.dataset.number = String(step);
    item.dataset.active = String(step === currentWizardStep);
    item.dataset.complete = String(step < currentWizardStep);
    item.textContent = label;
    wizardProgress.appendChild(item);
  });
  document.querySelectorAll(".wizard-step").forEach((section) => {
    section.hidden = Number(section.dataset.step) !== currentWizardStep;
  });
  previousStepButton.hidden = currentWizardStep === 1;
  nextStepButton.hidden = currentWizardStep === 5;
  analyzeButton.hidden = currentWizardStep !== 5;
}

function validateCurrentStep() {
  let message = "";
  if (currentWizardStep === 1 && !selectedSituation) message = "Choisissez le type de situation à traiter.";
  if (currentWizardStep === 2 && queryInput.value.trim().length < 12) message = "Décrivez la situation en quelques mots avant de continuer.";
  if (currentWizardStep === 5 && !selectedOutcome) message = "Choisissez le résultat souhaité.";
  wizardError.textContent = message;
  wizardError.hidden = !message;
  return !message;
}

function openWorkspace(workspace, preset = "", employeePath = "") {
  if (workspace === "employee") {
    currentEmployeePath = employeePath || currentEmployeePath || "QUESTION_SALARIE";
  } else {
    currentEmployeePath = null;
  }
  const definition = workspaceDefinition(workspace);
  if (!definition) return;
  currentWorkspace = workspace;
  currentWizardStep = 1;
  selectedSituation = preset || (
    currentEmployeePath === "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"
      ? "entretien-prealable"
      : ""
  );
  selectedOutcome = "";
  queryInput.value = "";
  wizardWorkspaceLabel.textContent = definition.label;
  wizardTitle.textContent = definition.title;
  wizardDescription.textContent = definition.description;
  payrollWarning.hidden = workspace !== "payroll";
  renderSituationChoices(definition);
  renderContextFields(definition);
  renderDocumentChoices(definition);
  renderOutcomeChoices(definition);
  renderWizardProgress();
  wizardError.hidden = true;
  showOnly("wizard");
  wizardTitle.focus?.();
}

function getContextValues() {
  const values = {};
  contextFields.querySelectorAll("input, select").forEach((field) => {
    if (field.type === "checkbox") values[field.name] = field.checked;
    else if (field.value) values[field.name] = field.value;
  });
  return values;
}

function buildStructuredRequest() {
  const definition = workspaceDefinition(currentWorkspace);
  const documents = Array.from(document.querySelectorAll('input[name="availableDocument"]:checked')).map((item) => item.value);
  const responseMode = document.querySelector('input[name="responseMode"]:checked')?.value || "CASE";
  const context = getContextValues();
  const interviewAnswers = getInterviewAnswers();
  const facts = Object.entries(context)
    .filter(([, value]) => value !== false && value !== "")
    .map(([key, value]) => `${key}: ${value === true ? "oui" : value}`);
  const query = [
    `[Espace métier: ${definition.label}]`,
    `[Type de situation: ${selectedSituation}]`,
    queryInput.value.trim(),
    facts.length ? `Repères: ${facts.join("; ")}.` : "",
    ...Object.entries(interviewAnswers).map(
      ([id, answer]) => `Question salarié — ${interviewQuestionLabel(id)} Réponse : ${answer}`
    ),
    documents.length ? `Documents disponibles: ${documents.join(", ")}.` : "Documents disponibles: non précisés.",
    `Résultat souhaité: ${selectedOutcome}.`,
    `Mode de réponse: ${responseMode}.`
  ].filter(Boolean).join("\n");
  return {
    query,
    source_limit: Number(sourceLimitInput.value || 6),
    employee_path: currentEmployeePath,
    portal_context: {
      workspace: currentWorkspace,
      employee_path: currentEmployeePath,
      situation_type: selectedSituation,
      user_question: queryInput.value.trim(),
      facts: context,
      employee_interview_answers: interviewAnswers,
      available_documents: documents,
      period: context.payrollMonth || context.startDate || context.meetingDate || null,
      urgency: Boolean(context.urgentSituation),
      desired_outcome: selectedOutcome,
      response_mode: responseMode,
      allowed_engines: currentWorkspace === "payroll" ? ["historical_payroll_if_enabled"] : ["assistant_router"],
      confidentiality: confidentialityLevel.value
    }
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateCurrentStep()) return;
  const requestPayload = buildStructuredRequest();

  setStatus("Analyse...", null);
  const button = analyzeButton;
  button.disabled = true;
  showOnly("loading");

  try {
    const payload = await requestNexusAnalysis(requestPayload);
    renderResult(payload);
    setStatus("Analyse OK", payload.orchestration?.niveau_de_confiance || payload.answer.confidence);
  } catch (error) {
    const userMessage =
      error instanceof NexusRequestError
        ? error.message
        : "Une erreur interne Nexus est survenue.";
    renderError(userMessage);
    setStatus("Erreur", "faible");
    showOnly("result");
  } finally {
    button.disabled = false;
  }
});

document.querySelectorAll("[data-open-workspace]").forEach((button) => {
  button.addEventListener("click", () => openWorkspace(button.dataset.openWorkspace, button.dataset.preset || "", button.dataset.employeePath || ""));
});
document.querySelectorAll("[data-return-home]").forEach((button) => {
  button.addEventListener("click", () => showOnly("home"));
});
nextStepButton.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  currentWizardStep = Math.min(5, currentWizardStep + 1);
  renderWizardProgress();
  document.querySelector(`.wizard-step[data-step="${currentWizardStep}"]`)?.focus?.();
});
previousStepButton.addEventListener("click", () => {
  currentWizardStep = Math.max(1, currentWizardStep - 1);
  renderWizardProgress();
});
editInformationButton.addEventListener("click", () => showOnly("wizard"));
addDocumentButton.addEventListener("click", () => {
  currentWizardStep = 4;
  renderWizardProgress();
  showOnly("wizard");
});
newAnalysisButton.addEventListener("click", () => {
  if (currentWorkspace) openWorkspace(currentWorkspace, "", currentEmployeePath || "");
  else showOnly("home");
});
settingsButton.addEventListener("click", () => {
  const expanded = settingsButton.getAttribute("aria-expanded") === "true";
  settingsButton.setAttribute("aria-expanded", String(!expanded));
  settingsPanel.hidden = expanded;
});
closeSettingsButton.addEventListener("click", () => {
  settingsPanel.hidden = true;
  settingsButton.setAttribute("aria-expanded", "false");
  settingsButton.focus();
});
document.querySelectorAll("[data-secondary-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const messages = {
      search: "Utilisez l’espace Négociations et accords pour une recherche guidée dans les sources disponibles.",
      cases: "Aucun dossier enregistré dans cette version. Aucune donnée personnelle n’est conservée.",
      history: sessionHistoryCount ? `${sessionHistoryCount} analyse(s) réalisée(s) pendant cette session.` : "Aucune analyse dans cette session.",
      templates: "Lancez une analyse puis utilisez « Générer un brouillon » dans le plan d’action."
    };
    secondaryMessage.textContent = messages[button.dataset.secondaryAction] || "";
    secondaryMessage.hidden = false;
  });
});

generateReportButton.addEventListener("click", renderReport);
copyReportButton.addEventListener("click", copyReport);
downloadReportButton.addEventListener("click", downloadReport);
downloadInterviewButton.addEventListener("click", downloadInterview);

const pipelineLabels = {
  validate_case: "Validation du dossier",
  validate_documents: "Validation des documents",
  check_confidentiality: "Controle de confidentialite",
  classify_documents: "Classification documentaire",
  identify_themes: "Identification des themes",
  determine_required_documents: "Pieces necessaires",
  assess_document_completeness: "Completude documentaire",
  prepare_expert_contexts: "Contextes experts",
  collect_expert_analyses: "Analyses expertes",
  aggregate_results: "Agregation",
  detect_contradictions: "Contradictions",
  produce_diagnostic: "Diagnostic"
};

const statusLabels = {
  completed: "Terminee",
  warning: "Avertissement",
  blocked: "Bloquee",
  failed: "Echec",
  not_started: "Non commencee",
  running: "En cours",
  partial: "Partiel",
  unavailable: "Indisponible",
  refused: "Conclusion refusee"
};

function textNode(tag, text, className = "") {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text === null || text === undefined || text === "" ? "Non renseigne" : String(text);
  return element;
}

function displayValues(container, title, values) {
  const card = document.createElement("section");
  card.className = "data-card";
  card.appendChild(textNode("h3", title));
  const list = document.createElement("ul");
  const items = Array.isArray(values) && values.length ? values : ["Aucun element signale."];
  for (const value of items) list.appendChild(textNode("li", value));
  card.appendChild(list);
  container.appendChild(card);
}

function renderPipeline(steps) {
  pipelineSteps.textContent = "";
  for (const step of steps || []) {
    const item = document.createElement("li");
    item.dataset.status = step.status || "not_started";
    item.appendChild(textNode("strong", pipelineLabels[step.id] || step.id));
    item.appendChild(textNode("span", statusLabels[step.status] || step.status, "step-status"));
    pipelineSteps.appendChild(item);
  }
}

function renderDocumentSummary(payload) {
  documentSummary.textContent = "";
  const documents = payload.report?.sections?.documents || {};
  displayValues(documentSummary, "Pieces presentes", documents.present);
  displayValues(documentSummary, "Pieces recommandees", documents.recommended);
  displayValues(documentSummary, "Pieces manquantes", documents.missing);
  displayValues(documentSummary, "Pieces bloquantes", documents.blocking);
  completenessRate.textContent = `${payload.completeness?.rate_percent ?? 0} %`;
  completenessNotice.textContent = payload.completeness?.notice || "Taux documentaire fourni par le backend.";
}

function renderCaseDiagnostic(payload) {
  caseDiagnosticSummary.textContent = "";
  const summary = payload.report?.sections?.executive_summary || {};
  displayValues(caseDiagnosticSummary, "Resume executif", summary.paragraphs);
  displayValues(caseDiagnosticSummary, "Themes analyses", payload.themes_analyzed);
  displayValues(caseDiagnosticSummary, "Themes bloques", payload.themes_blocked);
  displayValues(
    caseDiagnosticSummary,
    "Contradictions",
    payload.contradictions?.length ? payload.contradictions : ["Aucune contradiction signalee par le pipeline."]
  );
}

function renderEmployeeCaseView(view) {
  caseReportView.textContent = "";
  displayValues(caseReportView, "Resume", view.summary?.paragraphs);
  displayValues(caseReportView, "Pieces a demander", view.documents?.missing);
  const themes = (view.themes || []).map((item) => {
    const missing = item.missing_documents?.length ? ` - pieces manquantes : ${item.missing_documents.join(", ")}` : "";
    return `${item.label} - ${statusLabels[item.status] || item.status}${missing}`;
  });
  displayValues(caseReportView, "Themes", themes);
  displayValues(caseReportView, "A verifier", view.actions?.to_verify);
  displayValues(caseReportView, "A demander", view.actions?.to_request);
  displayValues(caseReportView, "A controler", view.actions?.to_control);
  displayValues(caseReportView, "A completer", view.actions?.to_complete);
  displayValues(caseReportView, "Limites", view.limits);
}

function renderExpertSummary(container, title, summary) {
  const status = Array.isArray(summary?.status) ? summary.status.join(", ") : summary?.status;
  displayValues(container, `${title} - ${statusLabels[status] || status || "Indisponible"}`, [summary?.summary]);
  displayValues(container, `${title} - sources`, summary?.rules_or_sources);
  displayValues(container, `${title} - controles`, summary?.control_points);
  displayValues(container, `${title} - limites`, summary?.limits);
}

function renderExpertCaseView(view) {
  caseReportView.textContent = "";
  const sections = view.sections || {};
  displayValues(caseReportView, "Resume executif", sections.executive_summary?.paragraphs);
  for (const theme of sections.theme_analysis || []) {
    displayValues(caseReportView, `${theme.label} - ${statusLabels[theme.status] || theme.status}`, [
      theme.summary,
      ...(theme.findings || []),
      ...(theme.missing_documents || []).map((item) => `Piece manquante : ${item}`),
      ...(theme.limits || [])
    ]);
  }
  renderExpertSummary(caseReportView, "Expert Paie", sections.payroll_expert_summary);
  renderExpertSummary(caseReportView, "Juriste Travail", sections.legal_expert_summary);
  displayValues(caseReportView, "Contradictions", sections.contradictions?.items?.length ? sections.contradictions.items : ["Aucune contradiction signalee."]);
  displayValues(caseReportView, "Causes de confiance", sections.confidence?.causes);
  displayValues(caseReportView, "Elements favorables", sections.confidence?.strengthening_elements);
  displayValues(caseReportView, "Elements defavorables", sections.confidence?.weakening_elements);
  displayValues(caseReportView, "Limites", sections.limits?.items);
}

function renderSelectedCaseView() {
  if (!currentCasePayload) return;
  const employeeMode = currentCaseView === "employee";
  employeeViewButton.setAttribute("aria-pressed", String(employeeMode));
  expertViewButton.setAttribute("aria-pressed", String(!employeeMode));
  employeeViewButton.classList.toggle("is-active", employeeMode);
  expertViewButton.classList.toggle("is-active", !employeeMode);
  caseViewDescription.textContent = employeeMode
    ? "Vue salarie simple et pedagogique, fournie par employee_view."
    : "Vue expert detaillee, fournie par expert_view.";
  if (employeeMode) renderEmployeeCaseView(currentCasePayload.employee_view);
  else renderExpertCaseView(currentCasePayload.expert_view);
}

function renderEmployeeCase(payload) {
  currentCasePayload = payload;
  caseError.hidden = true;
  caseContent.hidden = false;
  caseHeaderTitle.textContent = payload.case?.title || payload.case?.case_id || "Dossier synthetique";
  caseHeaderMeta.textContent = `${payload.case?.case_id || "-"} | periode ${payload.case?.period || "-"}`;
  caseStatus.textContent = `Statut : ${statusLabels[payload.pipeline?.final_status] || payload.pipeline?.final_status || "-"}`;
  caseStatus.dataset.status = payload.pipeline?.final_status || "unknown";
  caseConfidentiality.textContent = `Confidentialite : ${payload.report_metadata?.confidentiality || "restricted"}`;
  caseConfidence.textContent = `Confiance : ${payload.diagnostic?.global_confidence || "UNKNOWN"}`;
  renderPipeline(payload.pipeline?.steps);
  renderDocumentSummary(payload);
  renderCaseDiagnostic(payload);
  renderSelectedCaseView();
}

function renderCaseError(message) {
  currentCasePayload = null;
  caseContent.hidden = true;
  caseError.hidden = false;
  caseError.textContent = message || "Dossier indisponible.";
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  let payload;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error("Reponse JSON invalide du serveur local.");
  }
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Erreur du serveur local.");
  return payload;
}

async function loadScenarios() {
  try {
    const payload = await fetchJson("/api/employee-case/scenarios");
    caseScenarioSelect.textContent = "";
    for (const scenario of payload.scenarios || []) {
      const option = document.createElement("option");
      option.value = scenario.id;
      option.textContent = scenario.label;
      caseScenarioSelect.appendChild(option);
    }
  } catch (error) {
    renderCaseError(`Liste des scenarios indisponible : ${error.message}`);
  }
}

async function loadEmployeeCase() {
  const scenario = caseScenarioSelect.value;
  if (!scenario) {
    renderCaseError("Selectionne un scenario synthetique.");
    return;
  }
  loadCaseButton.disabled = true;
  caseError.hidden = true;
  try {
    const payload = await fetchJson(`/api/employee-case/demo?scenario=${encodeURIComponent(scenario)}`);
    renderEmployeeCase(payload);
  } catch (error) {
    renderCaseError(`Chargement impossible : ${error.message}`);
  } finally {
    loadCaseButton.disabled = false;
  }
}

loadCaseButton.addEventListener("click", loadEmployeeCase);
caseScenarioSelect.addEventListener("change", loadEmployeeCase);
employeeViewButton.addEventListener("click", () => {
  currentCaseView = "employee";
  renderSelectedCaseView();
});
expertViewButton.addEventListener("click", () => {
  currentCaseView = "expert";
  renderSelectedCaseView();
});

loadScenarios().then(loadEmployeeCase);
