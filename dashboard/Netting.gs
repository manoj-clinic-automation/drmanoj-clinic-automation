/**
 * Netting.gs — turns raw call records into the net-missed callback list.
 *
 * Rules (UPGRADED 19-Jun-2026 to the accurate status signal; supersedes the
 * old "duration < 30s" proxy in MASTER_HANDOFF §10.1):
 *   - An INCOMING call is a missed-candidate if NO ONE answered it
 *     (status == 2  ->  is_missed). We no longer guess from talk duration: the
 *     record's "duration" includes ring time, so a genuine short connected call
 *     is NOT a miss, and a long-ringing abandon IS — status gets both right.
 *   - A number is RESOLVED (dropped from the list) if it had any CONNECTED call
 *     (status == 1, someone answered) that day, in EITHER direction — i.e. the
 *     patient got through, or the front desk called back and connected.
 *   - Repeat callers collapse to one row with an attempt count; >= HIGH_INTENT_ATTEMPTS
 *     is flagged priority.
 */

/** Pick the first present, non-empty key from a candidate list. */
function pick_(obj, keys) {
  for (var i = 0; i < keys.length; i++) {
    var v = obj[keys[i]];
    if (v !== undefined && v !== null && String(v).trim() !== '') return v;
  }
  return '';
}

/** Normalise an Indian phone number to its last 10 digits for matching. */
function normNumber_(raw) {
  var digits = String(raw || '').replace(/\D/g, '');
  if (digits.length > 10) digits = digits.slice(-10); // strip 91 / 0 / +91
  return digits;
}

/** Duration to seconds. Accepts a number, "ss", "mm:ss", or "hh:mm:ss". */
function toSeconds_(v) {
  if (v === '' || v === null || v === undefined) return 0;
  if (typeof v === 'number') return Math.round(v);
  var s = String(v).trim();
  if (/^\d+$/.test(s)) return parseInt(s, 10);
  if (s.indexOf(':') >= 0) {
    var parts = s.split(':').map(function (p) { return parseInt(p, 10) || 0; });
    while (parts.length < 3) parts.unshift(0);
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }
  var n = parseInt(s, 10);
  return isNaN(n) ? 0 : n;
}

/** Timestamp to a Date. Accepts unix seconds, unix ms, or a parseable string. */
function toDate_(v) {
  if (v === '' || v === null || v === undefined) return null;
  if (typeof v === 'number' || /^\d+$/.test(String(v))) {
    var num = Number(v);
    if (num < 1e12) num *= 1000; // seconds -> ms
    return new Date(num);
  }
  var d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

/** Is this an incoming call? Tolerant of various encodings. */
function isIncoming_(directionVal, statusVal) {
  var d = String(directionVal).toLowerCase();
  // Check "out" FIRST — note "outgoing" itself contains the substring "in".
  if (d.indexOf('out') >= 0) return false; // "outgoing", "outbound", "out"
  if (d.indexOf('in') >= 0) return true;   // "incoming", "inbound", "in"
  // Fall back to status wording if direction was blank/numeric.
  var s = String(statusVal).toLowerCase();
  if (s.indexOf('miss') >= 0 || s.indexOf('incom') >= 0) return true;
  return false; // default: treat unknown as not-incoming so we don't over-flag
}

/**
 * Was this call MISSED (no one answered)? The authoritative signal is status==2.
 * We also honour the boolean is_missed that MyOperator.gs adds during enrichment.
 */
function isMissed_(raw) {
  if (raw.is_missed === true) return true;
  return String(pick_(raw, FIELD_MAP.STATUS)) === '2';
}

/** Normalise one raw record into the fields the engine needs. */
function normalizeCall_(raw) {
  var dir = pick_(raw, FIELD_MAP.DIRECTION);
  var status = pick_(raw, FIELD_MAP.STATUS);
  return {
    number: normNumber_(pick_(raw, FIELD_MAP.NUMBER)),
    name: String(pick_(raw, FIELD_MAP.NAME) || '').trim(),
    durationSec: toSeconds_(pick_(raw, FIELD_MAP.DURATION)),
    incoming: isIncoming_(dir, status),
    missed: isMissed_(raw),                 // status==2 -> no one answered
    direction: String(dir || '').trim(),
    ts: toDate_(pick_(raw, FIELD_MAP.TIME))
  };
}

/** Local-time helpers (script timezone is Asia/Kolkata via appsscript.json). */
function fmtTime_(d) {
  if (!d) return '';
  return Utilities.formatDate(d, Session.getScriptTimeZone(), 'dd-MMM HH:mm');
}
function isAfterHours_(d) {
  if (!d) return false;
  var h = d.getHours();
  return h < CFG.WORKDAY_START_HOUR || h >= CFG.WORKDAY_END_HOUR;
}

/**
 * Core engine. Input: raw records for ONE day. Output:
 *   { entries: [...], stats: {...} }
 * entries are unresolved net-missed numbers, sorted priority-first.
 */
function computeNetMissed_(rawRecords) {
  var groups = {}; // normNumber -> {calls:[normalized]}
  var totalCalls = 0, incomingCount = 0;

  rawRecords.forEach(function (raw) {
    var c = normalizeCall_(raw);
    if (!c.number) return;        // skip unusable rows
    totalCalls++;
    if (c.incoming) incomingCount++;
    (groups[c.number] || (groups[c.number] = { calls: [] })).calls.push(c);
  });

  var entries = [];
  var resolvedCount = 0;

  Object.keys(groups).forEach(function (num) {
    var calls = groups[num].calls.sort(function (a, b) {
      return (a.ts ? a.ts.getTime() : 0) - (b.ts ? b.ts.getTime() : 0);
    });

    // Missed-candidate legs: incoming calls that no one answered (status==2).
    var missedIncoming = calls.filter(function (c) {
      return c.incoming && c.missed;
    });
    if (missedIncoming.length === 0) return; // never a missed-candidate

    // Resolution: any CONNECTED call (status==1, someone answered), either
    // direction — patient got through, or the desk called back and connected.
    var firstMissTs = missedIncoming[0].ts ? missedIncoming[0].ts.getTime() : 0;
    var resolved = calls.some(function (c) {
      if (c.missed) return false;            // not a connect
      if (CFG.RESOLUTION_MUST_BE_AFTER && c.ts && c.ts.getTime() < firstMissTs) return false;
      return true;
    });
    if (resolved) { resolvedCount++; return; }

    var attempts = missedIncoming.length;
    var first = missedIncoming[0];
    var last = missedIncoming[missedIncoming.length - 1];
    var name = '';
    for (var i = 0; i < calls.length; i++) { if (calls[i].name) { name = calls[i].name; break; } }

    entries.push({
      number: num,
      name: name,
      attempts: attempts,
      priority: attempts >= CFG.HIGH_INTENT_ATTEMPTS,
      firstTs: first.ts,
      lastTs: last.ts,
      attemptTimes: missedIncoming.map(function (c) { return c.ts; }), // every attempt, in order
      afterHours: isAfterHours_(last.ts)
    });
  });

  // Priority first, then most attempts, then most recent.
  entries.sort(function (a, b) {
    if (a.priority !== b.priority) return a.priority ? -1 : 1;
    if (a.attempts !== b.attempts) return b.attempts - a.attempts;
    var at = a.lastTs ? a.lastTs.getTime() : 0;
    var bt = b.lastTs ? b.lastTs.getTime() : 0;
    return bt - at;
  });

  return {
    entries: entries,
    stats: {
      totalCalls: totalCalls,
      incomingCount: incomingCount,
      netMissed: entries.length,
      resolved: resolvedCount
    }
  };
}
