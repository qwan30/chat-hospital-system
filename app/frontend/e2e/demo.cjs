"use strict";
const { chromium } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

const BASE_URL = process.env.QA_BASE_URL || "http://localhost:8082";
const VIDEO_DIR = path.join(__dirname, "screenshots");
const OUTPUT_NAME = "demo-HMS-Copilot.webm";
const REHEARSAL = process.argv.includes("--rehearse");

if (!fs.existsSync(VIDEO_DIR)) {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
}

// Helpers
async function injectCursor(page) {
  await page.evaluate(() => {
    if (document.getElementById("demo-cursor")) return;
    const cursor = document.createElement("div");
    cursor.id = "demo-cursor";
    cursor.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5 3L19 12L12 13L9 20L5 3Z" fill="white" stroke="black" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>`;
    cursor.style.cssText = `
      position: fixed; z-index: 999999; pointer-events: none;
      width: 24px; height: 24px;
      transition: left 0.1s, top 0.1s;
      filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.3));
    `;
    cursor.style.left = "0px";
    cursor.style.top = "0px";
    document.body.appendChild(cursor);
    document.addEventListener("mousemove", (e) => {
      cursor.style.left = e.clientX + "px";
      cursor.style.top = e.clientY + "px";
    });
  });
}

async function injectSubtitleBar(page) {
  await page.evaluate(() => {
    if (document.getElementById("demo-subtitle")) return;
    const bar = document.createElement("div");
    bar.id = "demo-subtitle";
    bar.style.cssText = `
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 999998;
      text-align: center; padding: 12px 24px;
      background: rgba(0, 0, 0, 0.75);
      color: white; font-family: -apple-system, "Segoe UI", sans-serif;
      font-size: 16px; font-weight: 500; letter-spacing: 0.3px;
      transition: opacity 0.3s;
      pointer-events: none;
    `;
    bar.textContent = "";
    bar.style.opacity = "0";
    document.body.appendChild(bar);
  });
}

async function showSubtitle(page, text) {
  await page.evaluate((t) => {
    const bar = document.getElementById("demo-subtitle");
    if (!bar) return;
    if (t) {
      bar.textContent = t;
      bar.style.opacity = "1";
    } else {
      bar.style.opacity = "0";
    }
  }, text);
  if (text) await page.waitForTimeout(800);
}

async function moveAndClick(page, locator, label, opts = {}) {
  const { postClickDelay = 800, ...clickOpts } = opts;
  const el = typeof locator === "string" ? page.locator(locator).first() : locator;
  const visible = await el.isVisible().catch(() => false);
  if (!visible) {
    console.error(`WARNING: moveAndClick skipped - "${label}" not visible`);
    return false;
  }
  try {
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await el.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
      await page.waitForTimeout(400);
    }
    await el.click(clickOpts);
  } catch (e) {
    console.error(`WARNING: moveAndClick failed on "${label}": ${e.message}`);
    return false;
  }
  await page.waitForTimeout(postClickDelay);
  return true;
}

async function typeSlowly(page, locator, text, label, charDelay = 35) {
  const el = typeof locator === "string" ? page.locator(locator).first() : locator;
  const visible = await el.isVisible().catch(() => false);
  if (!visible) {
    console.error(`WARNING: typeSlowly skipped - "${label}" not visible`);
    return false;
  }
  await moveAndClick(page, el, label);
  await el.fill("");
  await el.pressSequentially(text, { delay: charDelay });
  await page.waitForTimeout(500);
  return true;
}

(async () => {
  const browser = await chromium.launch({ headless: true });

  if (REHEARSAL) {
    console.log("Skipping rehearsal for brevity");
  }

  const context = await browser.newContext({
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } },
    viewport: { width: 1280, height: 720 },
  });
  const page = await context.newPage();

  try {
    // Inject auth to skip real login page manually clicking
    await page.addInitScript(() => {
      localStorage.setItem(
        "hms.session",
        JSON.stringify({ role: "cardiologist", workspaceId: "ws-cardio-4n" }),
      );
    });

    await page.goto(`${BASE_URL}/auth/login`);
    await injectCursor(page);
    await injectSubtitleBar(page);

    await showSubtitle(page, "Step 1 - Login");
    await moveAndClick(page, 'button:has-text("Demo Role")', "Demo Role");
    await moveAndClick(page, 'button:has-text("Sign in with Hospital SSO")', "Login SSO");

    await page.waitForURL("**/dashboard**", { timeout: 10000 });
    await injectCursor(page);
    await injectSubtitleBar(page);
    await showSubtitle(page, "Step 2 - Dashboard");
    await page.waitForTimeout(2000);

    await showSubtitle(page, "Step 3 - Patients");
    await moveAndClick(page, 'a[href="/patients"]', "Patients Nav");
    await page.waitForURL("**/patients**");
    await injectCursor(page);
    await injectSubtitleBar(page);

    await typeSlowly(
      page,
      'input[placeholder="Search by name, MRN..."]',
      "Eleanor",
      "Search Patient",
    );
    await page.waitForTimeout(1000);
    await moveAndClick(page, 'tr:has-text("Eleanor Vance")', "Eleanor Vance Row");

    await page.waitForURL("**/patients/**");
    await injectCursor(page);
    await injectSubtitleBar(page);
    await showSubtitle(page, "Step 4 - AI Summary");
    await page.waitForTimeout(2500);

    await showSubtitle(page, "Step 5 - Clinical Chat");
    await moveAndClick(page, 'a[href="/chat"]', "Chat Nav");
    await page.waitForURL("**/chat**");
    await injectCursor(page);
    await injectSubtitleBar(page);

    await typeSlowly(page, "textarea", "Anticoagulation protocol for AFib?", "Chat input", 40);
    await moveAndClick(page, 'button:has-text("Send")', "Send message");

    await showSubtitle(page, "Step 6 - AI Response");
    await page.waitForTimeout(5000);
    await showSubtitle(page, "");
  } catch (err) {
    console.error("DEMO ERROR:", err.message);
  } finally {
    await context.close();
    const video = page.video();
    if (video) {
      const src = await video.path();
      const dest = path.join(VIDEO_DIR, OUTPUT_NAME);
      try {
        fs.copyFileSync(src, dest);
        console.log("Video saved:", dest);
      } catch (e) {
        console.error("ERROR: Failed to copy video:", e.message);
      }
    }
    await browser.close();
  }
})();
