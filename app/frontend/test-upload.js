const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));

  console.log('Navigating to http://localhost:3000/login');
  await page.goto('http://localhost:3000/login');
  
  await context.clearCookies();
  await page.evaluate(() => localStorage.clear());
  
  console.log('Clicking SSO login...');
  await page.click('text=Sign in with Hospital SSO');
  
  // Wait for the redirect to dashboard
  await page.waitForURL('**/dashboard');
  console.log('Currently at:', page.url());

  // Click the 'Documents' link in the sidebar
  console.log('Clicking Documents link in sidebar');
  await page.click('a[href="/documents"]');
  await page.waitForURL('**/documents');
  
  console.log('Clicking Upload Documents button');
  await page.click('text=Upload');
  await page.waitForURL('**/documents/upload');

  console.log('Currently at:', page.url());

  const fileInput = await page.locator('input[type=file]');
  await fileInput.setInputFiles('D:/download/Jake_s_Resume (11).pdf');
  
  console.log('Clicking Start Upload');
  await page.click('text=Start Upload');
  
  // Wait for 100% or Error
  try {
      await page.waitForSelector('text=100%', { timeout: 10000 });
      console.log('Upload reached 100%');
  } catch (e) {
      console.log('Upload did not reach 100% in time.');
  }
  
  await page.screenshot({ path: 'upload_test_result.png' });
  console.log('Screenshot saved to upload_test_result.png');
  
  await browser.close();
})().catch(console.error);
