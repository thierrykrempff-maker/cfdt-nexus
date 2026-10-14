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
  ];
  const EMPTY = {
    reference: "",
    legifrance: "Aucun article du Code du travail retrouvé avec ces mots.",
    judilibre: "Aucune décision retrouvée avec ces mots.",
    convention: "Aucun passage de la convention collective retrouvé avec ces mots.",
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
    if (item.url && /^https:\/\/(www\.legifrance\.gouv\.fr|www\.courdecassation\.fr)\//.test(item.url)) {
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
        body: JSON.stringify({ query: text }),
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
  let dossierBusy = false;
  async function prepareDossier() {
    const question = (document.getElementById("resultQuestion") || {}).textContent || (document.getElementById("questionInput") || {}).value || "";
    const status = $("claudeDossierStatus");
    const area = $("claudeDossierText");
    if (!status || !area || dossierBusy) return;
    if (!question.trim()) {
      status.textContent = "Posez d’abord une question.";
      return;
    }
    dossierBusy = true;
    area.hidden = true;
    status.textContent = "Préparation du dossier (Légifrance, Judilibre, convention, accords, PV)…";
    try {
      const data = await api("/api/claude-dossier/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question }),
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
      status.textContent = `Dossier prêt : ${dossier.sources} sources numérotées. ` +
        (copied ? "Copié dans le presse-papiers : collez-le dans Claude." : "Sélectionné ci-dessous : copiez-le (Ctrl+C) puis collez-le dans Claude.");
    } catch (error) {
      status.textContent = "La préparation du dossier a échoué.";
    } finally {
      dossierBusy = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const button = $("claudeDossierButton");
    if (button) button.addEventListener("click", prepareDossier);
  });

  window.NexusOfficialSources = { showForQuestion };
})();
