// walk_watcher_s578.js -- the walk for Clinic_Portal_Watcher.gs (kit S578). Runs the REAL script in Node against a
// made-up Google (properties, mail, triggers) and a made-up Hostinger, with a clock moved 5 minutes per check.
// Nothing real is called.   node walk_watcher_s578.js [path/to/Clinic_Portal_Watcher.gs]
// Exit 0 only if every check is green.
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path');
const GS = path.resolve(process.argv[2] || path.join(__dirname, 'Clinic_Portal_Watcher.gs'));
const SRC = fs.readFileSync(GS, 'utf8');
const KEY = 'hkWalkSecret991', TOPIC = 'walkTopic77', HOST = 'srv1746119.hstgr.cloud';
const T0 = Date.parse('2026-10-18T05:00:00Z');

function world(opts) {
  const w = Object.assign({ portal: true, site: true, vmState: 'running', lock: 'unlocked', actions: [], apiCode: 200,
    key: KEY, fixAfterMin: 10, now: T0, props: {}, mails: [], pushes: [], posts: [], gets: 0 }, opts || {});
  w.props.NTFY_TOPIC = TOPIC;
  if (w.key) w.props.HOSTINGER_KEY = w.key;
  class FDate extends Date { constructor(...a) { if (a.length) super(...a); else super(w.now); } static now() { return w.now; } }
  const P = { getProperty: k => (k in w.props ? w.props[k] : null), setProperty: (k, v) => { w.props[k] = String(v); } };
  const resp = (code, obj) => ({ getResponseCode: () => code, getContentText: () => JSON.stringify(obj === undefined ? {} : obj) });
  const ctx = {
    Date: FDate, JSON, Math, String, Array, Object, Error,
    PropertiesService: { getScriptProperties: () => P },
    MailApp: { sendEmail: (to, t, b) => w.mails.push({ to, t, b }) },
    Utilities: { sleep: () => {}, formatDate: (d) => new Date(d.getTime() + 19800000).toISOString().slice(5, 16).replace('T', ' ') },
    ScriptApp: { getProjectTriggers: () => [], deleteTrigger: () => {}, newTrigger: () => ({ timeBased: () => ({ everyMinutes: () => ({ create: () => {} }) }) }) },
    UrlFetchApp: { fetch: (url, o) => {
      o = o || {};
      if (url.indexOf('https://ntfy.sh/') === 0) { w.pushes.push({ url, title: o.headers.Title, body: o.payload, pri: o.headers.Priority, click: o.headers.Click }); return resp(200); }
      if (url.indexOf('followup.dr-manoj.in') >= 0) { if (w.portal) return resp(200); throw new Error('timeout'); }
      if (url.indexOf('drmanojagarwal.com') >= 0) { if (w.site) return resp(200); throw new Error('timeout'); }
      if (url.indexOf('https://developers.hostinger.com/') === 0) {
        if (!o.headers || o.headers.Authorization !== 'Bearer ' + KEY) return resp(401, { message: 'Unauthenticated' });
        if (w.apiCode !== 200) return resp(w.apiCode, {});
        const p = url.split('/virtual-machines')[1];
        if ((o.method || 'get') === 'post') {
          w.posts.push(p);
          w.vmState = 'running'; w.recoverAt = w.now + w.fixAfterMin * 60000;
          return resp(200, { id: 1, name: p.split('/').pop(), state: 'success' });
        }
        w.gets++;
        if (p === '') return resp(200, [{ id: 4401, hostname: 'other.example' }, { id: 4402, hostname: HOST }]);
        if (p === '/4402') return resp(200, { id: 4402, hostname: HOST, state: w.vmState, actions_lock: w.lock });
        if (p === '/4402/actions') return resp(200, { data: w.actions, meta: {} });
        return resp(404, {});
      }
      throw new Error('unexpected URL ' + url);
    } },
  };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx, { filename: 'Clinic_Portal_Watcher.gs' });
  w.check = (n) => { for (let i = 0; i < (n || 1); i++) {
      if (w.recoverAt && w.now >= w.recoverAt) { w.portal = true; w.site = true; w.recoverAt = null; }
      ctx.check(); w.now += 5 * 60000; } };
  w.ctx = ctx;
  return w;
}

const R = [];
function check(name, cond) { R.push([name, !!cond]); console.log((cond ? 'GREEN ' : 'RED   ') + name); }
const titles = w => w.pushes.map(p => p.title);
const high = w => w.pushes.filter(p => p.pri === 'high');

let w;
// 1 all good
w = world(); w.check(3);
check('1 all good: no mail, no push, lastOk set, Hostinger never asked', w.mails.length === 0 && w.pushes.length === 0 && w.props.lastOk && w.gets === 0);

// 2 server on, portal down: wait for the server's own repair, alert at the third check with step 3
w = world({ portal: false }); w.check(2);
check('2 server on, portal down 10 min: no alert yet (the server is repairing itself)', w.pushes.length === 0);
w.check(1);
check('2 at 15 min: one high alert naming step 3, opening #s3', high(w).length === 1 && /step 3/.test(high(w)[0].body) && high(w)[0].click.endsWith('#s3'));
check('2 Hostinger is never pressed while the website answers', w.posts.length === 0);
w.check(6);
check('2 no second alert within the hour', high(w).length === 1);

