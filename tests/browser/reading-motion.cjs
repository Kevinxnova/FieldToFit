// Run after the production build. All requests, including APIs, stay in this fixture.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const dist = path.resolve(__dirname, '../../frontend/dist');
const history = require('../../backend/seo/changelog.json');
const origin = 'http://fieldtofit.test';
const records = Array.from({length: 5}, (_, n) => ({
  id: 'demo-' + n, title: 'Resource ' + n, kind: 'resource', object_type: 'tool',
  topics: [], metadata: {}, facts: {}, evidence: [], verifications: [], history: [], relations: [],
  canonical_url: 'https://example.com/', source_id: 'test', summary: 'Test resource',
}));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

function lookup(label) {
  const hit = {
    id: 'demo', name: label, introduction: 'Fixture', types: [], scope: 'news', web_url: '/about',
    match_reasons: [], sources: [], snippets: [], materials: [], coverage: {}, bundle_ref: {id: 'demo'},
  };
  return {items: [hit], total: 1, offset: 0, coverage: {}, has_more: false};
}

async function intercept(page) {
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/api/changelog') {
      const language = url.searchParams.get('lang') || 'zh';
      const items = history.items.map(entry => ({...entry, ...entry.copy[language], status: 'unverified'}));
      return route.fulfill({json: {...history, items, language}});
    }
    if (url.pathname === '/api/v1/records') return route.fulfill({json: {items: records, total: 5, next_offset: null}});
    if (url.pathname.startsWith('/api/v1/records/')) return route.fulfill({json: records[4]});
    if (url.pathname === '/api/v1/platform/lookup') return route.fulfill({json: lookup('original')});
    if (url.pathname.startsWith('/api/')) return route.fulfill({status: 404, json: {}});
    if (route.request().isNavigationRequest()) return route.fulfill({path: path.join(dist, 'index.html')});
    return route.fulfill({path: path.join(dist, url.pathname)});
  });
}

async function disclosure(page) {
  const toggle = page.locator('.changelog-disclosure').first();
  const notes = page.locator('.changelog-notes').first();
  await toggle.press('Enter');
  await page.waitForFunction(() => document.querySelector('.changelog-notes').getBoundingClientRect().height > 0);
  await toggle.press('Space');
  assert.equal(await notes.getAttribute('inert'), '');
  await page.waitForFunction(() => document.querySelector('.changelog-notes').getBoundingClientRect().height === 0);
  assert(await toggle.evaluate(el => document.activeElement === el));
}

async function more(page) {
  const trigger = page.locator('.mobile-navigation > nav button');
  const modal = page.locator('#mobile-more-dialog');
  const toggle = modal.locator('.mobile-bottom-nav button');
  await trigger.click();
  await modal.waitFor();
  await toggle.press('Enter');
  await toggle.press('Enter');
  await page.waitForTimeout(210);
  assert(await modal.evaluate(el => el.open && !!el.dataset.presented));
  await page.keyboard.press('Escape');
  await modal.waitFor({state: 'hidden'});
  assert(await trigger.evaluate(el => el === document.activeElement));
  await trigger.click();
  await modal.click({position: {x: 2, y: 2}});
  await modal.waitFor({state: 'hidden'});
  await trigger.click();
  await page.evaluate(() => window.dispatchEvent(new Event('fieldtofit:open-contents')));
  await modal.waitFor({state: 'hidden'});
  const viewport = page.viewportSize();
  await trigger.click();
  await page.setViewportSize({...viewport, width: 768});
  await page.waitForFunction(() => !document.querySelector('#mobile-more-dialog').open);
  await page.setViewportSize(viewport);
  await page.emulateMedia({reducedMotion: 'reduce'});
  await trigger.click();
  assert.equal(await modal.locator('section').evaluate(el => el.getAnimations().length), 0);
  await page.keyboard.press('Escape');
  await modal.waitFor({state: 'hidden'});
  await page.emulateMedia({reducedMotion: 'no-preference'});
  await trigger.click();
  await modal.locator('nav a[href$="/about"]').first().click();
  await page.waitForFunction(() => location.pathname.endsWith('/about') && document.activeElement.id === 'main-content');
}

