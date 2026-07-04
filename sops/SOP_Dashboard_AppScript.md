# SOP — Dashboard & Apps Script
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Call Console Spec v1.5. KB wins on any conflict.**

> **What this SOP is.** The operational guide for the staff dashboard and the Google Apps
> Script project behind it. Use it when the dashboard won't load, shows stale data, a
> feature stops working, or after any deploy. It covers where things live, what healthy
> looks like, and the deploy discipline that keeps the URL stable.

---

## 1. What the dashboard is

The dashboard is the single screen the clinic staff use all day: it shows the WhatsApp
inbound feed, the follow-up call list, lets staff place calls (tap-to-call), and lets them
log call outcomes. It is a Google Apps Script **web app** bound to the "Clinic Callback
Tracker" Google Sheet. It reads the MyOperator Call/Logs API (System A) live on each page
load — not via triggers.

| Item | Value |
|---|---|
| Live URL | `https://script.google.com/macros/s/AKfycby…/exec` (requires `?k=KEY`) |
| Access key | `DASH_KEY` in Script Properties; the key value lives ONLY in the owner's Apple Notes |
| Current version | **v18.18** (footer should read `v18.18`) |
| Backing sheet | "Clinic Callback Tracker" ID `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` |

---

## 2. The Apps Script project (12 files)

| File | Role | Rule |
|---|---|---|
| `WebApp.gs` | The web-app entry point / router | **NEVER TOUCHED (D34).** All new server functions go elsewhere. |
| `CallConsole.gs` | Call placing, duration gate, dialer server functions | New call-side functions go here |
| `OutcomeLog.gs` | Outcome writing / verification | New outcome-side functions go here |
| `Diagnostics.gs` | Follow-up stale-list sentinel + checks | Surveillance logic |
| `Dashboard.html` | The entire front-end (HTML + one big `<script>`) | The screen staff see |
| *(+ 7 more)* | Supporting `.gs` / includes | Per the 12-file project in `dashboard/` |

**Key sheet tabs the dashboard reads/writes:**
`Followups_Today`, `Followup_Outcomes`, `Followup_Escalations`, `Followups_Settled`,
`Call_Feed`, `WA_Inbox`, `Agents`, `Patient_Master`, `Call_Durations`.

**One-writer-per-table invariant:** each tab has exactly one writer. Never add a second
writer to a tab — it is the rule that keeps the data trustworthy.

---

## 3. What "healthy" looks like

- Dashboard loads at the live URL **with `?k=KEY`** appended and shows today's data.
- Footer build stamp reads the current version (**v18.18**).
- WhatsApp inbound feed populates; green `📞 Call` button appears on inbound rows.
- Follow-up list shows today's rows (after the morning VPS push).
- Outcome dropdown unlocks only after a call is confirmed bridged (≥15s talk — the duration gate).
- No red stale-list banner across the top.

---

## 4. Known failure modes & fix paths

### Dashboard shows "Unauthorized" / blank
- The `?k=KEY` is missing or wrong. The URL only works with the key appended.
- Confirm `DASH_KEY` still exists in **Project Settings → Script Properties**.

### Dashboard loads but data is stale / empty
- **Follow-up list empty:** the morning VPS push didn't land — see `SOP_FollowUp_Tracker.md`
  and check `Followups_Today`. The stale-list sentinel emails you if the list is stale.
- **WhatsApp feed empty:** `wa-receiver` on the VPS may be down (writes WA_Inbox) — see `SOP_VPS_Services.md`.
- **Call data stale:** the Call/Logs API (System A) may be failing — the dashboard reads it live.

### A feature stopped working after a deploy
- **The build stamp is the tripwire, not the proof (D53).** Seeing the new version number
  only means the file loaded — it does NOT prove the feature works. Always do a **feature
  check**: actually use the changed feature once.
- If the stamp is old, the paste didn't take or the wrong deployment was updated → §5.

### "Agent shows as Staff" on escalations
- Known display bug; owner indicated resolved. If it recurs, check the `Agents` roster
  mapping used by the escalation writer. *(Verify + close is a standing backlog item.)*

### Duration gate won't unlock the outcome dropdown
- The call wasn't confirmed bridged: customer leg needs `result == "answered"` AND ≥15s talk.
- Duration data comes from `Call_Durations`, keyed on `client_ref_id`, written by
  `call-hook.service` on the VPS. If that service is down, no durations arrive.

---

## 5. Deploy discipline (the rules that protect the URL)

**These rules exist because breaking them changes the live URL and every staff bookmark.**

1. **To ship a change:** open the Apps Script project → **Deploy → Manage deployments** →
   edit the **existing** deployment (pencil) → **Version: New version** → Deploy.
2. **NEVER "New deployment"** — that mints a brand-new URL and orphans every bookmark.
3. **Installing `Dashboard.html`:** paste the full file into the Apps Script editor, save,
   then deploy a New version of the existing deployment, then **hard-refresh** the browser.
4. **Full-file replacement only** — never hand-edit diffs into the editor.
5. **The `var PAGE_BUILD = 'vX.Y · …'` line is the deploy tripwire** — bump it every deploy
   so you can confirm the new file actually loaded.
6. **After deploy: feature-check, not just stamp-check (D53).**

---

## 6. Manual fallback (dashboard unavailable)

- Staff dial patients directly through the MyOperator IVR panel.
- Outcomes can be recorded on paper / in the sheet directly and reconciled later.
- The follow-up list can be read straight from the `Followups_Today` tab in the Sheet.

---

## 7. Emergency contacts

| For | Who |
|---|---|
| The access key (`DASH_KEY`) | Owner's Apple Notes — only place it lives |
| MyOperator Call/Logs API issues | Lokesh Kumar VB |
| Sheet / Apps Script | Owner (build project session with Claude) |

---

*Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update this SOP in the same
session any `.gs`/HTML file or deploy rule changes (KB discipline).*
