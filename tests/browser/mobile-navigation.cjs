const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({headless: true, executablePath: process.env.READING_CHROMIUM});
  const base = process.env.READING_BASE_URL || 'http://127.0.0.1:18046';
  const out = process.env.READING_OUTPUT || '/tmp/fieldtofit-mobile-navigation';
  fs.mkdirSync(out, {recursive: true});
  try {
    const context = await browser.newContext({viewport: {width: 390, height: 844}});
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    if (process.env.READING_API_URL) await page.route('**/api/**', async route => {
      const url = new URL(route.request().url());
      if (!url.pathname.startsWith('/api/')) return route.continue();
      const response = await context.request.fetch(process.env.READING_API_URL + url.pathname + url.search, {method: route.request().method(), headers: route.request().headers(), data: route.request().postData() || undefined});
      await route.fulfill({response});
    });
    const dialog = page.locator('#mobile-more-dialog');
    const more = page.locator('.mobile-navigation > .mobile-bottom-nav button');
    const open = async () => { await more.click(); await dialog.waitFor({state: 'visible'}); };
    const closed = async () => { await dialog.waitFor({state: 'hidden'}); assert.notEqual(await page.evaluate(() => getComputedStyle(document.body).overflow), 'hidden'); };
    await page.goto(base + '/for-you'); await more.waitFor();
    assert.equal(await page.locator('.mobile-navigation > nav > *').count(), 3);
    await open();
    assert.deepEqual(await dialog.locator('.mobile-more-panel nav a').evaluateAll(nodes => nodes.map(n => n.getAttribute('href'))), ['/about', '/community', '/sources', '/admin']);
    assert.equal(await page.evaluate(() => getComputedStyle(document.body).overflow), 'hidden');
    for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); assert(await page.evaluate(() => !!document.activeElement.closest('#mobile-more-dialog'))); }
    await page.keyboard.press('Escape'); await closed(); assert(await more.evaluate(n => n === document.activeElement));
    for (const path of ['/about', '/community', '/sources', '/admin']) {
      await open(); await dialog.locator(`.mobile-more-panel a[href="${path}"]`).click(); await page.waitForURL(base + path); await closed();
      await page.waitForFunction(() => document.activeElement?.id === 'main-content');
      assert.equal(await more.getAttribute('aria-current'), 'location');
      await open(); assert.equal(await dialog.locator(`.mobile-more-panel a[href="${path}"]`).getAttribute('aria-current'), 'page');
      await dialog.getByRole('button', {name: '关闭更多导航'}).click(); await closed();
    }
    await page.locator('.management-login').waitFor();
    if (process.env.READING_ADMIN_PASSWORD) {
      assert.equal((await context.request.get((process.env.READING_API_URL || base) + '/api/v1/admin/workspace/operations')).status(), 401);
      await page.locator('.management-login input').fill(process.env.READING_ADMIN_PASSWORD);
      await page.locator('.management-login button[type="submit"], .management-login button').last().click();
      await page.locator('.management-nav').waitFor();
      await open(); await dialog.locator('.mobile-more-panel a[href="/about"]').click();
      await open(); await dialog.locator('.mobile-more-panel a[href="/admin"]').click();
      await page.locator('.management-nav').waitFor();
    }
    await page.goBack(); await closed(); await page.goForward(); await closed(); await page.reload();
    assert.equal(await more.getAttribute('aria-current'), 'location');
    await open(); await dialog.locator('.mobile-bottom-nav button').click(); await closed();
    await open(); await page.mouse.click(5, 5); await closed();
    await open(); await dialog.locator('.mobile-bottom-nav a[href="/for-you"]').click(); await closed();
    assert.equal(await more.getAttribute('aria-current'), null);
    const toc = page.locator('#reading-toc-drawer');
    await page.locator('.reading-toc-toggle').click(); await toc.waitFor({state: 'visible'});
    assert.equal(await page.evaluate(() => getComputedStyle(document.body).overflow), 'hidden');
    await page.keyboard.press('Escape'); await toc.waitFor({state: 'hidden'});
    await open();
    // Exercise the shared coordination path even though modal backgrounds block pointer clicks.
    await page.evaluate(() => document.querySelector('.reading-toc-toggle').click());
    await toc.waitFor({state: 'visible'}); await dialog.waitFor({state: 'hidden'});
    await page.evaluate(() => document.querySelector('.mobile-navigation > nav button').click());
    await dialog.waitFor({state: 'visible'}); await toc.waitFor({state: 'hidden'});
    assert.equal(await page.locator('dialog[open]').count(), 1);
    await page.keyboard.press('Escape'); await closed();
    for (const [width, height] of [[320, 568], [390, 844], [430, 932], [667, 375]]) {
      await page.setViewportSize({width, height}); await open();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const panel = await dialog.locator('.mobile-more-panel').boundingBox(), bar = await dialog.locator('.mobile-bottom-nav').boundingBox();
      assert(panel.y >= 0 && panel.y + panel.height <= bar.y + 1 && bar.y + bar.height <= height + 1);
      await dialog.locator('.mobile-more-panel a').last().scrollIntoViewIfNeeded();
      await page.screenshot({path: out + `/more-${width}.png`});
      await page.keyboard.press('Escape'); await closed();
    }
    await page.setViewportSize({width: 390, height: 844});
    await page.locator('.language-button').click(); await page.locator('.topbar button[aria-label="Dark theme"]').click();
    await open(); assert.match(await dialog.innerText(), /FieldToFit Community/);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: out + '/more-english-dark.png'});
    await page.setViewportSize({width: 1440, height: 1000}); await closed();
    assert(await page.locator('.sidebar').isVisible()); assert(!(await page.locator('.mobile-navigation').isVisible()));
    assert.deepEqual(errors, []);
    fs.writeFileSync(out + '/result.json', JSON.stringify({passed: true, base, isolatedApi: process.env.READING_API_URL || null, authenticatedNavigation: !!process.env.READING_ADMIN_PASSWORD, widths: [320,390,430,667,1440], errors}, null, 2));
    console.log('PASS ' + out + '/result.json');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
