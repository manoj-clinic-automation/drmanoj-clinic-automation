// walk_s835_page.js -- S835_CREDIT_NOTES: the desk page itself, as the app renders it (desk.html from walk_s835_app.py with S835_DUMP),
// run in a headless DOM (jsdom). The server is replaced by the JSON the walk's real app served; every click is a real DOM event.
// usage: NODE_PATH=<node_modules> node walk_s835_page.js <dump dir> [--expect-red]
const fs = require('fs'), path = require('path');
const { JSDOM } = require('jsdom');
const dir = process.argv[2], RED = process.argv.includes('--expect-red');
const html = fs.readFileSync(path.join(dir, 'desk.html'), 'utf8');
const pj = JSON.parse(fs.readFileSync(path.join(dir, 'p.json'), 'utf8'));
const h2 = JSON.parse(fs.readFileSync(path.join(dir, 'h2.json'), 'utf8'));
const P = pj.P, H1 = pj.H1, H2 = pj.H2, posted = [], asked = [], RES = {};
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://walk.invalid/scanapp/desk',
  beforeParse(w) {
    w.fetch = (u, o) => {
      const J = (x) => Promise.resolve({ ok: true, status: 200, type: 'basic', json: () => Promise.resolve(x) });
      u = String(u);
      if (/\/desk\/api\/list/.test(u)) return J({ ok: true, papers: [{ id: P, stamp: pj.paper_P.stamp, month: 'Mar 2031', supplier: 'Walk Dealer835', hint: 'This looks like a credit note', why: [] },
                                                                      { id: H2, stamp: h2.stamp, month: 'Mar 2031', supplier: 'Walk Dealer835', hint: '', why: [] }], total: 2 });
      if (/cn_vendor=/.test(u)) { asked.push(u); const q = JSON.parse(JSON.stringify(pj.paper_P)); q.cn.cands = q.cn.cands.filter((c) => c.id === H2).map((c) => Object.assign(c, { pre: false })); return J(q); }
      if (/\/desk\/api\/paper\//.test(u)) return J(u.endsWith('/' + H2) ? h2 : pj.paper_P);
      if (/\/desk\/api\/suppliers/.test(u)) return J({ suppliers: [] });
      if (/\/desk\/api\/save/.test(u)) { posted.push(JSON.parse(o.body)); return J({ ok: true, message: 'saved', next: 0 }); }
      return J({ ok: true });
    };
    w.confirm = () => true;
    w.HTMLIFrameElement.prototype.focus = () => {};
  } });
