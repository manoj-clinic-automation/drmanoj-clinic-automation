# Clinic Master KB / Systems Register — v1.28

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document for v1.28.** Carries forward everything in v1.27 (attendance-session close, S59, D99–D100) and all prior versions unchanged, and adds the **Session 60 block (§60)** with decisions **D101–D105**, plus a §12 state update. **Code WAS touched this session (full EOS):** the follow-up daily push was migrated OFF the failing clinic-PC Windows watcher and ONTO the VPS end-to-end. **KB wins on any conflict.**
>
> **Session-numbering note (important):** Session 59 was the *attendance* subsystem work (HTTPS subdomain + cookie login; D99–D100; `att_dashboard.py`) — closed earlier the same day (04 Jul 2026). **This session (60) is a separate, later session** covering the follow-up-push migration. The two were briefly at risk of a numbering collision (both drafted as "59"); resolved: attendance = S59/D99–D100, follow-up-push = **S60/D101–D105**.

---

## §12 STATE — what is live right now (updated at Session 60 close)

- **GAP A COMPLETE — the follow-up daily push no longer depends on the clinic PC / Windows login.** The single most recurring failure in the whole system (stale follow-up list because the "At log on" watcher didn't fire — incidents in §55, §24/D40) is now **structurally impossible.** New chain, all live and owner-verified end-to-end:
  > **PC** generates the workbook (currently ~9 PM; sometimes late/next morning) → **the app auto-uploads it to the VPS** (owner saw `Uploaded to VPS ✓` in the result notices) → **VPS catcher** stores it in `/root/wa/followup-inbox/` → **VPS timer** pushes it to the Google Sheet on its own clock → dashboard shows it.
- **VPS follow-up catcher is LIVE (D101).** `clinic-followup-receiver.service` — Flask via gunicorn on `127.0.0.1:8100`, walled-off, own systemd unit. Route `/fu-upload` (secret-gated via `X-FU-Secret`, `.xlsx`-only, atomic temp→rename write into `/root/wa/followup-inbox/`) + `/fu-ping` liveness. Public HTTPS via two new OpenLiteSpeed proxy contexts (`/fu-upload`, `/fu-ping`) placed **above** the catch-all `context /` (which still routes to wa-receiver). Secret `FU_UPLOAD_SECRET` lives only in `/root/wa/.env` (chmod 600). Stores files only — never parses/logs patient data.
- **VPS follow-up pusher is LIVE (D102).** `push_followups_vps.py` = the owner's exact live `push_followups_today.py` with **only two lines changed** (`OUTPUTS_DIR → /root/wa/followup-inbox`, `KEY_DIR → /root/wa`; both env-overridable). All safety behaviour identical: reads workbook read-only, replace-only on `Followups_Today`+`Followups_Settled`, refuses an empty list, masks phones in console, never touches `Followup_Outcomes`. Uses the existing `patient-mirror-key.json` (verified exactly one service-account key in `/root/wa/`). Proven live: **223 worklist + 153 settled** rows written, dashboard-verified (bucket totals reconciled to 223; the one-row Actionable-Missed diff = today's already-filed outcome, confirming it's live data not a stale coincidence).
- **VPS push timer is ARMED (D103).** `clinic-followup-push.timer` (oneshot service) fires **22:00 + 07:00 + 11:00 IST daily**, `Persistent=true`. Safety-net re-push (replace-only → harmless when nothing new arrived). Schedule brackets the owner's variable workbook-arrival pattern and guarantees the board is correct before the post-lunch calling window. Backstop only — the PC hook uploads instantly on generate.
- **PC auto-upload hook is LIVE (D104).** New helper `push_to_vps.py` in the tracker folder (reads `FU_UPLOAD_SECRET` from a gitignored `fu_upload.env`; POSTs the workbook to the catcher; **never raises**). `app.py` carries a **13-line, non-fatal** hook placed right after `INGEST_NOTICES` is imported in the `/run` route (import-order bug caught & fixed offline): after `run_daily` writes the workbook, it uploads `staff_path` and appends the result to the on-screen notices. Any failure is a notice only — it can **never** break report generation. Owner verified `Uploaded to VPS ✓ (Staff_Action_Today_2026-07-04.xlsx)` on the result screen.
- **Old Windows watcher RETIRED (D105).** The clinic-PC Task Scheduler task **`\Follow-up Auto-Push Watcher`** (the recurring "At log on" failure, §24/D40 & §55) is **DISABLED** (reversible, not deleted; required an admin Command Prompt). New path supersedes it. Manual fallbacks remain on both ends: `push_followups_vps.py --push` (VPS) and `python push_followups_today.py --push` (PC).
- **openpyxl 3.1.5 installed into the VPS venv** (`/root/wa/venv`) — the pusher needs it to read `.xlsx`; not previously present.
- **Tracker day-anchoring confirmed healthy.** The 04-Jul run reported `Anchored to consultation date 2026-07-03 → loaded the next call day (2026-07-04): 31 of 171 rows` — the app correctly derives *tomorrow's* call day from *yesterday's* consultation report. This is the mechanism the (deferred) morning-generate redesign would build on.
- **All §12 state from v1.27 stands verbatim** (attendance at `https://attendance.dr-manoj.in` D99/D100; Dashboard v18.18; WhatsApp tap-to-call D97; stale-list top-bar guard D98; D66 vanish-on-file live; duration gate D82; call-hook D80; per-agent logins D76; caller-ID SOP D93; key rotation 🔴 overdue; AKEY_14 flagged; PHI base swap deferred).

**Known open (top of next backlog):** **Goal 2 — the diagnostics/surveillance system across all active + hosted projects** (owner's explicit 2nd goal this session; deliberately deferred to a clean session — read `Diagnostics_Surveillance_System_Spec_v1_2.md` first). Then: **"Agent shows as Staff" attribution bug** (owner said "already solved" — verify & close in KB). The **data pass** (Docterz fill → one-month analysis → tier/track finalise → track-first flowchart). The **workflow redesign** (morning-generate / call-the-afternoon-before — Claude's recommendation: pursue it; it fixes the two-CSV anchor friction and likely lifts return rates for travel-dependent patients; but it changes the live PC `processor.py` day-math → its own tested session; the installed timer already works for both flows). P1–P10 lock (**D83–D92** reserved); D78 sticky counter (after the data pass). Parallel: 🔴 service-account key rotation (Lokesh); AKEY_14; PHI base swap; Sarvam retry; Call_Feed D61; commit `call_transcription.py` + **this session's new files** to GitHub; commit non-secret attendance files (from S59).

---

## §60 SESSION 60 — Follow-up push migrated off the Windows watcher onto the VPS (04 Jul 2026)

**Code changed. Full EOS.** Decisions **D101–D105**. This was "Gap A" — the reliability fix for the follow-up daily push. (Owner's second stated goal, the cross-project **diagnostics system**, was scoped and deliberately deferred to a clean session.)

### The problem (root cause, re-confirmed)
The follow-up list reaches the dashboard only if a **push** runs. On the clinic PC that push was triggered by a Task Scheduler task set to "At log on," which on a continuously-logged-in PC **silently failed to re-fire** (recurred twice — §24, §55). Result: yesterday's list stayed on the board. The 2 PM email sentinel + the S57 top-bar guard *detected* it but nothing *fixed* it without a manual run.

### The architecture decision (deep analysis first)
Reading the full tracker (`app.py` = 2,137-line Flask back-office; `processor.py::run_daily`) established: the tracker is a large **interactive** app the owner drives in a browser (currently ~9 PM), fusing **two** Docterz CSVs — consultation + follow-up log — where the consultation date **anchors** the follow-up slice to *tomorrow* (`anchor + 1`). It also does far more than follow-ups (Patient Master + diagnosis refresh, visit ledger, lab/pharmacy revenue sorting with a manual-unclassified pile, vacation/unavailability, revenue & patient lookup, Call_Feed pull). It cannot and must not go headless. **Therefore only the unattended *push* moves to the VPS; the app stays on the PC**, and the workbook it generates is mirrored up (one-way, push-up only — the proven patient-mirror pattern). WABA sender question resolved: **the VPS is the single WABA sender** (token already lives there; the PC can't sensibly send — it needs a URL/token that must not leave the VPS). WABA *trigger* itself is a later build ("Gap C"), not this session.

### What shipped (5 pieces; each built+tested offline, md5-verified, installed one step at a time)
1. **VPS catcher** — `followup_receiver.py` + `clinic-followup-receiver.service` (:8100) + 2 vhost proxy contexts. (D101)
2. **VPS pusher** — `push_followups_vps.py` (2-line diff off the live PC script); 223+153 rows proven. (D102)
3. **VPS timer** — `clinic-followup-push.service`+`.timer` (22:00/07:00/11:00 IST). (D103)
4. **PC hook** — `push_to_vps.py` + 13-line non-fatal hook in `app.py`; secret in gitignored `fu_upload.env`. (D104)
5. **Retire** old `\Follow-up Auto-Push Watcher` (disabled). (D105)

### Hard-won notes
- **`.env` secret lost to an SSH reconnect.** The first `FU_UPLOAD_SECRET` append was reverted when the SSH session dropped and `.env` returned to its 17-line state → catcher correctly returned `401` (security working). Fix: re-write the secret, **restart the service so it reloads `.env`**, then upload succeeded. Verify writes with anchored `grep -c '^FU_UPLOAD_SECRET=' .env` (a loose "SECRET" substring matched `CALLHOOK_SECRET` and misled briefly).
- **Import-order bug caught offline.** First hook draft used `INGEST_NOTICES` before it was imported in `/run` → would `NameError`. Fixed by placing the hook immediately after the import. Exactly why offline `py_compile` + read-back matters.
- **openpyxl** missing from the VPS venv; installed 3.1.5.
- **Windows admin needed:** `schtasks /change /disable` → `Access is denied` from a normal prompt; needs "Run as administrator". Re-enable with `/enable`.
- **Vhost editing is the riskiest step:** back up the live `vhost.conf` (`/root/vhost.conf.bak_session60`), keep a one-line rollback ready, and after `lswsctrl restart` verify existing routes (portal → 302) before trusting the new one. New contexts must sit **above** the catch-all `context /`.

### Deferred (with owner agreement)
- **Goal 2 (diagnostics system across all projects)** — owner's second goal; substantial; deferred to a clean session.
- **Workflow redesign (morning-generate / call-afternoon-before)** — recommended, but touches live `processor.py` day-math → its own tested session. The installed timer already works for both the current and the redesigned flow, so nothing installed must be undone.

---

## DECISIONS ADDED THIS SESSION

| # | Decision |
|---|---|
| **D101** | **VPS follow-up catcher (LIVE).** `clinic-followup-receiver.service`, gunicorn `127.0.0.1:8100`; `/fu-upload` (secret-gated, `.xlsx`-only, atomic write to `/root/wa/followup-inbox/`) + `/fu-ping`. Public via 2 new vhost proxy contexts above the catch-all. Secret in `.env` only. Stores files; never parses patient data. |
| **D102** | **VPS follow-up pusher (LIVE).** `push_followups_vps.py` = the live PC push script with only `OUTPUTS_DIR` + `KEY_DIR` repointed (env-overridable). Replace-only, empty-list-refusing, phone-masking, `Followup_Outcomes` untouched. Uses existing `patient-mirror-key.json`. Proven: 223 + 153 rows, dashboard-verified. |
| **D103** | **VPS push timer (ARMED).** `clinic-followup-push.timer` fires 22:00/07:00/11:00 IST daily, `Persistent=true`. Safety-net (replace-only) bracketing the owner's variable workbook-arrival pattern; PC hook uploads instantly on generate. |
| **D104** | **PC auto-upload hook (LIVE).** `push_to_vps.py` helper (secret from gitignored `fu_upload.env`, never raises) + 13-line non-fatal hook in `app.py`'s `/run` route after `run_daily`. Surfaces `Uploaded to VPS ✓` in notices. Cannot break report generation. Owner-verified live. |
| **D105** | **Old Windows watcher retired.** `\Follow-up Auto-Push Watcher` (recurring "At log on" failure) **disabled** (reversible). New VPS path supersedes it; manual `--push` fallbacks (PC + VPS) remain. |

---

## CHANGELOG
- **v1.28** (04 Jul 2026, Session 60 — full EOS, code changed): +§60. Decisions **D101–D105**. Gap A shipped end-to-end: follow-up daily push migrated off the failing clinic-PC Windows watcher onto the VPS (catcher :8100, pusher, timer 22:00/07:00/11:00, PC auto-upload hook). Old watcher disabled. openpyxl added to VPS venv. Session-numbering collision with the attendance S59 resolved (attendance = S59/D99–D100; this = S60/D101–D105). Goal 2 (diagnostics) + workflow redesign deferred. All prior D-series (D1–D100) in force verbatim; P1–P10 remain reserved D83–D92.
- **v1.27** (04 Jul 2026, Session 59 — full EOS): attendance subsystem to HTTPS subdomain (`attendance.dr-manoj.in`) + cookie-session login. D99–D100. Follow-up dashboard untouched (v18.18).
- **v1.26** (04 Jul 2026, Session 57 — full EOS): +§57. D97–D98 (WhatsApp tap-to-call; stale-list top-bar guard). Dashboard v18.16 → v18.18. D66 verified live.
- **v1.25** (04 Jul 2026, Session 56 — EOS-light): +§56. D93–D96.
- **v1.24** (03 Jul 2026, Session 55 — EOS-light): +§55. P1–P10 proposed.
- **v1.23** (Session 54): v18.16 duration gate. D80–D82.
- **v1.22** (Session 53): v18.15. D76–D79.
- **v1.21** (Session 52): v18.14. D70–D74.
- **v1.20** (Session 51): v18.8. D67–D69.
- **v1.19** (Sessions 46–50): D62–D66.
- **v1.18** (Sessions 31–45): D53–D61.
