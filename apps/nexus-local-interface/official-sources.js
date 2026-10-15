// Bloc « Sources officielles à vérifier » sous chaque réponse : Légifrance, Judilibre, convention collective.
// Reste à l'écran : hors #reportPanel, donc jamais dans la copie, l'impression ni le téléchargement.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const SECTIONS = [
    ["reference", "Légifrance — articles de référence du sujet"],
    ["legifrance", "Légifrance — autres articles trouvés par mots-clés"],
    ["judilibre", "Judilibre — Cour de cassation"],
    ["convention", "Convention collective des industries chimiques (IDCC 44)"],
    ["reglement", "Règlement intérieur d’INEOS Sarralbe"],
    ["autres", "Autres sources officielles (CDTN, service-public, CNIL, DREETS, CARSAT, INRS)"],
  ];
  const EMPTY = {
    reference: "",
    legifrance: "Aucun article du Code du travail retrouvé avec ces mots.",
    judilibre: "Aucune décision retrouvée avec ces mots.",
    convention: "Aucun passage de la convention collective retrouvé avec ces mots.",
    reglement: "Aucun passage du règlement intérieur retrouvé avec ces mots.",
    autres: "Aucune page de ces sites officiels ne correspond à ces mots.",
  };
  let ticket = 0;

  async function api(path, options) {
    const response = await fetch(path, { cache: "no-store", ...options });
    if (!response.ok) throw new Error("http " + response.status);
    return response.json();
  }

  function paragraph(text, className) {
    const p = document.createElement("p");
    p.className = className || "source-context-notice";
    p.textContent = text;
    return p;
  }

  function row(item) {
    const section = document.createElement("section");
    section.className = "cse-previous-minute pv-archive-card";
    const title = document.createElement("strong");
    title.textContent = [item.title, item.date, item.detail].filter(Boolean).join(" — ");
    const excerpt = document.createElement("mark");
    excerpt.className = "nexus-source-highlight";
    excerpt.textContent = item.excerpt || "Extrait non disponible.";
    section.append(title, excerpt);
    if (item.url && /^https:\/\//.test(item.url)) {
      const link = document.createElement("a");
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Ouvrir le texte officiel";
      section.append(link);
    }
    return section;
  }

  function render(body, data) {
    body.textContent = "";
    if (data.status !== "READY") {
      body.append(paragraph(data.notice, "pv-archive-message"));
      return;
    }
    body.append(paragraph(`Mots-clés envoyés aux services officiels : ${data.keywords.join(", ")}.`));
    if (data.topics && data.topics.length) body.append(paragraph(`Sujet reconnu : ${data.topics.join(" ; ")}.`));
    SECTIONS.forEach(([key, label]) => {
      const part = (data.sections || {})[key];
      if (key === "reference" && (!part || (part.status === "READY" && !part.rows.length))) return; // aucun sujet reconnu
      if (!part) return;
      const heading = document.createElement("h3");
      heading.textContent = label;
      body.append(heading);
      if (part.status === "READY" && part.rows.length) {
        const grid = document.createElement("div");
        grid.className = "cse-previous-minutes";
        part.rows.forEach((item) => grid.append(row(item)));
        body.append(grid);
      } else {
        body.append(paragraph(part.status === "READY" ? EMPTY[key] : part.notice || "Source indisponible.", "pv-archive-message"));
      }
      if (part.status === "READY" && part.notice) body.append(paragraph(part.notice));
    });
    body.append(paragraph(data.notice));
  }

  // Parcours « Questions salariés » / « Assistance entretien disciplinaire » : le type de situation et les réponses recueillies
  // enrichissent la recherche et alimentent le dossier de défense.
  let currentCase = null;
  let currentSituation = "";
  let currentCaseMode = "defense";
  function setCase(request, situationLabel, mode) {
    currentCase = request && request.portal_context ? request : null;
    currentSituation = String(situationLabel || "");
    currentCaseMode = mode === "paie" ? "paie" : "defense";
    const box = $("defenseDossier");
    if (box) box.hidden = !currentCase;
    const button = $("defenseDossierButton");
    if (button) {
      button.textContent = currentCaseMode === "paie"
        ? "Préparer le dossier de contrôle de paie et de congés pour Claude"
        : "Préparer le dossier de défense pour Claude";
    }
    const area = $("defenseDossierText");
    if (area) area.hidden = true;
  }

  function caseFacts() {
    const context = (currentCase && currentCase.portal_context) || {};
    const lines = [];
    (context.employee_interview || []).forEach((item) => lines.push(`- ${item.question} → ${item.answer}`));
    Object.entries(context.facts || {}).forEach(([key, value]) => {
      if (value !== false && value !== "" && value != null) lines.push(`- ${key} : ${value === true ? "oui" : value}`);
    });
    if ((context.available_documents || []).length) lines.push(`- Documents disponibles : ${context.available_documents.join(", ")}`);
    if (context.desired_outcome) lines.push(`- Résultat souhaité : ${context.desired_outcome}`);
    if (context.urgency) lines.push("- Situation signalée comme urgente");
    return lines.join("\n");
  }

  function prepareDefenseDossier() {
    if (!currentCase) return;
    const context = currentCase.portal_context;
    copyDossier({
      key: "defense", url: "/api/claude-dossier/defense",
      body: {
        mode: currentCaseMode,
        kind: currentSituation || context.situation_type || "Situation d’un salarié",
        question: context.user_question || "",
        facts: `${context.user_question || ""}
${caseFacts()}`.trim(),
      },
      statusId: "defenseDossierStatus", areaId: "defenseDossierText",
      wait: currentCaseMode === "paie" ? "Préparation du dossier de contrôle de paie (toutes les sources)…" : "Préparation du dossier de défense (toutes les sources)…",
    });
  }

  async function showForQuestion(questionText) {
    const inline = $("officialSourcesInline");
    const body = $("officialSourcesBody");
    if (!inline || !body) return;
    const text = String(questionText || "").trim();
    const mine = ++ticket;
    inline.hidden = true;
    if (!text) return;
    try {
      const status = await api("/api/official-sources/status");
      if (mine !== ticket || !status.enabled) return; // option désactivée : aucun bloc, comportement inchangé
      inline.hidden = false;
      body.textContent = "";
      body.append(paragraph("Recherche dans Légifrance, Judilibre et la convention collective…", "pv-archive-message"));
      const data = await api("/api/official-sources/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentCase && currentSituation ? `${currentSituation}. ${text}` : text }),
      });
      if (mine === ticket) render(body, data.official_sources || { status: "UNAVAILABLE", notice: "Recherche indisponible." });
    } catch (error) {
      if (mine === ticket && !inline.hidden) {
        body.textContent = "";
        body.append(paragraph("La recherche dans les sources officielles a échoué.", "pv-archive-message"));
      }
    }
  }

  // Dossier « Nexus → Claude » : toutes les sources rassemblées, copiées sur demande de l'utilisateur uniquement.
  const busy = new Set();
  async function copyDossier({ key, url, body, statusId, areaId, wait }) {
    const status = $(statusId);
    const area = $(areaId);
    if (!status || !area || busy.has(key)) return;
    busy.add(key);
    area.hidden = true;
    status.textContent = wait;
    try {
      const data = await api(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const dossier = data.dossier || {};
      if (dossier.status !== "READY") {
        status.textContent = dossier.notice || "Dossier indisponible.";
        return;
      }
      area.value = dossier.markdown;
      area.hidden = false;
      let copied = false;
      try {
        await navigator.clipboard.writeText(dossier.markdown);
        copied = true;
      } catch (error) {
        area.select();
      }
      status.textContent = `Dossier prêt : ${dossier.sources} sources numérotées` +
        (dossier.points ? ` pour ${dossier.points} point(s). ` : ". ") +
        (copied ? "Copié dans le presse-papiers : collez-le dans Claude." : "Sélectionné ci-dessous : copiez-le (Ctrl+C) puis collez-le dans Claude.");
    } catch (error) {
      status.textContent = "La préparation du dossier a échoué.";
    } finally {
      busy.delete(key);
    }
  }

  function prepareQuestionDossier() {
    const question = (document.getElementById("resultQuestion") || {}).textContent || (document.getElementById("questionInput") || {}).value || "";
    if (!question.trim()) {
      const status = $("claudeDossierStatus");
      if (status) status.textContent = "Posez d’abord une question.";
      return;
    }
    copyDossier({
      key: "question", url: "/api/claude-dossier/build", body: { query: question },
      statusId: "claudeDossierStatus", areaId: "claudeDossierText",
      wait: "Préparation du dossier (Légifrance, Judilibre, convention, accords, PV, guides officiels)…",
    });
  }

  // Ordre du jour du CSE : les titres des points déjà analysés (jamais le document) servent à interroger toutes les sources.
  let agendaAnalysis = null;
  function setAgenda(analysis) {
    agendaAnalysis = analysis && analysis.status === "READY" ? analysis : null;
    const box = $("agendaDossier");
    if (box) box.hidden = !agendaAnalysis;
  }

  function prepareAgendaDossier() {
    if (!agendaAnalysis) return;
    copyDossier({
      key: "agenda", url: "/api/claude-dossier/agenda",
      body: { points: (agendaAnalysis.points || []).map((p) => ({ position: p.position, title: p.title })), meeting: agendaAnalysis.agenda_document || "" },
      statusId: "agendaDossierStatus", areaId: "agendaDossierText",
      wait: "Préparation du dossier de l’ordre du jour (toutes les sources, point par point : environ une minute)…",
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const question = $("claudeDossierButton");
    if (question) question.addEventListener("click", prepareQuestionDossier);
    const defense = $("defenseDossierButton");
    if (defense) defense.addEventListener("click", prepareDefenseDossier);
    const agenda = $("agendaDossierButton");
    if (agenda) agenda.addEventListener("click", prepareAgendaDossier);
  });

  window.NexusOfficialSources = { showForQuestion, setAgenda, setCase };
})();
