// Print the datasheet HTML to an A4 PDF with Chromium (Playwright): running header, page numbers, outline.
// Usage: node print_pdf.mjs <in.html> <out.pdf> <print_config.json>
// The config gives the header/footer templates and the page margins (written by build_datasheet.py).
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
const require = createRequire(import.meta.url);
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const { chromium } = require(PW);
const [, , htmlPath, pdfPath, cfgPath] = process.argv;
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'load', timeout: 300000 });
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: pdfPath, format: 'A4', printBackground: true, displayHeaderFooter: true,
    headerTemplate: cfg.header, footerTemplate: cfg.footer, margin: cfg.margin,
    outline: true, tagged: true,
  });
  console.log('printed ' + pdfPath);
} finally {
  await browser.close();
}
