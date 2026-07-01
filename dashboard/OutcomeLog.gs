/* ===========================================================================
 * OutcomeLog.gs — STAFF OUTCOME LOG (read-only)  ·  added Session 25
 * ---------------------------------------------------------------------------
 * Serves the "Staff outcome log" section of the Console: a read-only, TODAY-only
 * view of every outcome staff have logged, drawn from the Followup_Outcomes tab.
 *
 * DESIGN (matches CallConsole.gs, D34):
 *   - This is a STANDALONE file. It does NOT modify WebApp.gs.
 *   - It only READS. It never writes to Followup_Outcomes (that tab stays
 *     write-once from the outcome forms in WebApp.gs).
 *   - It reuses core helpers already defined in WebApp.gs (same project =
 *     shared global namespace): dashRole_(), fuSheet_(), fuReadObjects_(),
 *     dateVal_(). It does NOT depend on any WebApp label maps — its own
 *     label table lives below, so it can't drift/break if WebApp changes.
 *
 * ACCESS: FULL (doctor) key ONLY. Staff never see this.
 *
 * NOTE (scale, future): reads the whole Followup_Outcomes tab and keeps only
 *   today's rows. Fine for now (a few hundred rows/day). When the tab grows to
 *   many thousands of rows, switch to reading only the last N rows.
 * ========================================================================= */

var OL_TAB = 'Followup_Outcomes';

/* Friendly labels for the outcome codes stored in the log. Covers the
 * follow-up codes and the incoming-call codes. Anything not listed is shown
 * as a humanised version of the raw code (see OL_label_). */
var OL_LABELS = {
  coming: 'Coming / will visit',
  out_of_town: 'Out of town',
  on_medication: 'On medication',
  cant_communicate: "Couldn't communicate",
  dikha_chuke: 'Already visited (dikha chuke)',
  problem: 'Problem / needs attention',
  close_followup: 'Close follow-up · complete',
  not_interested: 'Not interested',
  treatment_elsewhere: 'Treatment elsewhere',
  // incoming-call outcomes (both prefixed and plain, to be safe)
  in_resolved_on_call: 'Incoming · resolved on call',
  resolved_on_call: 'Resolved on call',
  in_appointment_booked: 'Incoming · appointment booked',
  appointment_booked: 'Appointment booked',
  in_info_given: 'Incoming · info given',
  in_info_given_will_act: 'Incoming · info given, will act',
  info_given_will_act: 'Info given, will act',
  in_needs_callback: 'Incoming · needs callback',
  needs_callback: 'Needs callback',
  in_escalated: 'Incoming · escalated to doctor',
  escalated: 'Escalated to doctor',
  in_cant_communicate: "Incoming · couldn't communicate",
  in_will_come: 'Incoming · will come / considering',
  will_come: 'Will come / considering',
  in_enquiry_only: 'Incoming · enquiry only',
  enquiry_only: 'Info given / enquiry only',
  in_no_action: 'Incoming · no action',
  no_action: 'No action / not relevant',
  in_not_relevant: 'Incoming · not relevant'
};

/** Turn an outcome code into a readable label. Unknown codes are humanised. */
function OL_label_(code) {
  code = String(code || '').trim().toLowerCase();
  if (!code) return '—';
  if (OL_LABELS[code]) return OL_LABELS[code];
  return code.replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
}

/**
 * getOutcomeLog(key) — DOCTOR ONLY. Returns TODAY's logged outcomes.
 * Return shape (all read-only):
 *   { ok:true, count, dateLabel, sheetUrl,
 *     tally: [ { by, n }, ... ],           // per-staff counts, busiest first
 *     rows:  [ { t, time, outcome, patient, last4, by, source }, ... ] }  // newest first
 * On any problem: { error: '...' }.
 */
function getOutcomeLog(key) {
  try {
    if (dashRole_(key) !== 'full') return { error: 'Not authorized.' };

    var ss = fuSheet_();
    if (!ss) return { error: 'Sheet not configured.' };

    var tz = Session.getScriptTimeZone();
    var todayStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');

    var objs;
    try { objs = fuReadObjects_(ss, OL_TAB) || []; }
    catch (e) { return { error: 'Could not read the outcome log tab.' }; }

    var rows = [], byStaff = {};
    for (var i = 0; i < objs.length; i++) {
      var o = objs[i];
      var t = dateVal_(o['when']);
      if (!t) continue;
      if (Utilities.formatDate(new Date(t), tz, 'yyyy-MM-dd') !== todayStr) continue;

      var by = String(o['handled by'] || '').trim() || 'Unknown';
      var mob = String(o['mobile'] || '').replace(/\D/g, '');
      var src = String(o['source'] || '').trim().toLowerCase();

      rows.push({
        t: t,
        time: Utilities.formatDate(new Date(t), tz, 'h:mm a'),
        outcome: OL_label_(o['outcome']),
        patient: String(o['patient'] || '').trim(),
        last4: mob ? mob.slice(-4) : '',        // PHI: last-4 only
        by: by,
        source: (src.indexOf('incoming') >= 0 || src === 'in') ? 'in' : ''
      });
      byStaff[by] = (byStaff[by] || 0) + 1;
    }

    rows.sort(function (a, b) { return b.t - a.t; });   // newest first

    var tally = Object.keys(byStaff).map(function (k) { return { by: k, n: byStaff[k] }; })
                  .sort(function (a, b) { return b.n - a.n; });

    // deep-link straight to the Followup_Outcomes tab
    var url = ss.getUrl();
    var sh = ss.getSheetByName(OL_TAB);
    if (sh) url = url + '#gid=' + sh.getSheetId();

    return {
      ok: true,
      count: rows.length,
      dateLabel: Utilities.formatDate(new Date(), tz, 'EEE d MMM'),
      sheetUrl: url,
      tally: tally,
      rows: rows
    };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

/** OL_SELFTEST — run from the editor to sanity-check without the UI. */
function OL_SELFTEST() {
  var ss = fuSheet_();
  Logger.log('sheet: ' + (ss ? ss.getName() : 'NONE'));
  var objs = ss ? (fuReadObjects_(ss, OL_TAB) || []) : [];
  Logger.log('total rows in ' + OL_TAB + ': ' + objs.length);
  if (objs.length) Logger.log('headers seen: ' + Object.keys(objs[0]).join(', '));
}
