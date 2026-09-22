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
const documentsSummaryPanel = document.getElementById("documentsSummaryPanel");
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
const printReportButton = document.getElementById("printReportButton");
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
const stepTwoTitle = document.getElementById("stepTwoTitle");
const questionInputLabel = document.getElementById("questionInputLabel");
const privacyInputNotice = document.getElementById("privacyInputNotice");
const questionDocuments = document.getElementById("questionDocuments");
const questionDocumentTitle = document.getElementById("questionDocumentTitle");
const questionDocumentStatus = document.getElementById("questionDocumentStatus");
const clearQuestionDocuments = document.getElementById("clearQuestionDocuments");
const questionDocumentDropZone = document.getElementById("questionDocumentDropZone");
const questionDocumentList = document.getElementById("questionDocumentList");
const cseAgendaWorkflow = document.getElementById("cseAgendaWorkflow");
const verifyCseAgendaButton = document.getElementById("verifyCseAgendaButton");
const cseAgendaVerificationStatus = document.getElementById("cseAgendaVerificationStatus");
const cseAgendaSelection = document.getElementById("cseAgendaSelection");
const cseAgendaChoices = document.getElementById("cseAgendaChoices");
const csePreviousPvDocuments = document.getElementById("csePreviousPvDocuments");
const clearCsePreviousPvDocuments = document.getElementById("clearCsePreviousPvDocuments");
const csePreviousPvDropZone = document.getElementById("csePreviousPvDropZone");
const csePreviousPvStatus = document.getElementById("csePreviousPvStatus");
const csePreviousPvList = document.getElementById("csePreviousPvList");
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
const chatbotDetailsButton = document.getElementById("chatbotDetailsButton");
const chatbotSourcesSummary = document.getElementById("chatbotSourcesSummary");
const chatbotSourcesList = document.getElementById("chatbotSourcesList");
const chatbotConnectorsSummary = document.getElementById("chatbotConnectorsSummary");
const chatbotConnectorsList = document.getElementById("chatbotConnectorsList");
const chatbotPvSummary = document.getElementById("chatbotPvSummary");
const chatbotPvList = document.getElementById("chatbotPvList");
const editInformationButton = document.getElementById("editInformationButton");
const addDocumentButton = document.getElementById("addDocumentButton");
const newAnalysisButton = document.getElementById("newAnalysisButton");
const secondaryMessage = document.getElementById("secondaryMessage");
const disciplinaryPanel = document.getElementById("disciplinaryPanel");
const disciplinaryContent = document.getElementById("disciplinaryContent");
const generalFollowupGrid = document.getElementById("generalFollowupGrid");
const factualEnrichmentPanel = document.getElementById("factualEnrichmentPanel");
const followUpHistory = document.getElementById("followUpHistory");
const followUpDocuments = document.getElementById("followUpDocuments");
const followUpQuestions = document.getElementById("followUpQuestions");
const followUpAdditional = document.getElementById("followUpAdditional");
const followUpDocumentInput = document.getElementById("followUpDocumentInput");
const followUpDocumentStatus = document.getElementById("followUpDocumentStatus");
const followUpDocumentList = document.getElementById("followUpDocumentList");
const refineAnalysisButton = document.getElementById("refineAnalysisButton");
const followUpStatus = document.getElementById("followUpStatus");
const employeeInterview = document.getElementById("employeeInterview");
const interviewSaveActions = document.getElementById("interviewSaveActions");
const downloadInterviewButton = document.getElementById("downloadInterviewButton");
const interviewSaveStatus = document.getElementById("interviewSaveStatus");
const nexusVersionValue = document.getElementById("nexusVersionValue");
const settingsVersionValue = document.getElementById("settingsVersionValue");
const optionalFormatsValue = document.getElementById("optionalFormatsValue");
const cseCorpusStatusValue = document.getElementById("cseCorpusStatusValue");
const cseAgendaPanel = document.getElementById("cseAgendaPanel");
const cseAgendaSummary = document.getElementById("cseAgendaSummary");
const cseAgendaPoints = document.getElementById("cseAgendaPoints");
const officialConnectorsStatusValue = document.getElementById("officialConnectorsStatusValue");
const legifranceStatusValue = document.getElementById("legifranceStatusValue");
const judilibreStatusValue = document.getElementById("judilibreStatusValue");
const historyView = document.getElementById("historyView");
const historyHomeButton = document.getElementById("historyHomeButton");
const historyAverage = document.getElementById("historyAverage");
const historyVersion = document.getElementById("historyVersion");
const historyWarning = document.getElementById("historyWarning");
const historyScoreExplanation = document.getElementById("historyScoreExplanation");
const historySearch = document.getElementById("historySearch");
const historyFilters = document.getElementById("historyFilters");
const historyCases = document.getElementById("historyCases");
const historyEmpty = document.getElementById("historyEmpty");
const historyResultCount = document.getElementById("historyResultCount");
const historyListPanel = document.getElementById("historyListPanel");
const historyDetail = document.getElementById("historyDetail");
const historyBackToList = document.getElementById("historyBackToList");
const historyDetailId = document.getElementById("historyDetailId");
const historyDetailTitle = document.getElementById("historyDetailTitle");
const historyDetailMeta = document.getElementById("historyDetailMeta");
const historyDetailScore = document.getElementById("historyDetailScore");
const historyDetailBadges = document.getElementById("historyDetailBadges");
const historySpecialNotes = document.getElementById("historySpecialNotes");
const historyRefreshSourcesButton = document.getElementById("historyRefreshSourcesButton");
const historySourceRefresh = document.getElementById("historySourceRefresh");
const historySections = document.getElementById("historySections");
const historyCopyButton = document.getElementById("historyCopyButton");
const historyPrintButton = document.getElementById("historyPrintButton");
const historyCopyStatus = document.getElementById("historyCopyStatus");
const casesView = document.getElementById("casesView");
const casesHomeButton = document.getElementById("casesHomeButton");
const refreshCasesButton = document.getElementById("refreshCasesButton");
const casesStatus = document.getElementById("casesStatus");
const casesList = document.getElementById("casesList");
const casesEmpty = document.getElementById("casesEmpty");
const caseFileDetail = document.getElementById("caseFileDetail");
const caseFileSnapshot = document.getElementById("caseFileSnapshot");
const caseBackToList = document.getElementById("caseBackToList");
const deleteCaseButton = document.getElementById("deleteCaseButton");
const caseFileForm = document.getElementById("caseFileForm");
const caseReference = document.getElementById("caseReference");
const caseFileTitle = document.getElementById("caseFileTitle");
const caseFileStatus = document.getElementById("caseFileStatus");
const caseFileNotes = document.getElementById("caseFileNotes");
const caseFileActions = document.getElementById("caseFileActions");
const caseDecisionDate = document.getElementById("caseDecisionDate");
const caseDecisionType = document.getElementById("caseDecisionType");
const caseDecisionAuthor = document.getElementById("caseDecisionAuthor");
const caseDecisionSummary = document.getElementById("caseDecisionSummary");
const caseDecisionDocument = document.getElementById("caseDecisionDocument");
const caseFileSaveStatus = document.getElementById("caseFileSaveStatus");
const saveCaseButton = document.getElementById("saveCaseButton");
const caseSaveDialog = document.getElementById("caseSaveDialog");
const caseSaveForm = document.getElementById("caseSaveForm");
const newCaseTitle = document.getElementById("newCaseTitle");
const newCaseStatus = document.getElementById("newCaseStatus");
const newCaseNotes = document.getElementById("newCaseNotes");
const newCaseSaveStatus = document.getElementById("newCaseSaveStatus");
const cancelCaseSaveButton = document.getElementById("cancelCaseSaveButton");
const pilotBannerInput = document.getElementById("pilotBannerInput");
const pilotBannerResult = document.getElementById("pilotBannerResult");
const pilotBannerReport = document.getElementById("pilotBannerReport");

const rgpdToolCard = document.getElementById("rgpdToolCard");
const rgpdView = document.getElementById("rgpdView");
const rgpdHomeButton = document.getElementById("rgpdHomeButton");
const rgpdDocumentInput = document.getElementById("rgpdDocumentInput");
const rgpdUploadButton = document.getElementById("rgpdUploadButton");
const rgpdUploadStatus = document.getElementById("rgpdUploadStatus");
const rgpdSelectedDocument = document.getElementById("rgpdSelectedDocument");
const rgpdAnalyzeUploadButton = document.getElementById("rgpdAnalyzeUploadButton");
const rgpdCorpusScanButton = document.getElementById("rgpdCorpusScanButton");
const rgpdAnalysisStatus = document.getElementById("rgpdAnalysisStatus");
const rgpdResults = document.getElementById("rgpdResults");

let currentPayload = null;
let currentReportMarkdown = "";
let currentCasePayload = null;
let currentCaseView = "employee";
let currentWorkspace = null;
let currentEmployeePath = null;
let currentWizardStep = 1;
let selectedSituation = "";
let controlledPilot = { enabled: false, title: "", notice: "" };
let selectedOutcome = "";
let sessionHistoryCount = 0;
let historicalCatalog = null;
let historicalSelectedFilter = "all";
let currentHistoricalCase = null;
let currentAnalysisRequest = null;
let followUpConversation = [];
let currentLocalCase = null;
let uploadedQuestionDocuments = [];
let uploadedFollowUpDocuments = [];
let uploadedCsePreviousPvDocuments = [];
let questionDocumentsLoading = false;
let currentCseAgendaPreview = null;

const MAX_QUESTION_DOCUMENTS = 3;
const MAX_QUESTION_DOCUMENT_BYTES = 5 * 1024 * 1024;
const ALLOWED_QUESTION_DOCUMENT_EXTENSIONS = [".pdf", ".docx", ".txt", ".md", ".jpg", ".jpeg"];

function questionDocumentExtension(name) {
  const normalized = String(name || "").toLowerCase();
  return ALLOWED_QUESTION_DOCUMENT_EXTENSIONS.find((extension) => normalized.endsWith(extension)) || "";
}

function fileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const encoded = String(reader.result || "").split(",", 2)[1] || "";
      resolve(encoded);
    });
    reader.addEventListener("error", () => reject(new Error(`Lecture impossible : ${file.name}`)));
    reader.readAsDataURL(file);
  });
}

function documentKey(documentItem) {
  return `${String(documentItem.name || "").toLowerCase()}|${Number(documentItem.size || 0)}`;
}

function renderSelectedDocuments(listElement, documents, removeDocument) {
  if (!listElement) return;
  listElement.textContent = "";
  for (const documentItem of documents) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    const sizeKb = Math.max(1, Math.round(Number(documentItem.size || 0) / 1024));
    name.textContent = `${documentItem.name} · ${sizeKb} Ko`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Retirer";
    remove.setAttribute("aria-label", `Retirer ${documentItem.name}`);
    remove.addEventListener("click", () => removeDocument(documentKey(documentItem)));
    item.append(name, remove);
    listElement.appendChild(item);
  }
}

function updateQuestionDocumentDisplay() {
  renderSelectedDocuments(questionDocumentList, uploadedQuestionDocuments, (key) => {
    uploadedQuestionDocuments = uploadedQuestionDocuments.filter((item) => documentKey(item) !== key);
    updateQuestionDocumentDisplay();
  });
  clearQuestionDocuments.hidden = uploadedQuestionDocuments.length === 0;
  questionDocumentStatus.dataset.state = uploadedQuestionDocuments.length ? "ready" : "";
  questionDocumentStatus.textContent = uploadedQuestionDocuments.length
    ? `${uploadedQuestionDocuments.length} document(s) seront lus uniquement pour cette analyse.`
    : "Vous pouvez coller un texte, déposer un fichier ici ou utiliser le bouton.";
}

function updateFollowUpDocumentDisplay() {
  renderSelectedDocuments(followUpDocumentList, uploadedFollowUpDocuments, (key) => {
    uploadedFollowUpDocuments = uploadedFollowUpDocuments.filter((item) => documentKey(item) !== key);
    updateFollowUpDocumentDisplay();
  });
  followUpDocumentStatus.textContent = uploadedFollowUpDocuments.length
    ? `${uploadedFollowUpDocuments.length} nouveau(x) document(s) seront intégrés à la prochaine réponse.`
    : "Aucun nouveau document joint.";
}

