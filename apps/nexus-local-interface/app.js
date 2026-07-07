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

let currentPayload = null;
let currentReportMarkdown = "";

const examples = [
  "classification",
  "Un salarie en 5x8 peut-il assister a une reunion du CSE pendant son repos, et comment ce temps doit-il etre traite ?",
  "Un salarie d'astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste : quels sont ses droits en matiere de repos et comment l'intervention doit-elle apparaitre sur la paie ?",
  "Je pense qu'il manque des heures de nuit et une majoration dimanche sur mon bulletin. Que faut-il controler ?"
];

queryInput.value = examples[1];

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
    code_travail: "Code du travail absent du socle documentaire local actuel.",
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
      if (source.chunk_id) metaParts.push(source.chunk_id);
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
  emptyState.hidden = true;
  resultContent.hidden = false;
  resultQuestion.textContent = orchestration.question_posee || answer.query;
  setConfidence(confidenceValue, orchestration.niveau_de_confiance || answer.confidence);
  fillInlineList(domainsList, orchestration.domaines_detectes || answer.route.domains || []);
  fillInlineList(expertsList, orchestration.experts_mobilises || []);
  shortAnswer.textContent = orchestration.reponse_synthetique_nexus || answer.short_answer || "A completer.";
  workingPosition.textContent = orchestration.position_de_travail || answer.working_position || "A completer.";
  renderSources(sourcesList, answer, orchestration);
  fillList(findingsList, answer.findings || []);
  fillList(documentsList, orchestration.documents_necessaires || answer.documents_to_request || []);
  fillList(questionsList, orchestration.questions_utiles || answer.questions_to_ask || []);
  fillList(warningsList, orchestration.limites || answer.warnings || []);
  renderIssueGroups(answer.issue_groups || []);
  renderExperts(payload);
  resetReportState();
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  setStatus("Analyse...", null);
  const button = form.querySelector("button");
  button.disabled = true;

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        source_limit: Number(sourceLimitInput.value || 6)
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Erreur locale.");
    }
    renderResult(payload);
    setStatus("Analyse OK", payload.orchestration?.niveau_de_confiance || payload.answer.confidence);
  } catch (error) {
    renderError(error.message);
    setStatus("Erreur", "faible");
  } finally {
    button.disabled = false;
  }
});

generateReportButton.addEventListener("click", renderReport);
copyReportButton.addEventListener("click", copyReport);
downloadReportButton.addEventListener("click", downloadReport);
