const navItems = document.querySelectorAll("[data-target]");
const views = document.querySelectorAll(".view");
const sidebar = document.querySelector(".sidebar");
const menuToggle = document.querySelector(".menu-toggle");
const caseForm = document.querySelector("#case-form");
const caseList = document.querySelector("#case-list");
const caseCount = document.querySelector("#case-count");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatLog = document.querySelector("#chat-log");
const demoPromptButtons = document.querySelectorAll("[data-demo-prompt]");

// Données de démonstration. À terme, ce tableau pourra venir de n8n,
// d'une base documentaire, de GitHub ou d'un backend sécurisé.
const demoCases = [
  {
    title: "Entretien préalable - salarié A",
    category: "Discipline",
    status: "En cours",
  },
  {
    title: "Question prime panier",
    category: "Paie",
    status: "À traiter",
  },
  {
    title: "Signalement chaleur atelier",
    category: "Santé / Sécurité",
    status: "En cours",
  },
];

const showView = (targetId) => {
  views.forEach((view) => {
    view.classList.toggle("view--active", view.id === targetId);
  });

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("nav-item--active", item.dataset.target === targetId);
  });

  if (sidebar?.classList.contains("sidebar--open")) {
    sidebar.classList.remove("sidebar--open");
    menuToggle?.setAttribute("aria-expanded", "false");
  }
};

const renderCases = () => {
  if (!caseList || !caseCount) return;

  caseList.innerHTML = demoCases
    .map(
      (item) => `
        <article class="case-card">
          <strong>${item.title}</strong>
          <div class="case-card__meta">
            <span>${item.category}</span>
            <span>${item.status}</span>
          </div>
        </article>
      `
    )
    .join("");

  caseCount.textContent = `${demoCases.length} dossier${demoCases.length > 1 ? "s" : ""}`;
};

const addMessage = (content, type = "assistant") => {
  if (!chatLog) return;

  const message = document.createElement("div");
  message.className = `message message--${type}`;
  message.textContent = content;
  chatLog.appendChild(message);
  chatLog.scrollTop = chatLog.scrollHeight;
};

const simulateAssistantResponse = (message) => {
  const normalized = message.toLowerCase();

  if (normalized.includes("codex") || normalized.includes("site")) {
    return "Réponse simulée : je préparerais un prompt Codex clair avec objectif, fichiers concernés, contraintes, vérifications et message de commit.";
  }

  if (normalized.includes("article") || normalized.includes("tract") || normalized.includes("flash")) {
    return "Réponse simulée : je proposerais une structure CFDT courte : contexte, ce qu'il faut comprendre, position CFDT, points utiles aux salariés et prochaine action.";
  }

  return "Réponse simulée : je commencerais par distinguer faits, preuves, textes, accords, analyse et stratégie, puis je proposerais 3 à 5 questions utiles avant d'aller plus loin.";
};

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const target = item.dataset.target;
    if (target) showView(target);
  });
});

menuToggle?.addEventListener("click", () => {
  const isOpen = !sidebar?.classList.contains("sidebar--open");
  sidebar?.classList.toggle("sidebar--open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
});

caseForm?.addEventListener("submit", (event) => {
  event.preventDefault();

  const formData = new FormData(caseForm);
  demoCases.unshift({
    title: formData.get("caseTitle").toString().trim(),
    category: formData.get("caseCategory").toString(),
    status: formData.get("caseStatus").toString(),
  });

  caseForm.reset();
  renderCases();
});

chatForm?.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = chatInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  chatInput.value = "";

  // Simulation V1 : aucune donnée n'est envoyée à un service externe.
  setTimeout(() => addMessage(simulateAssistantResponse(message)), 250);
});

demoPromptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (!chatInput) return;

    chatInput.value = button.dataset.demoPrompt;
    chatInput.focus();
  });
});

renderCases();
