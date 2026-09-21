/**
 * Config.gs — Dr. Manoj Agarwal Clinic · MyOperator call digest + monitor (Part A)
 * ---------------------------------------------------------------------------
 * Everything you might tune lives here. No secrets in this file: the API token
 * is read from Script Properties (MYOP_TOKEN). The output Sheet is identified
 * by Script Property SHEET_ID.
 *
 * WORKING 19-Jun-2026 — confirmed against a live success response:
 *   - ENDPOINT is .../search. Parameters go in a RAW JSON BODY of a POST
 *     (NOT the query string). Records arrive at data.hits[]; each call's fields
 *     are under each hit's "_source" (MyOperator.gs unwraps + enriches them).
 *   - FIELD_MAP below is locked to the real field names from that response.
 */

var CFG = {

  // --- Secrets / IDs (set in Project Settings -> Script Properties) ---------
  TOKEN_PROP: 'MYOP_TOKEN',     // the Call/Logs API token (the "3f76..." value)
  SHEET_ID_PROP: 'SHEET_ID',    // the Google Sheet to write into

  // --- MyOperator Search Logs API ------------------------------------------
  ENDPOINT: 'https://developers.myoperator.co/search',
  REQUEST_AS_JSON: true,        // params are sent in a JSON body (see MyOperator.gs)
  DATA_PATH: 'data.hits',       // response.data.hits — the array of call records
  PAGE_SIZE: 100,               // API max is 100
  MAX_PAGES: 50,                // safety stop for pagination

  // --- Business logic -------------------------------------------------------
  SHORT_CALL_SECONDS: 30,       // legacy; superseded by status==2 (see Netting.gs)
  HIGH_INTENT_ATTEMPTS: 3,      // this many missed attempts from one number = priority
  RESOLUTION_MUST_BE_AFTER: false,

  // Working window (local time) — used for the "after-hours" flag and the
  // monitor's busiest-hours range.
  WORKDAY_START_HOUR: 8,
  WORKDAY_END_HOUR: 21,         // 9 pm

  // --- Trigger schedule -----------------------------------------------------
  INTRADAY_HOURS: [8, 10, 12, 14, 16, 18, 20], // live refresh of callbacks + monitor
  SUNDAY_LAST_HOUR: 14,         // Sun 08:00 -> 14:00 only
  MORNING_REPORT_HOUR: 7,       // ~07:30 next-morning full prior-day report

  // --- Summary email --------------------------------------------------------
  // Who receives the 11am / 3pm / 7pm summary email. Comma-separate for more
  // than one recipient, e.g. 'drmka.ortho@gmail.com, assistant@example.com'.
  // The email is SENT FROM whichever Google account runs this script.
  EMAIL_TO: 'drmka.ortho@gmail.com',
  EMAIL_HOURS: [11, 15, 19],    // 11 AM, 3 PM, 7 PM (local)

  // --- Sheet (tab) names ----------------------------------------------------
  TAB_CALLBACKS: 'Callbacks_Today',
  TAB_REPORT_LOG: 'Daily_Report_Log',
  TAB_SUMMARY: 'Daily_Summary',
  TAB_ARCHIVE: 'Callbacks_Archive',
  TAB_MONITOR: 'Daily_Monitor',

  CALLBACK_HEADERS: [
    'Auto-Status', 'Priority', 'Phone', 'Caller Name', 'Attempts',
    'First Call', 'Last Call', 'After-Hours', 'Staff Status', 'Staff Notes'
  ],
  STAFF_COL_COUNT: 2            // last N columns are staff-owned, preserved on refresh
};

/**
 * FIELD_MAP — how to read one (already-unwrapped + enriched) call record.
 * Each entry is a list of CANDIDATE key names; the first present one is used.
 * LOCKED 19-Jun-2026 to the live response field names; derived fields first.
 *   - NUMBER   : phone10 (clean last-10), then raw/e164 forms.
 *   - NAME     : caller name is not in the record (PHI-clean) — stays blank.
 *   - DURATION : duration_seconds (parsed from "HH:MM:SS" by MyOperator.gs).
 *   - DIRECTION: direction ('incoming'/'outgoing', derived from event).
 *   - STATUS   : status (1 = answered, 2 = missed).
 *   - TIME     : start_time (UTC unix seconds).
 */
var FIELD_MAP = {
  NUMBER:    ['phone10', 'caller_number_raw', 'caller_number', 'number', 'from'],
  NAME:      ['caller_name', 'name', 'contact_name', 'customer_name'],
  DURATION:  ['duration_seconds', 'duration', 'talk_duration', 'seconds'],
  DIRECTION: ['direction', 'type', 'call_type', 'call_direction'],
  STATUS:    ['status', 'call_status', 'disposition'],
  TIME:      ['start_time', 'synced_time', '_ms', 'time', 'date']
};