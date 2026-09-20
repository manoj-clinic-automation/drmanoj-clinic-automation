# START HERE — SESSION 278 — written at the S277 close (the parent), 20-Sep-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Run `START_HERE_PROMPT_v10` Phase 0 first, then this file.

*Numbers come from the System Board `board/_numbers` only (NUMBERS_PROTOCOL_v1): claim session 278 there as your
first act (read it, pinned write). Session 275 is reserved for the Sanjeevni chat; if the board has moved past 278,
take the next free number and say so in your first line.*

---

## 0 · THE MANDATE — the owner's words, 20-Sep-2026, settled as D586 and D587

**Read `S277_BUILD_BRIEF.md` first.** Three blocks of work, in his order. His part across all three: ticks on two
pages, one look at a drafted layout, and the VPS lines. Everything else is the assistant's.

**But first, the one thing ahead of the blocks:** if the *X-ray test* folder now holds 2–3 days of staff files, read
the test page (it reads 8 of 9 on the 20-Sep files) and build the **live X-ray filing** in `S273_BUILD_BRIEF §2`'s
order, inheriting D584 (films per study) and D585 (the file-name rule) as they stand. If it does not, say so in one
line and open Block B.

### Block B — the mail flood: investigate thoroughly, then retire what is redundant (D586)

1. **Measure at the source.** In both inboxes — the clinic account and the owner's — count every automated mail of
   the last 30 days by sender project and subject: the vehicle tracker, the UPI-received chain, the old Google-Form
   daily-payments system (Sanjeevni · Marg · the doctors · Labmate · NK Pathology submissions → Sheet → mail), and
   **the Callback Tracker's own mails** (intraday digests, the 11/15/19 summaries, the morning report). One table:
   project · mail · how many a day · to which inbox · which Sheet it fills · which PWA tile points at it · the VPS
   surface that now does the job.
2. **Evidence for "redundant", row by row.** Where the VPS does not yet carry the figure, the row says so and is not
   retired — the form chain's *submissions* may still be how Labmate / NK figures arrive; checked, not assumed.
3. **What stays without asking:** the ICICI bank-statement relay → UPI Reconciliation → VPS (load-bearing); UPI
   Reconciliation itself (the live lab and WhatsApp filing); the Daily Clinic Report; **the system-health email**
   (his word: it continues, beside the ntfy alert). The Callback Tracker's dashboard, web app, Sheet and data are
   untouched — **HOLD 2 is lifted for its email triggers only.**
4. **One page he ticks:** KEEP · RETIRE per row. Then, for every RETIRE: triggers switched off inside his signed-in
   browser (the D577 way; nothing deleted, one click restores), the Sheets left in place and marked *stopped on
   <date>*, the code kept photographed (S230 · `GAS_CURRENT`), the tile removed in Block A's kit, and after one quiet
   week the mail count measured again against step 1 — a mail that still arrives has its source named, not guessed.

### Block C — the Callback Tracker: kept, and its frictions fixed (D587)

Build order: **4 first** (it unblocks the staff today), then the investigations of 1 and 2, then 3 and 5.

1. **The caller tile on the staff phone.** Today an incoming call shows only the MyOperator number in the phone's
   own dialler. The finalised design — **read it back from the record first, do not redesign it** — is: the call event
   reaches the server within seconds, the server finds the patient by number, and a notification tile shows clinic
   ID, name, last visit and open items. Investigate before building: confirm the incoming-call event reaches our
   receiver (the record says only outbound calls were ever captured — `call_hook_capture.py` skips incoming) and
   measure the delay end to end on a real call.
2. **It loads slowly.** Measure where the seconds go (the dashboard asks MyOperator for the calls on every load);
   then fix the biggest one — most likely serving the call list from the VPS's own copy.
3. **Buttons for everyone.** The WhatsApp call and WhatsApp reply buttons are shown only to the owner; they become
   available to every signed-in staff member, and the record of who used them stays.
4. **One sign-in, through the PWA.** Staff sign in once to the Clinic app and the Tracker opens from it without a
   second login — the portal's single-sign-on (`clinic_sso.py`) wired to it. Shavez has been signed out for days
   because a password had to be fetched from the Apps Script project; this ends that.
5. **The WhatsApp-message ntfy alert (owner and staff) shows the sender's number**, not only the content — his
   ruling; the last-4 masking rule stays for chat and the repository. The Gist and Call Console tiles carry their
   own *needs improvement* list on the same page he ticks.

### Block A — the PWA tiles, last

1. Draft the new layout as a page he opens on his phone — **his own screen first** (35 tiles in six flat sections:
   which sections collapse, the personal cluster behind one door, Stock Check and Marg opening a small menu instead of
   one wrong door, the money tiles whose names do not say what they do), then each staff member's screen. Nothing
   live changes. It runs last because Blocks B and C decide which tiles vanish and which appear.
2. He ticks or corrects on that page.
3. One kit makes it live. The tile system (`portal.py` roles + `tile_grants.json`) stays as it is — it is sound.

**Standing owner rulings:** short, plain English; one paste or one double-click; decide technical questions
yourself; full paths and URLs in copy blocks; do not hand him steps that are not his; Apps Script changes are placed
by the assistant in his signed-in browser, inside the page (D577), and update `GAS_CURRENT` in the same breath
(D583); every walk keeps one check on the real thing (F-590).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_117_S277close.md` |
| History Archive | `KB_History_Archive_v1_114_S277close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_102.md` |
| Runbook | `HANDOFF_RUNBOOK_2026-09-20_Session277close_v197.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| evergreen prompt | `START_HERE_PROMPT_v10.md` |
| live pins | `live_pins_S277close.txt` |
| build brief | `S277_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — mirror at this close: **D588 · F-597 · A-D25 · kit S354 · Session 275 (Sanjeevni) / 278 (this)** |

## 2 · FIRST CHECKS AT THE OPEN

1. **The 21-Sep 01:35 bundle carries `root/finance/spine/`** (12 files) and the 01:50 state-backup log says ~251 files (S347's first real night; carried from S276). If not, that is the first finding.
2. **The 21-Sep Daily Clinic Report (11:39 IST)** reads real attendance — *N present · M absent · K late* — for 20-Sep (S348's first real run; carried).
3. The bulk pin check expects `records.py` `07ec9b41` (S353) — the bundle will still show `8cdd334f` if the open is before 01:35 on 21-Sep; after it, `07ec9b41`. `finance_app.py` `29819879` unchanged.
4. `https://followup.dr-manoj.in/finance/records/xray-test` — one read; state matched / numbered / check and the clock verdict. On the 20-Sep files it read **8 · 0 · 1**.
5. The rescue check's first line: `UNATTENDED_2026-09-21_Q5.md` will be in project knowledge only (F-587) until proposal (c) lands (his one line).
6. `D:\dr-manoj-git\_to_delete_S277\KB_canon_all_bak\` — forty-one checksum backups with `WHY_SAFE.txt`; the canon gate at the open must read green without them (F-596).

*Written at the S277 close, 20-Sep-2026.*
