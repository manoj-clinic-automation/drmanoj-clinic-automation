# Call Console Evolution Spec — v1.5 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward v1.4 unchanged. Records Session 57: **WhatsApp tap-to-call AS BUILT (D97, v18.17b)** and the **stale-list top-bar guard AS BUILT (D98, v18.18)**. Where this delta describes shipped behaviour it is authoritative.

---

## §H — WhatsApp tap-to-call, AS BUILT (D97; v18.17 → v18.17b)

**A second call surface. Same dialer, same gate.**

### H.1 The surface
- The **Recent WhatsApp** feed renders inbound + outbound messages. Each row already carries a clean `m.number` (used by Chat/Reply). Session 57 adds a green **📞 Call** button on **inbound rows only** (`inbound ? …Call… : ''`) — patients we might call back, never our own outgoing entries.

### H.2 The two taps
1. **Tap 1 → `waCall(number, name)`** opens a **custom in-page dialog** (`#waCallOverlay`): title "📞 Call this patient?", the patient's name (if known) + full number with a (…last4) hint, the reassurance line "Your phone rings first, then the patient is connected.", and **[Cancel] [📞 Call]**. Tap-outside cancels. This mirrors the `#threadOverlay` pattern.
2. **Tap 2 (📞 Call) → `waCallGo()` → the existing live `placeCall(number)`** → `triggerCall(DASH_KEY, number, number)`. Agent's phone rings first (a few seconds), then the patient is connected. Login guard (`CALLER_NAME`) enforced exactly as elsewhere.

### H.3 Why no gate risk
The call goes through the **same** OBD path as every other dashboard call. The server stamps the `reference_id`; the duration gate (§G) matches it back exactly as it does for follow-up-tile calls. No new server call path was added. A WhatsApp-feed call still produces a `Call_Durations` row + recording like any other call — it simply has no follow-up tile to unlock, which is expected and harmless.

### H.4 The native-dialog trap (the v18.17 → v18.17b fix)
The first build used the browser's native `confirm()`. In the Apps Script sandbox, the browser force-prepends the served page URL — **"An embedded page at …googleusercontent.com says"** — above the message. To a non-technical user this reads as a scary code. **No web page can remove that header from a native dialog.** Fix: a **custom in-page modal** (H.2), which has no browser header and full copy control.
**Standing rule (D97 corollary): never use native `confirm/alert/prompt` in the dashboard — always an in-page dialog.**

---

## §I — Stale-list top-bar guard, AS BUILT (D98; v18.18)

**A live on-screen twin of the 2 PM email sentinel.**

### I.1 The server signal (read-only)
`CallConsole.gs::getFollowupFreshness(key)` → `{ ok, stale, today, newestDue, rows }`:
- Key-gated (`dashRole_(key)`), read-only, **WebApp.gs untouched**.
- Reads `Followups_Today`, finds the newest `Due Date` (parser handles `DD-Mon-YYYY`, Date objects, ISO), computes `stale = !(newestDue >= today)` on yyyy-MM-dd strings.
- **Identical rule to `Diagnostics.gs::checkFollowupListFresh`** — one truth, so the bar and the email can never disagree.
- **No PHI** — returns dates + a row-count only. Fail-safe: any error → reports not-stale (never blocks the board).

### I.2 The tile
- `checkFreshness()` runs on **every poll** (load + each refresh) and, when `stale:true`, shows `#staleBar` — a **fixed red bar at the very top of the whole page** (z-index 9500), with the message "⚠️ This may be YESTERDAY'S list…" + newest-date/today sub-line + "run the follow-up push — or ask the doctor." `body.stale-on` pads the content down so nothing is hidden.
- **No recheck button** — the normal 60s auto-refresh clears the bar automatically once the push runs.

### I.3 Scope
- Catches the **stale** case (board showing an old day). The email sentinel additionally catches the **generation-missing** case (today's file never created) via Drive; the dashboard bar deliberately focuses on stale, which it can prove from the tab it already reads.

## CHANGELOG
| v1.5 | 04 Jul 2026 (Session 57) | +§H WhatsApp tap-to-call AS BUILT (D97; custom in-page dialog; same dialer/gate; native-dialog trap fix v18.17→v18.17b). +§I stale-list top-bar guard AS BUILT (D98; read-only `getFollowupFreshness`; shares the email sentinel's rule). |
| v1.4 | 03 Jul 2026 (Session 54) | Duration gate AS BUILT (v18.16, D82); real-body corrections (D81); call-hook receiver + Call_Durations (D80). |
| v1.3 | 03 Jul 2026 (Session 53) | D66 vanish-on-file as built; duration-gate design (D77); sticky-on-staff (D78). |
| v1.2 | 03 Jul 2026 (Session 51) | Missed-call binding (D68) + Escalations-card overhaul (D69). |
| v1.1 | (Session 25) | As previously recorded. |
