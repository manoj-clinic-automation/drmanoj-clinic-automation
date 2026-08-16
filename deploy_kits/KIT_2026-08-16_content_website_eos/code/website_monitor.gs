/**
 * Dr. Manoj Agarwal — Website Monitor  (Tier 2 of the estate monitoring system)
 * Standalone Google Apps Script (not container-bound), per house rule for pipeline automations.
 *
 * WHAT IT DOES (free, Google-native, no PHI):
 *   1. Uptime / HTTP status for key pages + the co-located lab
 *   2. Content assertions  — must-contain (page not silently broken)
 *                          — must-NOT-contain (guards the branding rules: alerts if
 *                            "Bareilly Orthopaedic Centre" / "Bareilly Arthritis Centre" reappear)
 *   3. Redirect / short-link resolution (incl. drmanojagarwal.in -> .com staying alive)
 *   4. Emails an alert on any failure + logs every run to a Google Sheet
 *
 * WHAT IT DOES NOT DO (use external UptimeRobot — Tier 1):
 *   SSL certificate expiry  +  domain-registration expiry
 *   (Apps Script/UrlFetchApp cannot read cert or WHOIS expiry reliably.)
 *
 * SETUP (see Runbook):
 *   1. Create a blank Google Sheet; copy its ID from the URL; paste into LOG_SHEET_ID.
 *   2. Create a standalone Apps Script project; paste this file.
 *   3. Set ALERT_EMAIL.
 *   4. Run setup() once and authorize.
 *   5. Add a time-driven trigger on runMonitor() (e.g. every 30 min or hourly).
 */

// ---------- CONFIG ----------
const ALERT_EMAIL   = 'drmka.ortho@gmail.com';         // where alerts go
const LOG_SHEET_ID  = 'PASTE_YOUR_GOOGLE_SHEET_ID_HERE'; // blank sheet you create
const LOG_TAB_NAME  = 'Monitor Log';

// Pages to check, with per-page content assertions.
const CHECKS = [
  {
    url: 'https://drmanojagarwal.com/',
    mustContain:    ['Dr. Manoj Agarwal', '9358008080'],
    mustNotContain: ['Bareilly Orthopaedic Centre', 'Bareilly Arthritis Centre']
  },
  {
    url: 'https://drmanojagarwal.com/about-us/',
    mustContain:    ['Dr. Manoj Agarwal', 'GSVM'],
    mustNotContain: ['Bareilly Orthopaedic Centre', 'Bareilly Arthritis Centre']
  },
  {
    url: 'https://drmanojagarwal.com/contact-us/',
    mustContain:    ['9358008080'],
    mustNotContain: []
  },
  {
    url: 'https://nkpathology.com/',
    mustContain:    ['NK'],
    mustNotContain: []
  }
  // add more pages as they go live (e.g. new blog URLs)
];

// Redirects / short-links that must keep resolving (status < 400 after following redirects).
const REDIRECTS_TO_CHECK = [
  'https://drmanojagarwal.in/',   // intended retirement redirect -> .com; alert if it breaks
  'https://map.dr-manoj.in'
  // add 'https://book.dr-manoj.in' etc. as needed
];
// ---------- END CONFIG ----------


function runMonitor() {
  const failures = [];
  const now = new Date();

  CHECKS.forEach(function (check) {
    try {
      const res  = UrlFetchApp.fetch(check.url, { muteHttpExceptions: true, followRedirects: true });
      const code = res.getResponseCode();
      const body = res.getContentText();

      if (code >= 400) {
        failures.push(check.url + '  ->  DOWN (HTTP ' + code + ')');
        logRow_(now, check.url, 'DOWN', 'HTTP ' + code);
        return;
      }
      const missing   = (check.mustContain    || []).filter(function (s) { return body.indexOf(s) === -1; });
      const forbidden = (check.mustNotContain || []).filter(function (s) { return body.indexOf(s) !== -1; });

      if (missing.length || forbidden.length) {
        const parts = [];
        if (missing.length)   parts.push('MISSING: ' + missing.join(' | '));
        if (forbidden.length) parts.push('SHOULD-NOT-BE-PRESENT: ' + forbidden.join(' | '));
        const detail = parts.join('   ;   ');
        failures.push(check.url + '  ->  CONTENT  (' + detail + ')');
        logRow_(now, check.url, 'CONTENT', detail);
      } else {
        logRow_(now, check.url, 'OK', 'HTTP ' + code);
      }
    } catch (e) {
      failures.push(check.url + '  ->  ERROR (' + e.message + ')');
      logRow_(now, check.url, 'ERROR', e.message);
    }
  });

  REDIRECTS_TO_CHECK.forEach(function (url) {
    try {
      const res  = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true });
      const code = res.getResponseCode();
      if (code >= 400) {
        failures.push(url + '  ->  REDIRECT FAIL (HTTP ' + code + ')');
        logRow_(now, url, 'REDIRECT-FAIL', 'HTTP ' + code);
      } else {
        logRow_(now, url, 'OK', 'resolved HTTP ' + code);
      }
    } catch (e) {
      failures.push(url + '  ->  ERROR (' + e.message + ')');
      logRow_(now, url, 'ERROR', e.message);
    }
  });

  if (failures.length) {
    MailApp.sendEmail({
      to: ALERT_EMAIL,
      subject: 'WEBSITE MONITOR ALERT - ' + failures.length + ' issue(s)',
      body: 'The website monitor found the following issue(s) at ' + now + ':\n\n' +
            failures.join('\n') +
            '\n\nFull history is in the "' + LOG_TAB_NAME + '" sheet.'
    });
  }
}

// Optional: run manually to scan a page's internal .com links for 404s.
function scanLinks(pageUrl) {
  pageUrl = pageUrl || 'https://drmanojagarwal.com/';
  const body = UrlFetchApp.fetch(pageUrl, { muteHttpExceptions: true }).getContentText();
  const re = /href="(https:\/\/drmanojagarwal\.com[^"]*)"/g;
  const seen = {}, broken = [];
  let m;
  while ((m = re.exec(body)) !== null) {
    const link = m[1];
    if (seen[link]) continue;
    seen[link] = true;
    try {
      const code = UrlFetchApp.fetch(link, { muteHttpExceptions: true, followRedirects: true }).getResponseCode();
      if (code >= 400) broken.push(link + '  ->  HTTP ' + code);
    } catch (e) {
      broken.push(link + '  ->  ERROR ' + e.message);
    }
    Utilities.sleep(200); // be gentle
  }
  if (broken.length) {
    MailApp.sendEmail(ALERT_EMAIL, 'BROKEN LINKS on ' + pageUrl, broken.join('\n'));
  }
  logRow_(new Date(), pageUrl, broken.length ? 'BROKEN-LINKS' : 'LINKS-OK', broken.join(' | ') || 'all links OK');
  return broken;
}

function logRow_(ts, url, status, detail) {
  getLogSheet_().appendRow([ts, url, status, detail]);
}

function getLogSheet_() {
  const ss = SpreadsheetApp.openById(LOG_SHEET_ID);
  let sh = ss.getSheetByName(LOG_TAB_NAME);
  if (!sh) {
    sh = ss.insertSheet(LOG_TAB_NAME);
    sh.appendRow(['Timestamp', 'URL', 'Status', 'Detail']);
  }
  return sh;
}

// Run once after pasting the code + setting config, to create the log tab and do a first pass.
function setup() {
  getLogSheet_();
  runMonitor();
}
