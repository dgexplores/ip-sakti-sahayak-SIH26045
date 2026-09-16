/** Parity check for the i18n layer.
 *
 * The language dictionaries are three hand-maintained objects. TypeScript
 * catches a *missing* key only while `npm run build` can run; a stray extra
 * key or a drifted glossary term list is invisible. This runs the module
 * directly with Node's type stripping and asserts the three languages carry
 * exactly the same keys, and that every glossary term has a definition in
 * every language.
 *
 * Usage: node --experimental-strip-types eval/check_i18n.ts
 */
import { LANGS, t, tri, glossary, GLOSSARY_TERMS } from "../frontend/lib/i18n.ts";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

let failures = 0;

function fail(msg: string) {
  console.error(`FAIL  ${msg}`);
  failures++;
}

function ok(msg: string) {
  console.log(`ok    ${msg}`);
}

const ids = LANGS.map((l) => l.id);

// 1. The three UI dictionaries must be key-for-key identical.
const base = Object.keys(t("en")).sort();
for (const id of ids) {
  const keys = Object.keys(t(id)).sort();
  const missing = base.filter((k) => !keys.includes(k));
  const extra = keys.filter((k) => !base.includes(k));
  if (missing.length) fail(`${id}: missing keys -> ${missing.join(", ")}`);
  if (extra.length) fail(`${id}: unexpected keys -> ${extra.join(", ")}`);
  if (!missing.length && !extra.length) ok(`${id}: ${keys.length} UI keys, identical to en`);
}

// 2. No empty strings, and no string left identical to English by accident
//    for a language that is supposed to be translated. (Legal terms are the
//    deliberate exception, and they are short.)
for (const id of ids) {
  const dict = t(id);
  for (const [k, v] of Object.entries(dict)) {
    if (!String(v).trim()) fail(`${id}.${k} is empty`);
  }
  if (id !== "en") {
    const same = base.filter((k) => dict[k as keyof typeof dict] === t("en")[k as keyof ReturnType<typeof t>]);
    if (same.length) fail(`${id}: untranslated (identical to en) -> ${same.join(", ")}`);
    else ok(`${id}: every UI string differs from English`);
  }
}

// 3. The triage flow is a separate dictionary with a nested category map.
const triBase = Object.keys(tri("en")).sort();
for (const id of ids) {
  const keys = Object.keys(tri(id)).sort();
  const missing = triBase.filter((k) => !keys.includes(k));
  if (missing.length) fail(`triage ${id}: missing -> ${missing.join(", ")}`);
  const catBase = Object.keys(tri("en").cat).sort();
  const catKeys = Object.keys(tri(id).cat).sort();
  const catMissing = catBase.filter((k) => !catKeys.includes(k));
  if (catMissing.length) fail(`triage ${id}.cat: missing -> ${catMissing.join(", ")}`);
  if (!missing.length && !catMissing.length) ok(`triage ${id}: ${keys.length} keys + ${catKeys.length} categories`);
}

// 4. Every glossary term the renderer can match must resolve in every language.
for (const id of ids) {
  const dict = glossary(id);
  const undef = GLOSSARY_TERMS.filter((term) => !dict[term]);
  if (undef.length) fail(`glossary ${id}: no definition for -> ${undef.join(", ")}`);
  else ok(`glossary ${id}: ${GLOSSARY_TERMS.length} terms all defined`);
}

// 5. The regex the renderer builds must actually match each term in a sentence.
const re = new RegExp(`(${GLOSSARY_TERMS.map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "g");
const sample = `Under ${GLOSSARY_TERMS.join(" and ")} the rules apply.`;
const hits = new Set(sample.match(re) ?? []);
for (const term of GLOSSARY_TERMS) {
  if (!hits.has(term)) fail(`glossary regex does not match "${term}" (shadowed by a shorter key?)`);
}
if (hits.size >= GLOSSARY_TERMS.length) ok(`glossary regex matches all ${GLOSSARY_TERMS.length} terms unshadowed`);

// 6. Both directions of usage. A typo'd `s.answerIndai` is a silently blank
//    label at runtime and a build error only where the compiler runs; a key
//    nothing reads is a string someone translated for no reason.
const uiKeys = new Set(base);
const triKeys = new Set(triBase);
const srcRoot = fileURLToPath(new URL("../frontend", import.meta.url));
const used = new Map<string, Set<string>>(); // "ui" | "tri" -> keys
used.set("ui", new Set());
used.set("tri", new Set());

const sources: string[] = [];
(function collect(dir: string) {
  for (const entry of readdirSync(dir)) {
    if (["node_modules", ".next", ".git"].includes(entry)) continue;
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) collect(full);
    else if (/\.tsx?$/.test(entry)) sources.push(full);
  }
})(srcRoot);

for (const file of sources) {
  if (file.endsWith("i18n.ts")) continue;
  const text = readFileSync(file, "utf8");
  // `s` is the UI dictionary and `x` the triage dictionary by convention.
  for (const m of text.matchAll(/\bs\.([A-Za-z_][A-Za-z0-9_]*)/g)) used.get("ui")!.add(m[1]);
  for (const m of text.matchAll(/\bx\.([A-Za-z_][A-Za-z0-9_]*)/g)) used.get("tri")!.add(m[1]);
  // And the inline form, `t(lang).someKey`, which the small client islands use
  // because they have no local `s` binding.
  for (const m of text.matchAll(/\bt\([^)]*\)\.([A-Za-z_][A-Za-z0-9_]*)/g)) used.get("ui")!.add(m[1]);
}

// `cat` is the one nested map, read as x.cat[c]; `step` is shared with the
// progress counter. Everything else must be a flat key.
const TRI_NESTED = new Set(["cat"]);
const unknownUi = [...used.get("ui")!].filter((k) => !uiKeys.has(k) && !["errorHint", "placeholder"].includes(k));
const unknownTri = [...used.get("tri")!].filter((k) => !triKeys.has(k) && !TRI_NESTED.has(k));
if (unknownUi.length) fail(`used but not defined in UI dict -> ${unknownUi.join(", ")}`);
if (unknownTri.length) fail(`used but not defined in triage dict -> ${unknownTri.join(", ")}`);
if (!unknownUi.length && !unknownTri.length) {
  ok(`usage: ${used.get("ui")!.size} UI + ${used.get("tri")!.size} triage keys referenced from components`);
}

// Report (do not fail) keys nothing references: the glossary bar and the error
// pages read them through the dict, and a few are deliberately reserved.
const referenced = new Set([...used.get("ui")!]);
const dead = base.filter((k) => !referenced.has(k));
if (dead.length) {
  console.log(`note  ${dead.length} UI key(s) not referenced by name: ${dead.join(", ")}`);
} else {
  ok("every UI key is referenced somewhere");
}

console.log("");
if (failures) {
  console.error(`${failures} i18n problem(s).`);
  process.exit(1);
}
console.log("i18n parity OK.");
