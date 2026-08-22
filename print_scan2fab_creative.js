const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
      headless: "new"
  });
  const page = await browser.newPage();
  
  // Set viewport to exactly 1920x1080 to match our design
  await page.setViewport({ width: 1920, height: 1080 });
  
  // Load the HTML file
  await page.goto(`file://${__dirname}/diagram_scan2fab_creative.html`, { waitUntil: 'networkidle0' });
  
  // Give Lucide and background animations a moment to render completely
  await new Promise(r => setTimeout(r, 1000));
  
  // Print to PDF with landscape 1920x1080 exact dimensions
  await page.pdf({
    path: 'Scan2FabAI_CreativeLightArchitecture.pdf',
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }
  });

  await browser.close();
})();
