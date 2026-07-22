// Render guia.html → guia.pdf using puppeteer + chrome headless.
// Espera a que KaTeX termine de renderizar antes de imprimir.

const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  const fileUrl = 'file://' + path.resolve(__dirname, 'guia.html');
  console.log('[render] loading', fileUrl);

  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60_000 });

  // Espera a que KaTeX inyecte sus spans (.katex). Si no hay math, sigue.
  await page.evaluate(() => new Promise((resolve) => {
    if (typeof document.fonts !== 'undefined') {
      document.fonts.ready.then(resolve);
    } else {
      setTimeout(resolve, 500);
    }
  }));

  // Pequeño delay extra para que KaTeX scripts terminen de procesar
  await new Promise((r) => setTimeout(r, 2000));

  // Confirma que KaTeX corrió
  const katexCount = await page.evaluate(() => document.querySelectorAll('.katex').length);
  console.log('[render] KaTeX spans:', katexCount);

  await page.pdf({
    path: path.resolve(__dirname, 'guia.pdf'),
    format: 'A4',
    printBackground: true,
    margin: {
      top:    '24mm',
      bottom: '22mm',
      left:   '20mm',
      right:  '20mm',
    },
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="width:100%; font-family: 'Helvetica', sans-serif; font-size:8pt; color:#666; padding: 0 20mm; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:#0a2540; font-weight:600;">Tokenización y semántica vectorial en PLN</span>
        <span style="color:#F06105;">PLN con Deep Learning</span>
      </div>`,
    footerTemplate: `
      <div style="width:100%; font-family: 'Helvetica', sans-serif; font-size:8pt; color:#666; padding: 0 20mm; display:flex; justify-content:space-between; align-items:center;">
        <span>Raúl Andrés Alzate Gómez · Maestría en Ingeniería de Sistemas y Computación</span>
        <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
      </div>`,
  });

  await browser.close();
  console.log('[render] OK → guia.pdf');
})().catch((err) => { console.error(err); process.exit(1); });
