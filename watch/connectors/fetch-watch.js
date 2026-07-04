#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs/promises");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const STATUS_FILE = path.join(__dirname, "sources-status.json");
const DEFAULT_OUTPUT_DIR = path.join(ROOT, "local-index", "watch-connectors");
const USER_AGENT = "CFDT-Nexus-Watch/1.0 (local, no aggressive scraping)";
const REQUEST_TIMEOUT_MS = 12000;
const MAX_ITEMS_PER_SOURCE = 8;

const decodeHtml = (value) =>
  value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");

const cleanText = (value) =>
  decodeHtml(
    value
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim()
  );

const parseDateFromText = (value) => {
  const text = cleanText(value);
  const numeric = text.match(/\b(\d{2})\/(\d{2})\/(\d{4})\b/);
  if (numeric) return `${numeric[3]}-${numeric[2]}-${numeric[1]}`;

  const months = {
    janvier: "01",
    fevrier: "02",
    février: "02",
    mars: "03",
    avril: "04",
    mai: "05",
    juin: "06",
    juillet: "07",
    aout: "08",
    août: "08",
    septembre: "09",
    octobre: "10",
    novembre: "11",
    decembre: "12",
    décembre: "12",
  };
  const long = text.toLowerCase().match(/\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})\b/);
  if (!long) return null;

  return `${long[3]}-${months[long[2]]}-${long[1].padStart(2, "0")}`;
};

const removeLeadingDate = (value) => cleanText(value).replace(/^\d{2}\/\d{2}\/\d{4}\s+/, "").trim();

const toAbsoluteUrl = (href, baseUrl) => {
  try {
    return new URL(href, baseUrl).toString();
  } catch {
    return null;
  }
};

const uniqueBy = (items, keyFn) => {
  const seen = new Set();
  const result = [];

  for (const item of items) {
    const key = keyFn(item);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.push(item);
  }

  return result;
};

