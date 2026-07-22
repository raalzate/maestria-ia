// Render conceptos.html → conceptos-mobile.pdf con página angosta tipo móvil.
// Reusa conceptos.html pero inyecta style-mobile.css y desactiva style.css.

const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  const fileUrl = 'file://' + path.resolve(__dirname, 'conceptos.html');
  console.log('[render-mobile] loading', fileUrl);

  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60_000 });

  // Swap hoja desktop por hoja mobile sin tocar conceptos.html en disco.
  await page.evaluate(() => {
    document
      .querySelectorAll('link[rel="stylesheet"][href="style.css"]')
      .forEach((l) => l.parentNode.removeChild(l));
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'style-mobile.css';
    document.head.appendChild(link);
  });

  await page.evaluate(() => new Promise((resolve) => {
    if (typeof document.fonts !== 'undefined') {
      document.fonts.ready.then(resolve);
    } else {
      setTimeout(resolve, 500);
    }
  }));

  await new Promise((r) => setTimeout(r, 2000));

  const katexCount = await page.evaluate(() => document.querySelectorAll('.katex').length);
  console.log('[render-mobile] KaTeX spans:', katexCount);

  await page.pdf({
    path: path.resolve(__dirname, 'conceptos-mobile.pdf'),
    width: '100mm',
    height: '170mm',
    printBackground: true,
    margin: {
      top:    '14mm',
      bottom: '12mm',
      left:   '7mm',
      right:  '7mm',
    },
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="width:100%; font-family: 'Helvetica', sans-serif; font-size:6pt; color:#666; padding: 0 7mm; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:#0a2540; font-weight:600;">Tokenización · Semántica vectorial</span>
        <span style="color:#F06105;">PLN DL</span>
      </div>`,
    footerTemplate: `
      <div style="width:100%; font-family: 'Helvetica', sans-serif; font-size:6pt; color:#666; padding: 0 7mm; display:flex; justify-content:space-between; align-items:center;">
        <span>R. Alzate</span>
        <span><span class="pageNumber"></span>/<span class="totalPages"></span></span>
      </div>`,
  });

  await browser.close();
  console.log('[render-mobile] OK → conceptos-mobile.pdf');
})().catch((err) => { console.error(err); process.exit(1); });
