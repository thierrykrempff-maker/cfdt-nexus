// Recherche dans l'archive locale des PV du CE/CSE : bouton autonome et bloc sous chaque réponse.
// Les extraits restent à l'écran : ils ne font partie d'aucun rapport, copie, impression ni téléchargement.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { enabled: false, available: false, indexed: 0, inlineTicket: 0, rows: [], sort: "relevance" };

  async function api(path, options) {
    const response = await fetch(path, { cache: "no-store", ...options });
    if (!response.ok) throw new Error("http " + response.status);
    return response.json();
  }

  async function refreshStatus() {
    try {
      const data = await api("/api/pv-archive/status");
      state.enabled = Boolean(data.enabled);
      state.available = Boolean(data.available);
      state.indexed = Number(data.indexed_documents || 0);
    } catch (error) {
      state.enabled = false;
      state.available = false;
    }
    return state;
  }

  function statusMessage() {
    if (!state.enabled) {
      return "La recherche dans les PV n’est pas activée sur ce poste (option NEXUS_PV_ARCHIVE_ENABLED).";
    }
    if (!state.available) {
      return "Le service d’archive des PV est arrêté. Lancez le service « Précédents » puis réessayez.";
    }
    return `Archive des PV disponible${state.indexed ? ` · ${state.indexed} PV indexés` : ""}.`;
  }

  async function search(query, extra = {}) {
    const body = { query, ...extra };
    const data = await api("/api/pv-archive/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return data.pv_archive || { status: "UNAVAILABLE", results: [] };
  }

  function sorted(rows) {
    const copy = [...rows];
    if (state.sort === "recent") copy.sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
    if (state.sort === "old") copy.sort((a, b) => String(a.date || "9999").localeCompare(String(b.date || "9999")));
    return copy;
  }

  function card(row) {
    const section = document.createElement("section");
    section.className = "cse-previous-minute pv-archive-card";
    const title = document.createElement("strong");
    title.textContent = [row.title, row.date, row.instance, row.reference].filter(Boolean).join(" — ");
    const excerpt = document.createElement("mark");
    excerpt.className = "nexus-source-highlight";
    excerpt.textContent = row.excerpt || "Extrait non disponible.";
    const relation = document.createElement("p");
    relation.textContent = row.relation || "";
    const limits = document.createElement("small");
    limits.textContent = (row.limits || []).join(" ");
    section.append(title, excerpt, relation, limits);
    return section;
  }

  function note(text, className = "source-context-notice") {
    const paragraph = document.createElement("p");
    paragraph.className = className;
    paragraph.textContent = text;
    return paragraph;
  }

  function render(container, data, options = {}) {
    container.textContent = "";
    const status = data.status;
    if (status === "DISABLED" || status === "UNAVAILABLE" || status === "EMPTY_QUERY") {
      container.append(note(
        status === "UNAVAILABLE"
          ? "Le service d’archive des PV est injoignable. Aucun résultat n’a pu être recherché."
          : data.notice,
        "pv-archive-message",
      ));
      return;
    }
    const rows = options.rows || data.results || [];
    if (!rows.length) {
      container.append(note(
        "Aucun passage correspondant dans l’archive. Essayez d’autres mots (synonymes, ancien vocabulaire). " +
        "L’absence de résultat ne prouve pas que le sujet n’a jamais été traité.",
        "pv-archive-message",
      ));
      return;
    }
    if (data.concepts && data.concepts.length) {
      container.append(note(
        `Mots recherchés : ${data.concepts.join(", ")} (au moins ${data.required_matches} ensemble).`,
      ));
    }
    const grid = document.createElement("div");
    grid.className = "cse-previous-minutes";
    sorted(rows).forEach((row) => grid.append(card(row)));
    container.append(grid, note(data.notice));
  }

  // --- Bouton « Recherche dans les PV » (panneau autonome) -----------------------------------------
  const panel = $("pvArchivePanel");
  const form = $("pvArchiveForm");
  const results = $("pvArchiveResults");
  const statusLine = $("pvArchiveStatus");
  const openButton = $("pvSearchButton");
  let lastStandalone = null;

  async function openPanel(prefill) {
    panel.hidden = false;
    openButton.setAttribute("aria-expanded", "true");
    if (typeof prefill === "string") $("pvArchiveQuery").value = prefill;
    await refreshStatus();
    statusLine.textContent = statusMessage();
    $("pvArchiveQuery").focus();
  }

  function closePanel() {
    panel.hidden = true;
    openButton.setAttribute("aria-expanded", "false");
  }

  async function submitStandalone(event) {
    event.preventDefault();
    const query = $("pvArchiveQuery").value.trim();
    if (!query) {
      results.textContent = "";
      results.append(note("Saisissez une question ou des mots-clés.", "pv-archive-message"));
      return;
    }
    results.textContent = "";
    results.append(note("Recherche dans l’archive des PV…", "pv-archive-message"));
    const extra = { limit: 10 };
    if ($("pvArchiveSince").value) extra.since = $("pvArchiveSince").value;
    if ($("pvArchiveUntil").value) extra.until = $("pvArchiveUntil").value;
    try {
      lastStandalone = await search(query, extra);
      render(results, lastStandalone);
      statusLine.textContent = lastStandalone.results && lastStandalone.results.length
        ? `${lastStandalone.results.length} PV retrouvé(s).`
        : statusMessage();
    } catch (error) {
      results.textContent = "";
      results.append(note("La recherche a échoué. Nexus est-il toujours lancé ?", "pv-archive-message"));
    }
  }

  // --- Bloc sous chaque réponse (questions) ---------------------------------------------------------
  async function showForQuestion(questionText) {
    const inline = $("pvArchiveInline");
    const body = $("pvArchiveInlineBody");
    if (!inline || !body) return;
    const text = String(questionText || "").trim();
    const ticket = ++state.inlineTicket;
    if (!text) {
      inline.hidden = true;
      return;
    }
    await refreshStatus();
    if (ticket !== state.inlineTicket) return;
    if (!state.enabled) {
      inline.hidden = true; // option désactivée : aucun bloc, comportement inchangé
      return;
    }
    inline.hidden = false;
    body.textContent = "";
    body.append(note("Recherche dans l’archive des PV…", "pv-archive-message"));
    try {
      const data = await search(text, { limit: 4 });
      if (ticket !== state.inlineTicket) return; // une réponse plus récente a pris la place
      render(body, data);
    } catch (error) {
      if (ticket === state.inlineTicket) {
        body.textContent = "";
        body.append(note("La recherche dans l’archive a échoué.", "pv-archive-message"));
      }
    }
  }

  function init() {
    if (!panel) return;
    openButton.addEventListener("click", () => (panel.hidden ? openPanel() : closePanel()));
    $("pvArchiveClose").addEventListener("click", closePanel);
    form.addEventListener("submit", submitStandalone);
    $("pvArchiveSort").addEventListener("change", (event) => {
      state.sort = event.target.value;
      if (lastStandalone) render(results, lastStandalone);
    });
    const more = $("pvArchiveInlineMore");
    if (more) {
      more.addEventListener("click", () => {
        const text = (document.getElementById("questionInput") || {}).value || "";
        openPanel(text.trim());
        panel.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  window.NexusPvArchive = { showForQuestion, refreshStatus };
  document.addEventListener("DOMContentLoaded", init);
})();