async function search(page, lang) {
  await page.goto(origin + lang + '/for-your-ai?lookup=fixture');
  const area = page.locator('#ai-lookup');
  const scope = area.locator('.lookup-filters select').first();
  const hit = area.locator('.lookup-result h3');
  await hit.waitFor();
  let failure = 503;
  await page.route('**/api/v1/platform/lookup?**', async route => {
    const scope = new URL(route.request().url()).searchParams.get('scope');
    const status = scope === 'news' ? failure : 200;
    await wait(scope === 'watch' ? 20 : 220);
    await route.fulfill({status, json: status === 200 ? lookup(scope) : {detail: 'Fixture failure'}}).catch(() => {});
  });
  await scope.selectOption('news');
  assert.equal(await hit.innerText(), 'original');
  await area.getByRole('alert').waitFor();
  assert.match(await area.locator('.lookup-summary small').innerText(), /fixture/);
  await scope.selectOption('all');
  await scope.selectOption('watch');
  await page.waitForFunction(() => document.querySelector('.lookup-result h3')?.textContent === 'watch');
  await page.waitForTimeout(250);
  assert.equal(await hit.innerText(), 'watch');
  await scope.selectOption('news');
  await area.getByRole('alert').waitFor();
  failure = 200;
  await area.getByRole('button', {name: lang ? 'Retry' : '重试', exact: true}).click();
  await page.waitForFunction(() => document.querySelector('.lookup-result h3')?.textContent === 'news');
  assert(await area.locator('h2').evaluate(el => document.activeElement === el));
  await area.getByRole('button', {name: lang ? 'Add to package' : '加入资料包', exact: true}).click();
  await scope.selectOption('all');
  failure = 403;
  await scope.selectOption('news');
  await area.getByRole('alert').waitFor();
  assert.equal(await hit.count(), 0);
  assert.equal(await area.locator('.lookup-selected').count(), 0);
}

// Exercise state that crosses requests: paging, selected packages and read access.
async function lookupBoundaries(page) {
  let mode = 'ready';
  await page.route('**/api/v1/platform/lookup?**', async route => {
    const url = new URL(route.request().url());
    if (mode === 'denied' || mode === 'invalid') {
      return route.fulfill({status: mode === 'denied' ? 403 : 422, json: {detail: 'Fixture error'}});
    }
    const data = lookup(url.searchParams.has('lookup_cursor') || url.searchParams.has('cursor') ? 'next page' : 'first page');
    data.has_more = data.items[0].name === 'first page';
    data.next_cursor = data.has_more ? 'next' : null;
    data.previous_cursor = data.has_more ? null : 'previous';
    data.offset = data.has_more ? 0 : 10;
    if (mode === 'withdrawn') data.items = [{id: 'demo', unavailable: true}];
    if (mode === 'empty') { data.items = []; data.total = 0; data.has_more = false; }
    return route.fulfill({json: data});
  });
  await page.goto(origin + '/for-your-ai?lookup=boundary');
  const area = page.locator('#ai-lookup');
  const scope = area.locator('.lookup-filters select').first();
  await area.getByRole('button', {name: '下一页', exact: true}).click();
  await area.getByRole('heading', {name: 'next page'}).waitFor();
  await area.getByRole('button', {name: '加入资料包', exact: true}).click();
  mode = 'invalid';
  await scope.selectOption('news');
  await area.getByRole('alert').waitFor();
  assert.equal(await area.locator('.lookup-selected').count(), 1);
  mode = 'withdrawn';
  await area.getByRole('button', {name: '重试', exact: true}).click();
  await area.getByText(/此项已撤下/).waitFor();
  assert.equal(await area.locator('.lookup-selected').count(), 0);
  mode = 'empty';
  await scope.selectOption('watch');
  await area.getByText(/本站当前已发布资料中没有匹配项/).waitFor();
  assert.equal(await area.getByRole('alert').count(), 0);
  mode = 'ready';
  await scope.selectOption('all');
  await area.getByRole('heading', {name: 'first page'}).waitFor();
  mode = 'denied';
  await page.getByRole('button', {name: 'EN', exact: true}).click();
  await area.getByRole('alert').waitFor();
  assert.equal(await area.locator('.lookup-result').count(), 0);
}

