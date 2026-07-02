import { chromium } from "playwright";
import { pathToFileURL } from "url";

const [,, inputPath, outputPath] = process.argv;

if (!inputPath || !outputPath) {
  console.error("Usage: node scripts/screenshot.mjs <html-path> <output-png>");
  process.exit(1);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(pathToFileURL(inputPath).href, { waitUntil: "networkidle" });
await page.screenshot({ path: outputPath, fullPage: false });
await browser.close();