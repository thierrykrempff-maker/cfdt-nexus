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
const issueGroupsPanel = document.getElementById("issueGroupsPanel");
const issueGroups = document.getElementById("issueGroups");
const expertPanel = document.getElementById("expertPanel");
const expertContent = document.getElementById("expertContent");
const expertConfidence = document.getElementById("expertConfidence");

const examples = [
  "classification",
  "Un salarie en 5x8 peut-il assister a une reunion du CSE pendant son repos, et comment ce temps doit-il etre traite ?",
  "Un salarie d'astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste : quels sont ses droits en matiere de repos et comment l'intervention doit-elle apparaitre sur la paie ?"
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

function renderExpert(expert) {
  expertContent.textContent = "";
  if (!expert || !expert.active) {
    expertPanel.hidden = true;
    return;
  }
  expertPanel.hidden = false;
  setConfidence(expertConfidence, expert.niveau_de_confiance);
  expertContent.appendChild(expertBlock("Reponse courte", expert.response_courte));
  expertContent.appendChild(expertBlock("Ce qui est certain", expert.ce_qui_est_certain));
  expertContent.appendChild(expertBlock("Ce qui depend des textes locaux", expert.ce_qui_depend_des_textes_locaux));
  expertContent.appendChild(expertBlock("Raisonnement juridique prudent", expert.raisonnement_juridique_prudent));
  expertContent.appendChild(expertBlock("Questions a poser a la direction", expert.questions_a_poser_direction));
  expertContent.appendChild(expertBlock("Limites", expert.limites));
}

function renderResult(payload) {
  const answer = payload.answer;
  emptyState.hidden = true;
  resultContent.hidden = false;
  resultQuestion.textContent = answer.query;
  setConfidence(confidenceValue, answer.confidence);
  shortAnswer.textContent = answer.short_answer || "A completer.";
  workingPosition.textContent = answer.working_position || "A completer.";
  fillList(sourcesList, answer.sources || [], sourceLine);
  fillList(findingsList, answer.findings || []);
  fillList(documentsList, answer.documents_to_request || []);
  fillList(questionsList, answer.questions_to_ask || []);
  fillList(warningsList, answer.warnings || []);
  renderIssueGroups(answer.issue_groups || []);
  renderExpert(payload.expert_juriste);
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
    setStatus("Analyse OK", payload.answer.confidence);
  } catch (error) {
    renderError(error.message);
    setStatus("Erreur", "faible");
  } finally {
    button.disabled = false;
  }
});
