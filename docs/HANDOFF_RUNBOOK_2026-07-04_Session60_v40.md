# HANDOFF RUNBOOK — 2026-07-04 · Session 60 · v40

**Dr. Manoj Agarwal Clinic · Bareilly.** Read the KB (**v1.28**) + this runbook at session start.
**KB wins on any conflict.** This runbook = exactly where we stopped.

> **Numbering:** Session 59 = the *attendance* HTTPS/cookie-login work (D99–D100), closed earlier today. **This = Session 60**, the follow-up-push VPS migration, decisions **D101–D105**. (The two nearly collided as "59"; resolved.)

---

## §0 — WHAT HAPPENED THIS SESSION (Session 60)

**Goal 1 (Gap A) — DONE. Full EOS, code changed.**
Migrated the follow-up daily push **off the failing clinic-PC Windows watcher** onto the **VPS**, end-to-end. Kills the single most recurring failure in the system (stale follow-up list because the "At log on" watcher didn't re-fire — §24, §55).

**New chain (all live, owner-verified):**
> PC generates workbook → **app auto-uploads to VPS** (`Uploaded to VPS ✓` seen on the result screen) → **VPS catcher** stores it in `/root/wa/followup-inbox/` → **VPS timer** pushes to the sheet (22:00/07:00/11:00 IST) → dashboard.

**Five pieces (each built+tested offline, md5-verified, installed one step at a time):**
1. **VPS catcher** — `followup_receiver.py` + `clinic-followup-receiver.service` (gunicorn :8100) + 2 vhost proxy contexts (`/fu-upload`, `/fu-ping`) above the catch-all. Secret `FU_UPLOAD_SECRET` in `/root/wa/.env`. **(D101)**
2. **VPS pusher** — `push_followups_vps.py` (the live PC push script, only `OUTPUTS_DIR`+`KEY_DIR` repointed). Proven: **223 worklist + 153 settled** written, dashboard-verified. **(D102)**
3. **VPS timer** — `clinic-followup-push.service`+`.timer`, fires 22:00/07:00/11:00 IST, Persistent. Safety-net (replace-only). **(D103)**
4. **PC hook** — `push_to_vps.py` helper + 13-line non-fatal hook in `app.py` `/run` route; secret in gitignored `fu_upload.env`. **(D104)**
5. **Retire** — old Task Scheduler task `\Follow-up Auto-Push Watcher` **disabled** (reversible). **(D105)**

**Also:** openpyxl 3.1.5 installed into the VPS venv.

**Goal 2 (diagnostics system across all projects) — owner's second goal; NOT started, deliberately deferred to a clean session.**

**Deferred with owner agreement:**
- **Workflow redesign (morning-generate / call-the-afternoon-before)** — Claude recommends pursuing it (fixes the two-CSV anchor friction; likely lifts return rates for travel-dependent patients) but it touches the live `processor.py` day-math → its own tested session. The installed timer already works for both flows.

---

## §1 — CURRENT LIVE STATE (one-liners)

- **Follow-up push: VPS-native, watcher-free.** Catcher :8100 live; pusher proven; timer armed (22:00/07:00/11:00 IST); PC hook live; old watcher disabled.
- **Attendance (S59): live** at `https://attendance.dr-manoj.in` (cookie login), fallback `http://93.127.195.49:8042/`. Cold-kit with owner; only GitHub upload done; remaining uploads owner will do.
- **Dashboard v18.18 LIVE** (unchanged this session): WhatsApp tap-to-call (D97), stale-list top bar (D98), D66 vanish-on-file, duration gate (D82).
- **VPS services (all running):** wa-receiver :8095, wa-send-api :8096, call-api :8097, call-hook :8098, clinic-portal :8099, **clinic-followup-receiver :8100 (NEW)**, wa-notifier, attendance-dashboard :8042. Timers: call-recording-archive (2 AM), call-transcription (3 AM), **clinic-followup-push (22:00/07:00/11:00, NEW)**.
- **Tracker app** stays on the clinic PC (interactive; ~9 PM run; fuses 2 Docterz CSVs). Unchanged except the +13-line upload hook.
- Key rotation 🔴 overdue (Lokesh); AKEY_14 flagged; PHI base swap deferred.

---

## §2 — BACKLOG (next session picks from here)

**Recommended next: Goal 2 — Diagnostics/surveillance across all active + hosted projects.**
Owner's explicit second goal this session, and the natural companion to Gap A: now that push is VPS-native, one surveillance layer should watch every VPS service + scheduled job + token validity and alert (email/ntfy), extending the single `Diagnostics.gs` sentinel into a full layer across attendance, follow-up, WA, call-hook, transcription, portal. Read `Diagnostics_Surveillance_System_Spec_v1_2.md` first.

Then, roughly in priority:
1. **Verify & close "Agent shows as Staff"** — owner said "already solved"; confirm in the dashboard, record the fix in the KB.
2. **Commit new code to GitHub** — this session's follow-up-VPS files (below), plus the non-secret attendance files (S59) and the long-outstanding `call_transcription.py`.
3. **The data pass** — owner runs a fresh Docterz periodic fill → one-month follow-up analysis → finalise tier/track → draw the track-first flowchart. (Owner-gated: needs the fill + a PHI-strip decision first.)
4. **Workflow redesign** (morning-generate / call-afternoon-before) — design offline, test, install; changes `processor.py` day-anchoring.
5. **P1–P10 lock (D83–D92)**; then **D78 sticky-on-staff counter** (after the data pass).
6. **Parallel:** 🔴 service-account key rotation (book Lokesh); AKEY_14; PHI base swap; Sarvam retry; Call_Feed D61.

---

## §3 — KEY FACTS / GOTCHAS (this session's additions)

- **VPS follow-up inbox:** `/root/wa/followup-inbox/` (auto-created by the catcher on first upload).
- **Catcher secret:** `FU_UPLOAD_SECRET` in `/root/wa/.env` (chmod 600) AND the same value in the PC's gitignored `fu_upload.env`. After any change, **restart `clinic-followup-receiver.service`** so it reloads `.env`. Verify writes with anchored `grep -c '^FU_UPLOAD_SECRET=' /root/wa/.env`.
- **VPS pusher (manual):** `cd /root/wa && /root/wa/venv/bin/python3 push_followups_vps.py` (preview) / `--push` (live).
- **Disabling the watcher needs an ADMIN Command Prompt** (else `Access is denied`). Re-enable: `schtasks /change /tn "\Follow-up Auto-Push Watcher" /enable`.
- **Never edit vhost.conf without a backup + rollback in hand.** Session backup: `/root/vhost.conf.bak_session60`. After `lswsctrl restart`, verify existing routes (portal → 302) before trusting the new one. New contexts go **above** the catch-all `context /`.
- **PC app rollback:** `app.py.bak_session59` in the tracker folder (pre-hook copy).
- **openpyxl** now in the VPS venv (3.1.5).

---

## §4 — FILES PRODUCED THIS SESSION (for GitHub commit next session)

**VPS (`/root/wa/`):** `followup_receiver.py`, `push_followups_vps.py`
**VPS systemd (`/etc/systemd/system/`):** `clinic-followup-receiver.service`, `clinic-followup-push.service`, `clinic-followup-push.timer`
**VPS vhost:** `followup.dr-manoj.in/vhost.conf` (+2 proxy contexts)
**PC tracker folder:** `push_to_vps.py` (new), `app.py` (+13-line hook), `.gitignore` (+`fu_upload.env`)

**GitHub note:** secrets/PHI stay gitignored (`fu_upload.env`, `.env`, keys). Suggested repo location: a new `followup-vps/` folder (or `wa-send/`) — decide next session. Still outstanding from earlier: `call_transcription.py` commit, and the non-secret attendance files (S59).

---

## §5 — CANONICAL DOCS AFTER THIS SESSION
- KB: **Clinic_Master_KB_SystemsRegister_v1_28.md** (this EOS)
- Runbook: **HANDOFF_RUNBOOK_2026-07-04_Session60_v40.md** (this file)
- Umbrella: **Dr_Manoj_Clinic_Umbrella_Architecture_v1_22_Delta.md** (this EOS)
- Unchanged: Call_Console_Evolution_Spec v1.5, Diagnostics_Surveillance_Spec v1.2, Maintenance_SOP_Spec v1.1, Followup_Taxonomy_and_Lifecycle_Design v1(S56).

**Owner-side propagation (per the S58 archive rule):** GitHub + project knowledge = source of truth; Notion decisions log updated (D101–D105 block); Drive holds the current canonical set as a cold backup via owner PC drag-drop (the connector cannot write). **This session:** owner will do the remaining uploads (GitHub done by owner for attendance; follow-up-VPS files + these docs pending owner upload).
