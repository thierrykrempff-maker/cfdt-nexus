const STORAGE_KEY = "cfdt-nexus-cycle-cse-v1";
const SCHEMA_VERSION = "cycle-cse-v1";

const VIEWS = [
  ["dashboard", "Ma prochaine reunion"],
  ["preparation", "Preparation ODJ"],
  ["fieldQuestions", "Questions du terrain"],
  ["questionAnalysis", "Questions syndicales"],
  ["consultation", "Information-consultation"],
  ["meetingAssistant", "Assistant de seance"],
  ["afterMeeting", "Apres reunion"],
  ["finance", "Finance Sarralbe"],
  ["documentation", "Documentation"],
];

const CYCLE_STEPS = [
  ["Documents", "Pieces a lire, references et PV simules."],
  ["Preparation", "Analyse ODJ et angles morts."],
  ["Questions", "CFDT, autres organisations et terrain."],
  ["Reunion", "Notes, reponses et marqueurs rapides."],
  ["Analyse", "Reponses, engagements et contradictions."],
  ["Compte rendu", "Flash, adherents et memoire interne."],
  ["Relances", "Suivi vers la reunion suivante."],
];

const BASE_PREPARATION_QUESTIONS = [
  "De quoi parle ce point ?",
  "Que veut presenter la direction ?",
  "Pourquoi maintenant ?",
  "Quel est le contexte ?",
  "Quels documents sont fournis ?",
  "Quels documents manquent ?",
  "Ce sujet a-t-il deja ete aborde ?",
  "Existe-t-il des engagements anterieurs ?",
  "Existe-t-il une echeance anterieure ?",
  "Quels sont les enjeux pour les salaries ?",
  "Quels sont les risques ?",
  "Quels chiffres doivent etre verifies ?",
  "Quelles questions faut-il preparer ?",
  "Quelles relances prevoir ?",
];

const FIELD_TOPICS = [
  ["Effectifs", "Comparer charge, postes ouverts, absences et recours a l'interim."],
  ["Emploi", "Verifier les trajectoires d'embauche, mobilite et remplacement."],
  ["Interim", "Demander les volumes, motifs, durees et postes concernes."],
  ["Sous-traitance", "Identifier les activites externalisees et les impacts emploi."],
  ["Charge de travail", "Chercher les signaux de surcharge, retards et arbitrages."],
  ["Horaires", "Verifier delais de prevenance, repos et changements d'equipe."],
  ["Repos", "Comparer heures, astreintes, recuperations et fatigue."],
  ["Remuneration", "Surveiller primes, majorations, variables et regularisations."],
  ["Formation", "Verifier acces, postes exposes et besoins non couverts."],
  ["Egalite professionnelle", "Demander indicateurs, ecarts et mesures correctives."],
  ["Conditions de travail", "Relier organisation, charge, materiel et irritants terrain."],
  ["Securite", "Verifier accidents, presqu'accidents, maintenance et prevention."],
  ["RPS", "Chercher signaux faibles, isolement, pression et conflits d'organisation."],
  ["Investissements", "Relier projets, disponibilite, charge, maintenance et emploi."],
  ["Engagements precedents", "Reprendre les promesses non soldees et les echeances."],
];

const MARKER_TYPES = [
  "Engagement",
  "Chiffre",
  "Echeance",
  "Document promis",
  "A verifier",
  "Relance",
  "Desaccord",
  "Reponse incomplete",
];

const RESPONSE_CATEGORIES = [
  "complete",
  "partielle",
  "vague",
  "hors sujet",
  "a verifier",
  "engagement pris",
  "document promis",
  "echeance annoncee",
];

const REPORT_LEVELS = [
  ["flash", "Flash CSE"],
  ["adherents", "Compte rendu adherents"],
  ["memoire", "Memoire interne"],
];

const FINANCE_ACTIVITIES = [
  {
    id: "hdpe",
    label: "Sarralbe HDPE fictif",
    caseLabel: "Cas A",
    caseDescription: "Volume sous budget, marge sous budget et RC EBITDA degrade.",
    monthly: [
      ["Production", "kt fictives", 84, 100],
      ["Ventes", "kt fictives", 82, 101],
      ["Gross Margin", "M EUR fictifs", 18, 25],
      ["RC EBITDA", "M EUR fictifs", 8, 14],
      ["HC EBITDA", "M EUR fictifs", 7, 13],
    ],
    ytd: [
      ["Production", "kt fictives", 496, 590],
      ["Ventes", "kt fictives", 488, 582],
      ["Gross Margin", "M EUR fictifs", 111, 145],
      ["RC EBITDA", "M EUR fictifs", 49, 78],
      ["HC EBITDA", "M EUR fictifs", 44, 74],
    ],
  },
  {
    id: "pp",
    label: "Sarralbe PP fictif",
    caseLabel: "Cas B",
    caseDescription: "Volume sous budget, marge superieure au budget et RC EBITDA sous budget.",
    monthly: [
      ["Production", "kt fictives", 78, 98],
      ["Ventes", "kt fictives", 80, 96],
      ["Gross Margin", "M EUR fictifs", 24, 20],
      ["RC EBITDA", "M EUR fictifs", 9, 13],
      ["HC EBITDA", "M EUR fictifs", 6, 11],
    ],
    ytd: [
      ["Production", "kt fictives", 452, 560],
      ["Ventes", "kt fictives", 459, 552],
      ["Gross Margin", "M EUR fictifs", 139, 126],
      ["RC EBITDA", "M EUR fictifs", 57, 73],
      ["HC EBITDA", "M EUR fictifs", 47, 68],
    ],
  },
];

const MOTIVATED_OPINION_STRUCTURE = [
  "Objet de la consultation",
  "Documents examines",
  "Presentation du projet",
  "Constats du CSE",
  "Elements positifs",
  "Risques identifies",
  "Consequences pour les salaries",
  "Informations insuffisantes",
  "Reserves",
  "Demandes du CSE",
  "Mesures de prevention necessaires",
  "Alternatives proposees",
  "Engagements demandes",
  "Modalites de suivi",
  "Conclusion a valider par les elus",
];

const els = {};

let meetings = loadMeetings();
let state = {
  activeMeetingId: meetings[0]?.id || null,
  activeView: "dashboard",
  activePointId: meetings[0]?.agendaPoints?.[0]?.id || null,
  selectedConsultationId: meetings[0]?.consultations?.[0]?.id || null,
  selectedFinanceId: "hdpe",
  financeMode: "monthly",
  reportLevel: "flash",
  recording: false,
  recordingStartedAt: null,
  responseCategory: "partielle",
};

document.addEventListener("DOMContentLoaded", init);

function init() {
  cacheElements();
  setDefaultFormDate();
  bindStaticEvents();
  renderAll();
}

function cacheElements() {
  els.meetingPanel = document.querySelector("#meetingPanel");
  els.meetingForm = document.querySelector("#meetingForm");
  els.meetingSelect = document.querySelector("#meetingSelect");
  els.metricGrid = document.querySelector("#metricGrid");
  els.cycleChain = document.querySelector("#cycleChain");
  els.viewNav = document.querySelector("#viewNav");
  els.contextPanel = document.querySelector("#contextPanel");
  els.toast = document.querySelector("#toast");
}

function bindStaticEvents() {
  document.querySelector("#openMeetingPanel").addEventListener("click", () => {
    els.meetingPanel.hidden = false;
    els.meetingForm.title.focus();
  });

  document.querySelector("#closeMeetingPanel").addEventListener("click", closeMeetingPanel);
  document.querySelector("#cancelMeetingPanel").addEventListener("click", closeMeetingPanel);
  document.querySelector("#exportCycleButton").addEventListener("click", exportCycleData);

  els.meetingSelect.addEventListener("change", (event) => {
    state.activeMeetingId = event.target.value;
    const meeting = activeMeeting();
    state.activePointId = meeting?.agendaPoints?.[0]?.id || null;
    state.selectedConsultationId = meeting?.consultations?.[0]?.id || null;
    renderAll();
  });

  els.meetingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const created = createMeetingFromForm(new FormData(els.meetingForm));
    meetings.unshift(created);
    state.activeMeetingId = created.id;
    state.activePointId = created.agendaPoints[0]?.id || null;
    state.selectedConsultationId = created.consultations[0]?.id || null;
    saveMeetings();
    els.meetingForm.reset();
    setDefaultFormDate();
    closeMeetingPanel();
    renderAll();
    showToast("Reunion CSE creee en demonstration locale.");
  });
}

