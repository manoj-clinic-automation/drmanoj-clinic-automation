# START HERE — SESSION 279 — written at the S278 close (the parent), 20-Sep-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Run `START_HERE_PROMPT_v10` Phase 0 first, then this file.

*Numbers come from the System Board `board/_numbers` only (NUMBERS_PROTOCOL_v1): claim session 279 there as your
first act (read it, pinned write). Session 275 is reserved for the Sanjeevni chat; if the board has moved past 279,
take the next free number and say so in your first line.*

*v10 says `device_bash` fails since the 8-Sep update — **it worked all through S278.** Try it first; it is faster than
the file tools for every read.*

---

## 0 · THE MANDATE — the owner's order, 20-Sep-2026 (D589), and he has said: build it

**Read `S278_BUILD_BRIEF.md` first.** He ended S278 with: *"a new chat in this project where the sequence … decided
already by you, build you can do and start."* After Phase 0 and §1.5, **start building** — no further estimate is owed.

**Ahead of everything, only if ready:** if the *X-ray test* folder now holds 2–3 days of staff files, build the live
X-ray filing in `S273_BUILD_BRIEF §2`'s order (D584, D585). If not, one line, and go on.

1. **Callback Tracker — sign in once through the Clinic app.** The portal's token is `/root/portal/clinic_sso.py`
   (HMAC-signed cookie on `dr-manoj.in`, `make_token` / `verify_token`); the Tracker is a Google web app
   (the *Call Tracker* tile, `portal.py` L143, `script.google.com/macros/s/AKfycbyo…/exec`) that cannot read that cookie. Read the Tracker's
   current key gate first (`dashRole_`, `DASH_KEY`, the staff key, `CALLER_NAME` — `dashboard/` in the repository is its
   mirror; the live project is canonical, D160) and photograph the live project into `GAS_CURRENT` before any change
   (D583; it becomes the fourth project there). Design already chosen: the portal mints a short-lived signed pass per
   login, the tile opens the Tracker with it, the Tracker verifies it with a shared secret in its Script Properties and
   sets the caller's name; the old key path keeps working as the fallback. Placed in his signed-in browser (D577).
   VPS part: one kit, one line.
2. **The caller's name on the staff phone as it rings — D590, read the Archive §S278 text, do not paraphrase it.**
   Vendor facts: `api/MyOperator_API_Document_postman_collection.json` → *WebHooks(New) → Calls* — `call.dial_begin`
   (caller in `customer_identifier`; agent leg `phone_number` = the phone being rung, `result: "dialing"`; fires per agent
   hunted; may not fire for IVR-only / missed) and `call.answered`. Build: a **second** webhook entry (Dial Begin +
   Answered) to a **new** receiver path and service (the live `call-hook`, `call_hook_capture.py` `b8a1a293` on
   127.0.0.1:8098, is not touched); lookup in `/root/finance/finance.db` `patient_ref` (by `mobile`, with
   `mobile_dup_count` for family phones) + `patient_visit`; **Web Push** through the Clinic app — the portal PWA has a
   manifest (`/portal/manifest.webmanifest`) but **no service worker yet**; VAPID keys in the VPS env, never the repo;
   the agent-phone → login map in config off the repo (F-185; `wa/get_users.py` reads MyOperator's users); a per-call
   notification tag so *answered by …* replaces it on the others. **No ntfy for calls.** Each staff phone taps *Allow
   notifications* once; one real call measures the delay. The Tracker's at-hangup tile (D184, D225) stays.
3. Then the rest of Block C · Block B, the mails (D586) · Block A, the tiles · F-595 half 2 + F-596's durable fix ·
   Vitals & Plan to the VPS (F-598).

**Standing owner rulings:** short, plain English; one paste or one double-click; decide technical questions yourself and
never put them to him; full paths and URLs in copy blocks; do not hand him steps that are not his; Apps Script changes are
placed by the assistant in his signed-in browser (D577) and update `GAS_CURRENT` in the same breath (D583); every walk
keeps one check on the real thing (F-590); a decision is quoted from the record, not paraphrased (F-597).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_118_S278close.md` |
| History Archive | `KB_History_Archive_v1_115_S278close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_103.md` |
| Runbook | `HANDOFF_RUNBOOK_2026-09-20_Session278close_v198.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| evergreen prompt | `START_HERE_PROMPT_v10.md` |
| live pins | `live_pins_S278close.txt` |
| build brief | `S278_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — mirror at this close: **D591 · F-599 · A-D25 · kit S355 · Session 275 (Sanjeevni) / 279 (this)** |

## 2 · FIRST CHECKS AT THE OPEN

1. **`D:\Downloads\_kbtools\UNATTENDED_PULL_LATEST.txt`** (first run 21-Sep 03:10, S354): OK, with `_README_S278.txt`,
   `UNATTENDED_2026-09-21_Q5.md` and `UNATTENDED_QUEUE_2026-09-21.md` copied into
   `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_UNATTENDED\`. A WARN *source NOT FOUND* means Drive for desktop does not
   expose the folder on H: — the first finding. The 21-Sep unattended report should name two Drive file ids.
2. **The bulk pin check** against the 21-Sep 01:35 bundle: the eight S278 found post-bundle (`code_bundle.py`,
   `clinic_state_backup.py`, `finance_app.py` `29819879`, `portal.py` `d9a9dc40`, `tile_grants.json` `a5f8b3b1`,
   `reports_tile.py`, `marg_take.py`, `freshness_legs.json`) and `records.py` `07ec9b41` should now match; state the counts.
3. The 21-Sep bundle carries `root/finance/spine/`; the 11:39 Daily Clinic Report reads real attendance (carried from S276).
4. `https://followup.dr-manoj.in/finance/records/xray-test` — one read; the matched / numbered / check counts.
5. `MD5SUMS_ALL.txt.bak_*` inside `KB_canon_all` — the nightly still writes one each night until F-596's durable fix;
   move any found to `D:\dr-manoj-git\_to_delete_S279\` before the canon gate.

*Written at the S278 close, 20-Sep-2026.*
