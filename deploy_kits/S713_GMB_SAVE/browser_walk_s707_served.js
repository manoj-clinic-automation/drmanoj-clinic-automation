// S713: the S707 page walk unchanged except: the page is opened from an http address (argv[2]) and /portal/gmb/api/* answers ok.
// S707 browser walk — the GMB page in headless Chromium, clicked the way the owner uses it.
// usage: node browser_walk_s707.js <page.html>   → prints PASS/FAIL lines and a final BROWSER OK n/n | BROWSER RED k
const { chromium } = require('playwright');
const path = require('path');
const file = process.argv[2];
const NAME = /dr\.? manoj agarwal|डॉ\. मनोज अग्रवाल|डॉक्टर मनोज अग्रवाल/gi;
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log('PASS', m); } else { fail++; console.log('FAIL', m); } };
const wc = t => t.trim().split(/\s+/).filter(Boolean).length;
(async () => {
  const br = await chromium.launch();
  for (const vp of [{ width: 1366, height: 900, tag: 'PC' }, { width: 390, height: 844, tag: 'phone' }]) {
    const pg = await br.newPage({ viewport: { width: vp.width, height: vp.height } }); await pg.route('**/portal/gmb/api/**', r => r.fulfill({contentType:'application/json', body: JSON.stringify({ok:true,id:1,edited:false})}));
    const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await pg.goto(file);
    const cases = [
      { lang: 'Hindi', rel: 'mother', p: ['knee'], knee: ['bilateral', 'exercises', 'nutrition'], g: ['pain', 'walking', 'explained', 'nosurg'], q: ['listens'] },
      { lang: 'Hinglish', rel: 'self', p: ['fracture'], bone: 'wrist', side: 'left', g: ['plaster', 'charges', 'staff'], q: ['exp'] },
      { lang: 'English', rel: 'self', p: ['back'], g: ['explained', 'nosurg', 'pain', 'reports'], q: ['calm'] },
      { lang: 'Mixed', rel: 'wife', p: ['rheumatoid'], g: ['pain', 'charges', 'explained'], q: ['listens', 'person'] },
    ];
    for (const c of cases) {
      const tag = `${vp.tag} · ${c.lang} · ${c.p.join('+')}`;
      await pg.evaluate(() => resetAll());
      await pg.click(`.rb[data-r="${c.rel}"]`);
      await pg.click(`.lb[data-l="${c.lang}"]`);
      for (const p of c.p) await pg.click(`#pgrid .ptb[data-id="${p}"]`);
      if (c.bone) await pg.click(`.bnbtn[data-id="${c.bone}"]`);
      if (c.side) await pg.click(`.sdbtn[data-s="${c.side}"]`);
      for (const k of (c.knee || [])) await pg.click(`.kbtb[data-id="${k}"]`);
      for (const g of c.g) await pg.click(`#ggrid .gptb[data-id="${g}"]`);
      for (const q of c.q) await pg.click(`#qgrid .qb[data-id="${q}"]`);
      const seen = new Set();
      for (let press = 0; press < 3; press++) {
        await pg.click(press === 0 ? '#genbtn' : '.regen-btn');
        await pg.waitForSelector('#rt2');
        const t = await pg.$$eval('.rev-ta', a => a.map(x => x.value));
        ok(t.length === 3 && t.every(x => x && x.length > 10), `${tag} press ${press + 1}: three drafts on screen`);
        ok(t.every(x => !/undefined|«|»|(^|\s)(ko ko|को को|ne ne|ने ने)(\s|$)/.test(x)), `${tag} press ${press + 1}: no broken words`);
        ok(t.every(x => (x.match(NAME) || []).length === 1), `${tag} press ${press + 1}: the name exactly once in each`);
        ok(t.every(x => !/clinic,? bareilly|osteoarthritis|से जरूर मिलें|zaroor milein/i.test(x)), `${tag} press ${press + 1}: no clinic name, no osteoarthritis, no fixed close`);
        ok(wc(t[0]) >= 6 && wc(t[0]) <= 20 && wc(t[1]) <= 50 && wc(t[2]) <= 90, `${tag} press ${press + 1}: sizes ${wc(t[0])}/${wc(t[1])}/${wc(t[2])} within 20/50/90`);
        if (c.bone === 'wrist' && c.g.includes('plaster')) ok(t.every(x => !/\b\d+\s*(hafte|weeks|हफ्ते)/.test(x) || /\b6\s*(hafte|weeks|हफ्ते)/.test(x)), `${tag} press ${press + 1}: any plaster duration says 6 weeks`);
        const k = t.join('|'); ok(!seen.has(k), `${tag} press ${press + 1}: differs from the earlier presses`); seen.add(k);
      }
      // copy still works and the edit box takes an edit
      await pg.fill('#rt0', 'test edit');
      await pg.click('.rev-reset >> nth=0');
      const back = await pg.$eval('#rt0', x => x.value);
      ok(back !== 'test edit' && back.length > 10, `${tag}: Restore puts the draft back after an edit`);
    }
    const sw = await pg.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(sw <= 1, `${vp.tag}: no sideways scroll (${sw}px)`);
    ok(errs.length === 0, `${vp.tag}: no script error${errs.length ? ' — ' + errs[0] : ''}`);
    await pg.close();
  }
  await br.close();
  console.log(fail ? `BROWSER RED ${fail} of ${pass + fail}` : `BROWSER OK ${pass}/${pass}`);
  process.exit(fail ? 1 : 0);
})();
