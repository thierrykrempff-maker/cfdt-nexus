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
  let questionText = "";
  function setQuestionText(text) {
    questionText = String(text || "");
  }

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
    (context.follow_up_answers || []).forEach((item) => lines.push(`- Précision : ${item.question} → ${item.answer}`));
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
        question: [context.user_question || "", ...(context.follow_up_answers || []).map((item) => item.answer)].join(". ").slice(0, 900),
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
    const question = questionText || (document.getElementById("resultQuestion") || {}).textContent || (document.getElementById("questionInput") || {}).value || "";
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

  // Chaque point d'un ordre du jour : toutes les sources officielles et les documents, chargés à l'ouverture du volet.
  function appendPointSources(cardElement, point) {
    if (!cardElement || !point || !point.title) return;
    const details = document.createElement("details");
    details.className = "point-official-sources";
    const summary = document.createElement("summary");
    summary.textContent = "Sources officielles et documents pour ce point (Légifrance, Judilibre, convention, règlement intérieur, guides…)";
    const body = document.createElement("div");
    body.setAttribute("aria-live", "polite");
    details.append(summary, body);
    let loaded = false;
    details.addEventListener("toggle", async () => {
      if (!details.open || loaded) return;
      loaded = true;
      body.textContent = "";
      body.append(paragraph("Recherche dans toutes les sources…", "pv-archive-message"));
      try {
        const status = await api("/api/official-sources/status");
        if (!status.enabled) {
          body.textContent = "";
          body.append(paragraph("Le bloc « Sources officielles » n’est pas activé sur ce poste.", "pv-archive-message"));
          return;
        }
        const post = (url, extra) => api(url, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: point.title, ...extra }),
        });
        const [official, docs] = await Promise.all([
          post("/api/official-sources/search"),
          post("/api/docs-archive/search", { limit: 3 }).catch(() => null),
        ]);
        render(body, official.official_sources || { status: "UNAVAILABLE", notice: "Recherche indisponible." });
        const rows = docs && docs.pv_archive && docs.pv_archive.status === "READY" ? docs.pv_archive.results || [] : [];
        if (rows.length && window.NexusPvArchive) {
          const heading = document.createElement("h3");
          heading.textContent = "Vos documents syndicaux (paie, congés, NAO, branche…)";
          const grid = document.createElement("div");
          grid.className = "cse-previous-minutes";
          rows.forEach((row) => grid.append(window.NexusPvArchive.card(row)));
          body.append(heading, grid);
        }
      } catch (error) {
        loaded = false;
        body.textContent = "";
        body.append(paragraph("La recherche dans les sources officielles a échoué.", "pv-archive-message"));
      }
    });
    cardElement.append(details);
  }

  // « Recherche documentaire » : une requête, toutes les sources (officielles, PV, accords, documents).
  function openAll() {
    const panel = $("allSourcesPanel");
    if (!panel) return;
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
    const input = $("allSourcesQuery");
    if (input) input.focus();
  }

  // Toutes les sources pour une requête : officielles (Légifrance, Judilibre, convention, règlement, guides), PV, accords, documents.
  async function fillAllSources(out, query) {
    out.textContent = "";
    out.append(paragraph("Recherche dans toutes les sources…", "pv-archive-message"));
    const post = (url, extra) => api(url, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, ...extra }),
    });
    try {
      const [official, pv, accords, docs] = await Promise.all([
        post("/api/official-sources/search"),
        post("/api/pv-archive/search", { limit: 6 }).catch(() => null),
        post("/api/accords-archive/search", { limit: 6 }).catch(() => null),
        post("/api/docs-archive/search", { limit: 4 }).catch(() => null),
      ]);
      out.textContent = "";
      const officialBody = document.createElement("div");
      out.append(officialBody);
      render(officialBody, official.official_sources || { status: "UNAVAILABLE", notice: "Recherche indisponible." });
      [["Dans les PV du CE/CSE", pv], ["Dans les accords d’entreprise", accords], ["Dans vos documents syndicaux", docs]].forEach(([label, data]) => {
        const archive = data && data.pv_archive;
        const heading = document.createElement("h3");
        heading.textContent = label;
        out.append(heading);
        const rows = archive && archive.status === "READY" ? archive.results || [] : [];
        if (!rows.length) {
          out.append(paragraph(archive && archive.status !== "READY" ? (archive.notice || "Source non consultée.") : "Aucun passage correspondant.", "pv-archive-message"));
          return;
        }
        const grid = document.createElement("div");
        grid.className = "cse-previous-minutes";
        rows.forEach((item) => grid.append(window.NexusPvArchive ? window.NexusPvArchive.card(item) : document.createTextNode(item.excerpt)));
        out.append(grid);
      });
    } catch (error) {
      out.textContent = "";
      out.append(paragraph("La recherche a échoué. Nexus est-il toujours lancé ?", "pv-archive-message"));
    }
  }

  async function searchEverywhere(event) {
    event.preventDefault();
    const query = ($("allSourcesQuery") || {}).value || "";
    const out = $("allSourcesResults");
    if (!out) return;
    if (!query.trim()) {
      out.textContent = "";
      out.append(paragraph("Saisissez une question ou des mots-clés.", "pv-archive-message"));
      return;
    }
    await fillAllSources(out, query);
  }

  // Volet « toutes les sources » ajouté sous un résultat (analyse RGPD…), chargé à l'ouverture, avec le dossier pour Claude.
  function appendSources(container, query, title, key) {
    if (!container || !String(query || "").trim()) return;
    const old = container.querySelector(`details[data-sources-key="${key}"]`);
    if (old) old.remove();
    const details = document.createElement("details");
    details.className = "point-official-sources";
    details.dataset.sourcesKey = key;
    const summary = document.createElement("summary");
    summary.textContent = title;
    const body = document.createElement("div");
    body.setAttribute("aria-live", "polite");
    const dossier = document.createElement("div");
    dossier.className = "claude-dossier";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-button";
    button.textContent = "Préparer le dossier pour Claude";
    const status = document.createElement("p");
    status.className = "source-context-notice";
    status.id = `${key}DossierStatus`;
    status.setAttribute("aria-live", "polite");
    const area = document.createElement("textarea");
    area.id = `${key}DossierText`;
    area.rows = 10;
    area.readOnly = true;
    area.hidden = true;
    area.setAttribute("aria-label", "Dossier pour Claude");
    dossier.append(button, status, area);
    details.append(summary, body, dossier);
    let loaded = false;
    details.addEventListener("toggle", () => {
      if (!details.open || loaded) return;
      loaded = true;
      fillAllSources(body, query);
    });
    button.addEventListener("click", () => copyDossier({
      key, url: "/api/claude-dossier/build", body: { query }, statusId: status.id, areaId: area.id,
      wait: "Préparation du dossier (toutes les sources)…",
    }));
    container.append(details);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = $("allSourcesForm");
    if (form) form.addEventListener("submit", searchEverywhere);
    const close = $("allSourcesClose");
    if (close) close.addEventListener("click", () => { $("allSourcesPanel").hidden = true; });
  });

  // Accueil : une seule question, toutes les sources, un compte rendu lisible, puis la proposition d'une analyse avec Claude.
  const QUICK_TAGS = { verifie: "✔ vérifié dans le document" , non_retrouve: "⚠ non retrouvé dans le document : à vérifier" };
  let quickQuery = "";

  function quickRow(item) {
    const card = document.createElement("section");
    card.className = "cse-previous-minute pv-archive-card";
    const title = document.createElement("strong");
    title.textContent = `[S${item.number}] ${[item.title, item.date, item.detail].filter(Boolean).join(" — ")}`;
    const excerpt = document.createElement("mark");
    excerpt.className = "nexus-source-highlight";
    excerpt.textContent = item.excerpt || "Extrait non disponible.";
    card.append(title, excerpt);
    if (QUICK_TAGS[item.verification]) card.append(paragraph(QUICK_TAGS[item.verification], "source-context-notice"));
    if (item.url && /^https:\/\//.test(item.url)) {
      const link = document.createElement("a");
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Ouvrir le texte";
      card.append(link);
    }
    return card;
  }

  function renderQuick(digest, out) {
    out.textContent = "";
    const parts = digest.sections.map((section) => ({ ...section, rows: section.rows.filter((item) => !item.again) }));
    const found = parts.filter((section) => section.rows.length);
    const brief = document.createElement("div");
    brief.className = "quick-ask-brief";
    const topics = digest.topics && digest.topics.length ? ` Sujet reconnu : ${digest.topics.join(" ; ")}.` : "";
    brief.textContent = found.length
      ? `Compte rendu Nexus : ${digest.sources} source(s) retrouvée(s) dans ${found.length} rubrique(s) (${found.map((s) => s.label.split(" (")[0]).join(", ")}).${topics}`
      : `Aucune source trouvée avec ces mots.${topics} Reformulez avec d’autres termes.`;
    out.append(brief);
    parts.forEach((section) => {
      if (!section.rows.length) return;
      const heading = document.createElement("h3");
      heading.textContent = section.label;
      out.append(heading, paragraph(section.note));
      const grid = document.createElement("div");
      grid.className = "cse-previous-minutes";
      section.rows.forEach((item) => grid.append(quickRow(item)));
      out.append(grid);
    });
    const empty = parts.filter((section) => !section.rows.length).map((section) => section.label.split(" (")[0]);
    if (empty.length) out.append(paragraph(`Rien de pertinent trouvé dans : ${empty.join(", ")}.`, "pv-archive-message"));
    if (digest.dropped) out.append(paragraph(`${digest.dropped} extrait(s) écarté(s) automatiquement (illisibles ou sans rapport avec la question).`));
    (digest.divergences || []).forEach((line) => out.append(paragraph(`Valeurs différentes selon les sources (à confirmer) : ${line}`, "pv-archive-message")));
    if ((digest.unavailable || []).length) out.append(paragraph(`Sources non consultées : ${digest.unavailable.join(", ")}. L’absence de résultat ne prouve rien.`, "pv-archive-message"));
  }

  async function runQuickAsk(event) {
    event.preventDefault();
    const input = $("quickAskInput");
    const status = $("quickAskStatus");
    const out = $("quickAskResult");
    const closing = $("quickAskClaude");
    if (!input || !status || !out) return;
    const query = input.value.trim();
    closing.hidden = true;
    $("quickAskDossierText").hidden = true;
    $("quickAskDossierStatus").textContent = "";
    if (!query) {
      status.textContent = "Écrivez votre question.";
      return;
    }
    quickQuery = query;
    out.textContent = "";
    status.textContent = "Recherche dans toutes les sources (loi, jurisprudence, convention, accords, règlement intérieur, PV, guides)… environ 10 secondes.";
    $("quickAskButton").disabled = true;
    try {
      const data = await api("/api/digest", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }),
      });
      const digest = data.digest || {};
      if (digest.status !== "READY") {
        status.textContent = digest.notice || "Recherche indisponible.";
        return;
      }
      status.textContent = "";
      renderQuick(digest, out);
      closing.hidden = false;
      closing.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
      status.textContent = "La recherche a échoué. Nexus est-il toujours lancé ?";
    } finally {
      $("quickAskButton").disabled = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = $("quickAskForm");
    if (form) form.addEventListener("submit", runQuickAsk);
    const input = $("quickAskInput");
    if (input) input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) form.requestSubmit();
    });
    const yes = $("quickAskYes");
    if (yes) yes.addEventListener("click", async () => {
      await copyDossier({
        key: "quick", url: "/api/claude-dossier/build", body: { query: quickQuery },
        statusId: "quickAskDossierStatus", areaId: "quickAskDossierText",
        wait: "Préparation du dossier pour Claude…",
      });
      const status = $("quickAskDossierStatus");
      if (status && /Dossier prêt/.test(status.textContent)) {
        status.textContent += " Ensuite, écrivez simplement « analyse » dans Claude : il contrôlera les textes et vous fera un compte rendu synthétique.";
      }
    });
    const no = $("quickAskNo");
    if (no) no.addEventListener("click", () => {
      $("quickAskClaude").hidden = true;
      $("quickAskDossierText").hidden = true;
    });
  });

  window.NexusOfficialSources = { showForQuestion, setAgenda, setCase, appendPointSources, openAll, setQuestionText, appendSources };
})();
