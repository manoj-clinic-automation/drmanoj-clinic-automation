/**
 * MyOperator.gs — Search Logs API client.
 * Fetches call records for a time window (paginated) and exposes probeApi().
 *
 * WORKING 19-Jun-2026: confirmed against a live success response.
 *   - Parameters (token, from, to, log_from, page_size) are sent in a RAW JSON
 *     BODY of a POST — NOT in the query string. (Their written docs say query
 *     string, but that is wrong; the JSON body is what authenticates. This was
 *     the entire cause of the earlier "This not an authorized request" 400.)
 *   - The response is Elasticsearch-shaped: records live at response.data.hits[],
 *     each call's real fields under "_source". fetchCallsBetween_ UNWRAPS each
 *     hit's "_source" and ENRICHES it with clean derived fields:
 *        phone10          last-10-digit number (from caller_number_raw/caller_number)
 *        duration_seconds integer seconds (parsed from the "HH:MM:SS" string)
 *        direction        'incoming' unless event==2 (event: 1=Incoming, 2=Outgoing)
 *        is_missed        true if status==2 (no one answered) — accurate missed flag
 *   - We send no "filters"/"search_key": we pull every call and classify in code.
 */

/** Read the API token from Script Properties; throw a clear error if missing. */
function getToken_() {
  var raw = PropertiesService.getScriptProperties().getProperty(CFG.TOKEN_PROP);
  if (!raw) {
    throw new Error('No API token. Set Script Property "' + CFG.TOKEN_PROP +
                    '" (Project Settings -> Script Properties) to the FULL Call/Logs ' +
                    'token (the "3f76..." value, 32 characters).');
  }
  var t = String(raw).trim();   // defend against a stray space/newline from pasting
  Logger.log('Token check -> length:%s (should be 32) | starts:%s | ends:%s',
             t.length, t.substring(0, 2), t.substring(Math.max(0, t.length - 2)));
  return t;
}

/** Dig a value out of a JSON object by dotted path, e.g. "data" or "data.hits". */
function getByPath_(obj, path) {
  if (!path) return obj;
  var cur = obj;
  var parts = path.split('.');
  for (var i = 0; i < parts.length; i++) {
    if (cur == null) return null;
    cur = cur[parts[i]];
  }
  return cur;
}

/** Convert "HH:MM:SS" (or "MM:SS", or a number) to an integer number of seconds. */
function hhmmssToSeconds_(v) {
  if (v == null) return 0;
  if (typeof v === 'number') return Math.round(v);
  var p = String(v).split(':');
  if (p.length === 3) return (Number(p[0]) * 3600) + (Number(p[1]) * 60) + Number(p[2]);
  if (p.length === 2) return (Number(p[0]) * 60) + Number(p[1]);
  var n = Number(v);
  return isNaN(n) ? 0 : Math.round(n);
}

/** Reduce any number form to its last 10 digits (India mobile core). */
function last10_(v) {
  var digits = String(v == null ? '' : v).replace(/\D/g, '');
  return digits.length > 10 ? digits.slice(-10) : digits;
}

/**
 * Unwrap one Elasticsearch-style hit to its call record (_source) and add the
 * clean derived fields the pipeline expects. Mutates and returns the _source.
 */
function enrichRecord_(hit) {
  var s = (hit && hit._source) ? hit._source : (hit || {});
  s.duration_seconds = hhmmssToSeconds_(s.duration);
  // Direction comes from "event" (1 = Incoming, 2 = Outgoing). Default to
  // incoming for this inbound IVR unless event explicitly says outgoing.
  s.direction = (String(s.event) === '2') ? 'outgoing' : 'incoming';
  s.is_missed = (String(s.status) === '2');           // status 2 = no one answered
  s.phone10 = last10_(s.caller_number_raw || s.caller_number || '');
  s._hit_user_id = (hit && hit.user_id) ? hit.user_id : (s.allcaller_id || '');
  return s;
}

/**
 * Fetch ALL call records (both directions) between two Date objects.
 * Returns an array of enriched, flat record objects.
 */
function fetchCallsBetween_(startDate, endDate) {
  var token = getToken_();
  var fromUnix = Math.floor(startDate.getTime() / 1000);
  var toUnix = Math.floor(endDate.getTime() / 1000);

  var all = [];
  var offset = 0;

  for (var page = 0; page < CFG.MAX_PAGES; page++) {
    // Search Logs reads every parameter from a RAW JSON BODY (not the query
    // string). Token + time window + pagination all go inside this object.
    var payload = {
      token: token,
      from: String(fromUnix),
      to: String(toUnix),
      log_from: String(offset),
      page_size: String(CFG.PAGE_SIZE)
    };

    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    var resp = UrlFetchApp.fetch(CFG.ENDPOINT, options);
    var code = resp.getResponseCode();
    var body = resp.getContentText();

    if (code !== 200) {
      throw new Error('MyOperator API HTTP ' + code + ' : ' + body.slice(0, 300));
    }

    var json;
    try { json = JSON.parse(body); }
    catch (e) { throw new Error('Non-JSON response: ' + body.slice(0, 300)); }

    if (json.status && String(json.status).toLowerCase() === 'error') {
      throw new Error('API error: ' + JSON.stringify(json).slice(0, 300));
    }

    var batch = getByPath_(json, CFG.DATA_PATH);   // response.data.hits
    if (!Array.isArray(batch)) {
      throw new Error('Could not find a log array at DATA_PATH="' + CFG.DATA_PATH +
                      '". Run probeApi() and adjust CFG.DATA_PATH. Top-level keys: ' +
                      Object.keys(json).join(', '));
    }

    for (var i = 0; i < batch.length; i++) {
      all.push(enrichRecord_(batch[i]));           // unwrap _source + enrich
    }

    if (batch.length < CFG.PAGE_SIZE) break;       // last page
    offset += batch.length;
  }

  return all;
}

/**
 * probeApi() — RUN THIS ONCE to confirm the live pull works.
 * Pulls a tiny sample (last 24h, 5 records) and logs the shape so we can
 * confirm the field names. View output in: Executions / Logs.
 * The "number:" it prints is a real caller number — redact it if you paste it.
 */
function probeApi() {
  var end = new Date();
  var start = new Date(end.getTime() - 24 * 3600 * 1000);

  var savedPage = CFG.PAGE_SIZE;
  CFG.PAGE_SIZE = 5;            // tiny sample
  CFG.MAX_PAGES = 1;
  var records;
  try {
    records = fetchCallsBetween_(start, end);
  } finally {
    CFG.PAGE_SIZE = savedPage;
    CFG.MAX_PAGES = 50;
  }

  Logger.log('Records returned in last 24h sample: %s', records.length);
  if (records.length === 0) {
    Logger.log('No calls in the last 24h — try a wider window or confirm the token.');
    return;
  }
  var first = records[0];
  Logger.log('Field names on a record: %s', Object.keys(first).join(', '));

  // Show what the current FIELD_MAP resolves to, so mismatches are obvious.
  var n = normalizeCall_(first);
  Logger.log('Normalized by current FIELD_MAP -> number:%s | name:%s | durationSec:%s | direction:%s | time:%s',
             n.number, n.name, n.durationSec, n.direction, n.ts);
  Logger.log('If any of those look wrong/blank, fix the candidate lists in FIELD_MAP (Config.gs).');
}