function closeMeetingPanel() {
  els.meetingPanel.hidden = true;
}

function renderAll() {
  ensureState();
  renderMeetingSelect();
  renderMetrics();
  renderCycleChain();
  renderViewNav();
  renderActiveView();
  renderContextPanel();
}

function ensureState() {
  if (!meetings.length) meetings = [seedMeeting()];
  if (!meetings.some((meeting) => meeting.id === state.activeMeetingId)) {
    state.activeMeetingId = meetings[0].id;
  }

  const meeting = activeMeeting();
  if (!meeting.agendaPoints.some((point) => point.id === state.activePointId)) {
    state.activePointId = meeting.agendaPoints[0]?.id || null;
  }
  if (!meeting.consultations.some((item) => item.id === state.selectedConsultationId)) {
    state.selectedConsultationId = meeting.consultations[0]?.id || null;
  }
}

function renderMeetingSelect() {
  els.meetingSelect.innerHTML = meetings.map((meeting) => `
    <option value="${escapeAttr(meeting.id)}"${meeting.id === state.activeMeetingId ? " selected" : ""}>
      ${escapeHtml(meeting.title)} - ${escapeHtml(formatDateShort(meeting.date))}
    </option>
  `).join("");
}

function renderMetrics() {
  const meeting = activeMeeting();
  const docsToAnalyze = unique(meeting.agendaPoints.flatMap((point) => point.documents || [])).length;
  const incompleteResponses = meeting.responses.filter((item) => item.category !== "complete").length;
  const openCommitments = meeting.commitments.filter((item) => item.status !== "solde").length;
  const missingPromisedDocs = meeting.promisedDocuments.filter((item) => item.status !== "recu").length;

  els.metricGrid.innerHTML = [
    ["Points ODJ", meeting.agendaPoints.length],
    ["Docs a lire", docsToAnalyze],
    ["Engagements", openCommitments],
    ["Relances", incompleteResponses + missingPromisedDocs],
  ].map(([label, value]) => `
    <div class="metric">
      <strong>${escapeHtml(value)}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `).join("");
}

function renderCycleChain() {
  els.cycleChain.innerHTML = CYCLE_STEPS.map(([title, detail], index) => `
    <div class="cycle-step">
      <span>${index + 1}</span>
      <div>
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(detail)}</small>
      </div>
    </div>
  `).join("");
}

function renderViewNav() {
  els.viewNav.innerHTML = VIEWS.map(([id, label]) => `
    <button class="view-button${id === state.activeView ? " view-button--active" : ""}" type="button" data-view="${escapeAttr(id)}">
      ${escapeHtml(label)}
    </button>
  `).join("");

  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      renderAll();
    });
  });
}

function renderActiveView() {
  const viewIds = VIEWS.map(([id]) => id);
  viewIds.forEach((id) => {
    const panel = document.querySelector(`#${id}View`);
    if (panel) panel.hidden = id !== state.activeView;
  });

  const renderers = {
    dashboard: renderDashboard,
    preparation: renderPreparation,
    fieldQuestions: renderFieldQuestions,
    questionAnalysis: renderQuestionAnalysis,
    consultation: renderConsultation,
    meetingAssistant: renderMeetingAssistant,
    afterMeeting: renderAfterMeeting,
    finance: renderFinance,
    documentation: renderDocumentation,
  };

  renderers[state.activeView]?.();
  bindDynamicEvents();
}

function renderDashboard() {
  const meeting = activeMeeting();
  const nextTasks = dashboardTasks(meeting);
  const docs = unique(meeting.agendaPoints.flatMap((point) => point.documents || []));
  const financeSummary = financeSignals().slice(0, 3);

  setViewHtml("dashboard", `
    <div class="hero-grid">
      <section class="hero-card">
        <p class="eyebrow">Ma prochaine reunion</p>
        <h1>${escapeHtml(meeting.title)}</h1>
        <p>${escapeHtml(meeting.type)} - ${escapeHtml(formatDateLong(meeting.date))} - Referent : ${escapeHtml(meeting.referent || "a preciser")}</p>
        <div class="badge-row">
          ${badge(`${meeting.agendaPoints.length} points ODJ`, "blue")}
          ${badge(`${meeting.questions.cfdt.length} questions CFDT`, "green")}
          ${badge(`${meeting.consultations.length} consultation(s)`, "yellow")}
          ${badge("Validation humaine obligatoire", "red")}
        </div>
        <div class="compact-actions">
          <button class="button button--primary" type="button" data-go-view="preparation">Preparer l'ordre du jour</button>
          <button class="button button--ghost" type="button" data-go-view="meetingAssistant">Ouvrir l'assistant de seance</button>
        </div>
      </section>

      <section class="hero-card">
        <p class="eyebrow">Priorites</p>
        <h2>Ce qui demande attention</h2>
        <ul class="readiness-list">
          ${nextTasks.map((item) => `<li><strong>${escapeHtml(item.title)}</strong>${escapeHtml(item.detail)}</li>`).join("")}
        </ul>
      </section>
    </div>

    <div class="dashboard-grid">
      ${sectionListCard("Ce que je dois lire", docs, "Aucun document reference.")}
      ${sectionListCard("Ce que je dois verifier", verificationItems(meeting), "Aucun point de verification prioritaire.")}
      ${sectionListCard("Questions a preparer", preparedQuestionPreview(meeting), "Aucune question preparee.")}
      ${sectionListCard("Anciens engagements a relancer", meeting.commitments.map(commitmentLabel), "Aucun engagement ouvert.")}
      ${sectionListCard("Consultations a preparer", meeting.consultations.map((item) => item.title), "Aucune consultation ouverte.")}
      ${sectionListCard("Points financiers a comprendre", financeSummary, "Aucun signal financier fictif.")}
    </div>
  `);
}