function updateCsePreviousPvDisplay() {
  renderSelectedDocuments(csePreviousPvList, uploadedCsePreviousPvDocuments, (key) => {
    uploadedCsePreviousPvDocuments = uploadedCsePreviousPvDocuments.filter(
      (item) => documentKey(item) !== key
    );
    resetCseAgendaPreview();
    updateCsePreviousPvDisplay();
  });
  clearCsePreviousPvDocuments.hidden = uploadedCsePreviousPvDocuments.length === 0;
  csePreviousPvStatus.textContent = uploadedCsePreviousPvDocuments.length
    ? `${uploadedCsePreviousPvDocuments.length} ancien(s) PV seront comparés uniquement pendant cette analyse.`
    : "Aucun PV ajouté manuellement. Nexus consultera aussi CSE Memory.";
}

function setQuestionDocumentLoading(loading) {
  questionDocumentsLoading = loading;
  analyzeButton.disabled = loading;
  if (refineAnalysisButton) refineAnalysisButton.disabled = loading;
  if (verifyCseAgendaButton) verifyCseAgendaButton.disabled = loading;
}

function resetQuestionDocuments() {
  uploadedQuestionDocuments = [];
  if (questionDocuments) questionDocuments.value = "";
  updateQuestionDocumentDisplay();
  resetCseAgendaPreview();
}

function resetFollowUpDocuments() {
  uploadedFollowUpDocuments = [];
  if (followUpDocumentInput) followUpDocumentInput.value = "";
  updateFollowUpDocumentDisplay();
}

function resetCsePreviousPvDocuments() {
  uploadedCsePreviousPvDocuments = [];
  if (csePreviousPvDocuments) csePreviousPvDocuments.value = "";
  updateCsePreviousPvDisplay();
  resetCseAgendaPreview();
}

async function loadQuestionDocuments(filesInput, target = "initial") {
  const files = Array.from(filesInput || []);
  if (!files.length) return;
  const existing = target === "initial"
    ? uploadedQuestionDocuments
    : target === "cse-pv"
      ? uploadedCsePreviousPvDocuments
      : uploadedFollowUpDocuments;
  const reserved = target === "follow-up"
    ? (currentAnalysisRequest?.attachments || uploadedQuestionDocuments).length
    : 0;
  const uniqueFiles = files.filter(
    (file) => !existing.some((item) => documentKey(item) === `${file.name.toLowerCase()}|${file.size}`)
  );
  if (reserved + existing.length + uniqueFiles.length > MAX_QUESTION_DOCUMENTS) {
    const status = target === "initial"
      ? questionDocumentStatus
      : target === "cse-pv"
        ? csePreviousPvStatus
        : followUpDocumentStatus;
    status.dataset.state = "error";
    status.textContent = "Trois documents maximum peuvent être analysés dans une même conversation.";
    return;
  }
  const invalid = files.find(
    (file) => !questionDocumentExtension(file.name) || file.size > MAX_QUESTION_DOCUMENT_BYTES
  );
  if (invalid) {
    const status = target === "initial"
      ? questionDocumentStatus
      : target === "cse-pv"
        ? csePreviousPvStatus
        : followUpDocumentStatus;
    status.dataset.state = "error";
    status.textContent = `${invalid.name} n’est pas accepté ou dépasse 5 Mo.`;
    return;
  }
  const status = target === "initial"
    ? questionDocumentStatus
    : target === "cse-pv"
      ? csePreviousPvStatus
      : followUpDocumentStatus;
  status.dataset.state = "";
  status.textContent = "Lecture locale des documents…";
  setQuestionDocumentLoading(true);
  try {
    const prepared = await Promise.all(
      uniqueFiles.map(async (file) => ({
        name: file.name,
        size: file.size,
        mime_type: file.type || "application/octet-stream",
        content_base64: await fileAsBase64(file)
      }))
    );
    if (target === "initial") uploadedQuestionDocuments = [...existing, ...prepared];
    else if (target === "cse-pv") uploadedCsePreviousPvDocuments = [...existing, ...prepared];
    else uploadedFollowUpDocuments = [...existing, ...prepared];
    if (target === "initial" || target === "cse-pv") resetCseAgendaPreview();
    updateQuestionDocumentDisplay();
    updateFollowUpDocumentDisplay();
    updateCsePreviousPvDisplay();
  } catch (error) {
    status.dataset.state = "error";
    status.textContent = error instanceof Error ? error.message : "Lecture locale impossible.";
  } finally {
    setQuestionDocumentLoading(false);
  }
}

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

function applyControlledPilotMode(pilot) {
  controlledPilot = {
    enabled: Boolean(pilot?.enabled),
    title: pilot?.title || "PILOTE LOCAL — VALIDATION HUMAINE OBLIGATOIRE",
    notice:
      pilot?.notice ||
      "Cette analyse est une aide à la préparation syndicale. Elle doit être vérifiée avant toute utilisation auprès d’un salarié, de l’employeur ou d’une instance."
  };
  for (const banner of [pilotBannerInput, pilotBannerResult, pilotBannerReport]) {
    if (!banner) continue;
    banner.hidden = !controlledPilot.enabled;
    if (controlledPilot.enabled) {
      const title = banner.querySelector("strong");
      const notice = banner.querySelector("span");
      if (title) title.textContent = controlledPilot.title;
      if (notice) notice.textContent = controlledPilot.notice;
    }
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
    title: "Posez votre question",
    description: "Écrivez comme vous parleriez à votre délégué. Nexus répond d’abord, puis demande seulement les précisions vraiment utiles.",
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

async function requestCseAgendaPreview() {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), ANALYZE_TIMEOUT_MS);
  let response;
  try {
    response = await fetch("/api/cse/agenda-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        attachments: uploadedQuestionDocuments,
        cse_previous_pv_attachments: uploadedCsePreviousPvDocuments
      }),
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
  const payload = parseNexusResponse(await response.text());
  if (!response.ok) {
    throw new NexusRequestError("http", httpErrorMessage(response, payload), response.status);
  }
  if (!payload?.ok || !payload.cse_agenda_analysis) {
    throw new NexusRequestError("business", payload?.error || "L’ordre du jour n’a pas pu être vérifié.");
  }
  return payload.cse_agenda_analysis;
}

