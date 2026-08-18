# HANDOFF RUNBOOK — Session 19 close · 30 June 2026 · v17
**Dr. Manoj Agarwal Clinic, Bareilly.** Resume point + exact next steps for Session 20.
Canonical reference = `Clinic_Master_KB_SystemsRegister_v1.7.md` (§19 = this session). This runbook is the "where we stopped."

---

## §0. WHAT HAPPENED THIS SESSION

**Follow-up auto-push made automatic and live · the "2001" date bug fixed at the source · launcher portal built (not deployed) · Excel tools inspected · TPA verification brief produced.**

### A. Follow-up auto-push — now AUTOMATIC and LIVE (main work)

The dashboard's `Followups_Today` was empty because the push had never been deployed to the clinic PC and nothing ran it automatically. Closed end to end:

1. **`push_followups_today.py` deployed** to the tracker folder; first manual `--push` wrote **178 worklist rows + 144 settled**; dashboard confirmed "TODAY'S FOLLOW-UP CALLS 178" with Call buttons.
2. **Folder watcher `watch_and_push_followups.py`** — polls `outputs\` every 5s, dedups on name|size|mtime (`watch_pushed.seen`), waits 10s to settle, then calls the proven push with `--push --file`. Polling (not OS events) chosen because Drive sync churn creates false events.
3. **`start_followup_watcher.bat`** — auto-restart loop launcher.
4. **Windows Startup shortcut** — confirmed in place (`…\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\start_followup_watcher.bat - Shortcut`). Watcher starts on every login.

From now: process tracker → file lands in `outputs\` → watcher pushes automatically → dashboard updates. Manual fallback unchanged: `python push_followups_today.py --push`.

### B. "2001" due-date bug — fixed at the push source

Tracker writes yearless per-row dates (`30-Jun`); dashboard's `fmtDateCell_` defaults the missing year to 2001. **Fixed in `push_followups_today.py`** (NOT in the live dashboard — lower risk) with a defensive `to_full_date()` normaliser + `raw_cell()` accessor that always writes full `DD-Mon-YYYY` for the Call Sheet `Due Date` and the Settled `Due`/`When` columns. 17/17 unit cases pass; full reader run against a workbook mimicking the real file produces `30-Jun-2026` everywhere; `py_compile` clean. New file md5 `9e4bd2070079dc0d8542738c99aa76f6`. **Delivered to the owner to replace + re-run; preview/push confirmation was still pending at session close.**

### C. Unified launcher portal — BUILT, not deployed

`portal.py` (Flask :8090) at `followup.dr-manoj.in/portal` — Phase-1 doctor-only, 11 tiles (6 live links + 5 held labels). PIN + indefinite device-trust cookie (NOT biometric — survives device repair). "Forget all devices" button, sealed recovery reference. `py_compiled`, all 7 auth/render flows tested. Config in `portal_config.py` (VPS-only, chmod 600). **Not yet deployed** — see §2.

### D. Excel tools inspected + TPA brief

Surgical Estimate, Nutrition/Physio, Ayushman packages KB all inspected (future rebuilds, not Phase 1). Ayushman HTML finder = current working system, **do not modify, link only**. **TPA verification brief** (`TPA_Verification_Ingestion_Brief_v1_0.md`) produced for a separate background chat to visually verify 10 scanned TPA tariff PDFs against a suspect Gemini transcription.

---

## §1. MENTAL MODELS TO CARRY FORWARD

1. **Auto-push is live but the date fix is unconfirmed.** The watcher pushes automatically. BUT the owner still needs to replace `push_followups_today.py` with the Session-19 version and re-run once for the date fix to take effect. If they report "still 2001": confirm (a) new file saved over old, (b) `--push` run, (c) dashboard hard-refreshed. The fix is at the push, not the dashboard.

2. **Fix at the producer, not the live consumer (D24).** When a bug can be fixed either in the data producer or the live dashboard, fix the producer. The dashboard is the clinic's primary tool — keep its blast radius at zero.

3. **The launcher links, it never rebuilds (D23).** Tiles point at existing tools. Held tiles flip to live by editing one line in the `TILES` list. Phase 1 = doctor-only PIN; Phase 2 (staff RBAC) is the big deferred build.

4. **Build order unchanged:** finish launcher deploy → resume Call Console Step 1 (`WebApp.gs`) → Step 2 (`Dashboard.html`) → Diagnostics.gs Step 3. The failure-map comment-block discipline (D19) still applies to every new/changed file.

5. **Security hygiene pending:** a live service-account key was pasted into chat this session. Rotate it (KB §19.5). Not an emergency — the key only reaches the owner's own Sheet.

6. **Everything from Session 18 still holds:** tracker in GitHub, data on Drive, financial stack live+undocumented, "Daily Clinic Reports" sheet must not be renamed, 13 triggers to dedupe, Google storage review 1 Apr 2027.

---

## §2. OPEN ITEMS / BACKLOG (carried into Session 20)

### Immediate (this-session follow-through)
1. **Confirm the date fix** — owner replaces `push_followups_today.py`, runs preview then `--push`, confirms dashboard shows `30 Jun 2026`.
2. **Rotate the leaked service-account key** (KB §19.5) — Cloud Console → create new JSON key → replace on PC → delete old key id `ba8a4836…`.

### Launcher deploy (then Call Console)
3. **PIN-setup script** — one-time, creates `portal_config.py` on the VPS (PIN hash + salt + token seed).
4. **systemd unit** for `portal.py` on :8090.
5. **OLS reverse-proxy snippet** mapping `/portal` → `127.0.0.1:8090`.
6. **Deploy + smoke test** the launcher.
7. **Call Console Step 1 — `WebApp.gs`** — `allCallsToday_()`, `getAgentIdentity_()`, `logOutcome_()`, `Outcomes_Log` tab writer. Failure-map discipline. Spec: Call_Console_Evolution_Spec_v1.0.
8. **Call Console Step 2 — `Dashboard.html`** — full UI rebuild. After Step 1 tested.
9. **Diagnostics.gs Step 3a/3b/3c** — after Step 2. Now also covers `FOLLOWUPS_DATE_MALFORMED` (added to spec v1.1).

### Infrastructure
10. **Follow-Up Tracker VPS migration** — the proper long-term home for the auto-push (replaces the local watcher). venv + waitress/gunicorn + systemd + OLS reverse proxy + SSL.
11. **Maintenance project creation** — after Diagnostics.gs is live ≥1 real clinic day.

### Carried
12. **Held-bills review** — `/revenue/review`, ₹91,570 held.
13. **360° patient lookup card** — `lookupPatient360` server fn already in `WebApp.gs`; card UI needed.
14. **WhatsApp token rotation** — HIGH RISK, coordinate Lokesh Kumar VB.
15. **ntfy self-hosting** — deferred (free-tier 429 risk).
16. **Per-agent AKEY distribution** to staff.

### Session-18 audit items (still open)
17. Document financial ops stack in Clinic & Growth KB.
18. Fix Clinic Accounting Reports to use `openById()` not `openByName()`.
19. Clean up 4 dormant Apps Script projects.
20. Identify the Untitled spreadsheet in Drive root.
21. Fix outgoing WA phone-number format (bare 10-digit) in wa-send relay.
22. Run `setupTriggers()` to dedupe the 13 triggers on Clinic Callback Tracker.
23. **Claude Code VPS connection** — deferred until Maintenance project. Guide: `Claude_Code_VPS_Connection_Setup_v1_0_30Jun2026.md`. Per D18: Maintenance project only, doctor-approved, never automatic.

### Future rebuilds (no urgency)
24. Surgical Estimate → web tool. 25. Nutrition/Physio → web tool (safety-critical). 26. Unified costing tool combining Ayushman + Surgical Estimate + verified TPA tariffs. 27. Google storage review by 1 Apr 2027.

---

## §3. SESSION-CLOSE CHECKLIST

- GitHub: Session 19 commit prepared (push script date fix + watcher + launcher + setup note) — see commit message handed at close
- KB: v1.7 written ✅ (§19 added, §12 state updated)
- Runbook: this file ✅ (Session 19 v17)
- Umbrella Architecture: v1.6 ✅ (D22–D24, module inventory updated)
- Diagnostics Spec: v1.1 ✅ (`FOLLOWUPS_DATE_MALFORMED` added)
- Maintenance SOP Spec: v1.1 ✅ (auto-push watcher in surveillance register)
- API Quick-Ref Card: UNCHANGED ✅ (no API behaviour proven/corrected this session)
- Call Console Spec: UNCHANGED ✅ (console deferred; no design decisions changed)
- Notion: Tech & Systems Register + Active Projects + Decisions (D22–D24) updated during close ✅
- Drive: updated docs uploaded to the Generated Documents / Specs folder ✅
- Drive: incident report for the "2001" date bug created ✅
- ClickUp: backlog synced ✅
- Gmail: manual health digest drafted ✅
- Cold backup zip: generated ✅

---

## §4. UMBRELLA ARCHITECTURE UPDATE — DONE THIS SESSION

Added decisions **D22–D24** and updated §6 module inventory:

- **D22:** Follow-up auto-push is automatic via a local folder watcher + Windows Startup auto-start (interim until VPS migration); polling not OS events; dedup on name|size|mtime; manual `--push` fallback remains.
- **D23:** Unified launcher is phased — Phase 1 doctor-only (PIN + device-trust cookie, NOT biometric); Phase 2 staff RBAC deferred. The launcher links to tools, never rebuilds them.
- **D24:** Fix at the data producer, not the live consumer, when both could solve a bug (the "2001" date fix went into the push script, not the live dashboard).

§6: Brain row now notes auto-push; new **Launcher portal** row (BUILT / deploy pending).
