#!/usr/bin/env python3
# make_gas_s364.py -- the Tracker side of S364: two anchored edits on the LIVE Apps Script bytes
# (GAS_CURRENT/ClinicCallbackTracker, photographed 21-Sep-2026 from the editor, sha256 matched).
# Usage: python make_gas_s364.py <in dir> <out dir>
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
FROM = {"WebApp.gs": "989b7de917a99a93", "Dashboard.html": "440ca0b03ce0309b"}   # sha256[:16]
T = {}
for f, h in FROM.items():
    t = open(os.path.join(src, f), encoding="utf-8", newline="").read()
    assert hashlib.sha256(t.encode()).hexdigest()[:16] == h, f + " is not the live photograph"
    T[f] = t

def once(f, old, new, label):
    assert T[f].count(old) == 1, "anchor not unique: " + label
    T[f] = T[f].replace(old, new)

once("WebApp.gs",
"""var CALL_URL    = 'https://followup.dr-manoj.in/call';      // OBD click-to-call relay (NOT a secret)
""",
"""var CALL_URL    = 'https://followup.dr-manoj.in/call';      // OBD click-to-call relay (NOT a secret)
// S364 (21-Sep-2026): opened from the Clinic app, already signed in. The portal's pass is
// checked by the portal itself, server to server -- no secret is kept here for it.
var SSO_REDEEM_URL = 'https://followup.dr-manoj.in/portal/sso/tracker-redeem';   // NOT a secret
""", "const")

once("WebApp.gs",
"""/** Serve the dashboard page (access is enforced inside the page + on every data call). */
function doGet(e) {""",
"""/**
 * S364_TRACKER_SSO (21-Sep-2026) -- sign in once, through the Clinic app.
 * The Call Tracker tile in the Clinic app opens this page as .../exec?sso=<pass>. The pass is
 * the portal's (120 seconds, signed by the portal); we do not judge it here -- we hand it back
 * to the portal (SSO_REDEEM_URL), which answers who it belongs to. That person's own agent key
 * (AKEY_<ext>, or DASH_KEY for the doctor) is returned to the page, which then signs in exactly
 * as if the key had been typed. Every failure returns {ok:false} and the page falls back to the
 * old key login. A pass is used once: remembered for 10 minutes, refused a second time.
 * Portal user -> agent extension: SSO_USER_EXT below, or the Script Property SSO_USER_EXT
 * (JSON, e.g. {"shavez":"11"}) which wins when it is set. Nobody not on the map is signed in.
 */
var SSO_USER_EXT = { manoj: '10', shavez: '11', shivani: '12', bhati: '13', alisha: '14', darpan: '15' };

function ssoUserExt_() {
  try {
    var raw = (PropertiesService.getScriptProperties().getProperty('SSO_USER_EXT') || '').trim();
    if (raw) { var m = JSON.parse(raw); if (m && typeof m === 'object') return m; }
  } catch (e) {}
  return SSO_USER_EXT;
}

function ssoExchange(pass) {
  try {
    pass = String(pass || '').trim();
    if (!pass || pass.length > 600 || !/^[A-Za-z0-9_\\-]+\\.[A-Za-z0-9_\\-]+$/.test(pass)) return { ok: false };
    var seenKey = 'sso_' + Utilities.base64EncodeWebSafe(
      Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, pass)).slice(0, 40);
    var cache = CacheService.getScriptCache();
    if (cache.get(seenKey)) return { ok: false, reason: 'used' };
    cache.put(seenKey, '1', 600);
    var resp = UrlFetchApp.fetch(SSO_REDEEM_URL, {
      method: 'post', payload: { p: pass }, muteHttpExceptions: true, followRedirects: false
    });
    if (resp.getResponseCode() !== 200) return { ok: false, reason: 'portal ' + resp.getResponseCode() };
    var who = {};
    try { who = JSON.parse(resp.getContentText()); } catch (e) { who = {}; }
    if (!who || who.ok !== true || !who.user) return { ok: false };
    var ext = String(ssoUserExt_()[String(who.user).toLowerCase()] || '');
    if (!ext) return { ok: false, reason: 'not linked' };
    var sp = PropertiesService.getScriptProperties();
    var key = '';
    if (ext === '10') {
      if (who.role !== 'doctor') return { ok: false, reason: 'not linked' };
      key = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
    } else {
      key = (sp.getProperty('AKEY_' + ext) || '').trim();
    }
    if (!key || dashRole_(key) === 'none') return { ok: false, reason: 'not linked' };
    return { ok: true, key: key };
  } catch (err) {
    return { ok: false };
  }
}

/** Serve the dashboard page (access is enforced inside the page + on every data call). */
function doGet(e) {""", "ssoExchange")

once("Dashboard.html",
"""  google.script.url.getLocation(function(loc){
    var signedOut=false; try{ signedOut=(localStorage.getItem('clinicSignedOut')==='1'); }catch(e){}
    if(signedOut){ showLogin(false); return; }  // F-11: after Sign out, ?k= and the stored key are both ignored
    var k=''; try{ k=(loc&&loc.parameter&&loc.parameter.k)?String(loc.parameter.k):''; }catch(e){}
    if(!k){ try{ k=localStorage.getItem('clinicDashKey')||''; }catch(e){} }
    if(k) tryKey(k, false); else showLogin(false);
  });""",
"""  google.script.url.getLocation(function(loc){
    function keyLogin(){
      var signedOut=false; try{ signedOut=(localStorage.getItem('clinicSignedOut')==='1'); }catch(e){}
      if(signedOut){ showLogin(false); return; }  // F-11: after Sign out, ?k= and the stored key are both ignored
      var k=''; try{ k=(loc&&loc.parameter&&loc.parameter.k)?String(loc.parameter.k):''; }catch(e){}
      if(!k){ try{ k=localStorage.getItem('clinicDashKey')||''; }catch(e){} }
      if(k) tryKey(k, false); else showLogin(false);
    }
    // S364: opened from the Clinic app -> signed in already. A fresh tap there is a real sign-in,
    // so it wins over an earlier Sign out here; a used or stale pass falls back to the key login.
    var sso=''; try{ sso=(loc&&loc.parameter&&loc.parameter.sso)?String(loc.parameter.sso):''; }catch(e){}
    if(!sso){ keyLogin(); return; }
    google.script.run
      .withSuccessHandler(function(r){ if(r&&r.ok&&r.key) tryKey(String(r.key), false); else keyLogin(); })
      .withFailureHandler(function(){ keyLogin(); })
      .ssoExchange(sso);
  });""", "page")

os.makedirs(out, exist_ok=True)
for f, t in T.items():
    open(os.path.join(out, f), "w", encoding="utf-8", newline="").write(t)
    print(f, "sha256", hashlib.sha256(t.encode()).hexdigest())