// 3 whole server off, no key: the old alert, step 4
w = world({ portal: false, site: false, key: null }); w.check(2);
check('3 no key: the S573 alert at 10 min, step 4, nothing pressed', high(w).length === 1 && /step 4/.test(high(w)[0].body) && w.posts.length === 0);

// 4 whole server stopped: start it at 10 minutes, tell him, then 'back'
w = world({ portal: false, site: false, vmState: 'stopped' }); w.check(1);
check('4 stopped, 5 min: nothing pressed yet', w.posts.length === 0);
w.check(1);
check('4 stopped, 10 min: START sent once to the clinic server (found by its name)', w.posts.length === 1 && w.posts[0] === '/4402/start' && w.props.HOSTINGER_VM === '4402');
check('4 a plain line says it was started automatically; no high alert', /started it automatically/.test(titles(w).join('|')) && high(w).length === 0);
w.check(3);
check('4 it comes back: one "back" line that says the watcher started it', /back/.test(titles(w).join('|')) && /started the server/.test(w.pushes[w.pushes.length - 1].body));
check('4 no high alert in the whole episode', high(w).length === 0);

// 5 whole server running but not answering: restart at 15 minutes, not before
w = world({ portal: false, site: false, vmState: 'running' }); w.check(2);
check('5 running but dead, 10 min: nothing pressed', w.posts.length === 0);
w.check(1);
check('5 at 15 min: RESTART sent once', w.posts.length === 1 && w.posts[0] === '/4402/restart');

// 6 the restart does not help: wait 15 min, then one alert with step 4; never a second press within the hour
w = world({ portal: false, site: false, vmState: 'running', fixAfterMin: 9999 }); w.check(3);
w.check(2);
check('6 within 15 min of the restart: no alert, no second press', high(w).length === 0 && w.posts.length === 1);
w.check(2);
check('6 after that: one high alert, step 4, saying what the watcher already did', high(w).length === 1 && /step 4/.test(high(w)[0].body) && /restarted the server through Hostinger/.test(high(w)[0].body));
check('6 still one press in the first hour', w.posts.length === 1);
w.check(8);
check('6 after an hour: one more restart (once an hour), never more', w.posts.length === 2);

// 7 Hostinger busy (locked): never pressed, told once
w = world({ portal: false, site: false, vmState: 'stopped', lock: 'locked' }); w.check(6);
check('7 locked: nothing pressed', w.posts.length === 0);
check('7 locked: one plain "Hostinger is working on it" line, no high alert in the first 30 min', titles(w).filter(t => /working on it/.test(t)).length === 1 && high(w).length === 0);
w.check(10);
check('7 still locked after an hour: one high alert, step 4', high(w).length === 1 && /step 4/.test(high(w)[0].body));

// 8 a Hostinger action still open (e.g. its own maintenance restart): never pressed
w = world({ portal: false, site: false, vmState: 'stopped', actions: [{ id: 9, name: 'restart', state: 'sent' }] }); w.check(4);
check('8 an open Hostinger action: nothing pressed', w.posts.length === 0 && /working on it/.test(titles(w).join('|')));

// 9 the key refused: no press, alert step 4 saying why
w = world({ portal: false, site: false, vmState: 'stopped', key: 'wrong-key' }); w.check(2);
check('9 key refused: nothing pressed, high alert step 4, says the key was refused', w.posts.length === 0 && high(w).length === 1 && /key was refused/.test(high(w)[0].body));

// 10 suspended / error: not ours to press
w = world({ portal: false, site: false, vmState: 'suspended' }); w.check(3);
check('10 suspended: nothing pressed, one high alert naming the state', w.posts.length === 0 && high(w).length === 1 && /suspended/.test(high(w)[0].title));

// 11 secrets: the key and the topic never appear in a mail, a push body, the log or the state
w = world({ portal: false, site: false, vmState: 'stopped', fixAfterMin: 9999 }); w.check(20);
const blob = JSON.stringify(w.mails) + JSON.stringify(w.pushes.map(p => [p.title, p.body])) + (w.props.log || '') + (w.props.state || '');
check('11 the Hostinger key and the topic are never in a mail, push text, log or state', blob.indexOf(KEY) < 0 && blob.indexOf(TOPIC) < 0);
check('11 every attempt is in the log property', /Hostinger start -> accepted/.test(w.props.log || ''));

// 12 testHostinger reads only
w = world({ vmState: 'running' }); const t = typeof w.ctx.testHostinger === 'function' ? w.ctx.testHostinger() : 'no testHostinger';
check('12 testHostinger: says the key is good and the state, presses nothing', /key good/.test(t) && /running/.test(t) && w.posts.length === 0);

// 13 the hour rule survives a recovery
w = world({ portal: false, site: false, vmState: 'stopped', fixAfterMin: 5 }); w.check(5);
w.portal = false; w.site = false; w.vmState = 'stopped'; w.check(3);
check('13 down again within the hour after a start: not pressed again', w.posts.length === 1);

const g = R.filter(r => r[1]).length;
console.log('\nwalk_watcher_s578: ' + g + ' of ' + R.length + ' green');
process.exit(g === R.length ? 0 : 1);