function appendHighlightedExcerpt(container, value) {
  const text = String(value || "").trim();
  if (!text) return;
  const highlight = document.createElement("mark");
  highlight.className = "nexus-source-highlight";
  highlight.textContent = text;
  container.appendChild(highlight);
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
    "1_facts_understood": "1. Faits compris",
    "2_points_to_verify": "2. Ce qui reste à vérifier",
    "3_provisional_qualification": "3. Qualification provisoire",
    "4_real_disciplinary_risk": "4. Risque disciplinaire réel",
    "5_main_defense_line": "5. Ligne de défense principale",
    "6_questions_for_employee": "6. Questions à poser au salarié",
    "7_questions_for_management": "7. Questions à poser à la direction",
    "8_interview_preparation": "8. Préparation de l’entretien",
    "9_points_not_to_say": "9. Points à ne pas dire",
    "10_after_interview": "10. Action après entretien"
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

function publicSourcesForLayers(publicSummary) {
  return (publicSummary.source_extractions || publicSummary.sources || []).map((source) => {
    const provider = String(source.provider || "").trim();
    const title = String(source.title || "").trim();
    const status = String(source.availability_status || "").toUpperCase();
    return {
      document: [provider, title].filter(Boolean).join(" — ") || "Source métier",
      article_or_section: source.reference || "",
      excerpt: source.excerpt || "",
      source_layer: source.source_layer || "autre",
      source_quality_warning: status === "FOUND_VERSION_UNCERTAIN"
        ? "Version applicable à la date des faits à confirmer."
        : status === "TITLE_ONLY" || status === "METADATA_ONLY"
          ? "Référence repérée sans extrait exploitable."
          : ""
    };
  });
}

function renderSources(element, answer, orchestration, publicSummary = {}) {
  element.textContent = "";
  const publicSources = publicSourcesForLayers(publicSummary);
  const answerSources = Array.isArray(answer.sources) ? answer.sources : [];
  const layers = answer.source_layers || orchestration.source_layers || sourceLayerFallback(
    answerSources.length ? answerSources : publicSources
  );
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
        appendHighlightedExcerpt(excerpt, source.excerpt);
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
  if (printReportButton) printReportButton.disabled = true;
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

function summaryReportMarkdown(report) {
  const pilotLines = controlledPilot.enabled
    ? [`# ${controlledPilot.title}`, "", controlledPilot.notice, ""]
    : [];
  const lines = [`# ${report.title || "Synthèse opérationnelle Nexus"}`];
  lines.unshift(...pilotLines);
  if (report.nexus_version) lines.push("", `Version CFDT Nexus : ${report.nexus_version}`);
  for (const section of report.sections || []) {
    if (!section.items?.length) continue;
    lines.push("", `## ${section.title}`);
    for (const item of section.items) lines.push(`- ${String(item)}`);
  }
  return lines.join("\n");
}

function renderReport() {
  const report = currentPayload?.analysis_report;
  if (!report) {
    resetReportState("Aucun rapport Nexus n'est disponible pour cette analyse.");
    return;
  }
  currentReportMarkdown = summaryReportMarkdown(report);
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

  const detailedAnalysis = currentPayload?.detailed_analysis || {};
  const detailSections = [
    { title: "Faits détaillés", items: detailedAnalysis.factual_core },
    { title: "Sources secondaires", items: detailedAnalysis.secondary_sources },
    { title: "Sources écartées", items: detailedAnalysis.rejected_sources },
    { title: "Sources encore nécessaires", items: detailedAnalysis.source_requirements },
    { title: "Limites détaillées", items: detailedAnalysis.warnings }
  ].filter((section) =>
    Array.isArray(section.items)
      ? section.items.length
      : section.items && Object.keys(section.items).length
  );
  if (report.detail_available && detailSections.length) {
    const details = document.createElement("details");
    details.className = "report-details";
    const summary = document.createElement("summary");
    summary.textContent = "Afficher l’analyse détaillée";
    details.appendChild(summary);
    const note = document.createElement("p");
    note.className = "report-details-note";
    note.textContent =
      "Cette partie complète la synthèse. Elle n’est pas incluse dans la copie, l’impression ou l’export.";
    details.appendChild(note);
    for (const section of detailSections) {
      const values = Array.isArray(section.items)
        ? section.items.map((item) =>
            typeof item === "object" ? JSON.stringify(item, null, 2) : item
          )
        : Object.entries(section.items || {}).flatMap(([label, items]) =>
            (Array.isArray(items) ? items : [items]).map((item) => `${label} : ${item}`)
          );
      details.appendChild(reportBlock(section.title, values));
    }
    reportOutput.appendChild(details);
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
  if (printReportButton) printReportButton.disabled = !currentReportMarkdown;
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

function printReport() {
  if (!currentReportMarkdown) return;
  window.print();
}

function followUpQuestionText(item) {
  if (typeof item === "string") return item.trim();
  if (item && typeof item.question === "string") return item.question.trim();
  return "";
}

function renderFollowUpHistory() {
  followUpHistory.textContent = "";
  followUpHistory.hidden = followUpConversation.length === 0;
  if (!followUpConversation.length) return;
  const heading = document.createElement("strong");
  heading.textContent = `${followUpConversation.length} précision(s) déjà intégrée(s) à cette session`;
  const list = document.createElement("ul");
  for (const entry of followUpConversation) {
    const item = document.createElement("li");
    const question = document.createElement("strong");
    question.textContent = `${entry.question} : `;
    item.append(question, document.createTextNode(entry.answer));
    list.appendChild(item);
  }
  followUpHistory.append(heading, list);
}

function renderFollowUpForm(publicSummary) {
  followUpQuestions.textContent = "";
  followUpDocuments.textContent = "";
  followUpAdditional.value = "";
  followUpStatus.textContent = "";
  resetFollowUpDocuments();
  const answered = new Set(
    followUpConversation.map((entry) => entry.question.trim().toLocaleLowerCase())
  );
  const questions = (publicSummary.priority_questions || [])
    .map(followUpQuestionText)
    .filter((question) => question && !answered.has(question.toLocaleLowerCase()))
    .slice(0, usesConversationalEmployeeFlow() ? 1 : 10);
  questions.forEach((question, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "follow-up-field";
    const label = document.createElement("label");
    const fieldId = `followUpAnswer${index}`;
    label.htmlFor = fieldId;
    label.textContent = question;
    const field = document.createElement("textarea");
    field.id = fieldId;
    field.rows = 3;
    field.dataset.followUpQuestion = question;
    field.placeholder = "Réponse obtenue ou fait à confirmer";
    wrapper.append(label, field);
    followUpQuestions.appendChild(wrapper);
  });
  if (!questions.length) {
    const notice = document.createElement("p");
    notice.className = "follow-up-empty";
    notice.textContent =
      "Toutes les questions prioritaires déjà affichées ont reçu une réponse. Vous pouvez ajouter une autre précision.";
    followUpQuestions.appendChild(notice);
  }
  const suggestedDocuments = (publicSummary.documents || [])
    .map((item) =>
      typeof item === "string" ? item.trim() : String(item?.document || "").trim()
    )
    .filter(Boolean)
    .slice(0, 6);
  followUpDocuments.hidden = suggestedDocuments.length === 0;
  if (suggestedDocuments.length) {
    const heading = document.createElement("strong");
    heading.textContent = "Pièces à fournir seulement si elles sont utiles et disponibles";
    const notice = document.createElement("p");
    notice.textContent =
      "Ne bloquez pas l’échange pour les rechercher immédiatement. Indiquez ci-dessous ce que vous avez ou ce que la direction doit encore remettre.";
    const list = document.createElement("ul");
    for (const documentName of suggestedDocuments) {
      const item = document.createElement("li");
      item.textContent = documentName;
      list.appendChild(item);
    }
    followUpDocuments.append(heading, notice, list);
  }
  renderFollowUpHistory();
  factualEnrichmentPanel.hidden = false;
}

function collectFollowUpAnswers() {
  const rows = [];
  followUpQuestions.querySelectorAll("textarea[data-follow-up-question]").forEach((field) => {
    const answer = field.value.trim();
    const question = field.dataset.followUpQuestion?.trim();
    if (question && answer) rows.push({ question, answer });
  });
  const additional = followUpAdditional.value.trim();
  if (additional) {
    rows.push({
      question: "Quelle autre précision utile doit être intégrée au dossier ?",
      answer: additional
    });
  }
  return rows;
}

function conversationalDirectAnswer(answer, publicSummary, orchestration) {
  if (publicSummary.analysis_suspended) {
    const reason = String(publicSummary.urgency_reason || "").trim();
    return reason || "L’analyse est suspendue tant qu’une information indispensable manque.";
  }
  const candidates = [
    ...(publicSummary.syndical_position || []),
    ...(publicSummary.rule_to_facts || []).flatMap((item) => [
      item?.employee_argument,
      item?.conclusion
    ]),
    orchestration.reponse_synthetique_nexus
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);
  const unique = candidates.filter(
    (item, index, rows) =>
      rows.findIndex((candidate) => candidate.toLocaleLowerCase() === item.toLocaleLowerCase()) === index
  );
  return unique[0] ||
    "Nexus a besoin d’une précision supplémentaire pour vous répondre utilement.";
}

function conversationalNextSteps(answer, publicSummary) {
  const actions = [
    ...(publicSummary.next_actions || []),
    ...(publicSummary.strategy?.position || []),
    ...(publicSummary.strategy?.before || []),
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .filter(
      (item, index, rows) =>
        rows.findIndex((candidate) => candidate.toLocaleLowerCase() === item.toLocaleLowerCase()) === index
    )
    .slice(0, 2);
  return actions.join(" ") || (publicSummary.syndical_position || []).slice(0, 2).join(" ");
}

function renderConversationalSources(publicSummary) {
  chatbotSourcesList.textContent = "";
  const sources = (publicSummary.source_extractions || publicSummary.sources || [])
    .map((item) => ({
      provider: String(item?.provider || "").trim(),
      title: String(item?.title || "").trim(),
      reference: String(item?.reference || "").trim(),
      excerpt: String(item?.excerpt || "").trim(),
      linkToFacts: String(item?.link_to_facts || "").trim(),
      practicalScope: String(item?.practical_scope || item?.scope || "").trim(),
      reserve: String(item?.reserve || "").trim(),
      status: String(item?.availability_status || "").trim(),
    }))
    .filter((item) => item.title)
    .filter(
      (item, index, rows) =>
        rows.findIndex(
          (candidate) =>
            `${candidate.provider}|${candidate.title}`.toLocaleLowerCase() ===
            `${item.provider}|${item.title}`.toLocaleLowerCase()
        ) === index
    )
    .slice(0, 3);
  for (const source of sources) {
    const item = document.createElement("li");
    item.className = "chatbot-source-card";
    const title = document.createElement("strong");
    const label = source.provider
      ? `${source.provider} — ${source.title}`
      : source.title;
    title.textContent =
      source.status === "FOUND_VERSION_UNCERTAIN"
        ? `${label} (version applicable à confirmer)`
        : label;
    item.appendChild(title);
    if (source.reference) {
      const reference = document.createElement("p");
      reference.textContent = `Référence : ${source.reference}`;
      item.appendChild(reference);
    }
    if (source.excerpt) {
      const excerpt = document.createElement("blockquote");
      appendHighlightedExcerpt(excerpt, source.excerpt);
      item.appendChild(excerpt);
    }
    if (source.linkToFacts) {
      const use = document.createElement("p");
      use.textContent = `Lien avec votre situation : ${source.linkToFacts}`;
      item.appendChild(use);
    }
    if (source.practicalScope) {
      const scope = document.createElement("p");
      scope.className = "source-context-notice";
      scope.textContent = source.practicalScope;
      item.appendChild(scope);
    }
    if (source.reserve) {
      const reserve = document.createElement("p");
      reserve.className = "source-context-notice";
      reserve.textContent = `Réserve : ${source.reserve}`;
      item.appendChild(reserve);
    }
    chatbotSourcesList.appendChild(item);
  }
  chatbotConnectorsList.textContent = "";
  const connectors = (publicSummary.connector_activity || []).slice(0, 8);
  for (const connector of connectors) {
    const item = document.createElement("li");
    const label = String(connector.connector || "Connecteur officiel");
    const status = String(connector.status || "");
    const statusLabel = {
      RESULTAT_UTILISE: "résultat utilisé",
      CATALOGUE_SEULEMENT: "catalogue seulement, aucune preuve utilisée",
      INDISPONIBLE: "indisponible"
    }[status] || status;
    item.textContent = `${label} — ${statusLabel}. ${connector.explanation || ""}`.trim();
    chatbotConnectorsList.appendChild(item);
  }
  chatbotConnectorsSummary.hidden = connectors.length === 0;
  chatbotPvList.textContent = "";
  const pvContexts = (publicSummary.cse_context || [])
    .filter((item) => String(item?.excerpt || "").trim())
    .slice(0, 3);
  for (const context of pvContexts) {
    const item = document.createElement("li");
    item.className = "chatbot-source-card pv-context-card";
    const title = document.createElement("strong");
    title.textContent = [context.title, context.date].filter(Boolean).join(" — ") || "Ancien PV";
    const excerpt = document.createElement("blockquote");
    appendHighlightedExcerpt(excerpt, context.excerpt);
    const limit = document.createElement("p");
    limit.className = "source-context-notice";
    limit.textContent = (context.limits || []).join(" ") ||
      "Ce passage apporte un contexte factuel et ne constitue pas une norme juridique.";
    item.append(title, excerpt, limit);
    chatbotPvList.appendChild(item);
  }
  chatbotPvSummary.hidden = pvContexts.length === 0;
  chatbotSourcesSummary.hidden =
    !usesConversationalEmployeeFlow() ||
    (sources.length === 0 && connectors.length === 0 && pvContexts.length === 0);
}

async function refineAnalysisWithFollowUp() {
  if (!currentAnalysisRequest) return;
  const newRows = collectFollowUpAnswers();
  const newDocuments = [...uploadedFollowUpDocuments];
  if (!newRows.length && !newDocuments.length) {
    followUpStatus.textContent = "Répondez à une question, ajoutez une précision ou joignez un document.";
    return;
  }
  if (newDocuments.length) {
    newRows.push({
      question: "Quels documents ont été ajoutés à cette étape ?",
      answer: newDocuments.map((documentItem) => documentItem.name).join(", ")
    });
  }
  followUpConversation.push(...newRows);
  const requestPayload = {
    ...currentAnalysisRequest,
    attachments: [
      ...(currentAnalysisRequest.attachments || []),
      ...newDocuments
    ],
    portal_context: {
      ...(currentAnalysisRequest.portal_context || {}),
      follow_up_answers: followUpConversation.map(({ question, answer }) => ({
        question,
        answer
      })),
      conversation_round: followUpConversation.length
    }
  };
  refineAnalysisButton.disabled = true;
  followUpStatus.textContent = "Votre précision est intégrée aux faits. Nexus adapte la recherche et la réponse.";
  setStatus("Analyse enrichie...", null);
  showOnly("loading");
  try {
    const payload = await requestNexusAnalysis(requestPayload);
    currentAnalysisRequest = requestPayload;
    renderResult(payload);
    setStatus(
      "Réponse améliorée",
      payload.orchestration?.niveau_de_confiance || payload.answer.confidence
    );
  } catch (error) {
    const userMessage =
      error instanceof NexusRequestError
        ? error.message
        : "Une erreur interne Nexus est survenue.";
    renderError(userMessage);
    setStatus("Erreur", "faible");
    showOnly("result");
  } finally {
    refineAnalysisButton.disabled = false;
  }
}

function selectedCseAgendaPoints() {
  return Array.from(cseAgendaChoices.querySelectorAll('input[name="cseAgendaPoint"]:checked'))
    .map((input) => ({ position: input.value, title: input.dataset.title || "" }));
}

function updateCseAgendaAnalyzeButton() {
  if (currentWorkspace !== "cse") return;
  const count = selectedCseAgendaPoints().length;
  analyzeButton.disabled = count === 0;
  analyzeButton.textContent = count
    ? `Analyser et développer ${count} point(s) sélectionné(s)`
    : "Sélectionnez au moins un point";
}

function resetCseAgendaPreview() {
  currentCseAgendaPreview = null;
  if (cseAgendaChoices) cseAgendaChoices.textContent = "";
  if (cseAgendaSelection) cseAgendaSelection.hidden = true;
  if (cseAgendaVerificationStatus) cseAgendaVerificationStatus.textContent = "";
  if (currentWorkspace === "cse") {
    analyzeButton.hidden = true;
    analyzeButton.disabled = false;
  }
}

function renderCseAgendaSelection(analysis) {
  currentCseAgendaPreview = analysis;
  cseAgendaChoices.textContent = "";
  cseAgendaVerificationStatus.textContent =
    `${analysis.agenda_point_count} point(s) identifié(s) ; ` +
    `${analysis.points_with_previous_minutes} déjà rapproché(s) d’anciens PV. ` +
    `${analysis.uploaded_previous_minutes_count || 0} PV ajouté(s) manuellement. ` +
    `${analysis.corpus_notice || ""}`;
  (analysis.points || []).forEach((point) => {
    const label = document.createElement("label");
    label.className = "cse-agenda-choice";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "cseAgendaPoint";
    checkbox.value = point.position;
    checkbox.dataset.title = point.title;
    checkbox.addEventListener("change", updateCseAgendaAnalyzeButton);
    const content = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = `${point.display_label || `Point ${point.position}`} — ${point.title}`;
    const history = document.createElement("small");
    if (point.previously_discussed) {
      const references = (point.previous_minutes || [])
        .map((item) => [item.title, item.date].filter(Boolean).join(" — "))
        .filter(Boolean)
        .slice(0, 2);
      history.textContent = `Déjà traité : ${references.join(" ; ")}.`;
      history.dataset.previous = "true";
    } else {
      history.textContent = "Aucun passage comparable retrouvé dans les PV disponibles.";
    }
    content.append(title, history);
    label.append(checkbox, content);
    cseAgendaChoices.appendChild(label);
  });
  const allPoints = analysis.points || [];
  const directionCount = allPoints.filter((point) => String(point.position || "").startsWith("D")).length;
  const memberCount = allPoints.length - directionCount;
  cseAgendaVerificationStatus.textContent =
    `${directionCount} point(s) de la Direction et ${memberCount} question(s) des membres identifiés ; ` +
    `${analysis.points_with_previous_minutes} déjà rapproché(s) d’anciens PV. ` +
    `${analysis.uploaded_previous_minutes_count || 0} PV ajouté(s) manuellement. ` +
    `${analysis.corpus_notice || ""}`;

  const choiceLabels = Array.from(cseAgendaChoices.children);
  const appendChoiceGroup = (titleText, helpText, labels, groupKind) => {
    if (!labels.length) return;
    const section = document.createElement("section");
    section.className = `cse-agenda-group ${groupKind}`;
    const heading = document.createElement("div");
    heading.className = "cse-agenda-group-heading";
    const headingText = document.createElement("div");
    const title = document.createElement("h4");
    title.textContent = `${titleText} (${labels.length})`;
    const help = document.createElement("p");
    help.textContent = helpText;
    headingText.append(title, help);
    const selectButton = document.createElement("button");
    selectButton.type = "button";
    selectButton.className = "text-button";
    selectButton.textContent = "Tout sélectionner";
    selectButton.addEventListener("click", () => {
      section.querySelectorAll('input[name="cseAgendaPoint"]').forEach((input) => {
        input.checked = true;
      });
      updateCseAgendaAnalyzeButton();
    });
    heading.append(headingText, selectButton);
    const list = document.createElement("div");
    list.className = "cse-agenda-group-list";
    labels.forEach((label) => list.appendChild(label));
    section.append(heading, list);
    cseAgendaChoices.appendChild(section);
  };
  appendChoiceGroup(
    "Points mis à l’ordre du jour par la Direction",
    "Projets, informations et consultations présentés par la Direction.",
    choiceLabels.filter((label) => String(label.querySelector("input")?.value || "").startsWith("D")),
    "direction"
  );
  appendChoiceGroup(
    "Questions des membres et organisations syndicales",
    "Questions à développer et à rapprocher des anciens PV.",
    choiceLabels.filter((label) => !String(label.querySelector("input")?.value || "").startsWith("D")),
    "members"
  );
  cseAgendaSelection.hidden = false;
  analyzeButton.hidden = false;
  updateCseAgendaAnalyzeButton();
}

async function verifyCseAgenda() {
  wizardError.hidden = true;
  if (!uploadedQuestionDocuments.length) {
    wizardError.textContent = "Choisissez ou déposez d’abord l’ordre du jour.";
    wizardError.hidden = false;
    return;
  }
  verifyCseAgendaButton.disabled = true;
  cseAgendaVerificationStatus.textContent = "Lecture de l’ordre du jour et comparaison avec les anciens PV…";
  try {
    const analysis = await requestCseAgendaPreview();
    if (analysis.status !== "READY") {
      throw new NexusRequestError("business", analysis.message || "Ordre du jour illisible.");
    }
    renderCseAgendaSelection(analysis);
  } catch (error) {
    currentCseAgendaPreview = null;
    cseAgendaSelection.hidden = true;
    cseAgendaVerificationStatus.textContent = error instanceof Error
      ? error.message
      : "La vérification de l’ordre du jour a échoué.";
  } finally {
    verifyCseAgendaButton.disabled = false;
  }
}

function appendCseList(container, values) {
  const list = document.createElement("ul");
  (values || []).forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
  container.appendChild(list);
}

function renderCseAgendaAnalysis(analysis) {
  cseAgendaPoints.innerHTML = "";
  cseAgendaPanel.hidden = currentWorkspace !== "cse" || !analysis;
  if (cseAgendaPanel.hidden) return;

  if (analysis.status !== "READY") {
    cseAgendaSummary.textContent = analysis.message ||
      "Importez un ordre du jour lisible pour lancer la préparation du CSE.";
    return;
  }

  const previousCount = Number(analysis.points_with_previous_minutes || 0);
  cseAgendaSummary.textContent =
    `${analysis.agenda_point_count} point(s) analysé(s) dans ${analysis.agenda_document}. ` +
    `${previousCount} point(s) rapproché(s) d’anciens PV. ${analysis.corpus_notice || ""}`;

  (analysis.points || []).forEach((point) => {
    const card = document.createElement("article");
    card.className = "cse-agenda-point";

    const heading = document.createElement("div");
    heading.className = "cse-agenda-point-heading";
    const title = document.createElement("h3");
    title.textContent = `Point ${point.position} — ${point.title}`;
    const badge = document.createElement("span");
    badge.className = point.previously_discussed
      ? "cse-agenda-badge previous"
      : "cse-agenda-badge";
    badge.textContent = point.previously_discussed
      ? "Sujet retrouvé dans un ancien PV"
      : "Aucun précédent retrouvé";
    heading.append(title, badge);
    card.appendChild(heading);

    const analysisText = document.createElement("p");
    analysisText.className = "cse-agenda-analysis-text";
    analysisText.textContent = point.analysis;
    card.appendChild(analysisText);

    if ((point.previous_minutes || []).length) {
      const previousTitle = document.createElement("h4");
      previousTitle.textContent = "Ce qui a déjà été traité";
      card.appendChild(previousTitle);
      const previousGrid = document.createElement("div");
      previousGrid.className = "cse-previous-minutes";
      point.previous_minutes.forEach((previous) => {
        const source = document.createElement("section");
        source.className = "cse-previous-minute";
        const sourceTitle = document.createElement("strong");
        sourceTitle.textContent = [previous.title, previous.date, previous.instance]
          .filter(Boolean)
          .join(" — ");
        const excerpt = document.createElement("mark");
        excerpt.className = "nexus-source-highlight";
        excerpt.textContent = previous.excerpt || "Extrait non disponible.";
        const relation = document.createElement("p");
        relation.textContent = previous.relation ||
          "Passage rapproché du point par les termes factuels du sujet.";
        const limit = document.createElement("small");
        limit.textContent = (previous.limits || []).join(" ");
        source.append(sourceTitle, excerpt, relation, limit);
        previousGrid.appendChild(source);
      });
      card.appendChild(previousGrid);
    }

    const questionsTitle = document.createElement("h4");
    questionsTitle.textContent = "Questions pertinentes à poser à la direction";
    card.appendChild(questionsTitle);
    appendCseList(card, point.questions_for_management);

    const checks = document.createElement("details");
    const checksTitle = document.createElement("summary");
    checksTitle.textContent = "Points à vérifier avant la réunion";
    checks.appendChild(checksTitle);
    appendCseList(checks, point.checks_before_meeting);
    card.appendChild(checks);
    cseAgendaPoints.appendChild(card);
  });
}

function renderResult(payload) {
  applyControlledPilotMode(payload.controlled_pilot || controlledPilot);
  currentPayload = payload;
  const conversationalFlow = usesConversationalEmployeeFlow();
  statusPill.classList.toggle("chatbot-status-hidden", conversationalFlow);
  resultView.classList.toggle("chatbot-result", conversationalFlow);
  resultView.classList.remove("chatbot-details-open");
  chatbotDetailsButton.hidden = !conversationalFlow;
  chatbotDetailsButton.textContent = "Voir les sources et le détail";
  factualEnrichmentPanel.querySelector("h2").textContent = conversationalFlow
    ? "Poursuivre la discussion"
    : "Répondre aux questions et mettre à jour l’analyse";
  documentsSummaryPanel.hidden = usesConversationalEmployeeFlow();
  generalFollowupGrid.classList.toggle(
    "single-panel",
    usesConversationalEmployeeFlow()
  );
  addDocumentButton.textContent = usesConversationalEmployeeFlow()
    ? "Signaler une pièce dans la discussion"
    : "Ajouter un document";
  const answer = payload.answer;
  const orchestration = payload.orchestration || {};
  const finalAssistant = payload.final_assistant_runtime?.assistant || null;
  const finalSummary = finalAssistant?.summary || {};
  const finalTrace = finalAssistant?.trace || {};
  const publicSummary = payload.public_summary || answer.public_summary || {};
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
  shortAnswer.textContent = conversationalFlow
    ? conversationalDirectAnswer(answer, publicSummary, orchestration)
    : (publicSummary.situation || []).join(" ") ||
      orchestration.reponse_synthetique_nexus ||
      answer.short_answer ||
      "A completer.";
  workingPosition.textContent = conversationalFlow
    ? conversationalNextSteps(answer, publicSummary)
    : (publicSummary.syndical_position || []).join(" ") ||
      orchestration.position_de_travail ||
      answer.working_position ||
      "A completer.";
  renderCseAgendaAnalysis(payload.cse_agenda_analysis || null);
  renderConversationalSources(publicSummary);
  renderSources(sourcesList, answer, orchestration, publicSummary);
  fillList(findingsList, publicSummary.strengths || answer.findings || []);
  fillList(
    documentsList,
    (publicSummary.documents || []).map((item) => item.document) ||
      finalSummary.documents_or_actions ||
      orchestration.documents_necessaires ||
      answer.documents_to_request ||
      []
  );
  fillList(
    questionsList,
    (publicSummary.priority_questions || []).map(
      (item) => `${item.target} — ${item.question}`
    ) ||
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
  renderFollowUpForm(publicSummary);
  factualEnrichmentPanel.hidden = false;
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
  resultModeNotice.textContent = conversationalFlow
    ? publicSummary.analysis_suspended === true
      ? "Nexus attend une précision déterminante avant de lancer une recherche documentaire ciblée."
      : "Nexus a recherché les documents pertinents à partir des faits actuellement connus."
    : finalEnabled
      ? "L’Assistant avancé a enrichi cette analyse."
      : "Analyse avancée non activée : Nexus utilise le moteur historique.";
  analysisState.hidden = true;
  wizardView.hidden = true;
  homeView.hidden = true;
  resultView.hidden = false;
  editInformationButton.textContent = conversationalFlow
    ? "← Modifier la question"
    : "← Modifier les informations";
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

function normalizeHistoricalSearch(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function historicalMatches(item, query, category) {
  if (category !== "all" && !(item.categories || []).includes(category)) {
    return false;
  }
  const normalizedQuery = normalizeHistoricalSearch(query);
  if (!normalizedQuery) return true;
  const searchable = [
    item.id,
    item.title,
    item.domain,
    item.path_label,
    ...(item.keywords || [])
  ]
    .map(normalizeHistoricalSearch)
    .join(" ");
  return searchable.includes(normalizedQuery);
}

function historyBadge(text, variant = "") {
  const badge = document.createElement("span");
  badge.className = `history-badge ${variant}`.trim();
  badge.textContent = text;
  return badge;
}

function renderHistoricalFilters() {
  historyFilters.textContent = "";
  for (const filter of historicalCatalog?.filters || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-filter";
    button.textContent = filter.label;
    button.dataset.filter = filter.id;
    button.setAttribute(
      "aria-pressed",
      String(historicalSelectedFilter === filter.id)
    );
    button.addEventListener("click", () => {
      historicalSelectedFilter = filter.id;
      renderHistoricalFilters();
      renderHistoricalCards();
    });
    historyFilters.appendChild(button);
  }
}

function historyStateClass(state) {
  if (state === "SUSPENDU") return "is-suspended";
  if (state === "LIMITÉ PAR SOURCE ABSENTE") return "is-limited";
  return "is-analyzed";
}

function renderHistoricalCards() {
  historyCases.textContent = "";
  const query = historySearch.value;
  const matches = (historicalCatalog?.cases || []).filter((item) =>
    historicalMatches(item, query, historicalSelectedFilter)
  );
  historyResultCount.textContent = `${matches.length} dossier${matches.length > 1 ? "s" : ""} affiché${matches.length > 1 ? "s" : ""} sur 11`;
  historyEmpty.hidden = matches.length !== 0;

  for (const item of matches) {
    const card = document.createElement("article");
    card.className = `history-card ${historyStateClass(item.state)}`;

    const headingRow = document.createElement("div");
    headingRow.className = "history-card-heading";
    const id = document.createElement("strong");
    id.textContent = `Dossier ${String(item.id || "").slice(-2)}`;
    const score = document.createElement("span");
    score.className = "history-card-score";
    score.textContent = `Score historique ${item.score}/100`;
    headingRow.append(id, score);

    const title = document.createElement("h3");
    title.textContent = item.title;
    const domain = document.createElement("p");
    domain.className = "history-card-domain";
    domain.textContent = item.domain;
    const capacity = document.createElement("p");
    capacity.className = "history-card-capacity";
    capacity.textContent = item.capacity;
    const path = document.createElement("p");
    path.className = "history-card-path";
    path.textContent = `Parcours : ${item.path_label}`;

    const badges = document.createElement("div");
    badges.className = "history-card-badges";
    badges.append(
      historyBadge(item.state, historyStateClass(item.state)),
      historyBadge(item.test_status),
      historyBadge(`V${item.validated_version}`)
    );

    const button = document.createElement("button");
    button.type = "button";
    button.className = "primary-button history-open-button";
    button.textContent = "Voir le dossier traité";
    button.setAttribute(
      "aria-label",
      `Voir le dossier traité — ${item.title}`
    );
    button.addEventListener("click", () => openHistoricalCase(item.id));

    card.append(headingRow, title, capacity, domain, path, badges, button);
    historyCases.appendChild(card);
  }
}

function appendHistoricalSection(
  title,
  values,
  formatter = (item) => String(item),
  container = historySections
) {
  const normalized = Array.isArray(values)
    ? values.filter(Boolean)
    : values
      ? [values]
      : [];
  if (!normalized.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const list = document.createElement("ul");
  for (const value of normalized) {
    const item = document.createElement("li");
    item.textContent = formatter(value);
    list.appendChild(item);
  }
  section.append(heading, list);
  container.appendChild(section);
}

function appendHistoricalRules(rules, container = historySections) {
  if (!Array.isArray(rules) || !rules.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section";
  const heading = document.createElement("h3");
  heading.textContent = "Règles principales comparées aux faits";
  section.appendChild(heading);

  for (const rule of rules) {
    const card = document.createElement("article");
    card.className = "history-rule-card";
    const source = document.createElement("h4");
    source.textContent = rule.source || "Source à vérifier";
    const ruleText = document.createElement("p");
    ruleText.className = "history-rule-excerpt";
    if (rule.rule) appendHighlightedExcerpt(ruleText, rule.rule);
    else ruleText.textContent = "Règle non restituée.";
    card.append(source, ruleText);

    const positions = [
      ["Position possible du salarié", rule.employee_argument],
      ["Position possible de la direction", rule.employer_argument],
      ["Conclusion testée", rule.conclusion],
      ["Action suivante", rule.next_action]
    ];
    for (const [label, value] of positions) {
      if (!value) continue;
      const paragraph = document.createElement("p");
      const strong = document.createElement("strong");
      strong.textContent = `${label} : `;
      paragraph.append(strong, document.createTextNode(String(value)));
      card.appendChild(paragraph);
    }
    section.appendChild(card);
  }
  container.appendChild(section);
}

function appendHistoricalStrategy(strategy, container = historySections) {
  if (!strategy || typeof strategy !== "object") return;
  const values = [
    ...(strategy.before || []).map((item) => `Avant : ${item}`),
    ...(strategy.during || []).map((item) => `Pendant : ${item}`),
    ...(strategy.position || []).map((item) => `Position : ${item}`)
  ];
  appendHistoricalSection("Stratégie syndicale", values, (item) => String(item), container);
}

function appendUnionCaseQuestionAnswers(rows) {
  if (!Array.isArray(rows) || !rows.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section union-case-section union-case-exchange";
  const heading = document.createElement("h3");
  heading.textContent = "Questions et réponses du dossier";
  const intro = document.createElement("p");
  intro.className = "union-case-intro";
  intro.textContent =
    "Les réponses ci-dessous reprennent uniquement les faits et constats présents dans le cas validé.";
  section.append(heading, intro);
  for (const row of rows) {
    const card = document.createElement("article");
    card.className = "union-case-qa";
    const question = document.createElement("h4");
    question.textContent = row.question;
    const status = document.createElement("p");
    status.className = "union-case-answer-status";
    status.textContent = row.answer_status;
    const answers = document.createElement("ul");
    for (const answer of row.answers || []) {
      const item = document.createElement("li");
      item.textContent = answer;
      answers.appendChild(item);
    }
    card.append(question, status, answers);
    section.appendChild(card);
  }
  historySections.appendChild(section);
}

function appendUnionCaseOpenQuestions(rows) {
  if (!Array.isArray(rows) || !rows.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section union-case-section";
  const heading = document.createElement("h3");
  heading.textContent = "Questions encore ouvertes";
  section.appendChild(heading);
  for (const row of rows) {
    const card = document.createElement("article");
    card.className = "union-case-open-question";
    const question = document.createElement("h4");
    question.textContent = row.question;
    const meta = document.createElement("p");
    meta.className = "union-case-answer-status";
    meta.textContent = `À poser à : ${row.asked_to}`;
    const answer = document.createElement("p");
    answer.textContent = row.answer;
    card.append(question, meta);
    if (row.reason) {
      const reason = document.createElement("p");
      reason.textContent = `Pourquoi : ${row.reason}`;
      card.appendChild(reason);
    }
    card.appendChild(answer);
    section.appendChild(card);
  }
  historySections.appendChild(section);
}

function appendUnionCaseSources(sources) {
  if (!Array.isArray(sources) || !sources.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section union-case-section union-case-sources";
  const heading = document.createElement("h3");
  heading.textContent = "Sources déterminantes";
  const intro = document.createElement("p");
  intro.className = "union-case-intro";
  intro.textContent = "Cinq sources au maximum, classées pour leur utilité concrète dans le dossier.";
  section.append(heading, intro);
  for (const source of sources) {
    const card = document.createElement("article");
    card.className = "union-case-source";
    const title = document.createElement("h4");
    title.textContent = source.title;
    card.appendChild(title);
    if (source.reference) {
      const reference = document.createElement("p");
      reference.className = "union-case-source-reference";
      reference.textContent = `Référence : ${source.reference}`;
      card.appendChild(reference);
    }
    if (source.excerpt) {
      const excerpt = document.createElement("blockquote");
      excerpt.className = "union-case-source-excerpt";
      appendHighlightedExcerpt(excerpt, source.excerpt);
      card.appendChild(excerpt);
    }
    const practicalUse = document.createElement("p");
    practicalUse.textContent = `Lien avec les faits : ${
      source.practical_use || "utilité pratique à confirmer avec les faits et la version applicable."
    }`;
    card.appendChild(practicalUse);
    if (source.reserve) {
      const reserve = document.createElement("p");
      reserve.className = "union-case-source-reserve";
      reserve.textContent = `Réserve : ${source.reserve}`;
      card.appendChild(reserve);
    }
    const meta = document.createElement("p");
    meta.className = "union-case-source-meta";
    meta.textContent = `${source.nature} · ${source.status}`;
    card.appendChild(meta);
    section.appendChild(card);
  }
  historySections.appendChild(section);
}

function appendHistoricalPvContext(contexts) {
  if (!Array.isArray(contexts) || !contexts.length) return;
  const usable = contexts.filter((item) => String(item?.excerpt || "").trim()).slice(0, 3);
  if (!usable.length) return;
  const section = document.createElement("section");
  section.className = "history-detail-section union-case-section historical-pv-context";
  const heading = document.createElement("h3");
  heading.textContent = "Extraits pertinents des anciens PV";
  const notice = document.createElement("p");
  notice.className = "source-context-notice";
  notice.textContent = "Ces passages documentent le contexte collectif. Ils ne constituent pas une norme juridique.";
  section.append(heading, notice);
  for (const context of usable) {
    const card = document.createElement("article");
    card.className = "union-case-source pv-context-card";
    const title = document.createElement("h4");
    title.textContent = [context.title, context.date].filter(Boolean).join(" — ") || "Ancien PV";
    const excerpt = document.createElement("blockquote");
    excerpt.className = "union-case-source-excerpt";
    appendHighlightedExcerpt(excerpt, context.excerpt);
    const limit = document.createElement("p");
    limit.className = "source-context-notice";
    limit.textContent = (context.limits || []).join(" ") ||
      "Passage contextuel uniquement ; il ne prouve pas à lui seul une obligation juridique.";
    card.append(title, excerpt, limit);
    section.appendChild(card);
  }
  historySections.appendChild(section);
}

function appendUnionCaseDocuments(rows) {
  appendHistoricalSection(
    "Pièces encore utiles si elles deviennent nécessaires",
    rows || [],
    (item) =>
      `${item.document}${item.reason ? ` — ${item.reason}` : ""}${item.priority ? ` [${item.priority}]` : ""}`
  );
}

function appendUnionCaseConclusion(conclusion) {
  if (!conclusion || typeof conclusion !== "object") return;
  const section = document.createElement("section");
  section.className = "history-detail-section union-case-conclusion";
  const heading = document.createElement("h3");
  heading.textContent = "Conclusion et conseils syndicaux";
  const headline = document.createElement("p");
  headline.className = "union-case-conclusion-headline";
  headline.textContent = conclusion.headline;
  section.append(heading, headline);

  const groups = [
    ["Position retenue", conclusion.position || []],
    ["Conseils syndicaux", conclusion.advice || []],
    ["Limites à garder en tête", conclusion.limits || []]
  ];
  for (const [label, values] of groups) {
    if (!values.length) continue;
    const title = document.createElement("h4");
    title.textContent = label;
    const list = document.createElement("ul");
    for (const value of values) {
      const item = document.createElement("li");
      item.textContent = value;
      list.appendChild(item);
    }
    section.append(title, list);
  }
  const warning = document.createElement("p");
  warning.className = "union-case-warning";
  warning.textContent = conclusion.warning;
  section.appendChild(warning);
  historySections.appendChild(section);
}

function appendHistoricalTechnicalAnalysis(detail, summary, notes) {
  const details = document.createElement("details");
  details.className = "history-technical-analysis";
  const toggle = document.createElement("summary");
  toggle.textContent = "Voir l’analyse technique validée";
  const content = document.createElement("div");
  content.className = "history-technical-content";
  details.append(toggle, content);

  const sourceStatusAtTest = detail.source_status_at_test || {};
  appendHistoricalSection(
    "Sources disponibles lors du test V1",
    sourceStatusAtTest.retrieved_sources || [],
    (item) =>
      `${item.provider || "Source"} — ${item.title || "Titre non restitué"}${item.nature ? ` — ${item.nature}` : ""} [${item.status || "DISPONIBLE"}]`,
    content
  );
  appendHistoricalSection(
    "Sources encore à obtenir lors du test V1",
    sourceStatusAtTest.sources_to_obtain || [],
    (item) => String(item),
    content
  );
  appendHistoricalRules(summary.rule_to_facts || [], content);
  appendHistoricalStrategy(summary.strategy, content);
  appendHistoricalSection(
    "Résultat du test V1",
    [
      `${detail.test_status} — ${detail.score}/100 — ${detail.state}`,
      detail.score_explanation
    ],
    (item) => String(item),
    content
  );
  if (notes.length) {
    appendHistoricalSection(
      "Limites particulières validées",
      notes,
      (item) => String(item),
      content
    );
  }
  historySections.appendChild(details);
}

function historicalCaseText(detail) {
  const dossier = detail.union_case_file || {};
  const conclusion = dossier.conclusion || {};
  const lines = [
    `${dossier.public_reference || "Dossier"} — ${detail.title}`,
    `Domaine : ${detail.domain}`,
    `Capacité démontrée : ${dossier.capacity || detail.capacity || ""}`,
    `Statut : ${detail.state}`,
    "",
    "QUESTIONS ET RÉPONSES",
    ...(dossier.question_answer_exchange || []).flatMap((row) => [
      `Question : ${row.question}`,
      ...(row.answers || []).map((answer) => `Réponse : ${answer}`)
    ]),
    "",
    "QUESTIONS ENCORE OUVERTES",
    ...(dossier.open_questions || []).map(
      (row) => `- ${row.question} — ${row.answer}`
    ),
    "",
    "CONCLUSION ET CONSEILS SYNDICAUX",
    conclusion.headline || "",
    ...(conclusion.position || []).map((item) => `- ${item}`),
    ...(conclusion.advice || []).map((item) => `- ${item}`),
    "",
    conclusion.warning || ""
  ];
  return lines.join("\n").trim();
}

function renderHistoricalDetail(detail) {
  currentHistoricalCase = detail;
  historyListPanel.hidden = true;
  historyDetail.hidden = false;
  historyDetailId.textContent =
    detail.union_case_file?.public_reference ||
    `Dossier ${String(detail.id || "").slice(-2)}`;
  historyDetailTitle.textContent = detail.title;
  historyDetailMeta.textContent = `${detail.domain} · ${detail.path_label} · Dossier anonymisé`;
  historyDetailScore.textContent = detail.score;
  historyDetailBadges.textContent = "";
  historyDetailBadges.append(
    historyBadge(detail.state, historyStateClass(detail.state)),
    historyBadge(detail.test_status)
  );
  historySpecialNotes.textContent = "";
  const notes = detail.special_notes || [];
  historySpecialNotes.hidden = notes.length === 0;
  if (notes.length) {
    const heading = document.createElement("h3");
    heading.textContent = "Limite particulière";
    const list = document.createElement("ul");
    for (const note of notes) {
      const item = document.createElement("li");
      item.textContent = note;
      list.appendChild(item);
    }
    historySpecialNotes.append(heading, list);
  }

  const summary = detail.public_summary || {};
  const dossier = detail.union_case_file || {};
  historySections.textContent = "";
  const dossierIntro = document.createElement("section");
  dossierIntro.className = "history-detail-section union-case-overview";
  const dossierLabel = document.createElement("p");
  dossierLabel.className = "eyebrow";
  dossierLabel.textContent = dossier.public_reference || "Dossier syndical";
  const capacityTitle = document.createElement("h3");
  capacityTitle.textContent = "Ce que ce dossier démontre";
  const capacity = document.createElement("p");
  capacity.className = "union-case-capacity";
  capacity.textContent = dossier.capacity || detail.capacity;
  dossierIntro.append(dossierLabel, capacityTitle, capacity);
  historySections.appendChild(dossierIntro);

  appendUnionCaseQuestionAnswers(dossier.question_answer_exchange || []);
  appendUnionCaseOpenQuestions(dossier.open_questions || []);
  appendUnionCaseSources(dossier.determinant_sources || []);
  appendHistoricalPvContext(summary.cse_context || []);
  appendUnionCaseDocuments(dossier.documents_still_needed || []);
  appendUnionCaseConclusion(dossier.conclusion || {});
  appendHistoricalTechnicalAnalysis(detail, summary, notes);
  historyCopyStatus.textContent = "";
  historySourceRefresh.hidden = true;
  historySourceRefresh.textContent = "";
  historyRefreshSourcesButton.disabled = false;
  historyDetail.focus();
  window.scrollTo({top: 0, behavior: "smooth"});
}

function sourceRefreshLine(item) {
  if (!item || typeof item !== "object") return String(item || "");
  return [
    item.provider,
    item.title,
    item.article_or_clause,
    item.excerpt,
    item.availability_status,
    item.message
  ].filter(Boolean).join(" — ");
}

async function refreshHistoricalSources() {
  if (!currentHistoricalCase) return;
  historyRefreshSourcesButton.disabled = true;
  historyCopyStatus.textContent = "Actualisation documentaire en cours…";
  try {
    const response = await fetch(
      `/api/historical-cases/${encodeURIComponent(currentHistoricalCase.id)}/refresh-sources`
    );
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Actualisation documentaire indisponible.");
    }
    const refresh = payload.refresh;
    historySourceRefresh.textContent = "";
    historySourceRefresh.hidden = false;
    const heading = document.createElement("h3");
    heading.textContent = "Analyse documentaire actuelle";
    const date = document.createElement("p");
    date.textContent = `Dernière actualisation : ${new Date(refresh.last_refreshed_at).toLocaleString("fr-FR")}. Le score V1 reste ${refresh.score}/100.`;
    historySourceRefresh.append(heading, date);
    const currentSources =
      refresh.current_documentary_analysis?.sources || [];
    const groups = [
      ["Sources actuellement retrouvées", currentSources],
      ["Nouvelles sources depuis le test", refresh.newly_found || []],
      ["Sources toujours absentes ou à clarifier", refresh.still_absent || []]
    ];
    for (const [title, rows] of groups) {
      if (!rows.length) continue;
      const label = document.createElement("h4");
      label.textContent = title;
      const list = document.createElement("ul");
      rows.forEach((item) => {
        const row = document.createElement("li");
        row.textContent = sourceRefreshLine(item);
        list.appendChild(row);
      });
      historySourceRefresh.append(label, list);
    }
    historyCopyStatus.textContent =
      "Sources actualisées séparément. L’analyse et le score historiques sont inchangés.";
  } catch (_error) {
    historyCopyStatus.textContent =
      "Les sources n’ont pas pu être actualisées. L’analyse historique reste inchangée.";
  } finally {
    historyRefreshSourcesButton.disabled = false;
  }
}

async function openHistoricalCase(caseId) {
  historyCopyStatus.textContent = "Chargement de la synthèse publique…";
  try {
    const response = await fetch(`/api/historical-cases/${encodeURIComponent(caseId)}`);
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Cas historique indisponible.");
    }
    renderHistoricalDetail(payload.case);
  } catch (_error) {
    historyCopyStatus.textContent =
      "La synthèse historique ne peut pas être chargée.";
  }
}

async function openHistoricalCases() {
  showOnly("history");
  historyListPanel.hidden = false;
  historyDetail.hidden = true;
  currentHistoricalCase = null;
  try {
    if (!historicalCatalog) {
      const response = await fetch("/api/historical-cases");
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "Historique indisponible.");
      }
      historicalCatalog = payload;
    }
    historyAverage.textContent = Number(historicalCatalog.score_average)
      .toFixed(2)
      .replace(".", ",");
    historyVersion.textContent = `Dossiers anonymisés issus de la validation V${historicalCatalog.product_version}`;
    historyWarning.textContent = historicalCatalog.warning;
    historyScoreExplanation.textContent = historicalCatalog.score_explanation;
    renderHistoricalFilters();
    renderHistoricalCards();
    historyView.focus();
  } catch (_error) {
    historyCases.textContent = "";
    historyEmpty.hidden = false;
    historyEmpty.textContent =
      "Les cas historiques ne peuvent pas être chargés.";
  }
}

async function copyHistoricalCase() {
  if (!currentHistoricalCase) return;
  const text = historicalCaseText(currentHistoricalCase);
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
  } else {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  historyCopyStatus.textContent = "Synthèse publique copiée.";
}

function printHistoricalCase() {
  if (!currentHistoricalCase) return;
  document.body.classList.add("print-historical-case");
  window.print();
  window.setTimeout(
    () => document.body.classList.remove("print-historical-case"),
    500
  );
}

function showHistoricalList() {
  historyDetail.hidden = true;
  historyListPanel.hidden = false;
  currentHistoricalCase = null;
  historyCopyStatus.textContent = "";
  historySearch.focus();
  window.scrollTo({top: 0, behavior: "smooth"});
}

const localCaseStatusLabels = {
  OPEN: "Ouvert",
  IN_PROGRESS: "En cours",
  WAITING: "En attente",
  CLOSED: "Clôturé",
  CANCELLED: "Annulé"
};

function caseText(value) {
  if (typeof value === "string") return value.trim();
  if (value && typeof value.text === "string") return value.text.trim();
  if (value && typeof value.document === "string") return value.document.trim();
  if (value && typeof value.action === "string") return value.action.trim();
  if (value && typeof value.question === "string") return value.question.trim();
  return "";
}

function currentCaseDraft() {
  const publicSummary = currentPayload?.report?.public_summary || {};
  const answer = currentPayload?.answer || {};
  const storedSummary = Object.keys(publicSummary).length
    ? publicSummary
    : {
        situation_summary: shortAnswer.textContent.trim(),
        working_position: workingPosition.textContent.trim(),
        domains: answer.route?.domains || [],
        documents: answer.documents_to_request || [],
        priority_questions: answer.questions_to_ask || [],
        limits: answer.warnings || []
      };
  return {
    title: newCaseTitle.value.trim(),
    status: newCaseStatus.value,
    question:
      currentAnalysisRequest?.portal_context?.user_question ||
      resultQuestion.textContent.trim(),
    public_summary: storedSummary,
    follow_up_answers: followUpConversation.map(({ question, answer: value }) => ({
      question,
      answer: value
    })),
    documents:
      storedSummary.documents ||
      answer.documents_to_request ||
      [],
    uploaded_documents: (storedSummary.uploaded_documents || []).map((item) => ({
      title: String(item?.title || "").trim(),
      format: String(item?.format || "").trim(),
      page_count: item?.page_count || null,
      paragraph_count: item?.paragraph_count || null,
      truncated: Boolean(item?.truncated),
      status: String(item?.status || "").trim()
    })),
    actions:
      storedSummary.priority_actions ||
      storedSummary.actions ||
      (answer.next_action ? [answer.next_action] : []),
    notes: newCaseNotes.value.trim(),
    final_decision: {}
  };
}

async function localCaseRequest(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || "Dossier local indisponible.");
  }
  return payload;
}

function openCaseSaveDialog() {
  if (!currentPayload) return;
  newCaseTitle.value = "";
  newCaseStatus.value = "OPEN";
  newCaseNotes.value = "";
  newCaseSaveStatus.textContent = "";
  caseSaveDialog.showModal();
  newCaseTitle.focus();
}

async function createLocalCase(event) {
  event.preventDefault();
  newCaseSaveStatus.textContent = "Enregistrement local…";
  try {
    const payload = await localCaseRequest("/api/local-cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentCaseDraft())
    });
    caseSaveDialog.close();
    setStatus(`Dossier ${payload.case.case_ref} enregistré`, "local");
  } catch (error) {
    newCaseSaveStatus.textContent =
      error instanceof Error ? error.message : "Enregistrement impossible.";
  }
}

function renderCaseSnapshot(item) {
  caseFileSnapshot.textContent = "";
  const heading = document.createElement("h2");
  heading.textContent = "Analyse enregistrée";
  const question = document.createElement("p");
  question.textContent = item.question || "Question non renseignée.";
  const summary = document.createElement("p");
  const publicSummary = item.public_summary || {};
  summary.textContent =
    caseText(publicSummary.situation_summary) ||
    caseText(publicSummary.short_answer) ||
    caseText(publicSummary.summary) ||
    "Synthèse publique non disponible.";
  const position = document.createElement("p");
  position.textContent = caseText(publicSummary.working_position);
  caseFileSnapshot.append(heading, question, summary);
  if (position.textContent) caseFileSnapshot.appendChild(position);
  const uploadedDocuments = item.uploaded_documents || publicSummary.uploaded_documents || [];
  if (uploadedDocuments.length) {
    const documentsHeading = document.createElement("h3");
    documentsHeading.textContent = "Pièces conservées dans le dossier";
    const documentsList = document.createElement("ul");
    for (const document of uploadedDocuments) {
      const row = document.createElement("li");
      const details = [document.format, document.page_count ? `${document.page_count} page(s)` : ""]
        .filter(Boolean)
        .join(" · ");
      row.textContent = `${document.title || "Document fourni"}${details ? ` — ${details}` : ""}${document.truncated ? " — lecture partielle" : ""}`;
      documentsList.appendChild(row);
    }
    caseFileSnapshot.append(documentsHeading, documentsList);
  }
}

function showCaseList() {
  caseFileDetail.hidden = true;
  casesList.hidden = false;
  currentLocalCase = null;
  casesStatus.textContent = "";
}

function renderCaseCards(items) {
  casesList.textContent = "";
  casesEmpty.hidden = items.length !== 0;
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "case-file-card";
    const heading = document.createElement("h2");
    heading.textContent = item.title;
    const meta = document.createElement("p");
    meta.textContent = `${localCaseStatusLabels[item.status] || item.status} · mis à jour ${item.updated_at || "date inconnue"}`;
    const decision = document.createElement("p");
    decision.textContent = item.decision_recorded
      ? "Décision finale renseignée"
      : "Décision finale à renseigner";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-button";
    button.textContent = "Ouvrir le dossier";
    button.addEventListener("click", () => loadLocalCase(item.case_ref));
    card.append(heading, meta, decision, button);
    casesList.appendChild(card);
  }
}

async function openLocalCases() {
  showOnly("cases");
  showCaseList();
  casesStatus.textContent = "Chargement des dossiers locaux…";
  try {
    const payload = await localCaseRequest("/api/local-cases");
    renderCaseCards(payload.cases || []);
    casesStatus.textContent = `${(payload.cases || []).length} dossier(s) local(aux).`;
    casesView.focus();
  } catch (error) {
    casesStatus.textContent =
      error instanceof Error ? error.message : "Dossiers locaux indisponibles.";
  }
}

async function loadLocalCase(caseRef) {
  casesStatus.textContent = "Chargement du dossier…";
  try {
    const payload = await localCaseRequest(
      `/api/local-cases/${encodeURIComponent(caseRef)}`
    );
    const item = payload.case;
    currentLocalCase = item;
    caseReference.value = item.case_ref || "";
    caseFileTitle.value = item.title || "";
    caseFileStatus.value = item.status || "OPEN";
    caseFileNotes.value = item.notes || "";
    caseFileActions.value = (item.actions || []).map(caseText).filter(Boolean).join("\n");
    caseDecisionDate.value = item.final_decision?.date || "";
    caseDecisionType.value = item.final_decision?.type || "";
    caseDecisionAuthor.value = item.final_decision?.author_role || "";
    caseDecisionSummary.value = item.final_decision?.summary || "";
    caseDecisionDocument.value = item.final_decision?.supporting_document || "";
    caseFileSaveStatus.textContent = "";
    renderCaseSnapshot(item);
    casesList.hidden = true;
    caseFileDetail.hidden = false;
    casesStatus.textContent = "";
    caseFileDetail.focus?.();
  } catch (error) {
    casesStatus.textContent =
      error instanceof Error ? error.message : "Dossier local indisponible.";
  }
}

async function updateLocalCase(event) {
  event.preventDefault();
  if (!currentLocalCase) return;
  caseFileSaveStatus.textContent = "Enregistrement local…";
  const payload = {
    ...currentLocalCase,
    case_ref: caseReference.value,
    title: caseFileTitle.value.trim(),
    status: caseFileStatus.value,
    notes: caseFileNotes.value.trim(),
    actions: caseFileActions.value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean),
    final_decision: {
      date: caseDecisionDate.value,
      type: caseDecisionType.value,
      author_role: caseDecisionAuthor.value.trim(),
      summary: caseDecisionSummary.value.trim(),
      supporting_document: caseDecisionDocument.value.trim()
    }
  };
  try {
    const response = await localCaseRequest("/api/local-cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    currentLocalCase = response.case;
    caseFileSaveStatus.textContent = "Dossier mis à jour sur ce poste.";
    renderCaseSnapshot(currentLocalCase);
  } catch (error) {
    caseFileSaveStatus.textContent =
      error instanceof Error ? error.message : "Mise à jour impossible.";
  }
}

async function deleteCurrentLocalCase() {
  if (!currentLocalCase) return;
  const confirmed = window.confirm(
    `Supprimer définitivement le dossier « ${currentLocalCase.title} » de ce poste ?`
  );
  if (!confirmed) return;
  try {
    await localCaseRequest(
      `/api/local-cases/${encodeURIComponent(currentLocalCase.case_ref)}`,
      { method: "DELETE" }
    );
    await openLocalCases();
  } catch (error) {
    caseFileSaveStatus.textContent =
      error instanceof Error ? error.message : "Suppression impossible.";
  }
}

function showOnly(view) {
  homeView.hidden = view !== "home";
  wizardView.hidden = view !== "wizard";
  resultView.hidden = view !== "result";
  analysisState.hidden = view !== "loading";
  historyView.hidden = view !== "history";
  casesView.hidden = view !== "cases";
  rgpdView.hidden = view !== "rgpd";
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
    if (
      currentWorkspace === "employee" &&
      currentEmployeePath === "QUESTION_SALARIE"
    ) {
      return;
    }
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

function usesConversationalEmployeeFlow() {
  return currentWorkspace === "employee" && currentEmployeePath === "QUESTION_SALARIE";
}

function wizardStepSequence() {
  if (currentWorkspace === "cse") return [2];
  return usesConversationalEmployeeFlow() ? [2] : [1, 2, 3, 4, 5];
}

function renderWizardProgress() {
  const labelsByStep = {
    1: "Besoin",
    2: usesConversationalEmployeeFlow() ? "Question" : "Description",
    3: "Échange",
    4: "Éléments",
    5: "Résultat"
  };
  if (currentWorkspace === "cse") labelsByStep[2] = "Ordre du jour";
  const steps = wizardStepSequence();
  wizardProgress.textContent = "";
  steps.forEach((step, index) => {
    const item = document.createElement("li");
    item.dataset.number = String(index + 1);
    item.dataset.active = String(step === currentWizardStep);
    item.dataset.complete = String(steps.indexOf(currentWizardStep) > index);
    item.textContent = labelsByStep[step];
    wizardProgress.appendChild(item);
  });
  document.querySelectorAll(".wizard-step").forEach((section) => {
    const step = Number(section.dataset.step);
    section.hidden = step !== currentWizardStep;
    const count = section.querySelector(".step-count");
    if (count) {
      count.textContent = `Étape ${steps.indexOf(step) + 1} sur ${steps.length}`;
    }
  });
  const lastStep = steps[steps.length - 1];
  previousStepButton.hidden = steps.indexOf(currentWizardStep) === 0;
  nextStepButton.hidden = currentWizardStep === lastStep;
  analyzeButton.hidden = currentWizardStep !== lastStep || (
    currentWorkspace === "cse" && !currentCseAgendaPreview
  );
  analyzeButton.textContent = usesConversationalEmployeeFlow()
    ? "Envoyer la question à Nexus"
    : "Analyser avec Nexus";
  if (currentWorkspace === "cse") {
    analyzeButton.textContent = "Analyser l’ordre du jour";
  }
}

function validateCurrentStep() {
  let message = "";
  if (questionDocumentsLoading) message = "Attendez la fin de la lecture locale des documents.";
  if (currentWizardStep === 1 && !selectedSituation) message = "Choisissez le type de situation à traiter.";
  if (
    currentWizardStep === 2 &&
    currentWorkspace !== "cse" &&
    queryInput.value.trim().length < 12
  ) {
    message = "Décrivez la situation en quelques mots avant de continuer.";
  }
  if (
    currentWizardStep === 2 &&
    currentWorkspace === "cse" &&
    uploadedQuestionDocuments.length === 0
  ) {
    message = "Choisissez ou déposez l’ordre du jour avant de lancer l’analyse.";
  }
  if (currentWizardStep === 2 && currentWorkspace === "cse" && !currentCseAgendaPreview) {
    message = "Vérifiez d’abord les points de l’ordre du jour et les anciens PV.";
  }
  if (
    currentWizardStep === 2 &&
    currentWorkspace === "cse" &&
    currentCseAgendaPreview &&
    selectedCseAgendaPoints().length === 0
  ) {
    message = "Choisissez au moins un point à analyser et développer.";
  }
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
  const conversationalFlow = usesConversationalEmployeeFlow();
  const csePreparation = workspace === "cse";
  currentWizardStep = conversationalFlow ? 2 : 1;
  if (csePreparation) currentWizardStep = 2;
  selectedSituation = preset || (
    currentEmployeePath === "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"
      ? "entretien-prealable"
      : csePreparation
        ? "ordre-du-jour"
      : conversationalFlow
        ? "question-salarie"
        : ""
  );
  selectedOutcome = csePreparation ? "Poser des questions" : "";
  currentAnalysisRequest = null;
  followUpConversation = [];
  queryInput.value = csePreparation
    ? "Analyser chaque point, rechercher les sujets déjà traités et préparer les questions à poser à la direction."
    : "";
  resetQuestionDocuments();
  resetCsePreviousPvDocuments();
  cseAgendaWorkflow.hidden = !csePreparation;
  wizardWorkspaceLabel.textContent = definition.label;
  wizardTitle.textContent = definition.title;
  wizardDescription.textContent = definition.description;
  wizardView.classList.toggle("chatbot-mode", conversationalFlow);
  statusPill.classList.toggle("chatbot-status-hidden", conversationalFlow);
  const wizardHomeButton = wizardView.querySelector("[data-return-home]");
  if (wizardHomeButton) {
    wizardHomeButton.textContent = conversationalFlow
      ? "← Autres outils Nexus"
      : "← Revenir à l’accueil";
  }
  stepTwoTitle.textContent = csePreparation
    ? "Importez l’ordre du jour"
    : conversationalFlow
      ? "Quelle est votre question ?"
      : "Décrivez la situation";
  questionInputLabel.textContent = csePreparation
    ? "Contexte de la réunion et points à vérifier"
    : conversationalFlow
      ? "Votre question"
      : "Décrivez la situation avec vos propres mots";
  questionDocumentTitle.textContent = csePreparation
    ? "Importer l’ordre du jour"
    : "Ajouter des documents utiles";
  queryInput.placeholder = csePreparation
    ? "Exemple : vérifier les suites données aux engagements précédents et préparer les questions à poser à la direction."
    : "Décrivez votre situation ici…";
  privacyInputNotice.textContent = csePreparation
    ? "Nexus compare chaque point avec les anciens PV disponibles localement. Un PV apporte un contexte historique ; il ne constitue jamais une règle juridique."
    : conversationalFlow
      ? "N’indiquez aucun nom ni donnée personnelle inutile. Après la première réponse, vous pourrez préciser les faits dans la conversation."
      : "N’indiquez aucune donnée personnelle inutile. Le texte n’est pas enregistré automatiquement.";
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
  const conversationalFlow = usesConversationalEmployeeFlow();
  const responseMode = conversationalFlow
    ? "QUICK"
    : document.querySelector('input[name="responseMode"]:checked')?.value || "CASE";
  const desiredOutcome = selectedOutcome || (
    conversationalFlow
      ? "Obtenir une réponse claire et savoir quoi faire ensuite"
      : ""
  );
  const context = getContextValues();
  const interviewAnswers = getInterviewAnswers();
  const selectedAgendaPoints = currentWorkspace === "cse"
    ? selectedCseAgendaPoints()
    : [];
  const facts = Object.entries(context)
    .filter(([, value]) => value !== false && value !== "")
    .map(([key, value]) => `${key}: ${value === true ? "oui" : value}`);
  const query = [
    `[Espace métier: ${definition.label}]`,
    `[Type de situation: ${selectedSituation}]`,
    queryInput.value.trim(),
    selectedAgendaPoints.length
      ? `Points CSE sélectionnés : ${selectedAgendaPoints.map((item) => item.title).join(" ; ")}.`
      : "",
    facts.length ? `Repères: ${facts.join("; ")}.` : "",
    ...Object.entries(interviewAnswers).map(
      ([id, answer]) => `Question salarié — ${interviewQuestionLabel(id)} Réponse : ${answer}`
    ),
    documents.length
      ? `Documents disponibles: ${documents.join(", ")}.`
      : usesConversationalEmployeeFlow()
        ? ""
        : "Documents disponibles: non précisés.",
    desiredOutcome ? `Résultat souhaité: ${desiredOutcome}.` : "",
    `Mode de réponse: ${responseMode}.`
  ].filter(Boolean).join("\n");
  return {
    query,
    source_limit: Number(sourceLimitInput.value || 6),
    employee_path: currentEmployeePath,
    attachments: uploadedQuestionDocuments,
    cse_previous_pv_attachments: uploadedCsePreviousPvDocuments,
    portal_context: {
      workspace: currentWorkspace,
      employee_path: currentEmployeePath,
      situation_type: selectedSituation,
      user_question: queryInput.value.trim(),
      facts: context,
      employee_interview_answers: interviewAnswers,
      employee_interview: Object.entries(interviewAnswers).map(([id, answer]) => ({
        question: interviewQuestionLabel(id),
        answer
      })),
      available_documents: documents,
      period: context.payrollMonth || context.startDate || context.meetingDate || null,
      urgency: Boolean(context.urgentSituation),
      desired_outcome: desiredOutcome,
      cse_selected_agenda_positions: selectedAgendaPoints.map((item) => item.position),
      cse_selected_agenda_titles: selectedAgendaPoints.map((item) => item.title),
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
  currentAnalysisRequest = requestPayload;
  followUpConversation = [];

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

questionDocuments?.addEventListener("change", () => loadQuestionDocuments(questionDocuments.files));
csePreviousPvDocuments?.addEventListener("change", () =>
  loadQuestionDocuments(csePreviousPvDocuments.files, "cse-pv")
);
followUpDocumentInput?.addEventListener("change", () =>
  loadQuestionDocuments(followUpDocumentInput.files, "follow-up")
);
clearQuestionDocuments?.addEventListener("click", resetQuestionDocuments);
clearCsePreviousPvDocuments?.addEventListener("click", resetCsePreviousPvDocuments);
queryInput?.addEventListener("paste", (event) => {
  const pastedFiles = Array.from(event.clipboardData?.files || []);
  if (pastedFiles.length) {
    event.preventDefault();
    loadQuestionDocuments(pastedFiles);
    return;
  }
  if (!uploadedQuestionDocuments.length) {
    questionDocumentStatus.dataset.state = "ready";
    questionDocumentStatus.textContent = "Texte collé dans la question. Il sera inclus dans l’analyse.";
  }
});
questionDocumentDropZone?.addEventListener("dragover", (event) => {
  event.preventDefault();
  questionDocumentDropZone.classList.add("is-dragging");
});
questionDocumentDropZone?.addEventListener("dragleave", () => {
  questionDocumentDropZone.classList.remove("is-dragging");
});
questionDocumentDropZone?.addEventListener("drop", (event) => {
  event.preventDefault();
  questionDocumentDropZone.classList.remove("is-dragging");
  loadQuestionDocuments(event.dataTransfer?.files || []);
});
questionDocumentDropZone?.addEventListener("click", (event) => {
  if (event.target.closest("label, button, input")) return;
  questionDocuments?.click();
});
csePreviousPvDropZone?.addEventListener("dragover", (event) => {
  event.preventDefault();
  csePreviousPvDropZone.classList.add("is-dragging");
});
csePreviousPvDropZone?.addEventListener("dragleave", () => {
  csePreviousPvDropZone.classList.remove("is-dragging");
});
csePreviousPvDropZone?.addEventListener("drop", (event) => {
  event.preventDefault();
  csePreviousPvDropZone.classList.remove("is-dragging");
  loadQuestionDocuments(event.dataTransfer?.files || [], "cse-pv");
});
verifyCseAgendaButton?.addEventListener("click", verifyCseAgenda);

refineAnalysisButton.addEventListener("click", refineAnalysisWithFollowUp);
chatbotDetailsButton.addEventListener("click", () => {
  const opened = resultView.classList.toggle("chatbot-details-open");
  chatbotDetailsButton.textContent = opened
    ? "Masquer les sources et le détail"
    : "Voir les sources et le détail";
});
saveCaseButton.addEventListener("click", openCaseSaveDialog);
caseSaveForm.addEventListener("submit", createLocalCase);
cancelCaseSaveButton.addEventListener("click", () => caseSaveDialog.close());
caseFileForm.addEventListener("submit", updateLocalCase);
deleteCaseButton.addEventListener("click", deleteCurrentLocalCase);
caseBackToList.addEventListener("click", openLocalCases);
casesHomeButton.addEventListener("click", () => showOnly("home"));
refreshCasesButton.addEventListener("click", openLocalCases);

let rgpdSelectedFile = null;

function renderRgpdSelectedDocument() {
  rgpdSelectedDocument.textContent = "";
  rgpdAnalyzeUploadButton.disabled = !rgpdSelectedFile;
  if (!rgpdSelectedFile) return;
  const item = document.createElement("li");
  const name = document.createElement("span");
  const sizeKb = Math.max(1, Math.round(rgpdSelectedFile.size / 1024));
  name.textContent = `${rgpdSelectedFile.name} · ${sizeKb} Ko`;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "Retirer";
  remove.setAttribute("aria-label", `Retirer ${rgpdSelectedFile.name}`);
  remove.addEventListener("click", () => {
    rgpdSelectedFile = null;
    rgpdDocumentInput.value = "";
    renderRgpdSelectedDocument();
  });
  item.append(name, remove);
  rgpdSelectedDocument.appendChild(item);
}

rgpdUploadButton?.addEventListener("click", () => rgpdDocumentInput?.click());
rgpdDocumentInput?.addEventListener("change", () => {
  const file = rgpdDocumentInput.files?.[0];
  rgpdUploadStatus.dataset.state = "";
  rgpdUploadStatus.textContent = "";
  if (!file) return;
  if (!questionDocumentExtension(file.name)) {
    rgpdUploadStatus.dataset.state = "error";
    rgpdUploadStatus.textContent = `${file.name} n’est pas un format accepté (PDF, DOCX, TXT, MD, JPG).`;
    rgpdDocumentInput.value = "";
    return;
  }
  if (file.size > MAX_QUESTION_DOCUMENT_BYTES) {
    rgpdUploadStatus.dataset.state = "error";
    rgpdUploadStatus.textContent = `${file.name} dépasse 5 Mo.`;
    rgpdDocumentInput.value = "";
    return;
  }
  rgpdSelectedFile = file;
  renderRgpdSelectedDocument();
});

const RGPD_TOPIC_LABELS = {
  videosurveillance_travail: "Vidéosurveillance",
  geolocalisation_vehicules: "Géolocalisation des véhicules",
  controle_horaires_acces: "Contrôle d’accès / badgeage",
  controle_acces_biometrique: "Contrôle d’accès biométrique",
  gestion_activite_equipements: "Cybersurveillance / contrôle de l’activité",
  intranet_messagerie_syndicats: "Communication syndicale (intranet, messagerie)",
  elections_pro_donnees: "Élections professionnelles",
  registre_traitements: "Registre des traitements",
  gestion_personnel: "Gestion du personnel",
  donnees_sante_pratique: "Données de santé",
};

const RGPD_RISK_LABELS = { eleve: "Risque élevé", moyen: "Risque moyen", faible: "Risque faible" };

function renderRgpdAnalysis(analysis) {
  rgpdResults.textContent = "";
  rgpdResults.hidden = false;

  const banner = document.createElement("div");
  banner.className = "rgpd-summary-banner";
  const documentCount = analysis.documents_scanned ?? analysis.documents_analyzed;
  const findingsCount = analysis.documents_with_findings ?? analysis.documents.length;
  banner.textContent =
    `${documentCount} document(s) analysé(s) · ${findingsCount} avec au moins un sujet sensible repéré · ` +
    `${analysis.total_gaps_found} mention(s) manquante(s) au total.`;
  rgpdResults.appendChild(banner);

  if (!analysis.documents.length) {
    const empty = document.createElement("p");
    empty.className = "rgpd-no-topic";
    empty.textContent =
      "Aucun sujet sensible (vidéosurveillance, géolocalisation, badgeage, biométrie, données de santé…) repéré dans le texte fourni.";
    rgpdResults.appendChild(empty);
  }

  for (const report of analysis.documents) {
    const card = document.createElement("article");
    card.className = "rgpd-document-report";
    const title = document.createElement("h3");
    title.textContent = report.document_name || "Document";
    card.appendChild(title);
    if (report.no_sensitive_topic_detected) {
      const p = document.createElement("p");
      p.className = "rgpd-no-topic";
      p.textContent = "Aucun sujet sensible repéré dans ce document.";
      card.appendChild(p);
      rgpdResults.appendChild(card);
      continue;
    }
    for (const topic of report.topics) {
      const topicCard = document.createElement("div");
      topicCard.className = "rgpd-topic-card";
      const head = document.createElement("div");
      head.className = "rgpd-topic-head";
      const label = document.createElement("strong");
      label.textContent = RGPD_TOPIC_LABELS[topic.topic_id] || topic.topic_id;
      const badge = document.createElement("span");
      badge.className = "rgpd-risk-badge";
      badge.dataset.risk = topic.risk_level;
      badge.textContent = RGPD_RISK_LABELS[topic.risk_level] || topic.risk_level;
      const link = document.createElement("a");
      link.href = topic.cnil_reference_url;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = "Référence CNIL ↗";
      head.append(label, badge, link);
      topicCard.appendChild(head);

      if (topic.excerpts?.length) {
        const excerptList = document.createElement("ul");
        excerptList.className = "rgpd-excerpts";
        for (const excerpt of topic.excerpts) {
          const li = document.createElement("li");
          li.textContent = excerpt.reference ? `${excerpt.reference} — « ${excerpt.text} »` : `« ${excerpt.text} »`;
          excerptList.appendChild(li);
        }
        topicCard.appendChild(excerptList);
      }

      const checklist = document.createElement("ul");
      checklist.className = "rgpd-checklist";
      for (const item of topic.checklist) {
        const li = document.createElement("li");
        li.dataset.present = String(item.present);
        const mark = document.createElement("span");
        mark.className = "rgpd-check-mark";
        mark.textContent = item.present ? "✓" : "✕";
        const text = document.createElement("span");
        const labelSpan = document.createElement("span");
        labelSpan.textContent = item.present ? item.label : `${item.label} — absent du texte fourni`;
        text.appendChild(labelSpan);
        if (item.present && item.evidence) {
          const evidence = document.createElement("span");
          evidence.className = "rgpd-evidence";
          evidence.textContent = item.evidence.reference
            ? `${item.evidence.reference} — « ${item.evidence.text} »`
            : `« ${item.evidence.text} »`;
          text.appendChild(evidence);
        }
        li.append(mark, text);
        checklist.appendChild(li);
      }
      topicCard.appendChild(checklist);
      card.appendChild(topicCard);
    }
    rgpdResults.appendChild(card);
  }
}

async function requestRgpdAnalysis(url, init) {
  rgpdAnalysisStatus.dataset.state = "";
  rgpdAnalysisStatus.textContent = "Analyse en cours…";
  rgpdResults.hidden = true;
  try {
    const response = await fetch(url, init);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "L’analyse RGPD a échoué.");
    }
    rgpdAnalysisStatus.textContent = "";
    renderRgpdAnalysis(data.rgpd_analysis);
  } catch (error) {
    rgpdAnalysisStatus.dataset.state = "error";
    rgpdAnalysisStatus.textContent = error.message || "L’analyse RGPD a échoué.";
  }
}

rgpdAnalyzeUploadButton?.addEventListener("click", async () => {
  if (!rgpdSelectedFile) return;
  rgpdAnalyzeUploadButton.disabled = true;
  try {
    const encoded = await fileAsBase64(rgpdSelectedFile);
    await requestRgpdAnalysis("/api/rgpd/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        attachments: [{ name: rgpdSelectedFile.name, content_base64: encoded }],
      }),
    });
  } catch (error) {
    rgpdAnalysisStatus.dataset.state = "error";
    rgpdAnalysisStatus.textContent = error.message || "Lecture du document impossible.";
  } finally {
    rgpdAnalyzeUploadButton.disabled = !rgpdSelectedFile;
  }
});

rgpdCorpusScanButton?.addEventListener("click", () => {
  requestRgpdAnalysis("/api/rgpd/corpus-scan", { method: "GET" });
});

rgpdToolCard?.addEventListener("click", () => showOnly("rgpd"));
rgpdHomeButton?.addEventListener("click", () => showOnly("home"));

document.querySelectorAll("[data-open-workspace]").forEach((button) => {
  button.addEventListener("click", () => openWorkspace(button.dataset.openWorkspace, button.dataset.preset || "", button.dataset.employeePath || ""));
});
document.querySelectorAll("[data-return-home]").forEach((button) => {
  button.addEventListener("click", () => showOnly("home"));
});
nextStepButton.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  const steps = wizardStepSequence();
  const currentIndex = steps.indexOf(currentWizardStep);
  currentWizardStep = steps[Math.min(steps.length - 1, currentIndex + 1)];
  renderWizardProgress();
  document.querySelector(`.wizard-step[data-step="${currentWizardStep}"]`)?.focus?.();
});
previousStepButton.addEventListener("click", () => {
  const steps = wizardStepSequence();
  const currentIndex = steps.indexOf(currentWizardStep);
  currentWizardStep = steps[Math.max(0, currentIndex - 1)];
  renderWizardProgress();
});
editInformationButton.addEventListener("click", () => showOnly("wizard"));
addDocumentButton.addEventListener("click", () => {
  if (usesConversationalEmployeeFlow()) {
    factualEnrichmentPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    followUpDocumentInput.click();
    followUpStatus.textContent =
      "Choisissez le document utile : il sera lu localement puis intégré à la prochaine réponse.";
    return;
  }
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
    if (button.dataset.secondaryAction === "history") {
      openHistoricalCases();
      return;
    }
    if (button.dataset.secondaryAction === "cases") {
      openLocalCases();
      return;
    }
    const messages = {
      search: "Utilisez l’espace Négociations et accords pour une recherche guidée dans les sources disponibles.",
      templates: "Lancez une analyse puis utilisez « Générer un brouillon » dans le plan d’action."
    };
    secondaryMessage.textContent = messages[button.dataset.secondaryAction] || "";
    secondaryMessage.hidden = false;
  });
});

