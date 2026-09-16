/** Syntax gate for the frontend.
 *
 * `next build` cannot run here (installing the frontend's node_modules is
 * blocked in this environment), so this parses every .ts/.tsx file under
 * frontend/ with the TypeScript parser and reports syntactic diagnostics.
 * That is not a typecheck — it will not catch a wrong prop type — but it does
 * catch unbalanced JSX, a stray brace, or a broken import statement, which is
 * the realistic failure mode of an edit made without a compiler.
 *
 * Usage: node --experimental-strip-types eval/check_frontend_syntax.ts
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// fileURLToPath, not .pathname: a workspace path containing spaces is
// percent-encoded in the URL and then cannot be found on disk.
const ROOT = fileURLToPath(new URL("../frontend", import.meta.url));

/** TypeScript is resolved from the frontend's own node_modules, which is where
 *  `npm ci` puts it. TYPESCRIPT_PATH overrides for an environment that keeps
 *  its toolchain elsewhere. */
const require_ = createRequire(join(ROOT, "package.json"));
let TS: any;
try {
  TS = require_(process.env.TYPESCRIPT_PATH ?? "typescript");
} catch {
  console.error(
    "typescript is not installed. Run `cd frontend && npm ci` first, " +
      "or point TYPESCRIPT_PATH at a typescript installation."
  );
  process.exit(2);
}
const SKIP = new Set(["node_modules", ".next", ".git", "dist", "out"]);

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    if (SKIP.has(entry)) continue;
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.tsx?$/.test(entry)) out.push(full);
  }
  return out;
}

const files = walk(ROOT).sort();
let problems = 0;

for (const file of files) {
  const source = readFileSync(file, "utf8");
  const kind = file.endsWith(".tsx") ? TS.ScriptKind.TSX : TS.ScriptKind.TS;
  const sf = TS.createSourceFile(file, source, TS.ScriptTarget.ES2022, true, kind);
  // `parseDiagnostics` is internal but is the only syntactic-only view: it
  // needs no type resolution and no emit, so it runs without node_modules.
  const fatal: any[] = (sf as any).parseDiagnostics ?? [];
  if (fatal.length) {
    problems += fatal.length;
    for (const d of fatal.slice(0, 3)) {
      const { line, character } = sf.getLineAndCharacterOfPosition(d.start ?? 0);
      console.error(`FAIL  ${relative(ROOT, file)}:${line + 1}:${character + 1}`);
      console.error(`        ${TS.flattenDiagnosticMessageText(d.messageText, " ")}`);
    }
  }
}

console.log(`${files.length} frontend file(s) parsed.`);
if (problems) {
  console.error(`${problems} syntax error(s).`);
  process.exit(1);
}
console.log("No syntax errors.");
