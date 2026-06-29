# Clinic Callback Tracker — Structured Troubleshooter (v1.1)
**Use with: Callback_Dashboard_KB_v1.md.** Built 29 Jun 2026 from the live 11-file project.
Rule of the road: **work top-down, do ONE step, read the result, then branch.** Never skip to a fix.

---

## THE GOLDEN FORK (always start here)
Before anything, classify the symptom into ONE of two worlds (see KB §2):

- **WORLD A — Reports/emails/Sheet tabs wrong or stale** → it's the **triggers** (Main.gs / CallField.gs.gs).
- **WORLD B — the live web dashboard wrong** (tiles/dropdowns/buttons) → it's **Path B** (WebApp.gs → Dashboard.html), and **triggers are irrelevant.**

> ❗The most expensive mistake (made in Session 16): treating a WORLD B dashboard symptom as a WORLD A trigger problem. Redeploying / rolling back / chasing `rebuildCallFeed` cannot fix a live-dashboard data issue. Classify first.

---

## DECISION TREE

### Q1. Is the problem the live web DASHBOARD, or the EMAILS / Sheet tabs?
- **Dashboard** → go to **B-FLOW**.
- **Emails or Sheet tabs (Call_Feed, Callbacks_Today, Daily_Monitor)** → go to **A-FLOW**.

---

## B-FLOW — Live dashboard problems

### B1. Does the page load at all?
- **Blank / won't load / "page not found"** → the deployment or URL is wrong.
  - Fix: confirm the URL ends with `?k=DASH_KEY`. Confirm a deployment exists (Deploy → Manage deployments). If needed, redeploy: **edit existing → New version** (never New deployment).
- **Page loads** → B2.

### B2. Does it show "Not authorized / please sign in again"?
- **Yes** → the **access key** is the problem.
  - Run **`keyInfo`** (WebApp.gs) → confirms whether DASH_KEY/SECRET_KEY/STAFF_KEY are set and free of stray spaces.
  - Confirm the `?k=` in your URL matches DASH_KEY exactly.
- **No (tiles render)** → B3.

### B3. Tiles show numbers, but EXPANDABLES (dropdowns) are EMPTY — no error.
This is the Session-16 symptom. Localise it with TWO read-only probes, in order.

**B3.1 — Is the API returning calls?** Run **`probeApi`** (MyOperator.gs). Read the log:
- `Records returned in last 24h sample: 0` → the API/token is the cause → go to **API-FIX**.
- `Records returned: N (N>0)` (e.g. 5) → API is healthy → B3.2. *(This was the case on 29 Jun.)*

**B3.2 — What does the dashboard actually RETURN?** Paste `probeDashboardData_` (below) into `Probe.gs.gs`, Run it, read the `COUNTS ->` line:
- **All counts 0** (`pending:0 … agents:0`) but probeApi showed calls → the emptiness is created **inside `computeDashboard_`** → go to **COMPUTE-FIX**.
- **Counts are non-zero** (e.g. `pending:6 agents:4 recentWA:11`) → the **server is fine; the PAGE isn't rendering** → go to **RENDER-FIX**.
- **`RETURNED ERROR: …`** → read the message → go to **COMPUTE-FIX** (a helper threw; the message names which).

### B4. Tiles AND dropdowns empty, but it's early morning (before ~9–10 AM IST)?
- Likely **normal** — the dashboard reads TODAY only. Confirm with `probeApi` (will still show last-24h calls). If `testIntradayNow` and the live API both show today's calls and only the *page* is empty, treat as B3.2.

