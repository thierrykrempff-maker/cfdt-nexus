// Recherche dans les archives locales (PV du CE/CSE, accords d'entreprise) : bouton autonome et bloc sous chaque réponse.
// Les extraits restent à l'écran : ils ne font partie d'aucun rapport, copie, impression ni téléchargement.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  async function api(path, options) {
    const response = await fetch(path, { cache: "no-store", ...options });
    if (!response.ok) throw new Error("http " + response.status);
    return response.json();
  }

  function note(text, className = "source-context-notice") {
    const paragraph = document.createElement("p");
    paragraph.className = className;
    paragraph.textContent = text;
    return paragraph;
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

  function sorted(rows, sort) {
    const copy = [...rows];
    if (sort === "recent") copy.sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
    if (sort === "old") copy.sort((a, b) => String(a.date || "9999").localeCompare(String(b.date || "9999")));
    return copy;
  }

  function render(container, data, sort, texts) {
    container.textContent = "";
    const status = data.status;
    if (status === "DISABLED" || status === "UNAVAILABLE" || status === "EMPTY_QUERY") {
      container.append(note(status === "UNAVAILABLE" ? texts.unreachable : data.notice, "pv-archive-message"));
      return;
    }
    const rows = data.results || [];
    if (!rows.length) {
      container.append(note(texts.empty, "pv-archive-message"));
      return;
    }
    if (data.concepts && data.concepts.length) {
      container.append(note(
        `Mots recherchés : ${data.concepts.join(", ")} (au moins ${data.required_matches} ensemble).`,
      ));
    }
    const grid = document.createElement("div");
    grid.className = "cse-previous-minutes";
    sorted(rows, sort).forEach((row) => grid.append(card(row)));
    container.append(grid, note(data.notice));
  }

  // Une « archive » = un corpus (PV ou accords) avec son bouton d'en-tête, son panneau autonome et son bloc sous la réponse.
  function createArchive(config) {
    const state = { enabled: false, available: false, indexed: 0, ticket: 0, sort: "relevance", last: null };
    const el = (suffix) => $(config.prefix + suffix);
    const texts = config.texts;

    async function refreshStatus() {
      try {
        const data = await api(config.api + "/status");
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
      if (!state.enabled) return texts.notEnabled;
      if (!state.available) return texts.stopped;
      return `${texts.available}${state.indexed ? ` · ${state.indexed} ${texts.unit} indexés` : ""}.`;
    }

    async function search(query, extra = {}) {
      const data = await api(config.api + "/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, ...extra }),
      });
      return data.pv_archive || { status: "UNAVAILABLE", results: [] };
    }

    // --- panneau autonome ---------------------------------------------------------------------
    async function openPanel(prefill) {
      config.onOpen?.();
      if ($("agreementComparePanel")) $("agreementComparePanel").hidden = true;
      if ($("compareSearchButton")) $("compareSearchButton").setAttribute("aria-expanded", "false");
      el("Panel").hidden = false;
      $(config.button).setAttribute("aria-expanded", "true");
      if (typeof prefill === "string") el("Query").value = prefill;
      await refreshStatus();
      el("Status").textContent = statusMessage();
      el("Query").focus();
    }

    function closePanel() {
      el("Panel").hidden = true;
      $(config.button).setAttribute("aria-expanded", "false");
    }

    async function submitStandalone(event) {
      event.preventDefault();
      const results = el("Results");
      const query = el("Query").value.trim();
      results.textContent = "";
      if (!query) {
        results.append(note("Saisissez une question ou des mots-clés.", "pv-archive-message"));
        return;
      }
      results.append(note(texts.searching, "pv-archive-message"));
      const extra = { limit: 10 };
      if (el("Since").value) extra.since = el("Since").value;
      if (el("Until").value) extra.until = el("Until").value;
      try {
        state.last = await search(query, extra);
        render(results, state.last, state.sort, texts);
        el("Status").textContent = state.last.results && state.last.results.length
          ? `${state.last.results.length} ${texts.found}`
          : statusMessage();
      } catch (error) {
        results.textContent = "";
        results.append(note("La recherche a échoué. Nexus est-il toujours lancé ?", "pv-archive-message"));
      }
    }

    // --- bloc sous la réponse à une question ----------------------------------------------------
    async function showForQuestion(questionText) {
      const inline = el("Inline");
      const body = el("InlineBody");
      if (!inline || !body) return;
      const text = String(questionText || "").trim();
      const ticket = ++state.ticket;
      if (!text) {
        inline.hidden = true;
        return;
      }
      await refreshStatus();
      if (ticket !== state.ticket) return;
      if (!state.enabled) {
        inline.hidden = true; // option désactivée : aucun bloc, comportement inchangé
        return;
      }
      inline.hidden = false;
      body.textContent = "";
      body.append(note(texts.searching, "pv-archive-message"));
      try {
        const data = await search(text, { limit: 4 });
        if (ticket !== state.ticket) return; // une réponse plus récente a pris la place
        render(body, data, "relevance", texts);
      } catch (error) {
        if (ticket === state.ticket) {
          body.textContent = "";
          body.append(note("La recherche a échoué.", "pv-archive-message"));
        }
      }
    }

    function init() {
      const panel = el("Panel");
      const button = $(config.button);
      if (!panel || !button) return;
      button.addEventListener("click", () => (panel.hidden ? openPanel() : closePanel()));
      el("Close").addEventListener("click", closePanel);
      el("Form").addEventListener("submit", submitStandalone);
      el("Sort").addEventListener("change", (event) => {
        state.sort = event.target.value;
        if (state.last) render(el("Results"), state.last, state.sort, texts);
      });
      const more = el("InlineMore");
      if (more) {
        more.addEventListener("click", () => {
          const text = (document.getElementById("questionInput") || {}).value || "";
          openPanel(text.trim());
          panel.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      }
    }

    return { init, closePanel, showForQuestion, refreshStatus };
  }

  const archives = [];
  const closeOthers = (self) => () => archives.forEach((archive) => archive !== self && archive.closePanel());

  const pv = createArchive({
    prefix: "pvArchive",
    button: "pvSearchButton",
    api: "/api/pv-archive",
    onOpen: () => closeOthers(pv)(),
    texts: {
      notEnabled: "La recherche dans les PV n’est pas activée sur ce poste (option NEXUS_PV_ARCHIVE_ENABLED).",
      stopped: "Le service d’archive des PV est arrêté. Lancez le service « Précédents » puis réessayez.",
      available: "Archive des PV disponible",
      unit: "PV",
      found: "PV retrouvé(s).",
      searching: "Recherche dans l’archive des PV…",
      unreachable: "Le service d’archive des PV est injoignable. Aucun résultat n’a pu être recherché.",
      empty: "Aucun passage correspondant dans l’archive. Essayez d’autres mots (synonymes, ancien vocabulaire). " +
        "L’absence de résultat ne prouve pas que le sujet n’a jamais été traité.",
    },
  });
  const accords = createArchive({
    prefix: "accordsArchive",
    button: "accordsSearchButton",
    api: "/api/accords-archive",
    onOpen: () => closeOthers(accords)(),
    texts: {
      notEnabled: "La recherche dans les accords n’est pas activée sur ce poste (option NEXUS_ACCORDS_ARCHIVE_ENABLED).",
      stopped: "Le service d’archive est arrêté ou l’index des accords est absent. Lancez le service « Précédents » puis réessayez.",
      available: "Archive des accords disponible",
      unit: "accords",
      found: "accord(s) retrouvé(s).",
      searching: "Recherche dans l’archive des accords…",
      unreachable: "Le service d’archive est injoignable. Aucun résultat n’a pu être recherché.",
      empty: "Aucun passage correspondant dans les accords. Essayez d’autres mots (synonymes, intitulé exact). " +
        "L’absence de résultat ne prouve pas qu’aucun accord n’existe.",
    },
  });
  archives.push(pv, accords);

  // Accords rapprochés des points d'un ordre du jour CSE (dans la carte de chaque point)
  function appendAgreements(cardElement, rows) {
    if (!cardElement || !Array.isArray(rows) || !rows.length) return;
    const title = document.createElement("h4");
    title.textContent = "Accords et textes de l’archive";
    const grid = document.createElement("div");
    grid.className = "cse-previous-minutes";
    rows.forEach((row) => grid.append(card(row)));
    cardElement.append(title, grid);
  }

  window.NexusPvArchive = {
    showForQuestion: (text) => archives.forEach((archive) => archive.showForQuestion(text)),
    refreshStatus: () => Promise.all(archives.map((archive) => archive.refreshStatus())),
    appendAgreements,
    card,
  };
  document.addEventListener("DOMContentLoaded", () => archives.forEach((archive) => archive.init()));
})();