async function compare(page, lang) {
  await page.goto(origin + lang + '/legacy/apps');
  const buttons = page.locator('.compare-feedback button');
  for (let i = 0; i < 5; i++) await buttons.nth(i).click();
  assert.equal(await page.locator('.compare-feedback [aria-pressed=true]').count(), 4);
  const notice = page.locator('.compare-feedback [role=status]');
  assert.match(await notice.innerText(), /已选满 4|Four items selected/);
  await page.locator('.record-title').last().click();
  await page.waitForURL('**/records/demo-4');
  await page.locator('.compare-feedback button.button').waitFor();
  await notice.waitFor();
  assert.equal(await page.locator('.compare-feedback button').getAttribute('aria-pressed'), 'false');
  await page.goBack();
  await buttons.first().click();
  assert.equal(await notice.count(), 0);
  await buttons.nth(4).click();
  assert.equal(await buttons.nth(4).getAttribute('aria-pressed'), 'true');
}

async function frameSample(page) {
  await page.goto(origin + '/changelog');
  await page.locator('.changelog-entry').first().waitFor();
  const more = page.getByRole('button', {name: '加载更多历史'});
  while (await more.count()) await more.click();
  return page.evaluate(async () => {
    const rows = [...document.querySelectorAll('.changelog-entry')];
    const times = [];
    let last;
    while (times.length < 300) {
      const now = await new Promise(requestAnimationFrame);
      if (last !== undefined) times.push(now - last);
      last = now;
      const n = times.length;
      window.scrollTo(0, n * 15);
      if (n % 15 === 0) {
        const row = document.elementFromPoint(innerWidth / 2, innerHeight / 2)?.closest('.changelog-entry');
        (row || rows[Math.floor(n / 15)]).querySelector('button').click();
      }
    }
    times.sort((a,b) => a-b);
    return {rows: rows.length, p50: times[149], p95: times[284], p99: times[296], over25ms: times.filter(t => t > 25).length};
  });
}

(async () => {
  const browser = await chromium.launch({executablePath: process.env.READING_CHROMIUM});
  try {
    for (const width of [320, 390, 768, 1440]) {
      for (const dark of [false, true]) {
        const page = await browser.newPage({viewport: {width, height: 850}, isMobile: width < 700, hasTouch: width < 700});
        page.setDefaultTimeout(6000);
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        await intercept(page);
        await page.addInitScript(value => localStorage.setItem('fieldtofit-workspace-dark', JSON.stringify(value)), dark);
        const lang = dark ? '/en' : '';
        await page.goto(origin + lang + '/changelog');
        assert.equal(await page.locator('html').getAttribute('data-theme'), dark ? 'dark' : 'light');
        await disclosure(page);
        await page.emulateMedia({reducedMotion: 'reduce'});
        await disclosure(page);
        assert.equal(await page.locator('.changelog-notes').first().evaluate(el => getComputedStyle(el).transitionDuration), '0s');
        await page.emulateMedia({reducedMotion: 'no-preference'});
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        if (width < 700) await more(page);
        await search(page, lang);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await compare(page, lang);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        if (width === 390 && !dark) {
          await lookupBoundaries(page);
          console.log('Mobile long-list sample', await frameSample(page));
        }
        if (width === 1440 && !dark) {
          for (let run = 0; run < 3; run++) console.log('Long-list sample', await frameSample(page));
        }
        assert.deepEqual(errors, []);
        await page.close();
        console.log('PASS', width, dark ? 'English / dark' : 'Chinese / light');
      }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
