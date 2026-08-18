### F-82 (S172, OPEN — VENDOR-SIDE) — MyOperator WhatsApp Developer API returns HTTP 500 {"message":null} on ALL authenticated calls

**Symptom.** Every AUTHENTICATED call to `https://publicapi.myoperator.co` for the clinic account returns `HTTP 500` with body `{"message": null}` — reads (`GET /chat/templates`, `GET /chat/phonenumbers`) AND sends (`POST /chat/messages`). Observed identically from (a) the new portal sender `portal_wa.py` and (b) the tracker's own long-proven `wa_send.py` path, using the identical token (sha8 `d47a090a`, = tracker `WA_TOKEN`), company ID `68384350414b9847`, WABA ID `2101222617483538`, phone-number ID `1090067637530949`.

**Not our code.** An UNauthenticated call to the same endpoint correctly returns `HTTP 401` — the API is up and the token authenticates past the auth gate; only account-resolution fails. Inbound WhatsApp (webhook → `/root/wa/wa_logs/*.jsonl`) is unaffected (today's file present + populated). Two independent code paths + two different read endpoints + the send endpoint all fail identically → not a payload, header, token or portal bug. **Root cause is account-side / provisioning at MyOperator**, starting today.

**Diagnostic ladder (the reusable playbook — run in this order):**
1. `tail` the send log `/root/wa/wa_portal/wa_portal_sends.csv` for the exact error string.
2. Fingerprint the portal token vs `.env`/`wa_send.env` by **len + sha8 only** (never print the token).
3. Live-send to the doctor's OWN number via the tracker's proven `wa_send.py` path (rules out portal request-shape).
4. Do a READ call (list templates). **If a read fails too, it is not payload.**
5. Do a NO-AUTH call. **401 = API up + account not resolving (vendor); 500 everywhere = wider outage.**

**Action.** Escalated to **Khushi** (MyOperator account manager, email with full request/response detail) + **Lokesh Kumar VB** (engineer). `PORTAL_WA_DRYRUN` returned to `"1"` (SAFE). Go-live blocked pending vendor restore; when restored, flip DRYRUN→`"0"`, restart, self-send `drmanoj_post_visit` to the doctor's own number, confirm, then live — no code change.

**Lesson.** Three successive wrong diagnoses (account → config → account) were resolved only by the no-auth 401 control — **run the auth-gate control EARLY**, before theorising. Related near-miss (NOT a fault): a first install targeted `/root/wa` instead of the real portal dir `/root/portal` — caught immediately by the md5 gate; the portal is `/root/portal/portal.py`.

*Full narrative: Archive §S172. Status: OPEN (vendor).*

### F-83 (S176, OPEN — mitigated) — Asset-app intake background OCR thread is fire-and-forget

**Symptom.** The first real reception bill (B-0001, Shri Ram Enterprise, ₹1,30,003) arrived on the checker's screen BLANK although Sarvam extraction was configured and working — a later manual re-run extracted vendor, bill number, total and all 5 line items correctly.

**Root cause.** The A-D21 reception intake fires the Sarvam extract in a plain background `threading.Thread` from the request handler: fire-and-forget. The thread **dies on service restart** (an install/restart between scan and completion kills the read) and the fill deliberately **skips non-draft bills** (non-clobber), so a bill promoted or touched before the thread completes never receives its read — with no visible trace of failure.

**Mitigation shipped (A-D23, S176, LIVE):** the read is no longer silent — `ocr_status` (reading / read / empty / failed) is stamped on the draft + the Purchases list; a **"Re-read with Sarvam"** button (non-clobber, works on drafts AND approved bills) recovers any lost read; approving a bill with blank fields now requires an explicit server-enforced confirm. B-0001 was recovered via Re-read.

**Durable fix (owed, A-D25 candidate):** replace the thread with a survivable path — either a queue + worker (systemd or cron sweep over `ocr_status='reading'|'failed'` drafts) or synchronous extract with a bounded timeout at scan time. Until then, restarts of `assetapp.service` should be followed by a glance at the Purchases list for stuck "reading" badges.

**Lesson.** A background thread inside a gunicorn worker is not a job system: anything that must complete needs a durable record of "not done yet" and a path to retry — visible status first (shipped), survivable execution second (owed).

*Full narrative: Archive §S176 (fold) + `KB_Asset_Register_v1_10_3.md` §7. Status: OPEN (mitigated by A-D23); asset-app located, clinic-numbered.*

---
*Consolidated append for `Fault_Action_Register` v2.16 → v2.17 (apply once, at the file's §7/Later-Findings tail): the F-82 entry above (owed since S172) + this F-83 entry (minted S176, folded S177). After applying, bump the register's version + changelog and re-pin its md5 in the manifest. Supersedes `F82_Fault_Register_append_S172.md`.*
