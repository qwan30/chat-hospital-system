const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('http://localhost:3000/login');
  await context.clearCookies();
  await page.evaluate(() => localStorage.clear());
  
  await page.click('text=Sign in with Hospital SSO');
  await page.waitForURL('**/dashboard');
  await page.click('a[href="/documents"]');
  await page.waitForURL('**/documents');
  await page.click('text=Upload');
  await page.waitForURL('**/documents/upload');

  const fileInput = await page.locator('input[type=file]');
  await fileInput.setInputFiles('D:/download/Jake_s_Resume (11).pdf');
  await page.click('text=Start Upload');
  
  // Wait for 'done' badge
  await page.waitForSelector('text=done', { timeout: 15000 });
  console.log('Upload done! Navigating to document view...');
  
  // Find the check circle link and click it
  await page.locator('a[href^="/documents/"]').first().click();
  
  // Wait for the document view page to load
  await page.waitForSelector('.lucide-image', { state: 'visible', timeout: 5000 }).catch(() => {});
  
  // Wait another 2 seconds for images to finish loading
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: 'doc_viewer_result.png', fullPage: true });
  console.log('Screenshot saved to doc_viewer_result.png');
  
  await browser.close();
})().catch(console.error);
