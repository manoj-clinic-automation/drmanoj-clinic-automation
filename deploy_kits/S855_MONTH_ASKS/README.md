# S855_MONTH_ASKS — a month's open asks, shown wherever they apply (17-Nov-2026, Sanjeevni session 476)

**Why.** The owner, 17-Nov 17:08–17:12 IST: October's bill-wise and supplier-wise statements disagreed (Kedar A000211, Yogendra 19612,
Shivaaz 3854 — Amir corrected Marg on 11-Nov, the supplier-wise statement on the server is of 06-Nov), and the system flagged it but asked nobody
for the fresh export; Janta 21965's old Wrong mark held the payment sheet while the purchase check said "clear". "It should also ask for
whatever reports are needed as a fresh export ... I should need not come to you for these things." "Show prominently at multiple places ...
the payments page, etc., for me as well as for Amir, as you had said for the statement part only."

**Now** (NEW `month_asks.py`, one source; a tail block in four files):
- **Export asks** (a month that has ended, not FINAL): a month-end report not received; the OLDER of the two statements where they disagree
  on a bill (Marg corrected after it); bills still without item lines. Shown on his **payment sheet** (a card at the top), his **purchase check**
  (a card at the top; row 8 counts them — never "clear" while one is open), his **Needs-you** (Bills & papers, opens that month's sheet) and
  **Amir's card** (Hindi: "Marg se yeh report TEXT file mein export kijiye: SUPPLIER WISE PURCHASE STATEMENT, FROM 01-10-2026 TO 31-10-2026").
  Each leaves by itself when the report reaches the server.
- **Wrong marks** (his pages only): settled as a purchase return (S740's track resolved by the dealer's revised bill / credit note) → resolved
  by itself and recorded (Janta 21965 → revised bill B-0271); the paper figure already in the newer report → inside the export ask; on Amir's
  correction list → "with Amir"; anything else → "nothing will clear it by itself" with his one tap **Correct — Marg's figure stands**
  (POST /finance/purchase/api/s855/correct, the doctor only).
- Writes only `purchase_bill.verdict` (those two resolutions, never a FINAL month) and `purchase_audit`. OFF: `/root/finance/_off/S855_OFF`.

**Files:** NEW `month_asks.py` · `purchase_app.py` c54b1c31 · `scan_register.py` 76ad0927 · `sanjeevni_approvals.py` 960efdd3 ·
`amir_day.py` 22d962b8 — whole files by `make_s855.py` (one tail block each, no anchor inside old text).
**Proof:** `synth_s855.py` on a made-up ended month (2025-02) in a copy of finance.db: T0–T12 (T11 the real pages and door in Flask; T12 a same-day disagreement asks no export); the
control (live files + the new module) red. On the box it adds R1–R3 on copies of the live databases (every open month read, its payment sheet
and purchase check drawn, the Needs-you and Amir's lines read — no frozen expectations) and runs walk_s781, walk_s761, walk_s750/753/755,
synth_s849, synth_s850, walk_s814, walk_s845 on the live and the new files — every last line the same.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S855_MONTH_ASKS/undo_s855.sh`.
