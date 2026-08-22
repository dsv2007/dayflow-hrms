const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
      headless: "new"
  });
  const page = await browser.newPage();
  
  // Set viewport to exactly 1920x1080 to match our design
  await page.setViewport({ width: 1920, height: 1080 });
  
  // Load the HTML file
  await page.goto(`file://${__dirname}/diagram_scan2fab.html`, { waitUntil: 'networkidle0' });
  
  // Give Lucide a moment to render SVG icons completely
  await new Promise(r => setTimeout(r, 1000));
  
  // Print to PDF with landscape 1920x1080 exact dimensions
  await page.pdf({
    path: 'Scan2FabAI_FrontierArchitecture.pdf',
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }
  });

  await browser.close();
})();
