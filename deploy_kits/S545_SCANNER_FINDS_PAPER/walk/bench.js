// S545 bench: runs the OLD (live 65127fcb) and NEW (patched) finders on made-up photos in Chromium with the pinned OpenCV.
// usage: node bench.js <old widget> <new widget>
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const [oldW, newW] = process.argv.slice(2);
function extract(file){
  const s = fs.readFileSync(file, 'utf8');
  const a = s.indexOf('  function orderQuad(pts){'), b = s.indexOf('  function fullCanvas(img){');
  if (a < 0 || b < 0) throw new Error('anchors missing in ' + file);
  return s.slice(a, b);
}
const factory = (body) => `(function(CVlib){ var CV = CVlib, cvReady = true, CV_DETECT = 640, CV_MAX_OUT = 2400;\n${body}\n return {find: cvFindQuad, warp: cvWarp, upright: (typeof cvUpright === 'function') ? cvUpright : null,
   paper: (typeof quadFromPaper === 'function') ? function(c){ var s = CV.imread(c); try { return quadFromPaper(s, c.width, c.height); } finally { s.delete(); } } : null}; })`;
const html = `<!doctype html><html><body><script src="file://${path.resolve('node_modules/@techstark/opencv-js/dist/opencv.js')}"></script></body></html>`;
fs.writeFileSync('bench.html', html);
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
  const pg = await br.newPage();
  await pg.goto('file://' + path.resolve('bench.html'));
  await pg.waitForFunction(() => window.cv && (window.cv.Mat || typeof window.cv.then === 'function'), null, { timeout: 120000 });
  await pg.evaluate(async () => { if (!window.cv.Mat && window.cv.then) { window.cv = await window.cv; } });
  await pg.waitForFunction(() => window.cv && window.cv.Mat, null, { timeout: 120000 });
  const res = await pg.evaluate(({ fo, fn, scenesSrc }) => {
    const OLD = eval(fo)(window.cv), NEW = eval(fn)(window.cv);
    eval(scenesSrc);
    return runAll(OLD, NEW);
  }, { fo: factory(extract(oldW)), fn: factory(extract(newW)), scenesSrc: fs.readFileSync('scenes.js', 'utf8') });
  console.log(JSON.stringify(res, null, 1));
  await br.close();
})().catch(e => { console.error(e); process.exit(2); });