function renderPreparation() {
  const meeting = activeMeeting();
  const activePoint = selectedPoint();

  setViewHtml("preparation", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Preparation ODJ direction</p>
        <h1>Fiches de preparation</h1>
        <p>Chaque point separe les faits disponibles, les hypotheses a verifier et les questions a preparer.</p>
      </div>
    </div>

    <div class="analysis-grid">
      <section class="section-card">
        <h3>Points inscrits</h3>
        <div class="point-list">
          ${meeting.agendaPoints.map((point) => pointButton(point)).join("")}
        </div>
      </section>

      <section class="section-card">
        ${activePoint ? preparationDetail(activePoint) : "<p class=\"empty-state\">Aucun point selectionne.</p>"}
      </section>
    </div>
  `);
}

function preparationDetail(point) {
  const indicators = indicatorsForPoint(point);
  const memory = memoryForPoint(point);
  return `
    <div class="section-title">
      <p class="eyebrow">${escapeHtml(point.category)}</p>
      <h2>${escapeHtml(point.title)}</h2>
    </div>
    <p>${escapeHtml(point.summary)}</p>
    <div class="badge-row">
      ${(point.tags || []).map((tag) => badge(tag, tagVariant(tag))).join("")}
    </div>

    ${memory ? `
      <div class="memory-alert">
        <strong>Alerte memoire CSE</strong>
        <span>${escapeHtml(memory)}</span>
      </div>
    ` : ""}

    <div class="indicator-grid">
      ${indicators.map((item) => `<span class="indicator">${escapeHtml(item)}</span>`).join("")}
    </div>

    <div class="prep-question-grid">
      ${BASE_PREPARATION_QUESTIONS.map((question) => `<div class="prep-question">${escapeHtml(question)}</div>`).join("")}
    </div>

    <div class="two-column">
      ${sectionListCard("Documents fournis ou attendus", point.documents, "Aucun document associe.")}
      ${sectionListCard("Questions et relances", point.preparedQuestions, "Aucune question preparee.")}
    </div>
  `;
}

function renderFieldQuestions() {
  const meeting = activeMeeting();

  setViewHtml("fieldQuestions", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Questions du terrain</p>
        <h1>Remontees salaries et angles morts</h1>
        <p>Une question brute reste une information a reformuler, verifier et rattacher a une action CSE.</p>
      </div>
    </div>

    <section class="section-card section-card--soft">
      <h3>Ajouter une question terrain</h3>
      <form class="quick-form" id="fieldQuestionForm">
        <label class="field-wide">
          <span>Question brute</span>
          <textarea name="raw" rows="3" required placeholder="Question transmise par un salarie, sans nom ni donnee sensible"></textarea>
        </label>
        <label>
          <span>Theme</span>
          <input name="theme" type="text" required placeholder="ex. horaires, securite, prime">
        </label>
        <label>
          <span>Salaries concernes</span>
          <input name="audience" type="text" placeholder="ex. equipe postee, maintenance">
        </label>
        <label class="field-wide">
          <span>Contexte</span>
          <textarea name="context" rows="2" placeholder="Elements factuels connus et points a verifier"></textarea>
        </label>
        <div class="form-actions field-wide">
          <button class="button button--primary" type="submit">Ajouter</button>
        </div>
      </form>
    </section>

    <div class="two-column">
      <section class="section-card">
        <h3>Questions en cours</h3>
        <div class="question-list">
          ${meeting.fieldQuestions.map(fieldQuestionCard).join("") || "<p class=\"empty-state\">Aucune question terrain ajoutee.</p>"}
        </div>
      </section>

      <section class="section-card">
        <h3>Quels sujets devraient etre verifies ?</h3>
        <div class="topic-grid">
          ${FIELD_TOPICS.map(([title, detail]) => `
            <article class="topic-card">
              <strong>${escapeHtml(title)}</strong>
              <span>${escapeHtml(detail)}</span>
            </article>
          `).join("")}
        </div>
      </section>
    </div>
  `);
}

function fieldQuestionCard(item) {
  return `
    <article class="question-card">
      <h3>${escapeHtml(item.theme)}</h3>
      <p>${escapeHtml(item.raw)}</p>
      <div class="badge-row">
        ${badge(item.audience || "public a preciser", "blue")}
        ${badge("reformulation a valider", "yellow")}
      </div>
      <ul class="plain-list">
        <li><strong>Formulation CSE</strong>${escapeHtml(item.cseWording)}</li>
        <li><strong>Argumentation</strong>${escapeHtml(item.argument)}</li>
        <li><strong>Relance possible</strong>${escapeHtml(item.followUp)}</li>
      </ul>
    </article>
  `;
}

function renderQuestionAnalysis() {
  const meeting = activeMeeting();
  const questions = [
    ...meeting.questions.cfdt.map((item) => ({ ...item, source: "CFDT" })),
    ...meeting.questions.other.map((item) => ({ ...item, source: item.author || "Autre organisation" })),
  ];

  setViewHtml("questionAnalysis", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Analyse des questions CSE</p>
        <h1>Comprendre toutes les questions</h1>
        <p>Les questions des autres organisations sont analysees pour intervenir utilement, sans jugement automatique.</p>
      </div>
    </div>

    <div class="output-grid">
      ${questions.map(questionAnalysisCard).join("")}
    </div>
  `);
}

function questionAnalysisCard(item) {
  return `
    <article class="question-card">
      <div class="badge-row">
        ${badge(item.source, item.source === "CFDT" ? "green" : "blue")}
        ${badge(item.theme || "theme a preciser", "yellow")}
      </div>
      <h3>${escapeHtml(item.original)}</h3>
      <div class="two-column">
        ${miniBlock("Sujet reel", item.realSubject)}
        ${miniBlock("Contexte", item.context)}
        ${miniBlock("Enjeu", item.issue)}
        ${miniBlock("Droit a verifier", item.lawCheck)}
        ${miniBlock("Document a demander", item.documentNeeded)}
        ${miniBlock("Reponse probable", item.probableAnswer)}
      </div>
      <ul class="plain-list">
        ${(item.followUps || []).map((relance, index) => `<li><strong>Relance ${index + 1}</strong>${escapeHtml(relance)}</li>`).join("")}
      </ul>
    </article>
  `;
}

function renderConsultation() {
  const meeting = activeMeeting();
  const consultation = selectedConsultation();

  setViewHtml("consultation", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Information-consultation</p>
        <h1>Preparer un projet d'avis motive</h1>
        <p>L'outil prepare les rubriques et les questions. Les elus decident de l'avis.</p>
      </div>
    </div>

    <div class="analysis-grid">
      <section class="section-card">
        <h3>Consultations ouvertes</h3>
        <div class="point-list">
          ${meeting.consultations.map((item) => `
            <button class="consultation-button${item.id === state.selectedConsultationId ? " consultation-button--active" : ""}" type="button" data-consultation-id="${escapeAttr(item.id)}">
              <strong>${escapeHtml(item.title)}</strong>
              <span>${escapeHtml(item.status)}</span>
            </button>
          `).join("")}
        </div>
      </section>

      <section class="section-card">
        ${consultation ? consultationDetail(consultation) : "<p class=\"empty-state\">Aucune consultation selectionnee.</p>"}
      </section>
    </div>
  `);
}

