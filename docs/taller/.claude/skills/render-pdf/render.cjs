/**
 * render-pdf — Render HTML to A4 PDF using Puppeteer.
 *
 * Usage:
 *   node .claude/skills/render-pdf/render.cjs [input.html] [output.pdf]
 *
 * Defaults (when run from project root with no args):
 *   input:  deliverables/taller_resuelto.html
 *   output: deliverables/Act_7_Taller_Investigacion_Usuarios_Resuelto.pdf
 */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const DEFAULT_IN = path.join(PROJECT_ROOT, 'deliverables', 'taller_resuelto.html');
const DEFAULT_OUT = path.join(PROJECT_ROOT, 'deliverables', 'Act_7_Taller_Investigacion_Usuarios_Resuelto.pdf');

const argIn = process.argv[2];
const argOut = process.argv[3];
const inputHtml = path.resolve(argIn || DEFAULT_IN);
const outputPdf = path.resolve(argOut || DEFAULT_OUT);

if (!fs.existsSync(inputHtml)) {
  console.error(`✗ HTML not found: ${inputHtml}`);
  process.exit(1);
}

(async () => {
  const fileUrl = 'file://' + inputHtml;
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: outputPdf,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: false,
  });
  await browser.close();
  console.log(`✓ PDF generated: ${outputPdf}`);
})();
