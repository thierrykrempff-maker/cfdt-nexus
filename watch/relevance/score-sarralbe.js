#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs/promises");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const RULES_FILE = path.join(__dirname, "sarralbe-rules.json");
const CONNECTOR_OUTPUT_DIR = path.join(ROOT, "local-index", "watch-connectors");
const RELEVANCE_OUTPUT_DIR = path.join(ROOT, "local-index", "watch-relevance");
const MAX_SCORE = 100;

const normalize = (value) =>
  value
    .toString()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const matchesKeyword = (normalizedText, keyword) => {
  const normalizedKeyword = normalize(keyword);
  if (normalizedKeyword.length <= 3 || /^[a-z0-9]+$/.test(normalizedKeyword)) {
    const pattern = new RegExp(`(^|[^a-z0-9])${escapeRegExp(normalizedKeyword)}([^a-z0-9]|$)`, "i");
    return pattern.test(normalizedText);
  }

  return normalizedText.includes(normalizedKeyword);
};

const unique = (values) => [...new Set(values.filter(Boolean))];

const findLatestConnectorOutput = async () => {
  const files = await fs.readdir(CONNECTOR_OUTPUT_DIR, { withFileTypes: true });
  const candidates = [];

  for (const file of files) {
    if (!file.isFile() || !file.name.endsWith(".private.json")) continue;
    const fullPath = path.join(CONNECTOR_OUTPUT_DIR, file.name);
    const stat = await fs.stat(fullPath);
    candidates.push({ fullPath, mtimeMs: stat.mtimeMs });
  }

  candidates.sort((a, b) => b.mtimeMs - a.mtimeMs);
  if (!candidates.length) {
    throw new Error(`Aucun fichier de veille privé trouvé dans ${path.relative(ROOT, CONNECTOR_OUTPUT_DIR)}`);
  }

  return candidates[0].fullPath;
};

const classifyScore = (score, classes) => {
  const match = classes.find((item) => score >= item.min && score <= item.max);
  return match || classes[0];
};

const detectContentNature = (text, rules) => {
  const normalized = normalize(text);
  const matches = [];

  for (const rule of rules) {
    if (rule.keywords.some((keyword) => normalized.includes(normalize(keyword)))) {
      matches.push({ label: rule.label, prudence: rule.prudence });
    }
  }

  return matches.length ? matches : [{ label: "actualité", prudence: "Information utile à qualifier avant toute action." }];
};

const scoreItem = (item, sourceResult, rules) => {
  const searchable = [item.title, item.url, item.published_at, sourceResult.source_name, sourceResult.source_id]
    .filter(Boolean)
    .join(" ");
  const itemSearchable = [item.title, item.url, item.published_at].filter(Boolean).join(" ");
  const normalized = normalize(searchable);
  const normalizedItem = normalize(itemSearchable);
  let score = 0;
  const reasons = [];
  const themes = [];
  const domains = [];
  const agents = [];
  const actions = [];

  for (const bonus of rules.source_bonuses) {
    if (bonus.source_id === sourceResult.source_id) {
      score += bonus.points;
      reasons.push(`${bonus.reason} : +${bonus.points}`);
      domains.push(...bonus.domains);
      agents.push(...bonus.agents);
    }
  }

  for (const theme of rules.themes) {
    const matchedKeywords = theme.keywords.filter((keyword) => matchesKeyword(normalizedItem, keyword));
    if (!matchedKeywords.length) continue;

    score += theme.points;
    themes.push(theme.label);
    domains.push(...theme.domains);
    agents.push(...theme.agents);
    actions.push(...theme.actions);
    reasons.push(`${theme.label} (${matchedKeywords.slice(0, 4).join(", ")}) : +${theme.points}`);
  }

  score = Math.min(score, MAX_SCORE);
  const classification = classifyScore(score, rules.classification);
  const suggestedActions = unique(actions.length ? actions : rules.fallback_actions[classification.label] || [classification.default_action]);
  const contentNature = detectContentNature(searchable, rules.content_type_rules);

  return {
    source: sourceResult.source_name,
    source_id: sourceResult.source_id,
    title: item.title,
    date: item.published_at || null,
    url: item.url,
    detected_themes: unique(themes),
    relevance_score: score,
    priority_level: classification.label,
    domains: unique(domains.length ? domains : ["Veille simple"]),
    agents: unique(agents.length ? agents : ["Veille Juridique et Sociale"]),
    suggested_actions: suggestedActions,
    action_status: rules.human_validation_label,
    content_nature: contentNature,
    ranking_reason: reasons.length ? reasons : ["aucun thème prioritaire Sarralbe détecté : +0"],
  };
};

const buildDistributions = (items, key) => {
  const distribution = {};
  for (const item of items) {
    const values = Array.isArray(item[key]) ? item[key] : [item[key]];
    for (const value of values.filter(Boolean)) {
      distribution[value] = (distribution[value] || 0) + 1;
    }
  }
  return Object.fromEntries(Object.entries(distribution).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));
};

const run = async () => {
  const rules = JSON.parse(await fs.readFile(RULES_FILE, "utf8"));
  const inputPath = process.argv[2] ? path.resolve(process.argv[2]) : await findLatestConnectorOutput();
  const connectorOutput = JSON.parse(await fs.readFile(inputPath, "utf8"));
  const scoredItems = [];

  for (const sourceResult of connectorOutput.results || []) {
    for (const item of sourceResult.items || []) {
      scoredItems.push(scoreItem(item, sourceResult, rules));
    }
  }

  scoredItems.sort((a, b) => b.relevance_score - a.relevance_score || a.title.localeCompare(b.title));

  const priorityCounts = rules.classification.reduce((acc, item) => {
    acc[item.label] = 0;
    return acc;
  }, {});

  for (const item of scoredItems) {
    priorityCounts[item.priority_level] = (priorityCounts[item.priority_level] || 0) + 1;
  }

  const report = {
    generated_at: new Date().toISOString(),
    input_file: path.relative(ROOT, inputPath),
    rules_version: rules.version,
    analyzed_count: scoredItems.length,
    priority_counts: priorityCounts,
    theme_distribution: buildDistributions(scoredItems, "detected_themes"),
    domain_distribution: buildDistributions(scoredItems, "domains"),
    action_distribution: buildDistributions(scoredItems, "suggested_actions"),
    top_5: scoredItems.slice(0, 5),
    items: scoredItems,
    warning: "Rapport local privé. Ne pas committer.",
  };

  await fs.mkdir(RELEVANCE_OUTPUT_DIR, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const outputPath = path.join(RELEVANCE_OUTPUT_DIR, `sarralbe-relevance-${stamp}.private.json`);
  await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");

  console.log(`Informations analysées : ${report.analyzed_count}`);
  for (const [label, count] of Object.entries(report.priority_counts)) {
    console.log(`- ${label}: ${count}`);
  }
  console.log("Top 5 :");
  for (const item of report.top_5) {
    console.log(`- [${item.relevance_score}/100] ${item.source} — ${item.title}`);
    console.log(`  Raisons: ${item.ranking_reason.join(" | ")}`);
    console.log(`  Action: ${item.suggested_actions[0]} (${item.action_status})`);
  }
  console.log(`Rapport local : ${path.relative(ROOT, outputPath)}`);
};

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
