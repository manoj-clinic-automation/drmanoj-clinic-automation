# S538 — KIT C DESIGN: Marg stock vouchers scanned on the pharmacy lane (kit C of S534_FINAL_BUILD_PLAN, D1091)
*Written at Sanjeevni session 538, 27-Nov-2026, after kit B (S971) went live 18:35 IST. Study by a sub-agent on the 27-Nov bundle (read only, no database).
For Opus to build in a fresh Sanjeevni chat. His "Proceed" 18:42 IST on kit C. Staff wording: mock-up v7 (approved, D1091).*

## What it does
A printed Marg Stock Issue (L0000nn) / Stock Receive (AD000nn) voucher, scanned on the existing PHARMACY lane, is recognised as a stock voucher
(not a bill, not a dealer summary), filed by its voucher number, its lines read (item as printed, qty, batch, expiry), and then:
* settles a kit-B claim Amir answered *Pehle bana chuka hoon* (`stock_voucher_claim` state 'yours', answer 'already'): the scan's number holds the
  item and quantity → closed "scan B-xxxx"; the item NOT on it → back to Amir as *bana dijiye* (a fresh claim round);
* names a cut item: a voucher line Marg's report cut to 15/20/24 letters → `mi_voucher_name` (source 'scan B-xxxx');
* the one-item Stock Register route (`voucher_judge.ask_registers`) stays SECOND: silent while a scan ask is open for that cut name (plan 2.4).

## Where (from the code map; line numbers of the 27-Nov bundle)
**Scan App (2 files — PLANNED line on board/_numbers first, D646; the Scan App chat told at the close):**
* `/root/assetapp/claude_reader.py`: a STOCK VOUCHER rule appended to the pharmacy prompt — BOTH `PHARMACY_PROMPT` and `_S783_PROMPT_BEFORE` rebound
  (the S783 `_post` recognises the pharmacy call by the exact prompt text, L1158; S841's L1222–1231 is the template); `clean` rebound to keep
  doc_kind 'stock_voucher' and `voucher_type` ISSUE/RECEIVE (S835 L1194 is the template).
* `/root/assetapp/asset_register.py`: an S-block cloned from S841 (credit note, L5872–6006): kind 'Stock voucher', doc_kind 'stock_voucher', set by
  compare-and-set BEFORE the fill; header lent: bill_no = the voucher number (`vno` form), bill_date, vendor None; heal after every POST; auto_home
  guard; switch setting `read.stock_voucher` (off = as before); 'Stock voucher' added to the two kind tuples (L2465, L3959 — the F-1422 lesson).
  A distinct kind keeps it OUT of `purchase_app._s452_scan_rows` (kind 'Pharmacy' AND status 'captured', L7663) — Amir's enter list and the
  scanned-not-in-Marg ask never see it.
* NOT touched: `scanner_widget.js` (posts uploadFields verbatim, knows no kind), `/root/shared/scan_checks_s441.py` (no kind filter; a header
  bill_no stops the no-header page join; null amounts never a sure double — one residual 'near' twin between L000045 and AD00045, accepted),
  `sarvam_ocr.py`, `assetapp_backup.py`.

**Sanjeevni (ours):**
* NEW `/root/finance/voucher_scan.py`: reads assets.db READ ONLY — `bills` kind 'Stock voucher' + `bill_items` + `claude_reading`; normalises
  the number with `voucher_judge.vno`; settles claims; writes cut names into `mi_voucher_name`; gates `ask_registers` while a scan ask is open.
  Called from `voucher_inquiry.sync` (fail-soft).
* `voucher_inquiry.py`: claim 'already' → state 'print' (not 'yours'): a print card on Amir's page (*Voucher ka print* — "Voucher ka print
  nikaliye aur reception ko dijiye — ya khud scan kariye (ITEM)" · **Print diya — reception ko** · **Khud scan karein**); scanned and read →
  settled / back to Amir; no scan in `stock.inq_question_days` after *Print diya* → the owner's list. Owner's words in `claims_view` updated
  (drop "the print and scan come with the next kit").
* `amir_day.py`: the print card; *Khud scan karein* = a link `/scanapp/intake?lane=pharmacy&bill_no=<L000045>&from=/finance/amir` (staff logins
  already pass the Scan App's door as 'reception', `_sso_user` L633 / `RECEPTION_OK` L694; the prefill files it by number) — no camera code.
* `/root/finance/porders_s454.py`: an S740-style wrapper on `s736_model` (L3339; S740 L3558 is the pattern) — reception's "Aaj ka bill kaam" gains
  *Stock voucher scan karna hai — ITEM (Amir ne print diya)* with the intake link; ONE push to the reception logins when Amir taps *Print diya*
  (`order_rules._push`, as kit B's `_push`).

## Proof (each in its live shape, F-1703)
A made-up voucher image read → classified 'stock_voucher' (not a bill, not a summary), filed as kind 'Stock voucher' with bill_no L000045; its
lines read; a claim settled by it; an item not on it → back to Amir; a cut name named by it; the register route silent while a scan ask is open;
the real bills' classification unchanged (the lane's own walk green; S841's and S754's walks green); `_s452_scan_rows` never lists it; the switch
off = as before. Cold review + second look + re-look by separate agents. Patterns: `deploy_kits\S971_AMIR_BY_HIMSELF\`, the Scan App's S841 kit.
