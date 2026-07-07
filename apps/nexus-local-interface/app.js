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
  if (source.article) parts.push(source.article);
  return parts.join(" | ");
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

function renderResult(payload) {
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
  fillList(sourcesList, orchestration.sources || answer.sources || [], sourceLine);
  fillList(findingsList, answer.findings || []);
  fillList(documentsList, orchestration.documents_necessaires || answer.documents_to_request || []);
  fillList(questionsList, orchestration.questions_utiles || answer.questions_to_ask || []);
  fillList(warningsList, orchestration.limites || answer.warnings || []);
  renderIssueGroups(answer.issue_groups || []);
  renderExperts(payload);
}

function renderError(message) {
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
