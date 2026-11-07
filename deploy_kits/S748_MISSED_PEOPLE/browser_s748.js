// browser_s748.js -- S748's browser walk (S747's whole, plus S9: missed calls as patients on the staff card), MADE-UP data only: the owner's Call Console card (the walk's rendered page) and the
// staff's own card on Aaj ka kaam (the made aaj_kaam.html, its doors answered from the walk's own JSON).
// usage: node browser_s747.js <console.html> <aaj_kaam.html> <card_today.json> <card_yesterday.json> [--control]
//   --control: run on the LIVE aaj_kaam.html -- the staff-card checks must go red.
const { chromium } = require('playwright');
const fs = require('fs');
const [CONSOLE, AAJ, CT, CY] = process.argv.slice(2, 6);
const CONTROL = process.argv.includes('--control');
let res = [];
function check(name, ok) { res.push([name, !!ok]); console.log((ok ? 'ok   ' : 'RED  ') + name); }

(async () => {
  const br = await chromium.launch();
  for (const w of [1366, 390]) {
    // ---------------------------------------------------------------- the owner's console card
    const p = await br.newPage({ viewport: { width: w, height: 900 } });
    const posts = [];
    await p.route('**/portal/console/api/**', async (r) => {
      posts.push([r.request().url(), r.request().postData()]);
      if (r.request().url().includes('/api/tx/')) return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ text: 'Staff: namaste. Patient: poori baat.' }) });
      return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, msg: 'Saved.' }) });
    });
    await p.route('http://walk/console', (r) => r.fulfill({ contentType: 'text/html', body: fs.readFileSync(CONSOLE, 'utf8') }));
    await p.goto('http://walk/console');
    if (!CONTROL) {
      await p.evaluate(() => { document.getElementById('st-shivani').open = true; });
      const mr = await p.locator('#st-shivani .fr[data-ref] button.rb', { hasText: 'Mark reviewed' }).first().elementHandle();
      await mr.click();
      await p.waitForTimeout(200);
      check(`C1 (${w}) Mark reviewed posts the call and its staff, and the button says so`, (await mr.textContent()).includes('Reviewed') && posts.some(x => x[0].endsWith('/review2') && x[1].includes('"act":"reviewed"') && x[1].includes('"staff":"shivani"')));
      const row = p.locator('#st-shivani .fr[data-ref]').nth(1);
      await row.locator('button', { hasText: 'Note to staff' }).click();
      check(`C2 (${w}) Note to staff opens a box in the row`, await row.locator('.nbox input').isVisible());
      await row.locator('.nbox input').fill('kal subah call karein');
      await row.locator('button', { hasText: 'Send note' }).click();
      await p.waitForTimeout(200);
      check(`C3 (${w}) the note is sent and shown under the call`, (await row.textContent()).includes('Note sent: “kal subah call karein”') && posts.some(x => x[1] && x[1].includes('"act":"note"')));
      const wt = p.locator('#st-shivani a', { hasText: 'whole transcript' }).first();
      check(`C4 (${w}) the transcript's first words and 'whole transcript' are on the staff card's calls`, await wt.count() > 0);
      if (await wt.count()) { await wt.click(); await p.waitForTimeout(200); check(`C5 (${w}) the whole transcript opens in place`, (await p.locator('#st-shivani .full').first().textContent()).includes('poori baat')); }
      const over = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      check(`C6 (${w}) no sideways scroll`, over <= 1);
    }
    await p.close();

    // ---------------------------------------------------------------- the staff's own card (Aaj ka kaam)
    const s = await br.newPage({ viewport: { width: w, height: 900 } });
    const sp = [];
    const today = JSON.parse(fs.readFileSync(CT, 'utf8')), yday = JSON.parse(fs.readFileSync(CY, 'utf8'));
    today.card.calls[0].name = '<img src=x onerror="window.__xss=1">';          // what a name holds is never markup
    await s.route('**/finance/aaj/api/list*', (r) => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, name: 'Shivani', day: 'Shanivar 7 Nov', as_of: '12:00', sections: [], tasks: [], has: false, today: '2026-11-07' }) }));
    await s.route('**/portal/console/api/mycard*', (r) => { sp.push(r.request().url()); return r.fulfill({ contentType: 'application/json', body: JSON.stringify(r.request().url().includes('span=today') ? today : yday) }); });
    await s.route('**/portal/console/api/mytx/**', (r) => { sp.push(r.request().url()); return r.fulfill({ status: 404, body: '' }); });
    await s.route('**/portal/console/api/myrec/**', (r) => { sp.push(r.request().url()); return r.fulfill({ contentType: 'audio/mpeg', body: '' }); });
    await s.route('**/portal/console/api/dispute', (r) => { sp.push(r.request().url() + ' ' + r.request().postData()); return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, msg: 'Doctor sahab ko bhej diya.' }) }); });
    await s.route('http://walk/aaj', (r) => r.fulfill({ contentType: 'text/html', body: fs.readFileSync(AAJ, 'utf8') }));
    await s.goto('http://walk/aaj');
    await s.waitForTimeout(400);
    const cc = s.locator('details.cc');
    check(`S9 (${w}) her card leads with 'Jinse baat nahin hui: 1 log' and the missed calls carry the patients ('2 chhoote (1 logon se)')`, (await s.locator('details.cc > summary').textContent()).includes('Jinse baat nahin hui: 1 log') && (await s.locator('details.cc > summary').textContent()).includes('2 chhoote (1 logon se)'));
    check(`S1 (${w}) the card is on her page, folded, 'Mere calls — kal' with the summary on the top line`, await cc.count() === 1 && !(await cc.getAttribute('open') !== null) && (await s.locator('details.cc > summary').textContent()).includes('Mere calls — kal'));
    if (await cc.count()) {
      await s.locator('details.cc > summary').click();
      await s.locator('details.all > summary').click();
      const allTxt = await s.locator('details.all').textContent();
      check(`S2 (${w}) yesterday's reception call listed with 'Recording sunein', and no transcript text anywhere on the card`, allTxt.includes('reception mobile') && allTxt.includes('Recording sunein') && !(await s.locator('details.cc').textContent()).includes('report dikhana'));
      await s.locator('details.all button.lnk', { hasText: 'Recording sunein' }).first().click(); await s.waitForTimeout(200);
      await s.waitForTimeout(500);
      check(`S3 (${w}) the recording is asked of HER door (myrec) in place, never a transcript door; a recording that cannot play says so`, sp.some(u => u.includes('/portal/console/api/myrec/')) && !sp.some(u => u.includes('/api/mytx/')) && ((await s.locator('details.all audio').count()) + (await s.locator('details.all .sub', { hasText: 'Recording abhi nahin chal paayi' }).count())) >= 1);
      await s.locator('.cc .tabs button', { hasText: 'Aaj' }).click(); await s.waitForTimeout(300);
      const txt = await s.locator('details.cc').textContent();
      check(`S4 (${w}) Aaj: the same figures, the owner's ask and his note, in Hindi`, txt.includes('Mere calls — aaj') && txt.includes('Doctor sahab: is call ka nateeja darj karein') && txt.includes('Doctor sahab ka sandesh') && txt.includes('isko kal call karna') && txt.includes('Call ka nateeja darj nahin kiya'));
      check(`S5 (${w}) an accepted dispute says so`, txt.includes('Doctor sahab ne maana'));
      const gal = s.locator('.cc .fg button.gal', { hasText: 'Galat hai?' }).first();
      await gal.click();
      await s.locator('.cc .pick input').first().check();
      await s.locator('.cc textarea').fill('maine log kiya tha');
      await s.locator('.cc button', { hasText: 'Doctor sahab ko bhejiye' }).click(); await s.waitForTimeout(300);
      check(`S6 (${w}) 'Galat hai?': pick a call, one line, sent to the dispute door with the call and the figure`, sp.some(u => u.includes('/api/dispute ') && u.includes('maine log kiya tha') && u.includes('"fig"')));
      check(`S7 (${w}) a name is shown as text, never run as markup`, !(await s.evaluate(() => window.__xss)) && (await s.locator('details.cc').textContent()).includes('<img'));
      const over = await s.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      check(`S8 (${w}) no sideways scroll on the phone page`, over <= 1);
    }
    await s.close();
  }
  await br.close();
  const red = res.filter(r => !r[1]);
  if (CONTROL) { const st = res.filter(r => r[0].startsWith('S')); const rr = st.filter(r => !r[1]); console.log(`CONTROL: ${rr.length} of ${st.length} staff-card checks red`); process.exit(rr.length === st.length ? 0 : 1); }
  console.log(`BROWSER ${red.length ? 'RED' : 'OK'}: ${res.length - red.length} of ${res.length}`);
  process.exit(red.length ? 1 : 0);
})();
