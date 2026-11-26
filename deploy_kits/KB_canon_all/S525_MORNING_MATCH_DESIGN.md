# S525_MORNING_MATCH_DESIGN — the Morning Match as he approved it (S525, the parent, 26-Nov-2026)

**His "ok" 12:58 IST 26-Nov** on mock-up v2.1: https://claude.ai/artifact/KVC77sMev1YwczYXWy4PzF
(canvas: 1 the full flow · 2 evening check · 3 refund · 4 staff morning · 5 his morning). Sample names only.
Records D1076 (his 11:44 / 11:55 words, S524) and D1080 (his ok and his S525 words below). F-1687: the reception agent posts reports only after its 5-min heartbeat (kit B).
F-1678 (refund drops out → false cards) and F-1679 (Shavez "Added" on slips only his login can back-date) are closed by kit C.

## His words this session
- 12:21 — evening: reception AND Shavez notified in minimum time, of the flaws and of the corrected export; "15 minutes is too much at closing".
  Refund: "sometimes docterz might also get this cancellation, so system shd behave accordingly". Morning: "drop cash / upi, as its
  already on physical register". The back-date list: "shavez also sees it so he can remind me" — "Automatic".
- 12:30 — "DIRECT server upload shd be there already, if not then how about it"; "a all good notification also if 1st export has no issues".
- 12:58 — "ok".

## What the live estate does today (read at S525 from the 26-Nov 03:18 bundle; RE-READ the newest bundle before building, F-472)
- FROMs: finance/day_check.py d5c95ea9 · not_in_docterz.py 4ad98ab0 · clinic_register.py 321f659a · slip_adjust.py 41c55a99 ·
  slip_log.py 3553a965 · finance/docterz_pickup.py a6cbdb8b · reception_door.py 417ae384 · docterz_ingest.py 4c7c055e ·
  followup_tracker/server_runner.py db758e8b · followup_tracker/docterz_pickup.py ddbed001 (QUIET_SECONDS 180) ·
  portal/callback_clock.py is DECLARED-PENDING 8cebe3b3 (S957) until the 27-Nov bundle — the bundle's 5fbcd29c is older.
- The chain from export to day check: export lands (reception agent direct POST after its 5-min heartbeat, or the Drive pickup
  cron */15) → tracker server_runner cron */5 (waits 180 s quiet) → outputs → docterz_ingest cron */10 → clinic_day_line /
  clinic_day_tender → day_check computes on read. Worst case ~30+ min.
- Measured on the 26-Nov database copy (counts only): 16–25 Nov, every evening consultation export (5 of 5) was taken by the
  Drive pickup, 3–13 min after Drive's file time; the direct road delivered only the morning catch-ups (20-Nov). Cause most
  likely: the agent sends reports only after its 5-min heartbeat (beat_seconds 300; tick_seconds 5) and the PC is off before that.
- Register (clinic_register_day): {cons,xray,proc,dress}_{cash,upi,card}_p — no refund column. Radd = slip_adjust kind 'cancel',
  cancel_how returned | never_taken, waits for approval, approved → slip state 'cancelled'.

## The three kits (order: A + B first — the evening is the priority — then C)

**A · EVENING_CHECK (server, the parent).**
1. On every TAKEN consultation report for TODAY (hook after docterz_pickup.take — both roads: reception_door and the Drive
   pickup), compute at once — never through the tracker's 180 s quiet — today's slips (OPD / X-ray / procedure, with a clinic
   ID, state ok, not refunded, not marked free/wrong in nid_mark) whose (clinic ID, kind) the export does not carry. Read the
   stored export with docterz_pickup's own reader; confirm from followup_tracker/processor.py that X-ray / procedure lines are
   in the consultation report (day_check's sections come from it).
2. Push to the Shavez and reception logins (the portal's Web Push, ntfy fallback — callback_clock.send()'s road), once per export:
   clean first export → "✓ <day>: sab parchi Docterz mein — PC band kar sakte hain"; slips missing → "N parchi Docterz mein nahi"
   with the names; a later export that clears a named list → "✓ Sab parchi Docterz mein — kaam poora".
3. The slip desk shows the panel (artboard 2): names, ID, what, amount; "Paise nahi liye" (nid_mark act free, staff-allowed).
4. Drive pickup every minute 19:00–22:59 Mon–Sat (a second cron line; */15 stays for the rest of the day).
Target: about 1 minute from the click of export to the phones.

**B · RECEPTION_FAST_UPLOAD (reception PC agent, the parent).** Decouple the report upload from the heartbeat: on each 5 s tick,
stat the two export folders (names + mtimes only); a new or changed report → the existing signed POST at once (same first-line
check, same md5 dedupe). Delivered by the signed server job door (reception_sign.py on manojz) — no visit to reception.
READ THE LIVE AGENT'S BYTES FIRST (a read-only job): the repository copies (S448 d3d4b67b, S449 74829388) may not be what runs.

**C · MORNING_MATCH (server, the parent; closes F-1678, F-1679).**
- Refund: "Fee lautai" on the slip → Cash / UPI → a Refunded tag at once (no approval wait — his screen accepted it).
  The register gains a refund line per tender (filled from the tags; staff confirm). Matched both ways: Docterz kept the bill →
  "billed · refunded ✓"; Docterz cancelled too → "cancelled · refunded ✓", never subtracted twice. A card only when tag and
  register line disagree.
- Top line: Register (net of refunds) = Docterz + slips not in Docterz − refunds Docterz still bills (+ not explained).
  Matched patients folded; refunds folded.
- No Cash / UPI taps. A slip still not in Docterz goes to HIS back-date list by itself (the same rows as
  /finance/clinic/not-in-docterz — one list). Shavez sees that list read-only, with "Dr sahab ko yaad dilayein" (a push to his
  login, rate-limited) and one tap "Paise liye hi nahi". No "Added" for any staff login.
- Staff exceptions left: Docterz bill with no slip → Parchi banao · payment mode · money not explained.
- His console line: "<day>: all matched" or the counts (artboard 5).

## Standing rules for the builder
Kit numbers from board/_numbers (read kit_next right before taking) · walk with a red control · rehearsal · cold review by a
sub-agent + a second look · live pages read by a sub-agent, counts only · no patient name, number or clinic ID in any kit file.