function consultationDetail(item) {
  return `
    <div class="section-title">
      <p class="eyebrow">${escapeHtml(item.status)}</p>
      <h2>${escapeHtml(item.title)}</h2>
    </div>
    <p>${escapeHtml(item.object)}</p>
    <div class="two-column">
      ${sectionListCard("Elements disponibles", item.available, "Aucun element disponible.")}
      ${sectionListCard("Elements manquants", item.missing, "Aucun element manquant identifie.")}
      ${sectionListCard("Points a verifier", item.checks, "Aucun point a verifier.")}
      ${sectionListCard("Questions a poser", item.questions, "Aucune question preparee.")}
    </div>
    <section class="notice-panel">
      <h3>Le CSE dispose-t-il des elements necessaires pour comprendre le projet ?</h3>
      <p>${escapeHtml(item.readiness)}</p>
    </section>
    <section class="section-card">
      <h3>Structure du projet d'avis motive</h3>
      <div class="four-column">
        ${MOTIVATED_OPINION_STRUCTURE.map((title, index) => `
          <div class="prep-question">
            <strong>${index + 1}. ${escapeHtml(title)}</strong>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function renderMeetingAssistant() {
  const meeting = activeMeeting();
  const point = selectedPoint();

  setViewHtml("meetingAssistant", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Assistant de reunion V1</p>
        <h1>Suivre la seance</h1>
        <p>Enregistrement manuel simule. Aucun audio reel n'est stocke dans le depot.</p>
      </div>
    </div>

    <div class="assistant-layout">
      <section class="meeting-console">
        <label>
          <span>Point en cours</span>
          <select id="currentPointSelect">
            ${meeting.agendaPoints.map((item) => `
              <option value="${escapeAttr(item.id)}"${item.id === state.activePointId ? " selected" : ""}>${escapeHtml(item.title)}</option>
            `).join("")}
          </select>
        </label>

        <div class="recording-panel">
          <div class="recording-state">
            <span class="recording-dot${state.recording ? " recording-dot--active" : ""}" aria-hidden="true"></span>
            <strong>${state.recording ? "Reponse en cours de saisie" : "Pret pour une reponse manuelle"}</strong>
          </div>
          <div class="compact-actions">
            <button class="button button--primary" type="button" id="toggleRecordingButton">
              ${state.recording ? "Stop" : "Enregistrer la reponse de la direction"}
            </button>
          </div>
          <label>
            <span>Reponse de la direction</span>
            <textarea id="manualResponseText" rows="5" placeholder="Saisir manuellement les propos importants, sans audio ni donnee sensible"></textarea>
          </label>
          <div class="response-evaluation">
            ${RESPONSE_CATEGORIES.map((category) => `
              <button class="chip-button${category === state.responseCategory ? " chip-button--active" : ""}" type="button" data-response-category="${escapeAttr(category)}">
                ${escapeHtml(category)}
              </button>
            `).join("")}
          </div>
          <div class="form-actions">
            <button class="button button--ghost" type="button" id="saveManualResponseButton">Rattacher au point</button>
          </div>
        </div>

        <section class="section-card">
          <h3>Marqueurs rapides</h3>
          <div class="marker-grid">
            ${MARKER_TYPES.map((type) => `
              <button class="marker-button" type="button" data-marker="${escapeAttr(type)}">${escapeHtml(type)}</button>
            `).join("")}
          </div>
        </section>
      </section>

      <aside class="section-card">
        <h3>${escapeHtml(point?.title || "Point non selectionne")}</h3>
        ${sectionListCard("Questions preparees", point?.preparedQuestions || [], "Aucune question preparee.")}
        ${sectionListCard("Anciens engagements", point?.previousCommitments || [], "Aucun engagement precedent.")}
        ${sectionListCard("Documents utiles", point?.documents || [], "Aucun document rattache.")}
        <label>
          <span>Notes de seance</span>
          <textarea id="meetingNotes" rows="8">${escapeHtml(meeting.notes || "")}</textarea>
        </label>
      </aside>
    </div>

    <section class="section-card">
      <h3>Marqueurs rattaches a la reunion</h3>
      <ul class="marker-list">
        ${meeting.markers.map(markerItem).join("") || "<li>Aucun marqueur enregistre.</li>"}
      </ul>
    </section>
  `);
}

function markerItem(marker) {
  const point = activeMeeting().agendaPoints.find((item) => item.id === marker.pointId);
  return `
    <li>
      <strong>${escapeHtml(marker.type)} - ${escapeHtml(marker.createdAt.slice(11, 16))}</strong>
      ${escapeHtml(point?.title || "Point a verifier")}
    </li>
  `;
}

function renderAfterMeeting() {
  const meeting = activeMeeting();
  const report = reportContent(meeting, state.reportLevel);

  setViewHtml("afterMeeting", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Apres reunion</p>
        <h1>Analyser, relancer, rendre compte</h1>
        <p>Les paroles de la direction, le resume, l'analyse CFDT et la communication adherents restent separes.</p>
      </div>
    </div>

    <div class="two-column">
      <section class="section-card">
        <h3>Reponses a analyser</h3>
        <div class="question-list">
          ${meeting.responses.map(responseCard).join("") || "<p class=\"empty-state\">Aucune reponse enregistree.</p>"}
        </div>
      </section>

      <section class="section-card">
        <h3>Engagements et relances</h3>
        ${sectionListCard("Engagements ouverts", meeting.commitments.map(commitmentLabel), "Aucun engagement ouvert.")}
        ${sectionListCard("Documents promis non recus", meeting.promisedDocuments.filter((doc) => doc.status !== "recu").map((doc) => doc.title), "Aucun document promis en attente.")}
      </section>
    </div>

    <section class="section-card">
      <div class="report-tabs">
        ${REPORT_LEVELS.map(([id, label]) => `
          <button class="chip-button${id === state.reportLevel ? " chip-button--active" : ""}" type="button" data-report-level="${escapeAttr(id)}">
            ${escapeHtml(label)}
          </button>
        `).join("")}
      </div>
      <article class="report-card">
        <p class="eyebrow">${escapeHtml(report.label)}</p>
        <h3>${escapeHtml(report.title)}</h3>
        <ul class="plain-list">
          ${report.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      </article>
    </section>
  `);
}

function responseCard(response) {
  return `
    <article class="question-card">
      <div class="badge-row">
        ${badge(response.category, response.category === "complete" ? "green" : "yellow")}
        ${badge("validation humaine", "red")}
      </div>
      <h3>${escapeHtml(response.pointTitle)}</h3>
      <ul class="plain-list">
        <li><strong>Paroles direction</strong>${escapeHtml(response.raw)}</li>
        <li><strong>Resume fidele</strong>${escapeHtml(response.summary)}</li>
        <li><strong>Analyse</strong>${escapeHtml(response.analysis)}</li>
        <li><strong>Commentaire CFDT</strong>${escapeHtml(response.cfdtComment)}</li>
      </ul>
    </article>
  `;
}

function renderFinance() {
  const activity = selectedFinanceActivity();
  const rows = financeRows(activity, state.financeMode);
  const questions = financeQuestions(activity, rows);
  const signals = financeSignalsForRows(activity, rows);

  setViewHtml("finance", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Analyse financiere Sarralbe</p>
        <h1>HDPE / PP fictifs</h1>
        <p>Lecture centree sur Sarralbe : volumes, production, ventes, marge, RC EBITDA, HC EBITDA et consequences possibles pour la charge.</p>
      </div>
    </div>

    <div class="finance-grid">
      <section class="section-card">
        <h3>Activite</h3>
        <div class="point-list">
          ${FINANCE_ACTIVITIES.map((item) => `
            <button class="activity-button${item.id === state.selectedFinanceId ? " activity-button--active" : ""}" type="button" data-finance-activity="${escapeAttr(item.id)}">
              <strong>${escapeHtml(item.label)}</strong>
              <span>${escapeHtml(item.caseLabel)} - ${escapeHtml(item.caseDescription)}</span>
            </button>
          `).join("")}
        </div>
        <label>
          <span>Lecture</span>
          <select id="financeModeSelect">
            <option value="monthly"${state.financeMode === "monthly" ? " selected" : ""}>Mensuelle</option>
            <option value="ytd"${state.financeMode === "ytd" ? " selected" : ""}>YTD</option>
          </select>
        </label>
        <section class="notice-panel">
          <h3>Modele economique a garder en tete</h3>
          <p>Sarralbe fonctionne en toll manufacturing / faconnage, avec modele local cost-plus et marge contractuelle de 3 %. Les decisions Groupe peuvent toutefois peser sur volumes, charge, frais fixes, organisation, maintenance, effectifs et investissements.</p>
        </section>
      </section>

      <section class="section-card">
        <div class="section-title">
          <p class="eyebrow">${escapeHtml(activity.caseLabel)}</p>
          <h2>${escapeHtml(activity.label)}</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Indicateur</th>
                <th>Actual</th>
                <th>Budget</th>
                <th>Ecart</th>
                <th>Ecart %</th>
                <th>Tendance</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map(financeRowHtml).join("")}
            </tbody>
          </table>
        </div>

        <div class="double-reading">
          <div class="reading-block">
            <h4>Vision Groupe / Principal</h4>
            <p>${escapeHtml(groupReading(activity, rows))}</p>
          </div>
          <div class="reading-block">
            <h4>Consequences possibles pour Sarralbe</h4>
            <p>${escapeHtml(siteReading(activity, rows))}</p>
          </div>
        </div>

        <div class="two-column">
          ${sectionListCard("Questions CSE prioritaires", questions, "Aucune question prioritaire generee.")}
          ${sectionListCard("Points a surveiller", signals, "Aucun signal prioritaire.")}
        </div>
      </section>
    </div>

    <section class="section-card">
      <h3>Demonstration des deux cas fictifs</h3>
      <div class="two-column">
        ${FINANCE_ACTIVITIES.map((item) => `
          <article class="finance-card">
            <p class="eyebrow">${escapeHtml(item.caseLabel)}</p>
            <h3>${escapeHtml(item.label)}</h3>
            <p>${escapeHtml(item.caseDescription)}</p>
            <p>${escapeHtml(caseExplanation(item))}</p>
          </article>
        `).join("")}
      </div>
    </section>
  `);
}

function financeRowHtml(row) {
  const percent = row.percent;
  const bad = row.name === "Gross Margin" ? percent < 0 : percent < -5;
  const good = row.name === "Gross Margin" ? percent > 0 : percent > 0;
  const width = Math.max(4, Math.min(100, Math.round((row.actual / Math.max(row.budget, 1)) * 100)));
  const widthBucket = Math.max(1, Math.min(10, Math.round(width / 10)));
  return `
    <tr>
      <td><strong>${escapeHtml(row.name)}</strong><br><span class="card-note">${escapeHtml(row.unit)}</span></td>
      <td>${escapeHtml(row.actual)}</td>
      <td>${escapeHtml(row.budget)}</td>
      <td class="variance${bad ? " variance--bad" : good ? " variance--good" : ""}">${escapeHtml(formatSigned(row.variance))}</td>
      <td class="variance${bad ? " variance--bad" : good ? " variance--good" : ""}">${escapeHtml(formatPercent(percent))}</td>
      <td>
        <div class="bar-track"><div class="bar-fill bar-fill--${widthBucket}"></div></div>
      </td>
    </tr>
  `;
}

function renderDocumentation() {
  setViewHtml("documentation", `
    <div class="section-heading">
      <div>
        <p class="eyebrow">Documentation V1</p>
        <h1>Limites, donnees et integrations futures</h1>
        <p>Le module prepare les structures necessaires sans simuler une IA reelle ni stocker de document confidentiel.</p>
      </div>
    </div>

    <div class="two-column">
      ${sectionListCard("Regles absolues", [
        "Aucun accord INEOS reel dans le depot.",
        "Aucun PV CSE reel, BDESE, enregistrement ou transcription reelle dans GitHub.",
        "Aucune donnee nominative dans les donnees de demonstration.",
        "Les chiffres financiers affiches sont fictifs et servent uniquement a tester les regles d'analyse.",
      ], "")}
      ${sectionListCard("Backend securise futur", [
        "Stockage prive des documents et audios.",
        "Chiffrement, controle d'acces, journalisation et cloisonnement par organisation.",
        "Duree de conservation, suppression et exports maitrises.",
        "Connexion future transcription, recherche documentaire, recherche PV et agents IA reels.",
      ], "")}
      ${sectionListCard("Modeles de donnees prepares", [
        "Reunion CSE, ordre du jour, points direction, questions CFDT et autres organisations.",
        "Questions terrain, consultations, avis motives, marqueurs de seance, reponses et engagements.",
        "Memoire PV simulee, documents promis, relances et rapports adherents.",
        "Analyse financiere Sarralbe HDPE/PP centree sur volumes, budget, RC, HC et questions CSE.",
      ], "")}
      ${sectionListCard("Points d'integration", [
        "Document Intelligence Center pour analyser les documents rattaches.",
        "Bibliotheque documentaire pour les references expurgees et la future recherche semantique.",
        "Dossiers d'accompagnement pour transformer une alerte collective en suivi structure.",
        "n8n ou backend futur pour relances, validations, exports et notifications.",
      ], "")}
    </div>
  `);
}

function renderContextPanel() {
  const meeting = activeMeeting();
  const point = selectedPoint();
  const financialSignals = financeSignals().slice(0, 2);

  els.contextPanel.innerHTML = `
    <section class="context-card">
      <p class="eyebrow">Cadre V1</p>
      <h2>Limites visibles</h2>
      <p>Pas d'IA reelle, pas de transcription automatique, pas de backend securise. Les donnees restent une demonstration locale du navigateur.</p>
    </section>

    <section class="context-card">
      <p class="eyebrow">Point actif</p>
      <h3>${escapeHtml(point?.title || "Aucun point")}</h3>
      <div class="badge-row">
        ${(point?.tags || []).map((tag) => badge(tag, tagVariant(tag))).join("")}
      </div>
    </section>

    <section class="context-card">
      <p class="eyebrow">Memoire et relances</p>
      <ul class="plain-list">
        ${meeting.commitments.slice(0, 3).map((item) => `<li><strong>${escapeHtml(item.dueDate || "Date a verifier")}</strong>${escapeHtml(item.title)}</li>`).join("")}
      </ul>
    </section>

    <section class="context-card">
      <p class="eyebrow">Signaux financiers fictifs</p>
      <ul class="plain-list">
        ${financialSignals.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ul>
    </section>
  `;
}

function bindDynamicEvents() {
  document.querySelectorAll("[data-go-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.goView;
      renderAll();
    });
  });

  document.querySelectorAll("[data-point-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activePointId = button.dataset.pointId;
      renderAll();
    });
  });

  document.querySelectorAll("[data-consultation-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedConsultationId = button.dataset.consultationId;
      renderAll();
    });
  });

  document.querySelectorAll("[data-finance-activity]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedFinanceId = button.dataset.financeActivity;
      renderAll();
    });
  });

  document.querySelector("#financeModeSelect")?.addEventListener("change", (event) => {
    state.financeMode = event.target.value;
    renderAll();
  });

  document.querySelectorAll("[data-report-level]").forEach((button) => {
    button.addEventListener("click", () => {
      state.reportLevel = button.dataset.reportLevel;
      renderAll();
    });
  });

  document.querySelector("#fieldQuestionForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    addFieldQuestion(new FormData(event.target));
    event.target.reset();
    renderAll();
    showToast("Question terrain ajoutee.");
  });

  document.querySelector("#currentPointSelect")?.addEventListener("change", (event) => {
    state.activePointId = event.target.value;
    renderAll();
  });

  document.querySelector("#toggleRecordingButton")?.addEventListener("click", () => {
    state.recording = !state.recording;
    state.recordingStartedAt = state.recording ? new Date().toISOString() : null;
    renderAll();
  });

  document.querySelectorAll("[data-response-category]").forEach((button) => {
    button.addEventListener("click", () => {
      state.responseCategory = button.dataset.responseCategory;
      renderAll();
    });
  });

  document.querySelector("#saveManualResponseButton")?.addEventListener("click", saveManualResponse);

  document.querySelectorAll("[data-marker]").forEach((button) => {
    button.addEventListener("click", () => addMarker(button.dataset.marker));
  });

  document.querySelector("#meetingNotes")?.addEventListener("change", (event) => {
    activeMeeting().notes = event.target.value;
    saveMeetings();
    showToast("Notes de seance enregistrees localement.");
  });
}

function addFieldQuestion(form) {
  const raw = String(form.get("raw") || "").trim();
  const theme = String(form.get("theme") || "").trim();
  const audience = String(form.get("audience") || "").trim();
  const context = String(form.get("context") || "").trim();
  if (!raw || !theme) return;

  activeMeeting().fieldQuestions.unshift({
    id: uid("field"),
    raw,
    theme,
    audience,
    context,
    cseWording: `La direction peut-elle preciser les elements disponibles sur le sujet ${theme} et les mesures prevues ?`,
    argument: context || "Question a rattacher a des faits verifies avant presentation.",
    followUp: "Demander un calendrier, un indicateur de suivi et une reponse ecrite si le sujet reste ouvert.",
    createdAt: new Date().toISOString(),
  });
  saveMeetings();
}

function saveManualResponse() {
  const text = document.querySelector("#manualResponseText")?.value.trim();
  if (!text) {
    showToast("Saisir une reponse avant de rattacher au point.");
    return;
  }
  const point = selectedPoint();
  activeMeeting().responses.unshift({
    id: uid("response"),
    pointId: point?.id || "",
    pointTitle: point?.title || "Point a verifier",
    raw: text,
    summary: "Resume a relire : " + shortText(text, 140),
    analysis: responseAnalysisFor(state.responseCategory),
    cfdtComment: "Commentaire CFDT a valider par les elus avant toute diffusion.",
    category: state.responseCategory,
    createdAt: new Date().toISOString(),
  });
  state.recording = false;
  state.recordingStartedAt = null;
  saveMeetings();
  renderAll();
  showToast("Reponse rattachee au point.");
}

function addMarker(type) {
  const meeting = activeMeeting();
  const point = selectedPoint();
  meeting.markers.unshift({
    id: uid("marker"),
    type,
    meetingId: meeting.id,
    pointId: point?.id || "",
    questionId: "",
    createdAt: new Date().toISOString(),
  });
  saveMeetings();
  renderAll();
  showToast(`Marqueur ajoute : ${type}.`);
}

function setViewHtml(viewId, html) {
  const panel = document.querySelector(`#${viewId}View`);
  if (panel) panel.innerHTML = html;
}

function sectionListCard(title, items, emptyText) {
  return `
    <section class="section-card">
      <h3>${escapeHtml(title)}</h3>
      ${items && items.length ? `
        <ul class="plain-list">
          ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      ` : `<p class="empty-state">${escapeHtml(emptyText || "Aucun element.")}</p>`}
    </section>
  `;
}

function miniBlock(title, text) {
  return `
    <div class="section-card section-card--soft">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(text || "A preciser.")}</p>
    </div>
  `;
}

function pointButton(point) {
  return `
    <button class="point-button${point.id === state.activePointId ? " point-button--active" : ""}" type="button" data-point-id="${escapeAttr(point.id)}">
      <strong>${escapeHtml(point.title)}</strong>
      <span>${escapeHtml(point.category)} - ${escapeHtml((point.tags || []).join(", "))}</span>
    </button>
  `;
}

function badge(label, variant = "") {
  const suffix = variant ? ` badge--${variant}` : "";
  return `<span class="badge${suffix}">${escapeHtml(label)}</span>`;
}

function dashboardTasks(meeting) {
  return [
    {
      title: "Analyser les points direction",
      detail: `${meeting.agendaPoints.filter((point) => point.category === "Direction").length} point(s) direction a preparer.`,
    },
    {
      title: "Relancer les engagements",
      detail: `${meeting.commitments.filter((item) => item.status !== "solde").length} engagement(s) ouvert(s).`,
    },
    {
      title: "Verifier les chiffres",
      detail: "Analyse financiere fictive HDPE/PP a transformer en questions ciblees.",
    },
    {
      title: "Preparer la communication",
      detail: "Flash CSE, compte rendu adherents et memoire interne separes.",
    },
  ];
}

function verificationItems(meeting) {
  return unique([
    ...meeting.agendaPoints.flatMap((point) => indicatorsForPoint(point)),
    ...meeting.consultations.flatMap((item) => item.missing || []).map((item) => `Element consultation manquant : ${item}`),
  ]).slice(0, 8);
}

function preparedQuestionPreview(meeting) {
  return [
    ...meeting.questions.cfdt.map((item) => item.original),
    ...meeting.agendaPoints.flatMap((point) => point.preparedQuestions || []),
  ].slice(0, 8);
}

function indicatorsForPoint(point) {
  const tags = new Set(point.tags || []);
  const indicators = [];
  if (tags.has("documentaire")) indicators.push("Analyse documentaire necessaire");
  if (tags.has("pv")) indicators.push("Recherche PV necessaire");
  if (tags.has("juridique")) indicators.push("Analyse juridique necessaire");
  if (tags.has("financier")) indicators.push("Analyse financiere necessaire");
  if (tags.has("cssct")) indicators.push("Analyse CSSCT necessaire");
  if (tags.has("consultation")) indicators.push("Avis motive a preparer");
  if (tags.has("terrain")) indicators.push("Consultation des salaries a envisager");
  return indicators;
}

function tagVariant(tag) {
  const variants = {
    documentaire: "blue",
    pv: "violet",
    juridique: "yellow",
    financier: "green",
    cssct: "red",
    consultation: "yellow",
    terrain: "blue",
  };
  return variants[tag] || "";
}

function memoryForPoint(point) {
  if (point.previousCommitments?.length) return point.previousCommitments[0];
  return "";
}

function commitmentLabel(item) {
  return `${item.title} - echeance ${item.dueDate || "a verifier"} - ${item.status}`;
}

function activeMeeting() {
  return meetings.find((meeting) => meeting.id === state.activeMeetingId) || meetings[0];
}

function selectedPoint() {
  return activeMeeting().agendaPoints.find((point) => point.id === state.activePointId) || activeMeeting().agendaPoints[0] || null;
}

function selectedConsultation() {
  return activeMeeting().consultations.find((item) => item.id === state.selectedConsultationId) || activeMeeting().consultations[0] || null;
}

function selectedFinanceActivity() {
  return FINANCE_ACTIVITIES.find((item) => item.id === state.selectedFinanceId) || FINANCE_ACTIVITIES[0];
}

function financeRows(activity, mode) {
  return activity[mode].map(([name, unit, actual, budget]) => {
    const variance = actual - budget;
    const percent = budget ? (variance / budget) * 100 : 0;
    return { name, unit, actual, budget, variance, percent };
  });
}

function rowByName(rows, name) {
  return rows.find((row) => row.name === name);
}

function financeQuestions(activity, rows) {
  const production = rowByName(rows, "Production");
  const grossMargin = rowByName(rows, "Gross Margin");
  const rc = rowByName(rows, "RC EBITDA");
  const hc = rowByName(rows, "HC EBITDA");
  const questions = [];

  if (production?.percent < -8) {
    questions.push("Quelles sont les causes precises du deficit de production et quelle part releve de la demande, de contraintes industrielles ou d'une allocation de volumes ?");
    questions.push("Quelle charge actualisee est prevue a 3 mois, 6 mois et 12 mois pour Sarralbe ?");
    questions.push("Le budget annuel reste-t-il realiste ou un forecast actualise sera-t-il presente au CSE ?");
  }

  if (grossMargin?.percent < -5 && rc?.percent < -5) {
    questions.push("Quelle part de l'ecart RC EBITDA provient du volume, de la marge et des couts ?");
    questions.push("Quelles actions sont prevues pour eviter un impact sur maintenance, organisation et effectifs ?");
  }

  if (grossMargin?.percent > 0 && production?.percent < -8 && rc?.percent < -5) {
    questions.push("Comment expliquer une marge superieure au budget alors que le volume et le RC EBITDA restent sous budget ?");
    questions.push("L'effet volume annule-t-il le gain de marge ou existe-t-il un autre facteur de cout a documenter ?");
  }

  if (hc && rc && hc.actual < rc.actual) {
    questions.push("Quels elements expliquent l'ecart entre RC EBITDA et HC EBITDA, sans confondre automatiquement les deux lectures ?");
  }

  questions.push("Quels indicateurs permettront au CSE de suivre la charge industrielle de Sarralbe lors des prochains mois ?");
  return unique(questions).slice(0, 7);
}

function financeSignals() {
  return FINANCE_ACTIVITIES.flatMap((activity) => financeSignalsForRows(activity, financeRows(activity, "monthly")));
}

function financeSignalsForRows(activity, rows) {
  const production = rowByName(rows, "Production");
  const grossMargin = rowByName(rows, "Gross Margin");
  const rc = rowByName(rows, "RC EBITDA");
  const signals = [];

  if (production?.percent < -8) {
    signals.push(`${activity.label} : volume durablement sous budget, risque a analyser sur charge et absorption des frais fixes.`);
  }
  if (grossMargin?.percent > 0 && production?.percent < -8 && rc?.percent < -5) {
    signals.push(`${activity.label} : marge superieure au budget mais RC sous budget, effet volume/couts a isoler.`);
  }
  if (grossMargin?.percent < -5 && rc?.percent < -5) {
    signals.push(`${activity.label} : marge et RC sous budget, causes commerciales, industrielles ou couts a documenter.`);
  }
  signals.push(`${activity.label} : toute conclusion strategique doit rester une hypothese a verifier.`);
  return unique(signals);
}

function groupReading(activity, rows) {
  const production = rowByName(rows, "Production");
  const grossMargin = rowByName(rows, "Gross Margin");
  const rc = rowByName(rows, "RC EBITDA");
  if (production.percent < -8 && grossMargin.percent > 0 && rc.percent < -5) {
    return "Le Principal peut voir une marge favorable, mais l'insuffisance de volumes degrade la contribution RC. La question centrale est l'arbitrage entre volume, prix/marge et couts.";
  }
  return "La lecture Groupe doit expliquer si l'ecart vient de la demande, d'une contrainte industrielle, d'un cout ou d'un arbitrage de volumes.";
}

function siteReading(activity, rows) {
  const production = rowByName(rows, "Production");
  const rc = rowByName(rows, "RC EBITDA");
  if (production.percent < -8 && rc.percent < -5) {
    return "Pour Sarralbe, le risque principal porte sur la securite de charge, l'absorption des frais fixes, l'organisation, la maintenance, l'interim, les effectifs et les investissements.";
  }
  return "Pour Sarralbe, la priorite est de relier les indicateurs aux consequences industrielles et sociales observables.";
}

function caseExplanation(activity) {
  if (activity.id === "pp") {
    return "Cette situation appelle des questions sur l'effet volume, l'effet marge et les couts : une bonne marge unitaire ne compense pas toujours un manque de volume.";
  }
  return "Cette situation appelle d'abord des questions sur les causes du deficit de volume, la degradation de marge et les consequences sur la charge.";
}

function reportContent(meeting, level) {
  if (level === "memoire") {
    return {
      label: "Memoire interne CFDT",
      title: "Trace interne a ne pas publier telle quelle",
      items: [
        "Strategie : relancer les engagements non soldes et demander un calendrier ecrit.",
        "Points faibles : plusieurs reponses restent partielles et dependent de documents promis.",
        "Contradictions potentielles : comparer les annonces de charge avec les engagements PV simules.",
        "Actions futures : preparer questions finance Sarralbe, CSSCT et suivi information-consultation.",
      ],
    };
  }
  if (level === "adherents") {
    return {
      label: "Compte rendu adherents",
      title: "Version claire a relire avant diffusion",
      items: [
        "La direction a presente plusieurs points d'organisation et de charge industrielle.",
        "La CFDT a demande des precisions sur les documents manquants, les impacts salaries et le calendrier.",
        "Plusieurs engagements restent a suivre, notamment sur les documents promis et les echeances.",
        "La CFDT reviendra vers les adherents apres verification des reponses et validation humaine.",
      ],
    };
  }
  return {
    label: "Flash CSE",
    title: "A retenir en 2 minutes",
    items: [
      `${meeting.agendaPoints.length} points etaient en preparation.`,
      `${meeting.commitments.filter((item) => item.status !== "solde").length} engagement(s) restent a suivre.`,
      "Les points financiers fictifs montrent des questions differentes selon HDPE et PP.",
      "Les informations insuffisantes feront l'objet de relances.",
    ],
  };
}

function responseAnalysisFor(category) {
  const map = {
    complete: "Reponse exploitable, a verifier avec les documents sources avant diffusion.",
    partielle: "Reponse partielle : une relance ou un document complementaire est necessaire.",
    vague: "Reponse trop generale : demander un indicateur, une date ou un engagement ecrit.",
    "hors sujet": "Reponse hors sujet : reformuler la question et demander une reponse ciblee.",
    "a verifier": "Point a verifier avec document, PV ou reference juridique.",
    "engagement pris": "Engagement a inscrire au suivi avec responsable et echeance.",
    "document promis": "Document promis a ajouter au suivi des pieces attendues.",
    "echeance annoncee": "Echeance a tracer dans les relances du prochain CSE.",
  };
  return map[category] || map.partielle;
}

function createMeetingFromForm(form) {
  const now = new Date().toISOString();
  const agendaLines = splitLines(form.get("agenda"));
  const cfdtQuestions = splitLines(form.get("cfdtQuestions"));
  const otherQuestions = splitLines(form.get("otherQuestions"));

  return {
    id: uid("meeting"),
    schemaVersion: SCHEMA_VERSION,
    title: String(form.get("title") || "").trim(),
    date: String(form.get("date") || today()),
    type: String(form.get("type") || "Ordinaire"),
    referent: String(form.get("referent") || "").trim(),
    createdAt: now,
    updatedAt: now,
    notes: String(form.get("notes") || "").trim(),
    agendaPoints: agendaLines.map((line, index) => ({
      id: uid(`point-${index}`),
      title: line,
      category: "Direction",
      summary: "Point a qualifier avec les documents fournis et les questions de preparation.",
      tags: ["documentaire", "pv"],
      documents: [],
      previousCommitments: [],
      preparedQuestions: [
        "Quel est l'objectif exact de ce point ?",
        "Quels documents manquent pour preparer une position CSE ?",
      ],
    })),
    questions: {
      cfdt: cfdtQuestions.map((question) => buildQuestion(question, "CFDT")),
      other: otherQuestions.map((question) => buildQuestion(question, "Autre organisation")),
    },
    fieldQuestions: [],
    consultations: [],
    commitments: [],
    promisedDocuments: [],
    responses: [],
    markers: [],
  };
}

function buildQuestion(original, author) {
  return {
    id: uid("question"),
    author,
    original,
    theme: "a qualifier",
    realSubject: "Sujet reel a reformuler apres lecture du contexte.",
    context: "Contexte a documenter.",
    issue: "Enjeu salarie a preciser.",
    lawCheck: "Droit applicable a verifier selon les documents.",
    documentNeeded: "Document source ou indicateur a demander.",
    probableAnswer: "Reponse probable a anticiper sans la supposer certaine.",
    followUps: [
      "Pouvez-vous preciser les donnees utilisees ?",
      "Quel calendrier de suivi proposez-vous ?",
      "Quelle reponse ecrite pourra etre transmise au CSE ?",
    ],
  };
}

function loadMeetings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [seedMeeting()];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length ? parsed : [seedMeeting()];
  } catch {
    return [seedMeeting()];
  }
}

