// walk_s838_page.js -- S838_SCANAPP_GOTO: The month page as the app renders it (month.html from walk_s838_app.py with S838_DUMP), in a
// headless DOM (jsdom): the Go to button opens the panel; a click inside keeps it; a click outside, Escape and "close" shut it.
// usage: NODE_PATH=<node_modules> node walk_s838_page.js <dump dir> [--expect-red]
const fs = require('fs'), path = require('path');
const { JSDOM } = require('jsdom');
const RED = process.argv.includes('--expect-red'), RES = {};
const dom = new JSDOM(fs.readFileSync(path.join(process.argv[2], 'month.html'), 'utf8'), { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://walk.invalid/scanapp/desk/month' });
const w = dom.window, d = w.document, b = d.getElementById('s838go'), p = d.getElementById('s838panel');
const click = (e) => e && e.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
function ck(n, ok) { RES[n.split(' ')[0]] = !!ok; console.log((ok ? 'GREEN ' : 'RED   ') + n); }
const open = () => !!p && !p.hidden;
ck('K1 the panel starts shut; Go to ▾ opens it (aria-expanded true)', b && p && !open() && (click(b), open()) && b.getAttribute('aria-expanded') === 'true');
click(p && p.querySelector('.s838h'));
ck('K2 a click inside the panel keeps it open', open());
click(d.body);
ck('K3 a click outside shuts it', !!p && !open() && b.getAttribute('aria-expanded') === 'false');
click(b); d.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
ck('K4 Escape shuts it', !!p && !open());
click(b); click(d.getElementById('s838close'));
ck('K5 “close ✕” shuts it', !!p && !open() && !!d.getElementById('s838close'));
const red = Object.keys(RES).filter((k) => !RES[k]);
if (RED) { console.log('WALK S838 PAGE CONTROL: ' + red.length + ' red of ' + Object.keys(RES).length + (red.length === Object.keys(RES).length ? ' -- AS IT MUST BE' : ' -- NOT AS IT MUST BE')); process.exit(red.length === Object.keys(RES).length ? 0 : 1); }
console.log('WALK S838 PAGE: ' + (Object.keys(RES).length - red.length) + ' green, ' + red.length + ' red'); process.exit(red.length ? 1 : 0);