const w = dom.window, d = w.document, $ = (i) => d.getElementById(i);
const tick = () => new Promise((r) => setTimeout(r, 30));
function ck(name, ok, detail) { RES[name.split(' ')[0]] = !!ok; console.log((ok ? 'GREEN ' : 'RED   ') + name + (!ok && detail ? ' -- ' + String(detail).slice(0, 400) : '')); }
const vis = (e) => !!e && e.style.display !== 'none';
const click = (e) => e && e.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
const change = (e) => e && e.dispatchEvent(new w.Event('change', { bubbles: true }));
const qs = (r, s) => (r ? r.querySelector(s) : null);
const pick = (e) => { if (e) { e.checked = true; change(e); } };
const input = (e, v) => { if (e) { e.value = v; e.dispatchEvent(new w.Event('input', { bubbles: true })); } };
(async () => {
  for (let i = 0; i < 20; i++) await tick();
  const fix = $('flags').textContent;
  ck('J1 the paper opens with the reader\'s line -- a CREDIT NOTE, its no., the invoice it names -- and "Make it a Credit note" / "No — leave it"',
     /CREDIT NOTE/.test(fix) && /CN-0045/.test(fix) && /WD\/0803/.test(fix) && /Make it a Credit note/.test(fix) && /No — leave it/.test(fix), fix);
  const chip = [...d.querySelectorAll('#kinds .b')].find((b) => b.textContent === 'Credit note');
  const box = $('cn835');
  ck('J2 the sixth chip "Credit note" is chosen, the credit note box shows: its no., date and amount, "Against which bill?", the reader\'s pick ticked',
     chip && /\bon\b/.test(chip.className) && vis(box) && (qs(box, 'input[data-cn=no]') || {}).value === 'CN-0045' && /Against which bill\?/.test(box.textContent)
     && (qs(box, 'input[data-cnag="' + H1 + '"]') || {}).checked && /the reader’s pick/.test(box.textContent), box && box.textContent.slice(0, 300));
  const det = qs(box, 'details[data-cnd="' + H1 + '"]');
  ck('J3 the picked pharmacy bill is open: its scan (open it full size) and Marg\'s purchase entry lines, beside the credit note\'s lines and "not entered yet"',
     det && det.open && (qs(det, 'iframe') || { getAttribute: () => '' }).getAttribute('src') && /open it full size/.test(det.textContent) && /Marg purchase entry — bill WD803/.test(det.textContent)
     && /WALKITEM ONE/.test(det.textContent) && /The credit note’s lines beside it/.test(det.textContent) && /not entered yet/.test(det.textContent), det && det.textContent.slice(0, 300));
  ck('J4 handed to Sanjeevni is said, "Where does it go?" is not asked, and Save is ready',
     !vis($('groupsbox')) && /Handed to Sanjeevni with/.test($('filedwith').textContent) && !$('save').disabled && $('save').textContent === 'Save — next paper',
     [$('filedwith').textContent, $('save').textContent]);
  const fv = $('f_vendor');
  input(fv, 'Walk Dealer Two');
  fv.dispatchEvent(new w.FocusEvent('focusin', { bubbles: true }));
  await tick();
  const nw = d.querySelector('[data-spnew715]');
  if (nw) { nw.dispatchEvent(new w.MouseEvent('mousedown', { bubbles: true, cancelable: true })); }
  for (let i = 0; i < 40; i++) await tick();
  const b1 = $('cn835');
  ck('J11 the supplier corrected on the desk: the bills are asked again for THAT supplier (not saved yet); the list redrawn, the old pick dropped, Save waits for a bill',
     asked.length >= 1 && /cn_vendor=Walk%20Dealer%20Two/.test(asked[asked.length - 1]) && !qs(b1, 'input[data-cnag="' + H1 + '"]') && !!qs(b1, 'input[data-cnag="' + H2 + '"]')
     && $('save').disabled && $('save').textContent === 'Choose the bill it is against', [asked, $('save').textContent]);
  pick(qs(box && $('cn835'), 'input[data-cnag="' + H2 + '"]'));
  await tick();
  const b2 = $('cn835');
  ck('J5 another bill chosen: its own panel opens (the lines saved on the desk), filed with it in its group',
     /Filed with .* in Procedure room/.test($('filedwith').textContent) && (qs(b2, 'details[data-cnd="' + H2 + '"]') || {}).open && /WALK GLOVES/.test(b2 ? b2.textContent : ''),
     $('filedwith').textContent);
  input(qs(b2, 'input[data-cn=amt]'), '');
  await tick();
  const t0 = [$('save').disabled, $('save').textContent];
  input(qs(b2, 'input[data-cn=amt]'), '500');
  await tick();
  ck('J6 no amount: Save waits with "Type the amount back"; typed in the box, it fills What was read and Save is ready',
     t0[0] && t0[1] === 'Type the amount back' && $('f_amt').value === '500' && !$('save').disabled, t0.concat([$('f_amt').value, $('save').disabled]));
  click($('save'));
  for (let i = 0; i < 5; i++) await tick();
  const bd = posted[0] || {};
  ck('J7 the Save sends the kind, the bill it is against and the amount -- and never stock lines, Procedure room lines, Other lines, a payment or challans',
     bd.kind === 'credit_note' && bd.cn && bd.cn.against === String(H2) && bd.total_amount === '500' && !('st_lines' in bd) && !('pr_lines' in bd)
     && !('fo_lines' in bd) && !('pay' in bd) && Array.isArray(bd.joins) && bd.joins.length === 0, JSON.stringify(bd).slice(0, 300));
  for (let i = 0; i < 10; i++) await tick();
  const bx = $('cn835');
  pick(qs(bx, 'input[data-cnag="acct"]'));
  await tick();
  const a0 = [vis($('groupsbox')), $('save').disabled, $('save').textContent];
  const pe = d.querySelector('#groups .d[data-d="pe"]'), lab = d.querySelector('#groups .d[data-d="lab"]');
  const dis = !!(pe && pe.disabled && lab && lab.disabled);
  click(d.querySelector('#groups .d[data-d="others"]'));
  await tick();
  ck('J8 on the dealer\'s account: "Where does it go?" is asked again (an expense file and NK Pathology not offered), Save waits for it, then is ready',
     dis && a0[0] && a0[1] && a0[2] === 'Choose where it goes' && !$('save').disabled && /On the dealer’s account/.test($('filedwith').textContent), a0);
  const wasBox = vis($('cn835'));
  click([...d.querySelectorAll('#kinds .b')].find((b) => b.textContent === 'Bill'));
  await tick();
  ck('J9 chosen as a Bill after all: the credit note box (showing until then) goes away', wasBox && !vis($('cn835')));
  click(d.querySelector('#list .row[data-id="' + H2 + '"]'));
  for (let i = 0; i < 10; i++) await tick();
  const cb = $('cnon835');
  ck('J10 the bill\'s own page: Bill · Credit note (− amount, its paper to open) · Still owed',
     vis(cb) && /Credit note CN-0045/.test(cb.textContent) && /− ₹500/.test(cb.textContent) && /Still owed/.test(cb.textContent) && /₹2,760/.test(cb.textContent)
     && qs(cb, '[data-id="' + P + '"]'), cb && cb.textContent);
  const red = Object.keys(RES).filter((k) => !RES[k]);
  if (RED) { console.log('WALK S835 PAGE CONTROL: ' + red.length + ' red of ' + Object.keys(RES).length + (red.length === Object.keys(RES).length ? ' -- AS IT MUST BE' : ' -- NOT AS IT MUST BE')); process.exit(red.length === Object.keys(RES).length ? 0 : 1); }
  console.log('WALK S835 PAGE: ' + (Object.keys(RES).length - red.length) + ' green, ' + red.length + ' red');
  process.exit(red.length ? 1 : 0);
})().catch((e) => { console.log('RED   the page walk itself failed: ' + e); process.exit(2); });
