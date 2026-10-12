// Exercise the rendered cards with real mouse, keyboard and touch input.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.READING_BASE_URL || 'http://127.0.0.1:18062';
const out = process.env.READING_OUTPUT || '/tmp/fieldtofit-hot-cards-motion';
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.READING_CHROMIUM || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  let checks = 0;
  const screenshots = [], errors = [];
  const observe = page => page.on('pageerror', error => errors.push(error.message));
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    const page = await context.newPage();
    observe(page);
    const state = () => page.locator('.hot-card-preview').first().evaluate(element => {
      const foil = element.querySelector('.hot-card-foil'), style = getComputedStyle(foil);
      return { active: element.dataset.presenting, x: parseFloat(style.getPropertyValue('--card-x')), y: parseFloat(style.getPropertyValue('--card-y')), transform: style.transform, light: getComputedStyle(foil, '::after').opacity };
    });
    const reset = () => page.waitForFunction(() => !document.querySelector('.hot-card-preview').dataset.presenting && !document.querySelector('.hot-card-foil').style.getPropertyValue('--card-x'));
    for (const lang of ['zh', 'en']) for (const theme of ['light', 'dark']) {
      await page.goto(base + (lang === 'en' ? '/en' : '') + '/for-you#hot-information-cards');
      await page.locator('.hot-card-preview').last().waitFor();
      await page.evaluate(value => document.documentElement.dataset.theme = value, theme);
      await page.locator('.hot-card-preview').first().scrollIntoViewIfNeeded();
      await page.mouse.move(2, 2);
      await page.waitForFunction(() => Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('.hot-card-foil')).transform).m13) > .05);
      const resting = (await state()).transform;
      assert.ok(resting.startsWith('matrix3d')); checks++;
      const box = await page.locator('.hot-card-preview').first().boundingBox();
      await page.mouse.move(box.x + box.width * .2, box.y + box.height * .25);
      const front = () => page.waitForFunction(() => {
        const matrix = new DOMMatrix(getComputedStyle(document.querySelector('.hot-card-foil')).transform);
        return matrix.is2D && matrix.a > 1.03 && matrix.b === 0 && matrix.c === 0;
      });
      await front();
      let value = await state();
      assert.equal(value.active, 'true'); checks++;
      await page.waitForFunction(() => parseFloat(document.querySelector('.hot-card-foil').style.getPropertyValue('--card-x')) < 25);
      await page.mouse.move(box.x + box.width * .8, box.y + box.height * .7);
      await page.waitForFunction(() => parseFloat(document.querySelector('.hot-card-foil').style.getPropertyValue('--card-x')) > 75);
      await front(); value = await state();
      assert.ok(value.x > 75 && value.y > 60); checks++;
      await page.waitForFunction(() => Number(getComputedStyle(document.querySelector('.hot-card-foil'), '::after').opacity) > .99);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
      const name = `${lang}-${theme}-front.png`;
      await page.locator('.hot-card-section').screenshot({ path: out + '/' + name }); screenshots.push(name);
      await page.mouse.move(2, 2); await reset();
      await page.waitForFunction(rest => getComputedStyle(document.querySelector('.hot-card-foil')).transform === rest, resting); checks++;
      const response = await context.request.get(base + '/api/v1/platform/news?id=D-83' + (lang === 'en' ? '&lang=en' : ''));
      const item = (await response.json()).items[0];
      const first = page.locator('.hot-card-preview').first();
      assert.equal(await first.locator('.hot-card-art strong').innerText(), item.hot_card.changes[0].title);
      assert.equal(await first.locator('.hot-card-source').getAttribute('href'), item.sources.find(s => s.id === item.hot_card.evidence[0].source_id).url);
      assert.equal(await first.locator('.hot-card-source').getAttribute('target'), '_blank'); checks++;
      if (lang === 'en') { assert.ok(!/[\u3400-\u9fff]/.test(await page.locator('.hot-card-grid').innerText())); checks++; }
      await page.mouse.move(box.x + box.width * .8, box.y + box.height * .3);
      await page.emulateMedia({ reducedMotion: 'reduce' }); await reset();
      await page.mouse.move(box.x + box.width * .3, box.y + box.height * .7);
      value = await state(); assert.equal(value.transform, 'none'); assert.equal(value.active, undefined); checks++;
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.mouse.move(box.x + box.width * .6, box.y + box.height * .3);
      await first.locator('h4 a').focus(); await reset(); await front(); checks++;
      assert.ok(await first.locator('h4 a').evaluate(e => document.activeElement === e));
      await page.keyboard.press('Enter'); await page.locator('.hot-card-sheet').waitFor();
      assert.ok(page.url().includes('/news/D-83#hot-information-card')); checks++;
      await page.locator('.published-detail>p>a').click();
      await page.waitForFunction(() => document.activeElement?.id === 'hot-information-cards'); checks++;
    }
    // All three cards remain individually targetable in the owner's narrow desktop window.
    await page.setViewportSize({ width: 882, height: 1100 });
    await page.goto(base + '/for-you#hot-information-cards');
    await page.locator('.hot-card-preview').last().waitFor();
    assert.equal(await page.locator('.hot-card-grid').evaluate(e => getComputedStyle(e).gridTemplateColumns.split(' ').length), 3); checks++;
    for (let index = 0; index < 3; index++) {
      const card = page.locator('.hot-card-preview').nth(index);
      await card.scrollIntoViewIfNeeded();
      const box = await card.boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + 150);
      await page.waitForFunction(i => {
        const cards = [...document.querySelectorAll('.hot-card-preview')];
        const matrix = new DOMMatrix(getComputedStyle(cards[i].querySelector('.hot-card-foil')).transform);
        return cards[i].dataset.presenting === 'true' && matrix.is2D && matrix.a > 1.03;
      }, index);
      assert.equal(await page.locator('[data-presenting="true"]').count(), 1); checks++;
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    }
    await page.mouse.move(2, 2);
    await page.locator('.hot-card-section').screenshot({ path: out + '/three-resting.png' }); screenshots.push('three-resting.png');
    await page.setViewportSize({ width: 1024, height: 1100 });
    assert.equal(await page.locator('.hot-card-grid').evaluate(e => getComputedStyle(e).gridTemplateColumns.split(' ').length), 3); checks++;
    await page.locator('.reading-toc-toggle').click();
    await page.locator('#reading-toc-drawer[open]').waitFor();
    await page.locator('#reading-toc-drawer').getByRole('link', { name: '热点信息卡', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('#reading-toc-drawer').open && document.activeElement?.id === 'hot-information-cards'); checks++;
    for (const width of [1024, 768, 390, 320]) {
      const touch = await browser.newContext({ viewport: { width, height: 900 }, isMobile: true, hasTouch: true });
      const p = await touch.newPage(); observe(p);
      for (const lang of ['zh', 'en']) {
        await p.goto(base + (lang === 'en' ? '/en' : '') + '/for-you#hot-information-cards');
        await p.locator('.hot-card-preview').last().waitFor();
        await p.locator('.hot-card-preview').first().scrollIntoViewIfNeeded();
        const box = await p.locator('.hot-card-preview').first().boundingBox();
        await p.touchscreen.tap(box.x + box.width / 2, box.y + 100);
        assert.equal(await p.locator('[data-presenting="true"]').count(), 0);
        assert.equal(await p.locator('.hot-card-foil').first().evaluate(e => getComputedStyle(e).transform), 'none'); checks++;
        assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
        assert.ok(await p.locator('.hot-card-preview-footer a').evaluateAll(links => links.every(a => a.getBoundingClientRect().height >= 44))); checks++;
        const name = `${lang}-${width}-touch.png`;
        await p.locator('.hot-card-section').screenshot({ path: out + '/' + name }); screenshots.push(name);
        await p.locator('.hot-card-read').first().tap(); await p.locator('.hot-card-sheet').waitFor(); checks++;
      }
      await touch.close();
    }
    // Long reviewed copy and correction status must remain readable on a small screen.
    const raw = await (await context.request.get(base + '/api/v1/platform/news')).json();
    await page.route('**/api/v1/platform/news', route => {
      const data = structuredClone(raw), card = data.items.find(i => i.id === 'D-83').hot_card;
      card.headline = card.headline.repeat(4); card.scope = card.scope.repeat(3);
      card.status = 'needs_update'; card.update_note = '套餐条件待核对，暂停分享图下载。';
      return route.fulfill({ json: data });
    });
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto(base + '/for-you#hot-information-cards');
    await page.reload();
    await page.locator('.hot-card-preview-maintenance').waitFor();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    assert.equal(await page.locator('.hot-card-preview-footer').count(), 3); checks++;
    await page.locator('.hot-card-preview').first().screenshot({ path: out + '/long-copy-correction.png' }); screenshots.push('long-copy-correction.png');
    assert.deepEqual(errors, []);
    fs.writeFileSync(out + '/result.json', JSON.stringify({ passed: true, checks, screenshots, errors }, null, 2));
    console.log(`PASS ${checks} motion/accessibility checks; ${screenshots.length} screenshots`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
