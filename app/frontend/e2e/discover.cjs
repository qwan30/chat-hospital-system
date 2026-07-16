"use strict";
const { chromium } = require("@playwright/test");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  await page.goto("http://localhost:8082");
  await page.waitForTimeout(2000);

  const fields = await page.evaluate(() => {
    const els = [];
    document
      .querySelectorAll("input, select, textarea, button, [contenteditable], a")
      .forEach((el) => {
        if (el.offsetParent !== null) {
          els.push({
            tag: el.tagName,
            type: el.type || "",
            name: el.name || "",
            placeholder: el.placeholder || "",
            text: el.textContent?.trim().substring(0, 40) || "",
          });
        }
      });
    return els;
  });
  console.log("Dashboard Fields:", JSON.stringify(fields, null, 2));

  await browser.close();
})();
