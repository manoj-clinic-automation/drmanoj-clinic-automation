// S544: the intake (switch ON) in Chromium -- tap the lane buttons and Dr MK / Dr Bhawna; read what the scanner will send.
// usage: node browser_s544.js <dir with intake_owner.html and intake_reception.html>
const path = require('path'); const { chromium } = require('playwright');
const DIR = process.argv[2]; const R = [];
const check = (n, ok, d) => { R.push(!!ok); console.log((ok ? 'GREEN ' : 'RED   ') + n + (ok ? '' : ' -- ' + JSON.stringify(d))); };
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  for (const role of ['reception', 'owner']) {
    const pg = await br.newPage({ viewport: { width: 390, height: 844 } }); const errs = [];
    pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto('file://' + path.join(DIR, 'intake_' + role + '.html')); await pg.waitForTimeout(600);
    const st = () => pg.evaluate(() => ({ lane: window.SCANNER_CONFIG.uploadFields.lane, who: window.SCANNER_CONFIG.uploadFields.pe_who || null,
      sel: document.getElementById('intake_lane').value, basic: document.getElementById('lane_basic').value,
      line: document.getElementById('lane_line').textContent, aspect: window.SCANNER_CONFIG.expectAspect || null,
      on: Array.from(document.querySelectorAll('.l5b')).filter(b => b.style.border.indexOf('3px') === 0).map(b => b.getAttribute('data-lane')),
      whoShown: (document.getElementById('l5who') || {style: {}}).style.display || null }));
    let s = await st();
    check(role + ': opens on Clinic, its button lit, the line says Clinic', s.lane === 'clinic' && s.on.join() === 'clinic' && s.line.indexOf('Clinic') === 0, s);
    await pg.click('.l5b[data-lane="pharmacy"]'); s = await st();
    check(role + ': tap Pharmacy -> the scanner sends pharmacy, the half-A4 hint set, the basic form too, one button lit', s.lane === 'pharmacy' && s.sel === 'pharmacy' && s.basic === 'pharmacy' && s.aspect && s.on.join() === 'pharmacy' && s.line.indexOf('Pharmacy') === 0, s);
    await pg.click('.l5b[data-lane="lab_purchase"]'); s = await st();
    check(role + ': tap NK Pathology -> lab_purchase, the half-A4 hint cleared, the line says NK Pathology (the button words)', s.lane === 'lab_purchase' && !s.aspect && s.line.indexOf('NK Pathology') === 0, s);
    await pg.click('#challan_btn'); s = await st();
    check(role + ': the CHALLAN button still works beside the lanes', s.line.indexOf('CHALLAN') > 0, s);
    await pg.click('#challan_btn');
    if (role === 'owner') {
      await pg.click('.l5b[data-lane="owner_expense"]'); s = await st();
      check('owner: tap Personal expense -> owner_expense, Dr MK / Dr Bhawna shown, the line says Dr MK', s.lane === 'owner_expense' && s.whoShown === 'grid' && s.line.indexOf('Personal expense · Dr MK') === 0, s);
      await pg.click('.l5w[data-who="bhawna"]'); s = await st();
      const tall = await pg.evaluate(() => Array.from(document.querySelectorAll('.l5w')).map(b => Math.round(b.getBoundingClientRect().height)));
      check('owner: Dr MK / Dr Bhawna shown at least 44 px tall', tall.length === 2 && tall.every(h => h >= 44), tall);
      check('owner: tap Dr Bhawna -> pe_who bhawna sent, the basic form too, the line says Dr Bhawna', s.who === 'bhawna' && (await pg.evaluate(() => document.getElementById('pe_basic').value)) === 'bhawna' && s.line.indexOf('Dr Bhawna') > 0, s);
      await pg.click('.l5b[data-lane="clinic"]'); s = await st();
      check('owner: back to Clinic -> the Dr MK / Dr Bhawna row hidden', s.lane === 'clinic' && s.whoShown === 'none', s);
    } else {
      const n = await pg.evaluate(() => document.querySelectorAll('.l5b[data-lane="owner_expense"], .l5w').length);
      check('reception: no Personal expense and no Dr MK / Dr Bhawna anywhere on the page', n === 0, n);
    }
    const small = await pg.evaluate(() => Array.from(document.querySelectorAll('.l5b,.l5w')).filter(b => b.offsetParent !== null && b.getBoundingClientRect().height < 44).length);
    check(role + ': every visible button at least 44 px tall on a 390-px phone', small === 0, small);
    const over = await pg.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    check(role + ': no sideways scroll at phone width', !over, over);
    check(role + ': no script error on the page', errs.length === 0, errs);
    await pg.close();
  }
  await br.close();
  const red = R.filter(x => !x).length; console.log(R.length + ' checks, ' + (R.length - red) + ' green, ' + red + ' red'); process.exit(red ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
