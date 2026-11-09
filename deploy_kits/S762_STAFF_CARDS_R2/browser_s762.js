// browser_s762.js -- S762_STAFF_CARDS_R2's browser walk, MADE-UP data only (walk_s762.py's dump): the owner's 7-day console
// (the Both on duty line, the own-card link, the jump link, no sideways scroll) and the staff's Mere calls on Aaj ka kaam
// (today's net missed on the folded line, the reached-later figure, 'punch se pehle'), at 1366 and 390 px.
// usage: node browser_s762.js <console7.html> <aaj_kaam.html> <card_y.json> <card_t.json> [--control]
const { chromium } = require('playwright');
const fs = require('fs');
const [CONSOLE, AAJ, CY, CT] = process.argv.slice(2, 6);
const CONTROL = process.argv.includes('--control');
let res = [];
function check(n, ok) { res.push([n, !!ok]); console.log((ok ? 'ok   ' : 'RED  ') + n); }
(async () => {
  const br = await chromium.launch();
  for (const w of [1366, 390]) {
    const errs = [];
    const p = await br.newPage({ viewport: { width: w, height: 900 } });
    p.on('pageerror', e => errs.push(String(e)));
    await p.route('**/portal/console/api/**', r => r.fulfill({ contentType: 'application/json', body: '{"ok":true}' }));
    await p.route('http://walk/console', r => r.fulfill({ contentType: 'text/html', body: fs.readFileSync(CONSOLE, 'utf8') }));
    await p.goto('http://walk/console');
    await p.evaluate(() => document.querySelectorAll('details').forEach(d => d.open = true));
    check(`P1 (${w}) the Both on duty line is on his page`, await p.locator('#st-both summary', { hasText: 'Both on duty' }).count() === 1);
    check(`P2 (${w}) Shivani's card links to her own card`, await p.locator('#st-shivani a[href="/finance/aaj?as=shivani"]').count() === 1);
    check(`P3 (${w}) the jump link reaches the staff section`, await p.locator('a[href="#staff"]').count() >= 1);
    check(`P4 (${w}) no sideways scroll, no script error`, (await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)) && errs.length === 0);
    await p.close();
    const q = await br.newPage({ viewport: { width: w, height: 900 } });
    const qe = [];
    q.on('pageerror', e => qe.push(String(e)));
    await q.route('**/portal/console/api/mycard*', r => r.fulfill({ contentType: 'application/json', body: fs.readFileSync(r.request().url().includes('span=today') ? CT : CY, 'utf8') }));
    await q.route('**/finance/**', r => r.fulfill({ contentType: 'application/json', body: '{"ok":true,"items":[]}' }));
    await q.route('http://walk/aaj', r => r.fulfill({ contentType: 'text/html', body: fs.readFileSync(AAJ, 'utf8') }));
    await q.goto('http://walk/aaj');
    await q.waitForTimeout(600);
    const sum = (await q.locator('#calls details.cc > summary').textContent().catch(() => '')) || '';
    const yj = JSON.parse(fs.readFileSync(CY, 'utf8'));
    check(`Q1 (${w}) the folded line says kal and 'aaj abhi tak: N log'`, sum.includes('kal') && sum.includes('aaj abhi tak: ' + yj.today.net_missed + ' log'));
    await q.evaluate(() => { const d = document.querySelector('#calls details.cc'); if (d) d.open = true; const a = document.querySelector('#calls details.all'); if (a) a.open = true; });
    const txt = (await q.locator('#calls').textContent()) || '';
    check(`Q2 (${w}) the reached-later figure`, txt.includes('Chhoote call ke baad baat ho gayi'));
    check(`Q3 (${w}) a miss before her punch says 'punch se pehle'`, txt.includes('punch se pehle'));
    check(`Q4 (${w}) the Aaj tab is still there`, await q.locator('#calls .tabs button', { hasText: 'Aaj' }).count() === 1);
    check(`Q5 (${w}) no sideways scroll, no script error`, (await q.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)) && qe.length === 0);
    await q.close();
  }
  await br.close();
  const red = res.filter(x => !x[1]).length;
  console.log(red ? `BROWSER RED: ${res.length - red} of ${res.length}` : `BROWSER GREEN: ${res.length} of ${res.length}`);
  process.exit(CONTROL ? (red >= 6 ? 0 : 1) : (red ? 1 : 0));
})();
