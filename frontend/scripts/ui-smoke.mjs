import { existsSync, readFileSync } from "node:fs";

const requiredFiles = [
  "components/ui.tsx",
  "app/globals.css",
  "components/AnalyticsDashboardView.tsx",
  "app/page.tsx",
];

for (const file of requiredFiles) {
  if (!existsSync(file)) {
    throw new Error(`Missing required frontend file: ${file}`);
  }
}

const css = readFileSync("app/globals.css", "utf8");
for (const className of [".app-card", ".data-table", ".field-error", ".status-pill"]) {
  if (!css.includes(className)) {
    throw new Error(`Missing shared class ${className}`);
  }
}

const dashboard = readFileSync("components/AnalyticsDashboardView.tsx", "utf8");
for (const symbol of ["MetricTile", "Panel", "sortConfig", "pageIndex"]) {
  if (!dashboard.includes(symbol)) {
    throw new Error(`Dashboard smoke check missing ${symbol}`);
  }
}

const home = readFileSync("app/page.tsx", "utf8");
const layout = readFileSync("app/layout.tsx", "utf8");
if (!home.includes("LegalSight") || !layout.includes("LegalSight")) {
  throw new Error("LegalSight branding is missing from the frontend shell");
}

console.log("UI smoke checks passed");
