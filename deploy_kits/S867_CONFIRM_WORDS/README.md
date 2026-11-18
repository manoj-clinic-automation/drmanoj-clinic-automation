# S867_CONFIRM_WORDS — an owner-confirmed dealer's line says settled or waiting (18-Nov-2026, Sanjeevni session 481; D1003 item 1)

**Why.** The payment sheet showed Ravi Medical Agency's summary as a green "your Confirm" — the same words whether the owner had given his
confirmation or not (his rule, 17-Nov 20:54: wording that reads two ways is reframed plainly). S857 fixed it on the purchase check's row 7
count line only.

**Now** (words only — no figure, state, hold or payable changes):
- **Payment sheet** (`/finance/purchase/page/pay/<month>`, and the printed sheet): "settled by your confirmation" (green) or
  "waiting for your confirmation (purchase check, row 3)" (amber).
- **Dealer ledger and row 7's dealer line:** "Settled by your confirmation — it stands as the summary · Marg ₹…" or
  "Waiting for your confirmation on row 3 of the purchase check — it will stand as the summary · Marg ₹…".
- Per dealer, from the one tally (`scan_register._s749_groups`: row 3's bills waiting vs confirmed); a counted month only. A tally that
  cannot be read says "see the purchase check, row 3" in amber — never green.

**Files:** `scan_register.py` 1aec54b4 · `purchase_app.py` 73e46df0 (one tail block each, `make_s867.py`).
**Proof:** `synth_s867.py` on a copy of finance.db (T0–T7; the real pages in Flask; nothing but the words changes in any counted month);
the control (the live files) red. On the box: R1 on copies of the live databases, and synth_s855/s857/s864, walk_s781/s761/s750/753/755,
synth_s849/s850, walk_s814/s845 the same on the live and the new files.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S867_CONFIRM_WORDS/undo_s867.sh`.
