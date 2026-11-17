# S850_MARG_IS_RIGHT — Marg taken over a misread scan line; "Marg is right"; the corrections kept (17-Nov-2026, Sanjeevni session 476; D993 b–d, D995; F-1440)

**Why.** The owner, 16-Nov 12:00–12:34 IST (D993): Marg accepted over a scanned line automatically when the totals agree, one tap
"Marg is right" otherwise; every accepted line kept as a correction, a monthly list to the Scan App's reader; built in a fresh session.
17-Nov 11:38: "ok" on mock-up v2 https://claude.ai/artifact/FY6ubLCgQTww6g3Aqsjjzh (tabs 3 and 4). F-1440: B-0122 showed "no clear match"
though its read number is Marg bill 3499 and its total agrees.

**Now** (NEW `marg_right.py`; seams in three files; no new screen):
- **Scan reading against Marg** (`/finance/purchase/page/sarvam?month=`) gets two cards under its table. *Lines that differ*: each linked bill
  with a scan line differing from Marg's (name, qty, rate, batch, expiry — as `purchase_sarvam_check` holds them), the scan's and Marg's
  values side by side. Totals agree (the stored `total_ok`, the scan's total within ₹1) → "Marg accepted — totals agree", by itself (folded).
  Totals differ → one tap **Marg is right** (the doctor; Undo beside it), or left for Amir's "Where Marg differs" as today.
  *Corrections kept*: by kind, by totals / by a tap, with the month's counts — the list for the Scan App chat (a board note each month; never
  its file). October on the 17-Nov copy: 84 bills, 64 with a line differing, 60 by totals, 4 for a tap.
- **The Item ledger**: each purchase row carries its line's verdict beside its Scan button ("Marg accepted — totals agree · scan read batch
  …", "Marg is right · manoj", "agrees", or "the scan differs — a tap on Scan reading against Marg").
- **F-1440** (`scan_ask._candidates`): a candidate whose number matches the paper's and whose total is within ₹2 is the best, whatever the
  read lines say (the only such one); its wording says so ("its bill number and its total agree …"; Amir: "bill number aur total same hai").
- `purchase_sarvam_check` stays strict (D891): never written. Writes: `s850_tap`, `s850_correction`, `purchase_audit`. `assets.db` read only.
  OFF: `/root/finance/_off/S850_OFF` (or ALL_OFF) — no cards, no ledger tags, no tap (F-1440 is not switched).

**Files:** NEW `marg_right.py` · `scan_ask.py` 41adf66b · `purchase_app.py` b789e379 (the page's cards + `/api/s850/line`) ·
`item_ledger.py` 49768145 — whole files by `make_s850.py` on exact anchors.
**Proof:** `synth_s850.py` 26/26 on made-up bills of a made-up month beside a copy of finance.db and a made-up assets.db (T0–T22, T16b/c F-1440 with no total read, T18 the real
page and route in a Flask app); the control (live files + the new module) red 3. Cold review: SAFE, its points 1–8 built in (a tap belongs to its Marg bill; lines paired as the check pairs them; a kept misread never overwritten); second look SAFE. Rehearsal 10/10. On the box the installer adds R1–R3 on copies of the live
databases (October judged, its corrections kept from the scans' own readings, a second open writes nothing; B-0122 names 3499 while asked)
and runs walk_s781, walk_s761, walk_s750/753/755, synth_s849, walk_s814, walk_s845 on the live and the new files — every last line the same.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S850_MARG_IS_RIGHT/undo_s850.sh`.
