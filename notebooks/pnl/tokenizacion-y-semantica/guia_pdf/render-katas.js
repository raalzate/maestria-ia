// Render KATAS.html → KATAS.pdf con puppeteer + chrome headless.
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  const fileUrl = 'file://' + path.resolve(__dirname, 'KATAS.html');
  console.log('[render] loading', fileUrl);
  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60_000 });
  await page.evaluate(() => new Promise((resolve) => {
    if (typeof document.fonts !== 'undefined') document.fonts.ready.then(resolve);
    else setTimeout(resolve, 500);
  }));
  await new Promise((r) => setTimeout(r, 1000));
  await page.pdf({
    path: path.resolve(__dirname, '..', 'KATAS.pdf'),
    format: 'A4',
    printBackground: true,
    margin: { top: '22mm', bottom: '22mm', left: '20mm', right: '20mm' },
  });
  await browser.close();
  console.log('[render] done → KATAS.pdf');
})();
