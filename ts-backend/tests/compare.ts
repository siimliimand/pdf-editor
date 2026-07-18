import * as fs from "node:fs";
import * as path from "node:path";

// ---------------------------------------------------------------------------
// HTML token types
// ---------------------------------------------------------------------------

interface HtmlTag {
  type: "tag";
  name: string;
  attributes: Record<string, string>;
  selfClosing: boolean;
  children: HtmlNode[];
}

interface HtmlText {
  type: "text";
  content: string;
}

type HtmlNode = HtmlTag | HtmlText;

// ---------------------------------------------------------------------------
// Parsing
// ---------------------------------------------------------------------------

function parseHtml(html: string): HtmlNode[] {
  const nodes: HtmlNode[] = [];
  const stack: HtmlTag[] = [];
  let cursor = 0;

  const tagRe = /<([^>]+)>/g;
  let match: RegExpExecArray | null;

  while ((match = tagRe.exec(html)) !== null) {
    const before = html.slice(cursor, match.index);
    if (before.trim()) {
      const textNode: HtmlText = { type: "text", content: before };
      if (stack.length > 0) {
        stack[stack.length - 1].children.push(textNode);
      } else {
        nodes.push(textNode);
      }
    }

    const raw = match[1];
    const isClosing = raw.startsWith("/");
    const isSelfClosing = raw.endsWith("/") || isVoidElement(raw.split(/\s/)[0].replace(/^\//, ""));

    if (isClosing) {
      const tagName = raw.replace(/^\//, "").trim().toLowerCase();
      if (stack.length > 0 && stack[stack.length - 1].name === tagName) {
        stack.pop();
      }
      cursor = match.index + match[0].length;
      continue;
    }

    const tagName = raw.split(/\s/)[0].toLowerCase();
    const attrs = parseAttributes(raw.slice(tagName.length));
    const tag: HtmlTag = {
      type: "tag",
      name: tagName,
      attributes: attrs,
      selfClosing: isSelfClosing,
      children: [],
    };

    if (stack.length > 0) {
      stack[stack.length - 1].children.push(tag);
    } else {
      nodes.push(tag);
    }

    if (!isSelfClosing) {
      stack.push(tag);
    }

    cursor = match.index + match[0].length;
  }

  const trailing = html.slice(cursor);
  if (trailing.trim()) {
    if (stack.length > 0) {
      stack[stack.length - 1].children.push({ type: "text", content: trailing });
    } else {
      nodes.push({ type: "text", content: trailing });
    }
  }

  return nodes;
}

function parseAttributes(raw: string): Record<string, string> {
  const attrs: Record<string, string> = {};
  const attrRe = /([a-zA-Z\-]+)(?:="([^"]*)")?/g;
  let m: RegExpExecArray | null;
  while ((m = attrRe.exec(raw)) !== null) {
    if (m[1] === "/") continue;
    attrs[m[1]] = m[2] ?? "";
  }
  return attrs;
}

function isVoidElement(tag: string): boolean {
  const voids = new Set([
    "area","base","br","col","embed","hr","img","input",
    "link","meta","param","source","track","wbr",
  ]);
  return voids.has(tag);
}

// ---------------------------------------------------------------------------
// Diff types
// ---------------------------------------------------------------------------

interface Diff {
  category: "structural" | "content" | "style" | "position";
  severity: "error" | "warning" | "info";
  message: string;
  path?: string;
}

// ---------------------------------------------------------------------------
// Comparison engine
// ---------------------------------------------------------------------------

function serializeStyle(attrs: Record<string, string>): Record<string, string> {
  const style: Record<string, string> = {};
  const raw = attrs["style"] ?? "";
  for (const decl of raw.split(";")) {
    const [prop, ...rest] = decl.split(":");
    if (prop && rest.length) {
      style[prop.trim()] = rest.join(":").trim();
    }
  }
  return style;
}

function compareNodes(
  a: HtmlNode[],
  b: HtmlNode[],
  path: string,
  diffs: Diff[],
): void {
  // Structural: different number of children
  if (a.length !== b.length) {
    diffs.push({
      category: "structural",
      severity: "warning",
      path,
      message: `Child count differs: ${a.length} vs ${b.length}`,
    });
  }

  const len = Math.min(a.length, b.length);
  for (let i = 0; i < len; i++) {
    const nodeA = a[i];
    const nodeB = b[i];
    const childPath = `${path}>[${i}]`;

    if (nodeA.type !== nodeB.type) {
      diffs.push({
        category: "structural",
        severity: "error",
        path: childPath,
        message: `Node type mismatch: ${nodeA.type} vs ${nodeB.type}`,
      });
      continue;
    }

    if (nodeA.type === "text" && nodeB.type === "text") {
      const textA = nodeA.content.trim();
      const textB = nodeB.content.trim();
      if (textA !== textB) {
        diffs.push({
          category: "content",
          severity: "error",
          path: childPath,
          message: `Text differs: "${truncate(textA, 80)}" vs "${truncate(textB, 80)}"`,
        });
      }
      continue;
    }

    if (nodeA.type === "tag" && nodeB.type === "tag") {
      // Tag name
      if (nodeA.name !== nodeB.name) {
        diffs.push({
          category: "structural",
          severity: "error",
          path: childPath,
          message: `Tag name differs: <${nodeA.name}> vs <${nodeB.name}>`,
        });
      }

      // Attributes
      compareAttributes(nodeA.attributes, nodeB.attributes, childPath, diffs);

      // Recurse
      compareNodes(nodeA.children, nodeB.children, childPath, diffs);
    }
  }
}

function compareAttributes(
  a: Record<string, string>,
  b: Record<string, string>,
  path: string,
  diffs: Diff[],
): void {
  const allKeys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const key of allKeys) {
    if (key === "style") {
      compareStyles(a, b, path, diffs);
      continue;
    }

    // Position attributes (absolute/relative coordinates)
    if (isPositionAttr(key)) {
      if (a[key] !== b[key]) {
        diffs.push({
          category: "position",
          severity: "warning",
          path,
          message: `Position attr "${key}" differs: ${a[key] ?? "(absent)"} vs ${b[key] ?? "(absent)"}`,
        });
      }
      continue;
    }

    if (!(key in a)) {
      diffs.push({
        category: "structural",
        severity: "info",
        path,
        message: `Attribute "${key}" missing in Python output`,
      });
    } else if (!(key in b)) {
      diffs.push({
        category: "structural",
        severity: "info",
        path,
        message: `Attribute "${key}" missing in TypeScript output`,
      });
    } else if (a[key] !== b[key]) {
      diffs.push({
        category: "structural",
        severity: "warning",
        path,
        message: `Attribute "${key}" differs: ${truncate(a[key], 60)} vs ${truncate(b[key], 60)}`,
      });
    }
  }
}

function isPositionAttr(name: string): boolean {
  const posAttrs = new Set([
    "left", "right", "top", "bottom",
    "x", "y", "width", "height",
    "data-x", "data-y", "data-width", "data-height",
    "transform", "margin-left", "margin-top",
  ]);
  return posAttrs.has(name.toLowerCase());
}

function compareStyles(
  a: Record<string, string>,
  b: Record<string, string>,
  path: string,
  diffs: Diff[],
): void {
  const styleA = serializeStyle(a);
  const styleB = serializeStyle(b);
  const allProps = new Set([...Object.keys(styleA), ...Object.keys(styleB)]);

  for (const prop of allProps) {
    if (isPositionStyleProp(prop)) {
      if (styleA[prop] !== styleB[prop]) {
        diffs.push({
          category: "position",
          severity: "warning",
          path,
          message: `Style "${prop}" differs: ${styleA[prop] ?? "(absent)"} vs ${styleB[prop] ?? "(absent)"}`,
        });
      }
      continue;
    }

    if (!(prop in styleA)) {
      diffs.push({
        category: "style",
        severity: "info",
        path,
        message: `Style property "${prop}" missing in Python output`,
      });
    } else if (!(prop in styleB)) {
      diffs.push({
        category: "style",
        severity: "info",
        path,
        message: `Style property "${prop}" missing in TypeScript output`,
      });
    } else if (styleA[prop] !== styleB[prop]) {
      diffs.push({
        category: "style",
        severity: "warning",
        path,
        message: `Style "${prop}" differs: ${styleA[prop]} vs ${styleB[prop]}`,
      });
    }
  }
}

function isPositionStyleProp(prop: string): boolean {
  const pos = new Set([
    "left", "right", "top", "bottom",
    "position", "transform", "margin", "margin-left", "margin-top",
    "margin-right", "margin-bottom",
  ]);
  return pos.has(prop.toLowerCase());
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max) + "…" : s;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface ComparisonResult {
  identical: boolean;
  diffs: Diff[];
  summary: {
    total: number;
    structural: number;
    content: number;
    style: number;
    position: number;
    errors: number;
    warnings: number;
  };
}

/**
 * Compare two HTML strings and return a structured diff report.
 */
export function compareHtmlFiles(pyHtml: string, tsHtml: string): ComparisonResult {
  const pyNormalized = normalizeForCompare(pyHtml);
  const tsNormalized = normalizeForCompare(tsHtml);

  if (pyNormalized === tsNormalized) {
    return {
      identical: true,
      diffs: [],
      summary: { total: 0, structural: 0, content: 0, style: 0, position: 0, errors: 0, warnings: 0 },
    };
  }

  const pyNodes = parseHtml(pyHtml);
  const tsNodes = parseHtml(tsHtml);
  const diffs: Diff[] = [];

  compareNodes(pyNodes, tsNodes, "root", diffs);

  const summary = {
    total: diffs.length,
    structural: diffs.filter((d) => d.category === "structural").length,
    content: diffs.filter((d) => d.category === "content").length,
    style: diffs.filter((d) => d.category === "style").length,
    position: diffs.filter((d) => d.category === "position").length,
    errors: diffs.filter((d) => d.severity === "error").length,
    warnings: diffs.filter((d) => d.severity === "warning").length,
  };

  return { identical: false, diffs, summary };
}

function normalizeForCompare(html: string): string {
  return html
    .replace(/\s+/g, " ")
    .replace(/>\s+</g, "><")
    .trim()
    .toLowerCase();
}

/**
 * Format a ComparisonResult into a human-readable report.
 */
export function formatReport(result: ComparisonResult, labelA = "Python", labelB = "TypeScript"): string {
  const lines: string[] = [];

  if (result.identical) {
    lines.push("✓ Outputs are identical (after normalization)");
    return lines.join("\n");
  }

  lines.push(`Comparison: ${labelA} vs ${labelB}`);
  lines.push("─".repeat(60));
  lines.push(
    `Total diffs: ${result.summary.total}  ` +
    `(${result.summary.errors} errors, ${result.summary.warnings} warnings)`,
  );
  lines.push(
    `By category: structural=${result.summary.structural}  ` +
    `content=${result.summary.content}  ` +
    `style=${result.summary.style}  ` +
    `position=${result.summary.position}`,
  );
  lines.push("");

  const groups = groupByCategory(result.diffs);
  for (const [category, diffs] of Object.entries(groups)) {
    lines.push(`── ${category.toUpperCase()} ──`);
    for (const d of diffs) {
      const icon = d.severity === "error" ? "✗" : d.severity === "warning" ? "⚠" : "·";
      const path = d.path ? ` [${d.path}]` : "";
      lines.push(`  ${icon}${path} ${d.message}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

function groupByCategory(diffs: Diff[]): Record<string, Diff[]> {
  const groups: Record<string, Diff[]> = {};
  for (const d of diffs) {
    (groups[d.category] ??= []).push(d);
  }
  return groups;
}

// ---------------------------------------------------------------------------
// Directory comparison (CLI entry point)
// ---------------------------------------------------------------------------

interface FilePair {
  name: string;
  pathA: string;
  pathB: string;
}

function findMatchingFiles(dirA: string, dirB: string): FilePair[] {
  const filesA = listHtmlFiles(dirA);
  const filesB = new Set(listHtmlFiles(dirB).map((f) => path.basename(f)));

  const pairs: FilePair[] = [];
  for (const f of filesA) {
    const base = path.basename(f);
    if (filesB.has(base)) {
      pairs.push({
        name: base,
        pathA: path.join(dirA, f),
        pathB: path.join(dirB, base),
      });
    }
  }

  return pairs.sort((a, b) => a.name.localeCompare(b.name));
}

function listHtmlFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => /\.html?$/i.test(f));
}

function runDirectoryComparison(dirA: string, dirB: string): string {
  const pairs = findMatchingFiles(dirA, dirB);
  const results: string[] = [];

  if (pairs.length === 0) {
    return `No matching HTML files found between:\n  ${dirA}\n  ${dirB}`;
  }

  let identicalCount = 0;
  let diffCount = 0;

  for (const pair of pairs) {
    const htmlA = fs.readFileSync(pair.pathA, "utf-8");
    const htmlB = fs.readFileSync(pair.pathB, "utf-8");
    const result = compareHtmlFiles(htmlA, htmlB);

    results.push(`\n${"═".repeat(60)}`);
    results.push(`FILE: ${pair.name}`);
    results.push(`${"═".repeat(60)}`);

    if (result.identical) {
      identicalCount++;
      results.push("  ✓ Identical");
    } else {
      diffCount++;
      results.push(formatReport(result));
    }
  }

  const summary = [
    `\n${"═".repeat(60)}`,
    "SUMMARY",
    `${"═".repeat(60)}`,
    `Files compared: ${pairs.length}`,
    `Identical: ${identicalCount}`,
    `Different: ${diffCount}`,
  ];

  return [...results, ...summary].join("\n");
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function main(): void {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: npx tsx tests/compare.ts <dir1> <dir2>");
    console.error("  Compares HTML files in <dir1> (Python output) vs <dir2> (TypeScript output)");
    process.exit(1);
  }

  const [dirA, dirB] = args.map((d) => path.resolve(d));

  if (!fs.existsSync(dirA)) {
    console.error(`Directory not found: ${dirA}`);
    process.exit(1);
  }
  if (!fs.existsSync(dirB)) {
    console.error(`Directory not found: ${dirB}`);
    process.exit(1);
  }

  const report = runDirectoryComparison(dirA, dirB);
  console.log(report);
}

main();