historyHomeButton.addEventListener("click", () => showOnly("home"));
historyBackToList.addEventListener("click", showHistoricalList);
historySearch.addEventListener("input", renderHistoricalCards);
historyCopyButton.addEventListener("click", copyHistoricalCase);
historyPrintButton.addEventListener("click", printHistoricalCase);
historyRefreshSourcesButton.addEventListener("click", refreshHistoricalSources);
historyView.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !historyDetail.hidden) {
    event.preventDefault();
    showHistoricalList();
  }
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

async function loadReleaseStatus() {
  try {
    const health = await fetchJson("/health");
    applyControlledPilotMode(health.controlled_pilot);
    nexusVersionValue.textContent = health.version;
    settingsVersionValue.textContent = health.version;
    const unavailable = Object.values(health.optional_dependencies || {})
      .filter((item) => !item.available)
      .map((item) => item.package);
    optionalFormatsValue.textContent = unavailable.length
      ? `Indisponibles : ${unavailable.join(", ")}`
      : "Tous disponibles";
    const capabilities = health.runtime_capabilities || {};
    const runtime = capabilities.runtime || {};
    const credentials = capabilities.credentials || {};
    const corpora = capabilities.local_corpora || {};
    cseCorpusStatusValue.textContent = corpora.cse_memory ? "Disponible localement" : "Non configuré";
    officialConnectorsStatusValue.textContent = runtime.official_connectors
      ? "Moteur activé"
      : "Moteur désactivé";
    legifranceStatusValue.textContent = credentials.legifrance ? "Configuré" : "Identifiants absents";
    judilibreStatusValue.textContent = credentials.judilibre ? "Configuré" : "Identifiants absents";
  } catch (_error) {
    nexusVersionValue.textContent = "indisponible";
    settingsVersionValue.textContent = "indisponible";
    optionalFormatsValue.textContent = "État indisponible";
    cseCorpusStatusValue.textContent = "État indisponible";
    officialConnectorsStatusValue.textContent = "État indisponible";
    legifranceStatusValue.textContent = "État indisponible";
    judilibreStatusValue.textContent = "État indisponible";
  }
}

printReportButton?.addEventListener("click", printReport);
loadReleaseStatus();
openWorkspace("employee", "", "QUESTION_SALARIE");