const isLikelyNavigation = (title, url) => {
  const normalizedTitle = title.toLowerCase();
  const normalizedUrl = url.toLowerCase();
  const blockedTitlePatterns = [
    /^recherche rapide$/,
    /^navigation principale$/,
    /^aller au contenu$/,
    /^pied de page$/,
    /^santé et sécurité au travail$/,
    /^sante et securite au travail$/,
    /^poser une question$/,
    /^risques professionnels$/,
    /^métiers et secteurs d'activité$/,
    /^metiers et secteurs d'activite$/,
    /^nous connaître$/,
    /^nous connaitre$/,
    /^découvrir france chimie$/,
    /^decouvrir france chimie$/,
    /^pourquoi adhérer/,
    /^pourquoi adherer/,
    /^base documentaire/,
    /^la chimie en france$/,
    /^l(&#039;|'|’)industrie de la chimie$/,
    /^environnement & rse$/,
    /^emploi & recrutement$/,
  ];

  if (blockedTitlePatterns.some((pattern) => pattern.test(normalizedTitle))) return true;
  if (normalizedUrl.startsWith("javascript:")) return true;
  if (normalizedUrl.includes("#")) return true;
  if (normalizedUrl.includes(".quicksearch_")) return true;
  return false;
};

const fetchText = async (url) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/rss+xml,application/atom+xml;q=0.9,*/*;q=0.8",
      },
      signal: controller.signal,
    });

    const body = await response.text();
    return {
      ok: response.ok,
      status: response.status,
      contentType: response.headers.get("content-type") || "",
      body,
    };
  } finally {
    clearTimeout(timeout);
  }
};

const extractRssItems = (xml, baseUrl) => {
  const itemMatches = [...xml.matchAll(/<(item|entry)\b[\s\S]*?<\/\1>/gi)];

  return itemMatches
    .map((match) => {
      const item = match[0];
      const title = cleanText((item.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || "");
      const rawLink =
        (item.match(/<link[^>]*href=["']([^"']+)["'][^>]*>/i) || [])[1] ||
        cleanText((item.match(/<link[^>]*>([\s\S]*?)<\/link>/i) || [])[1] || "");
      const publishedAt = cleanText(
        (item.match(/<(pubDate|published|updated)[^>]*>([\s\S]*?)<\/\1>/i) || [])[2] || ""
      );

      return {
        title,
        url: toAbsoluteUrl(rawLink, baseUrl),
        published_at: publishedAt || null,
        extraction_type: "rss",
      };
    })
    .filter((item) => item.title && item.url);
};

const extractPageItems = (html, baseUrl, sourceId) => {
  if (sourceId === "cnil") {
    const cnilItems = [];
    const cnilPattern = /<h3[^>]*>\s*<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>\s*<\/h3>([\s\S]*?)(?=<h3|$)/gi;

    for (const match of html.matchAll(cnilPattern)) {
      const title = cleanText(match[2]);
      const url = toAbsoluteUrl(match[1], baseUrl);
      if (!url || title.length < 12 || title.length > 220) continue;
      cnilItems.push({
        title,
        url,
        published_at: parseDateFromText(match[3]),
        extraction_type: "page-card",
      });
    }

    if (cnilItems.length) return uniqueBy(cnilItems, (item) => `${item.title}|${item.url}`).slice(0, MAX_ITEMS_PER_SOURCE);
  }

  const candidates = [];
  const linkPattern = /<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;

  for (const match of html.matchAll(linkPattern)) {
    const href = match[1];
    const title = cleanText(match[2]);
    const url = toAbsoluteUrl(href, baseUrl);

    if (!url || !title) continue;
    if (title.length < 12 || title.length > 180) continue;
    if (/^(en savoir plus|voir la carte|accueil|suivant|précédent|linkedin|facebook|instagram|youtube|twitter)$/i.test(title)) continue;
    if (isLikelyNavigation(title, url)) continue;

    candidates.push({
      title: removeLeadingDate(title),
      url,
      published_at: parseDateFromText(title),
      extraction_type: "page-link",
    });
  }

  if (sourceId === "france-chimie") {
    const headingPattern = /<(h2|h3|h4)\b[^>]*>([\s\S]*?)<\/\1>/gi;
    for (const match of html.matchAll(headingPattern)) {
      const title = cleanText(match[2]);
      if (title.length < 12 || title.length > 180) continue;
      candidates.push({
        title,
        url: baseUrl,
        published_at: null,
        extraction_type: "page-heading",
      });
    }
  }

  return uniqueBy(candidates, (item) => `${item.title}|${item.url}`).slice(0, MAX_ITEMS_PER_SOURCE);
};

const run = async () => {
  const status = JSON.parse(await fs.readFile(STATUS_FILE, "utf8"));
  const enabledSources = status.sources.filter((source) => source.enabled && source.status === "actif");
  const startedAt = new Date().toISOString();
  const results = [];

  for (const source of enabledSources) {
    const sourceResult = {
      source_id: source.id,
      source_name: source.name,
      watch_url: source.watch_url,
      access_type: source.access_type,
      fetched_at: new Date().toISOString(),
      ok: false,
      status_code: null,
      items: [],
      error: null,
      limits: source.known_limits,
      possible_business_uses: source.business_uses,
    };

    try {
      const response = await fetchText(source.watch_url);
      sourceResult.status_code = response.status;

      if (!response.ok) {
        sourceResult.error = `HTTP ${response.status}`;
      } else if (/rss|atom|xml/i.test(response.contentType)) {
        sourceResult.items = extractRssItems(response.body, source.watch_url);
        sourceResult.ok = true;
      } else {
        sourceResult.items = extractPageItems(response.body, source.watch_url, source.id);
        sourceResult.ok = true;
      }
    } catch (error) {
      sourceResult.error = error.name === "AbortError" ? "Timeout réseau" : error.message;
    }

    results.push(sourceResult);
  }

  const output = {
    generated_at: new Date().toISOString(),
    mission: "Connecteurs veille V1",
    started_at: startedAt,
    source_count: enabledSources.length,
    warning: "Sortie locale temporaire. Ne pas committer.",
    results,
  };

  await fs.mkdir(DEFAULT_OUTPUT_DIR, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const outputPath = path.join(DEFAULT_OUTPUT_DIR, `watch-demo-${stamp}.private.json`);
  await fs.writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, "utf8");

  console.log(`Sources testées : ${enabledSources.length}`);
  for (const result of results) {
    console.log(`- ${result.source_name}: ${result.ok ? "OK" : "ERREUR"} (${result.items.length} titre(s))`);
    if (result.error) console.log(`  Limite: ${result.error}`);
  }
  console.log(`Sortie locale : ${path.relative(ROOT, outputPath)}`);
};

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