function saveMeetings() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(meetings));
}

function seedMeeting() {
  return {
    id: "meeting-demo-cse-juillet",
    schemaVersion: SCHEMA_VERSION,
    title: "CSE ordinaire - demonstration fictive",
    date: "2026-07-18",
    type: "Ordinaire",
    referent: "Referent CFDT fictif",
    createdAt: "2026-07-03T08:00:00.000Z",
    updatedAt: "2026-07-03T08:00:00.000Z",
    notes: "Notes de demonstration. Ne pas utiliser avec des informations nominatives ou confidentielles.",
    agendaPoints: [
      {
        id: "point-charge-hdpe-pp",
        title: "Point charge industrielle HDPE / PP Sarralbe",
        category: "Direction",
        summary: "Lecture fictive des volumes, ventes, marge et EBITDA pour preparer des questions CSE centrees sur Sarralbe.",
        tags: ["financier", "documentaire", "pv"],
        documents: ["Tableau financier fictif HDPE/PP", "Budget fictif Sarralbe", "Forecast fictif a demander"],
        previousCommitments: ["Une trajectoire de charge devait etre representee au CSE suivant selon un engagement PV fictif de mai."],
        preparedQuestions: [
          "Quelle charge actualisee est prevue a 3 mois, 6 mois et 12 mois pour Sarralbe ?",
          "Quelle part de l'ecart RC EBITDA vient du volume, de la marge ou des couts ?",
          "Quels investissements restent maintenus pour securiser l'outil industriel ?",
        ],
      },
      {
        id: "point-organisation-maintenance",
        title: "Organisation maintenance ete",
        category: "Direction",
        summary: "Point fictif sur l'organisation des astreintes, priorites maintenance et risques de charge pendant la periode estivale.",
        tags: ["cssct", "juridique", "terrain"],
        documents: ["Planning maintenance fictif", "Synthese astreinte fictive"],
        previousCommitments: [],
        preparedQuestions: [
          "Quels effectifs seront disponibles par competence critique ?",
          "Comment les repos et astreintes seront-ils suivis ?",
          "Quels risques securite sont identifies pendant la periode estivale ?",
        ],
      },
      {
        id: "point-consultation-projet",
        title: "Information-consultation sur un projet d'organisation fictif",
        category: "Information-consultation",
        summary: "Projet fictif permettant de tester la preparation d'un avis motive sans decision automatique.",
        tags: ["consultation", "documentaire", "juridique", "cssct"],
        documents: ["Note de presentation fictive", "Calendrier projet fictif"],
        previousCommitments: [],
        preparedQuestions: [
          "Le CSE dispose-t-il de tous les documents necessaires pour comprendre le projet ?",
          "Quelles alternatives ont ete etudiees ?",
          "Quels impacts sont prevus pour les salaries concernes ?",
        ],
      },
      {
        id: "point-suivi-ventilation",
        title: "Suivi engagement ventilation atelier A fictif",
        category: "Sujet deja aborde",
        summary: "Exemple de memoire PV simulee pour relancer un engagement non solde.",
        tags: ["pv", "cssct", "terrain"],
        documents: ["Extrait PV fictif septembre", "Plan action prevention fictif a demander"],
        previousCommitments: ["La direction avait annonce une etude de ventilation a presenter lors d'une reunion suivante."],
        preparedQuestions: [
          "L'etude annoncee est-elle finalisee ?",
          "Quelles mesures provisoires ont ete prises ?",
          "Quelle echeance ferme peut etre inscrite au suivi CSE/CSSCT ?",
        ],
      },
    ],
    questions: {
      cfdt: [
        {
          id: "q-cfdt-charge",
          author: "CFDT",
          original: "Quelles garanties de charge sont prevues pour Sarralbe sur les prochains mois ?",
          theme: "charge industrielle",
          realSubject: "Securite des volumes confies au site et consequences sociales.",
          context: "Les donnees fictives montrent un volume sous budget sur HDPE et PP.",
          issue: "Anticiper les impacts sur organisation, interim, maintenance et emploi.",
          lawCheck: "Obligations d'information du CSE et documents economiques a verifier.",
          documentNeeded: "Forecast actualise, hypotheses budget et planning de charge.",
          probableAnswer: "La direction peut renvoyer a des arbitrages Groupe ou a une conjoncture de marche.",
          followUps: [
            "Quelles hypotheses de volumes sont retenues par ligne ?",
            "Quels ecarts au budget sont consideres comme temporaires ?",
            "Quelles mesures seront discutees si le deficit de volume dure ?",
          ],
        },
        {
          id: "q-cfdt-cssct",
          author: "CFDT",
          original: "Quels impacts l'organisation maintenance ete aura-t-elle sur fatigue, astreintes et securite ?",
          theme: "CSSCT",
          realSubject: "Charge de travail et prevention pendant une periode contrainte.",
          context: "Planning fictif incomplet, plusieurs competences critiques a verifier.",
          issue: "Eviter un transfert de risque vers les salaries presents.",
          lawCheck: "Regles sante securite, repos et suivi CSSCT a verifier.",
          documentNeeded: "Planning detaille, evaluation des risques et bilan astreintes.",
          probableAnswer: "La direction peut indiquer que le dispositif est habituel.",
          followUps: [
            "Quels indicateurs permettront de detecter la surcharge ?",
            "Quelle procedure en cas d'indisponibilite d'une competence critique ?",
            "La CSSCT sera-t-elle associee au retour d'experience ?",
          ],
        },
      ],
      other: [
        {
          id: "q-other-primes",
          author: "Autre organisation",
          original: "La direction prevoit-elle une adaptation des primes pendant la periode estivale ?",
          theme: "remuneration",
          realSubject: "Reconnaissance des contraintes de periode et conditions d'attribution.",
          context: "Question a comprendre sans la devaloriser automatiquement.",
          issue: "Verifier les effets concrets sur les salaries concernes.",
          lawCheck: "Accords primes, usages et egalite de traitement a verifier.",
          documentNeeded: "Regles d'attribution et historique des primes similaires.",
          probableAnswer: "La direction peut repondre que le cadre actuel suffit.",
          followUps: [
            "Quels criteres objectifs seraient retenus ?",
            "Quels salaries seraient concernes ou exclus ?",
            "Une reponse ecrite peut-elle etre transmise au CSE ?",
          ],
        },
      ],
    },
    fieldQuestions: [
      {
        id: "field-charge",
        raw: "On manque parfois de visibilite sur les changements de charge d'une semaine a l'autre.",
        theme: "charge de travail",
        audience: "equipes de production",
        context: "Remontee fictive sans nom ni service precis.",
        cseWording: "Quels outils de prevision et d'information permettent aux equipes de suivre les changements de charge ?",
        argument: "La visibilite de charge conditionne organisation, repos, maintenance et prevention.",
        followUp: "Demander un calendrier de communication et un indicateur de stabilite de charge.",
        createdAt: "2026-07-03T08:00:00.000Z",
      },
    ],
    consultations: [
      {
        id: "consult-organisation",
        title: "Projet d'organisation fictif",
        status: "elements insuffisants",
        object: "Projet fictif de reorganisation de flux internes, sans document reel.",
        available: ["Note de presentation fictive", "Calendrier cible fictif", "Perimetre general"],
        missing: ["Evaluation impacts par poste", "Alternatives etudiees", "Mesures de prevention", "Indicateurs de suivi"],
        checks: ["Cadre juridique a verifier", "Impacts emploi et charge", "Impacts sante securite", "Avis des salaries a recueillir"],
        questions: [
          "Quelles alternatives ont ete etudiees et pourquoi ont-elles ete ecartees ?",
          "Quels postes et equipes sont concernes directement ou indirectement ?",
          "Quels indicateurs seront transmis au CSE apres mise en oeuvre ?",
        ],
        readiness: "A ce stade fictif, le CSE ne dispose pas de tous les elements necessaires : les impacts par poste et les mesures de prevention manquent.",
      },
    ],
    commitments: [
      {
        id: "commit-ventilation",
        title: "Presenter l'etude ventilation atelier A fictive",
        dueDate: "2026-08-31",
        status: "a relancer",
      },
      {
        id: "commit-charge",
        title: "Transmettre un forecast de charge fictif",
        dueDate: "2026-07-31",
        status: "document attendu",
      },
    ],
    promisedDocuments: [
      {
        id: "doc-forecast",
        title: "Forecast de charge fictif",
        status: "attendu",
      },
      {
        id: "doc-prevention",
        title: "Plan prevention fictif organisation ete",
        status: "attendu",
      },
    ],
    responses: [
      {
        id: "resp-charge",
        pointId: "point-charge-hdpe-pp",
        pointTitle: "Point charge industrielle HDPE / PP Sarralbe",
        raw: "La direction indique que les volumes seront suivis mensuellement et qu'un forecast pourra etre partage.",
        summary: "Un suivi mensuel est annonce, avec un forecast promis.",
        analysis: "Reponse partielle : le format, la date et le niveau de detail du forecast restent a obtenir.",
        cfdtComment: "Demander une transmission ecrite et un point de suivi au prochain CSE.",
        category: "document promis",
        createdAt: "2026-07-03T09:00:00.000Z",
      },
    ],
    markers: [
      {
        id: "marker-demo",
        type: "Document promis",
        meetingId: "meeting-demo-cse-juillet",
        pointId: "point-charge-hdpe-pp",
        questionId: "q-cfdt-charge",
        createdAt: "2026-07-03T09:05:00.000Z",
      },
    ],
  };
}

function exportCycleData() {
  const payload = {
    exportedAt: new Date().toISOString(),
    module: "CFDT Nexus - Cycle CSE intelligent",
    version: "1.0.0",
    warning: "Export de demonstration locale, sans document confidentiel ni donnee nominative.",
    meetings,
    financeDemo: FINANCE_ACTIVITIES,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `cfdt-nexus-cycle-cse-${today()}.json`;
  link.click();
  URL.revokeObjectURL(url);
  showToast("Export JSON prepare.");
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function setDefaultFormDate() {
  const field = els.meetingForm?.date;
  if (field && !field.value) field.value = today();
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function uid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatDateShort(value) {
  if (!value) return "date a verifier";
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
  }).format(new Date(value));
}

function formatDateLong(value) {
  if (!value) return "date a verifier";
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

function formatSigned(value) {
  return `${value > 0 ? "+" : ""}${Number.isInteger(value) ? value : value.toFixed(1)}`;
}

function formatPercent(value) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)} %`;
}

function shortText(value, maxLength) {
  const text = String(value || "").trim();
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

function unique(items) {
  return [...new Set((items || []).filter(Boolean))];
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("toast--visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.remove("toast--visible");
  }, 2600);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}
