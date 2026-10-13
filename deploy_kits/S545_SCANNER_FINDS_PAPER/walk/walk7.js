// S545 walk of the seven surfaces: each surface's SCANNER_CONFIG shape, the OLD and the NEW widget loaded whole.
// The finance app's five and the scan app's asset page must render byte-identical DOM with no error; the intake (cvScan)
// must load the library and the NEW widget must find scene B where the OLD finds nothing (the control).
// usage: node walk7.js <old widget> <new widget>
const fs = require('fs'), path = require('path'); const { chromium } = require('playwright');
const [oldW, newW] = process.argv.slice(2);
const OCV = 'file://' + path.resolve('node_modules/@techstark/opencv-js/dist/opencv.js');
const base = {fileField: 'file', allowIdCard: false, allowBatch: false, backUrl: '/x'};
const SURF = [
  ['finance day scan', Object.assign({title: 'Day — 2099-01-01', uploadUrl: '/finance/api/day/2099-01-01/scan/z', uploadFields: {unit: 'U', business_date: '2099-01-01', doc_type: 'z'}, nameBase: 'S_z'}, base)],
  ['finance non-cash', Object.assign({title: 'NC -- 2099-01-01', uploadUrl: '/finance/api/day/2099-01-01/noncash-scan/u', uploadFields: {unit: 'U', business_date: '2099-01-01', noncash_uid: 'u'}, nameBase: 'S_b'}, base)],
  ['finance expense', Object.assign({title: 'Ex — 2099-01-01', uploadUrl: '/finance/api/day/2099-01-01/expense-scan/u', uploadFields: {unit: 'U', business_date: '2099-01-01', expense_uid: 'u'}, nameBase: 'S_e'}, base)],
  ['finance clinic day', Object.assign({title: 'C — 2099-01-01', uploadUrl: '/finance/clinic/api/day/2099-01-01/scan/z', uploadFields: {unit: 'C', business_date: '2099-01-01', doc_type: 'z'}, nameBase: 'C_z'}, base)],
  ['finance clinic expense', Object.assign({title: 'CE — 2099-01-01', uploadUrl: '/finance/clinic/api/day/2099-01-01/expense-scan/u', uploadFields: {unit: 'C', business_date: '2099-01-01', expense_uid: 'u'}, nameBase: 'C_e'}, base)],
  ['scan app asset page', Object.assign({title: 'Asset 1', uploadUrl: '/scanapp/files/upload', uploadFields: {entity: 'asset', entity_id: '1'}, nameBase: 'asset_1', allowIdCard: true}, base)],
  ['scan app intake (smart)', Object.assign({title: 'Scan the bill', uploadUrl: '/scanapp/intake/scan_submit', fileField: 'bill_scan', uploadFields: {lane: 'clinic', bill_month: '2099-01'}, nameBase: 'bill',
     autoPage: true, inlineStamp: true, retryUpload: true, directFile: true, slipJsonUrl: '/x/{id}', cvScan: true, cvUrl: OCV}, base, {fileField: 'bill_scan'})],
];
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const results = [];
  for (const [name, cfg] of SURF) {
    const dom = {};
    for (const [tag, file] of [['old', oldW], ['new', newW]]) {
      const pg = await br.newPage(); const errs = [];
      pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      const html = `<!doctype html><html><head><meta charset=utf-8></head><body><div id=scanroot></div>
<script>window.SCANNER_CONFIG = ${JSON.stringify(cfg)};</script><script src="file://${path.resolve(file)}"></script></body></html>`;
      fs.writeFileSync('walk_page.html', html);
      await pg.goto('file://' + path.resolve('walk_page.html'));
      let extra = {};
      if (cfg.cvScan) {
        await pg.waitForFunction(() => window.__scannerS523 && window.__scannerS523.ready(), null, { timeout: 120000 });
        extra = await pg.evaluate((src) => { eval(src); var sc = scene(Object.assign({}, CASES[1])); var q = window.__scannerCV.find(sc.canvas); return {found: !!q, score: score(q, sc.truth)}; },
                                  fs.readFileSync('scenes.js', 'utf8'));
      } else { await pg.waitForTimeout(400); }
      dom[tag] = {html: await pg.evaluate(() => document.getElementById('scanroot').innerHTML), errs, extra,
                  on: await pg.evaluate(() => window.__scannerS523 ? window.__scannerS523.on : null)};
      await pg.close();
    }
    const same = dom.old.html === dom.new.html;
    let verdict;
    if (!cfg.cvScan) verdict = (same && !dom.old.errs.length && !dom.new.errs.length && dom.new.on === false) ? 'GREEN (identical, no error, smart path off)' : 'RED';
    else verdict = (dom.new.extra.found && dom.new.extra.score.cov >= 0.97 && !dom.new.errs.length) ? ('GREEN (new finds scene B ' + dom.new.extra.score.iou + '; control old found=' + dom.old.extra.found + ')') : 'RED';
    results.push({surface: name, verdict, dom_identical: same, errs_old: dom.old.errs.length, errs_new: dom.new.errs, old_extra: dom.old.extra, new_extra: dom.new.extra});
  }
  results.forEach(r => console.log(r.surface.padEnd(26), r.verdict, r.errs_new.length ? JSON.stringify(r.errs_new).slice(0, 200) : ''));
  await br.close();
})().catch(e => { console.error(e); process.exit(2); });
