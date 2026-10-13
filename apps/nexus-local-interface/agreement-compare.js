// Comparer un ancien accord avec un nouvel accord, un avenant ou un projet, et vérifier les interférences.
// Les textes viennent de l'archive locale des accords ou d'un fichier importé (jamais conservé).
// Les extraits restent à l'écran : ils ne font partie d'aucun rapport, copie, impression ni téléchargement.
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const MAX_FILE_BYTES = 5 * 1024 * 1024;
  const state = { documents: [], filters: { cmpOld: "", cmpNew: "" } };

  const TYPE_LABELS = { modifie: "Modifié", ajoute: "Ajouté", supprime: "Supprimé" };

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  async function api(path, options) {
    const response = await fetch(path, { cache: "no-store", ...options });
    if (!response.ok) throw new Error("http " + response.status);
    return response.json();
  }

  function fold(value) {
    return String(value || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function optionLabel(document_) {
    return `${document_.date || "date inconnue"} — ${document_.titre} (${document_.type})`;
  }

  function fillSelect(prefix) {
    const select = $(prefix + "Select");
    const previous = select.value;
    const needle = fold(state.filters[prefix]);
    select.textContent = "";
    state.documents
      .filter((item) => !needle || fold(optionLabel(item)).includes(needle))
      .forEach((item) => {
        const option = el("option", "", optionLabel(item));
        option.value = item.id;
        select.append(option);
      });
    if (previous && [...select.options].some((option) => option.value === previous)) select.value = previous;
  }

  // --- panneau ---------------------------------------------------------------------------------
  async function loadList() {
    const status = $("cmpStatus");
    try {
      const data = await api("/api/agreements/list");
      state.documents = data.documents || [];
      fillSelect("cmpOld");
      fillSelect("cmpNew");
      if (data.status === "READY") {
        status.textContent = `${state.documents.length} accords dans l’archive. Choisissez ou importez les deux textes.`;
      } else {
        status.textContent = data.notice || "L’archive des accords n’est pas disponible.";
      }
    } catch (error) {
      status.textContent = "Impossible de lire l’archive des accords. Nexus est-il toujours lancé ?";
    }
  }

  function closeOtherPanels() {
    ["pvArchivePanel", "accordsArchivePanel"].forEach((id) => { if ($(id)) $(id).hidden = true; });
    ["pvSearchButton", "accordsSearchButton"].forEach((id) => { if ($(id)) $(id).setAttribute("aria-expanded", "false"); });
  }

  async function openPanel() {
    closeOtherPanels();
    $("agreementComparePanel").hidden = false;
    $("compareSearchButton").setAttribute("aria-expanded", "true");
    await loadList();
    $("cmpOldFilter").focus();
  }

  function closePanel() {
    $("agreementComparePanel").hidden = true;
    $("compareSearchButton").setAttribute("aria-expanded", "false");
  }

  function readFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
      reader.onerror = () => reject(new Error("Lecture du fichier impossible."));
      reader.readAsDataURL(file);
    });
  }

  async function side(prefix, label) {
    const file = $(prefix + "File").files[0];
    if (file) {
      if (file.size > MAX_FILE_BYTES) throw new Error(`${label} : le fichier dépasse 5 Mo.`);
      return {
        attachment: { name: file.name, mime_type: file.type || "application/octet-stream", content_base64: await readFile(file) },
      };
    }
    const id = $(prefix + "Select").value;
    if (!id) throw new Error(`${label} : choisissez un accord de l’archive ou importez un fichier.`);
    return { id };
  }

  async function submit(event) {
    event.preventDefault();
    const results = $("cmpResults");
    const status = $("cmpStatus");
    results.textContent = "";
    let payload;
    try {
      payload = { old: await side("cmpOld", "Ancien accord"), new: await side("cmpNew", "Nouvel accord") };
    } catch (error) {
      results.append(el("p", "pv-archive-message", error.message));
      return;
    }
    $("cmpRun").disabled = true;
    status.textContent = "Comparaison en cours…";
    try {
      const data = await api("/api/agreements/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      render(results, data.comparison || { status: "INVALID", message: "Réponse inattendue." });
      status.textContent = "";
    } catch (error) {
      results.append(el("p", "pv-archive-message", "La comparaison a échoué. Nexus est-il toujours lancé ?"));
      status.textContent = "";
    } finally {
      $("cmpRun").disabled = false;
    }
  }

  // --- affichage des résultats --------------------------------------------------------------------
  function heading(container, text) {
    container.append(el("h3", "cmp-heading", text));
  }

  function list(items) {
    const ul = el("ul", "cmp-list");
    items.forEach((text) => ul.append(el("li", "", text)));
    return ul;
  }

  function sentences(title, items) {
    const column = el("div", "cmp-column");
    column.append(el("strong", "", title));
    column.append(items.length ? list(items) : el("p", "cmp-empty", "—"));
    return column;
  }

  function changeNode(change, index) {
    const details = el("details", "cmp-change cmp-change--" + change.type);
    details.open = index < 6;
    const summary = el("summary");
    summary.append(el("span", "cmp-badge cmp-badge--" + change.type, TYPE_LABELS[change.type] || change.type));
    summary.append(el("strong", "", change.article));
    if (change.titre) summary.append(el("span", "", ` — ${change.titre}`));
    (change.valeurs || []).forEach((value) => summary.append(el("span", "cmp-figure", value)));
    details.append(summary);
    const columns = el("div", "cmp-columns");
    columns.append(sentences("Avant", change.avant || []), sentences("Après", change.apres || []));
    details.append(columns);
    if (change.termes_d_obligation && change.termes_d_obligation.length) {
      details.append(el("p", "cmp-detail", `Termes d’obligation : ${change.termes_d_obligation.join(" ; ")}`));
    }
    if (change.autres_phrases_modifiees) {
      details.append(el("p", "cmp-detail", `${change.autres_phrases_modifiees} autre(s) phrase(s) modifiée(s) non affichée(s).`));
    }
    return details;
  }

  function archiveCard(row) {
    const builder = window.NexusPvArchive && window.NexusPvArchive.card;
    const node = builder ? builder(row) : el("section", "cse-previous-minute", row.excerpt || "");
    (row.valeurs_differentes || []).forEach((text) => node.append(el("p", "cmp-warning", `⚠ Valeurs différentes — ${text}`)));
    return node;
  }

  function cards(rows) {
    const grid = el("div", "cse-previous-minutes");
    rows.forEach((row) => grid.append(archiveCard(row)));
    return grid;
  }

  function render(container, c) {
    container.textContent = "";
    if (c.status !== "READY") {
      const messages = {
        DISABLED: "La comparaison d’accords n’est pas activée sur ce poste (option NEXUS_ACCORDS_ARCHIVE_ENABLED).",
        UNAVAILABLE: "Le service d’archive est arrêté ou l’index des accords est absent. Lancez le service « Précédents ».",
      };
      container.append(el("p", "pv-archive-message", c.message || messages[c.status] || "Comparaison impossible."));
      return;
    }
    const r = c.resume;
    const head = el("div", "cmp-summary");
    head.append(el("h3", "cmp-heading", `${c.ancien.titre}  →  ${c.nouveau.titre}`));
    head.append(el("p", "cmp-detail",
      c.mode === "avenant"
        ? "Le nouveau texte est traité comme un avenant : seuls les articles qu’il reprend sont comparés."
        : "Le nouveau texte est traité comme un remplacement de l’ancien : tous les articles sont comparés."));
    const chips = el("p", "cmp-chips");
    [["modifies", "modifié(s)"], ["ajoutes", "ajouté(s)"], ["supprimes", "supprimé(s)"], ["inchanges", "inchangé(s)"]].forEach(([key, label]) => {
      chips.append(el("span", "cmp-chip", `${r[key]} ${label}`));
    });
    if (c.mode === "avenant") chips.append(el("span", "cmp-chip", `${r.non_vises_par_l_avenant} non visé(s)`));
    head.append(chips);
    container.append(head);

    heading(container, "Points d’attention");
    container.append(list(c.points_attention || []));

    heading(container, `Modifications article par article (${c.modifications.length}${c.modifications_non_affichees ? ` affichées, ${c.modifications_non_affichees} de plus` : ""})`);
    if (!c.modifications.length) container.append(el("p", "cmp-empty", "Aucune différence détectée."));
    c.modifications.forEach((change, index) => container.append(changeNode(change, index)));

    heading(container, "Autres accords concernés (interférences possibles)");
    if (c.interferences_status === "UNAVAILABLE") {
      container.append(el("p", "pv-archive-message", "Contrôle impossible : le service d’archive est arrêté."));
    } else if (!c.interferences.length) {
      container.append(el("p", "cmp-empty", "Aucun autre accord de l’archive ne traite des mêmes sujets (selon les mots-clés retenus)."));
    }
    (c.interferences || []).forEach((item) => {
      const block = el("div", "cmp-topic");
      block.append(el("h4", "", `${item.sujet} (${item.article})`), el("p", "cmp-detail", `Mots retenus : ${item.mots.join(", ")}`), cards(item.textes));
      container.append(block);
    });

    heading(container, "Textes cités ou visés par le nouvel accord");
    if (!c.citations.length) container.append(el("p", "cmp-empty", "Aucune référence datée à un autre texte."));
    else {
      const ul = el("ul", "cmp-list");
      c.citations.forEach((citation) => {
        const li = el("li");
        li.append(el("strong", "", `${citation.date} — ${citation.nature} — ${citation.effet}`));
        li.append(el("span", citation.dans_l_archive ? "cmp-ok" : "cmp-warning-inline",
          citation.dans_l_archive ? ` · retrouvé dans l’archive : ${citation.documents.join(" ; ")}` : " · non retrouvé dans l’archive"));
        li.append(el("p", "cmp-detail", `« ${citation.phrase} »`));
        ul.append(li);
      });
      container.append(ul);
    }

    heading(container, "Ce qui a été dit en réunion (PV du CE/CSE)");
    if (!c.reunions.length) container.append(el("p", "cmp-empty", "Aucun passage retrouvé (ou archive des PV non activée)."));
    else container.append(cards(c.reunions));

    const limits = el("div", "cmp-limits");
    (c.limites || []).forEach((text) => limits.append(el("p", "source-context-notice", text)));
    container.append(limits);
  }

  function init() {
    const panel = $("agreementComparePanel");
    if (!panel) return;
    $("compareSearchButton").addEventListener("click", () => (panel.hidden ? openPanel() : closePanel()));
    $("agreementCompareClose").addEventListener("click", closePanel);
    $("agreementCompareForm").addEventListener("submit", submit);
    ["cmpOld", "cmpNew"].forEach((prefix) => {
      $(prefix + "Filter").addEventListener("input", (event) => {
        state.filters[prefix] = event.target.value;
        fillSelect(prefix);
      });
    });
    const negotiationButton = $("negotiationCompareButton");
    if (negotiationButton) {
      negotiationButton.addEventListener("click", async () => {
        await openPanel();
        panel.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  // L'espace « Négociations et accords » affiche le bouton de comparaison (appelé par openWorkspace).
  function onWorkspace(workspace) {
    const block = $("negotiationCompareWorkflow");
    if (block) block.hidden = workspace !== "negotiation";
  }

  window.NexusAgreementCompare = { onWorkspace };
  document.addEventListener("DOMContentLoaded", init);
})();
