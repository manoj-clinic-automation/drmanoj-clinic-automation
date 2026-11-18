// walk_s862_js.js -- kit S862: the page's own script run under node with a stub page; draws every month and each new card.
//   node walk_s862_js.js <patients_page.html> <reading.json>      prints one JSON line
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const R0 = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const m = html.match(/<script>([\s\S]*)<\/script>/g);
const src = m[m.length - 1].replace(/^<script>/, '').replace(/<\/script>$/, '');
const els = {};
function el(id) { return els[id] || (els[id] = { id, innerHTML: '', textContent: '', title: '', style: {}, classList: { add() {}, remove() {} },
  querySelector() { return null; }, querySelectorAll() { return []; }, setAttribute() {}, getAttribute() { return null; } }); }
global.document = { getElementById: el, querySelectorAll: () => [], addEventListener() {} };
global.location = { hash: '' }; global.history = { replaceState() {} }; global.fetch = () => new Promise(() => {});
const out = { errors: [] };
try {
  const run = new Function('R0', 'out', 'els', src + '\n;R=R0;var ms=R0.months.map(function(x){return x.ym;});' +
    'ms.forEach(function(ym){M=ym;try{draw();out["page_"+ym]=els.page.innerHTML;}catch(e){out.errors.push(ym+": "+e);}});' +
    'M=ms[ms.length-1];out.words=wordsCard();out.became=becameTable();out.google=googleCard();' +
    'WMSG={t:"walk <b>msg</b>",bad:1};out.words_msg=wordsCard();');
  run(R0, out, els);
} catch (e) { out.errors.push('script: ' + e); }
console.log(JSON.stringify(out));