### B5. A specific section empty (only WhatsApp, or only Team), rest fine?
- **Only Clinic Team empty** → expected if today had only missed calls (agent names come from CONNECTED calls' `log_details`). Confirm there were connected calls today; if there were and it's still empty, the `Agents`/`log_details` mapping is suspect → COMPUTE-FIX, inspect `callAgentInfo_`.
- **Only WhatsApp empty** → check the `WA_Inbox` tab exists and has rows (it did on 29 Jun). If rows exist but section empty → RENDER-FIX scoped to `recentWA`.
- **Only Callbacks empty** → check `Callbacks_Today` tab + `computeNetMissed_`.

### B6. Buttons broken (Call / WhatsApp reply / recording won't play)?
- Call button → VPS `/call` relay + agent key; test `triggerCall`. WhatsApp reply → `sendReply` + WA send token. Recording → `getRecordingAudio` / `probeRecordingField`. (Separate subsystems; out of scope for empty-dropdown issue.)

---

## A-FLOW — Emails / Sheet-tab problems

### A1. Which is stale?
- **Summary emails not arriving** → trigger `runSummaryEmail` (Main.gs), hours in `CFG.EMAIL_HOURS`. Check Triggers screen: does it have recent runs? Run `testSummaryEmailNow`.
- **Callbacks_Today / Daily_Monitor stale** → trigger `runIntradayDigest`. Run `testIntradayNow`.
- **Morning report missing** → `runMorningReport`. Run `testMorningNow`.
- **Call_Feed tab stale** (Follow-Up Tracker complains) → `rebuildCallFeed` (CallField.gs.gs). Run `testCallFeedNow`. *(This is the ONLY thing rebuildCallFeed affects — never the dashboard.)*

### A2. A trigger stopped firing (no recent run, 0% errors)?
- Google occasionally drops a time-trigger. Re-install: run **`setupTriggers`** (re-creates all report triggers cleanly) and/or **`installCallFeedTrigger`** (Call_Feed). Both remove old copies first, so no doubling.
- If a trigger row names a function that no longer exists → it's a leftover; `removeTriggers` clears all, then `setupTriggers` rebuilds the correct set.

### A3. A trigger run is RED (failing)?
- Open the execution → read the error.
  - "No API token…" → Script Property `MYOP_TOKEN` missing → API-FIX.
  - "MyOperator API HTTP 4xx/5xx" → API-FIX.
  - "No spreadsheet…" → Script Property `SHEET_ID` missing/wrong.

---

## FIX BLOCKS

### API-FIX (the live call fetch is failing or returning 0)
1. Run `probeApi`. Read the token line: length should be **32**, starts `3f`.
   - Length 0 / "No API token" → set Script Property `MYOP_TOKEN` to the 32-char Call/Logs token (from MyOperator panel → Calling APIs). Re-run `probeApi`.
   - HTTP error in log → note code: 400/401/403 = token/auth (params must be JSON **body**, not query — already correct in code); 5xx = MyOperator side.
   - Records = 0 but no error → either genuinely no calls in window, OR token lost data scope. Try a wider window mentally (probe is last-24h) — if the panel shows calls today but probe returns 0, escalate to MyOperator (Lokesh) to confirm the token's log access.
2. Never regenerate the token casually — coordinate (it's shared infra).

### COMPUTE-FIX (API returns calls, but getDashboardData builds empty arrays / throws)
1. Read the `RETURNED ERROR` message from `probeDashboardData_` if present — it names the failing helper.
2. Likely suspects, in order:
   - **Sheet tab renamed/missing** — `Patient_Master`, `WA_Inbox`, `Callbacks_Today`, or `Agents`. The helpers open tabs by exact name (`patientLookup_`, `waLookup_`, `staffStatusMap_`, `rosterByExt_`). A renamed tab → that section silently empties (helpers are degrade-safe and return null/[]).
   - **`SHEET_ID` Script Property** wrong → every tab read fails together (would empty ALL sections at once — matches "everything empty").  ← check this FIRST when ALL sections are empty.
   - **`callAgentInfo_`/`log_details` shape changed** → only Team empties.
3. Verify tabs exist with exact names (KB §4). Verify `SHEET_ID` points at `1USj…klo0`.

### RENDER-FIX (server returns good data, page shows empty)
1. The deployed `Dashboard.html` has drifted from what `getDashboardData` returns, OR a client JS error halts rendering.
2. In the browser, open the dashboard, press **F12 → Console**, reload, and read any red error. A single JS exception stops all section rendering while tiles (rendered first) survive.
3. Fix: restore the matching `Dashboard.html` for this `WebApp.gs` (both are in the project export / GitHub once committed). Replace full file → deploy New version → hard-refresh (Ctrl+Shift+R).
4. Confirm the data keys the HTML reads (`d.pending, d.agents, d.recentWA, d.resolved, d.handled, d.kpis`) match the server's return object (they do in v17.1).

---

## THE READ-ONLY PROBE (paste into Probe.gs.gs, run, read log, then delete)
```javascript
/** READ-ONLY — logs what getDashboardData returns. No secrets printed. */
function probeDashboardData_() {
  var sp = PropertiesService.getScriptProperties();
  var key = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
  Logger.log('Key present: %s (role=%s)', key ? 'yes' : 'NO', dashRole_(key));
  var d = getDashboardData(key, true);            // force=true bypasses 90s cache
  if (d && d.error) { Logger.log('RETURNED ERROR: %s', d.error); return; }
  Logger.log('updated=%s build=%s', d.updated, d.build);
  Logger.log('kpis: %s', JSON.stringify(d.kpis));
  Logger.log('COUNTS -> pending:%s resolved:%s handled:%s recentWA:%s agents:%s',
    (d.pending||[]).length,(d.resolved||[]).length,(d.handled||[]).length,
    (d.recentWA||[]).length,(d.agents||[]).length);
}
```
To run it: select **`probeDashboardData_`** in the function dropdown (it ends with `_`; scroll the list). If it does not appear, the paste didn't save into the file — re-paste at the END of `Probe.gs.gs`, Ctrl+S, and re-open the dropdown.

---

## FIRST-FIVE-MINUTES CHECKLIST (when something's wrong and you're unsure)
1. Is it dashboard, or emails/tabs? (Golden Fork)
2. Dashboard: does it load + authorize? (B1/B2)
3. Run `probeApi` — API + token OK? records > 0?
4. Run `probeDashboardData_` — counts zero or non-zero?
5. Branch to COMPUTE-FIX (zero) or RENDER-FIX (non-zero). Done.

*Troubleshooter v1 · 29 Jun 2026 · pair with KB v1.*

---

## WORKED EXAMPLE (resolved) — empty dropdowns, good tiles
This exact case was solved 29 Jun 2026. If you see correct KPI tiles but every dropdown empty:
1. `probeApi` → data in? (it was: 5 records, token len 32).
2. `probeDashboardData_` via a plain-named wrapper → server returning it? (it was: pending 7, resolved 3, WA 12).
3. Both pass ⇒ **render bug.** F12 → Console → Ctrl+Shift+R. Found `i is not defined` at a line inside `Array.map`.
4. Cause: pending renderer was `p.map(function(e){` but used `i`. Fix: `p.map(function(e,i){`.
5. If the *same* error persists at the *same* line after the fix → the OLD version is still deployed. **Deploy → Manage deployments → ✏️ → Version → "New version" → Deploy**, then open `/exec?k=…` in a fresh tab.
Full write-up: `Callback_Dashboard_TROUBLESHOOT_LOG.md` Incident #1.

