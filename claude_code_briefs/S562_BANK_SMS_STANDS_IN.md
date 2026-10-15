# S562_BANK_SMS_STANDS_IN — brief for the build runner (Agent SDK, the API credits)

*Written 15-Oct-2026 ~15:10 IST by the parent (session 317). Kit **S562** and decision **D729** are claimed on the board `_numbers` (v433) with this kit's PLANNED line. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S562_BANK_SMS_STANDS_IN`. Read `BUILD_NORM_v1.md` and `CLAUDE.md` first; they bind.*

## 0 · For the owner (2 plain lines on top of the report)
The bank's morning UPI SMS now fills the bank figure on the clinic's and Sanjeevni's day pages as soon as it arrives, marked with the SMS time. When the MPR mail comes it takes over by itself, and the page shows both figures, both times and the difference (which should be zero).

## 1 · The owner's word (15-Oct 14:59 IST)
*"Bank SMS of the UPI done which is pulled through MacroDroid into the doctor's revenue and the Sanjeevani Marg EMR sales is a valid proof of the amount of the UPI done in that day. And it comes early. The email MPR report occasionally comes very late. So that SMS amount should fill the relevant pages and when the bank MPR comes, then that bank MPR should be added and then we will know if there is any discrepancy from the bank side also in both the figures. Which should not be there as it can be checked from historical data. And wherever this comes, the time should also be there bank SMS time this much amount this much and email MPR arrived at this time and all other details are already populated of the bank MPR email report."*

**D729 (the chat's reading of it, binding for this kit):**
1. The settlement SMS **stands in for the bank by itself** — no confirmation by anyone (he calls it valid proof). It differs from the S496 POS figure, which waits for his confirm.
2. **Order:** the MPR (upi_statement / upi_txn) > the SMS (bank_sms_settlement) > the owner-confirmed POS total (bank_standin). The bank's MPR always wins the moment its statement row exists.
3. **Times everywhere the figure shows:** *Bank SMS 07:02 · ₹X* while it stands; after the MPR lands: *Bank SMS 07:02 · ₹X · MPR mail taken 09:56 · ₹Y · difference ₹Z*. The MPR's own details (transactions, matching) stay exactly as they are today.
4. **A difference** between SMS and MPR beyond the existing tolerance (`bank_standin.tolerance_p`) is **one line for the owner only**, never for staff (his ruling of 12-Oct: day-by-day bank differences are not raised to reception or anyone).
5. **The POS field** (S496) is offered to staff only when **neither** the MPR **nor** the SMS is in by the expected time. With the SMS in, nobody is asked anything.
6. **No money row is written** — like S496 this is a stand-in for matching and display; no `day_entry`, `cash_movement`, `upi_statement` or `upi_txn` row is created, changed or removed.
7. **Installed OFF** behind one switch `bank_sms.standin_on` (kv/setting, default `0`), with an ON/OFF control in the owner's box on `https://followup.dr-manoj.in/finance/bank-sms`. With it off every page is byte-for-byte today's behaviour. The chat shows him; he switches it on.

## 2 · What was read (15-Oct, the 01:35 bundle and its finance.db copy, read only)
- **`/root/finance/bank_sms.py` `7cdd0ac9…`** (S290 → S405 → S439): the door `POST /finance/api/bank-sms`; table `bank_sms_settlement(unit, credit_date, business_date = credit_date − 1, amount_p, balance_p, acct_tail, ref, sms_text, received_at IST, seen)`; `sms_total_p(con, unit, business_date)` → paise or None; `_mpr_p`; the owner page `GET /finance/bank-sms` (Business day × Sanjeevni / Clinic table, Yes Bank SMS, Ignored).
- **`/root/finance/bank_standin.py` `a35d04f1…`** (S496, the parent's): `standing(con, unit, d)` is THE ONE FUNCTION both units read — `clinic_money.match_day` (line ~760, `standin = None if bank_known else _standin(...)`) and `darpan_kal` (line ~304, `_s496_standing` → `online_p`, `online_source="pos"`, `out["standin"]` with `typed_by, confirmed_by, by_owner, never, label`). Also `day()` (whether staff are offered the field), `sweep()`, `owner_items()`, `owner_block_html()`, `bank_state()` (via `bank_mpr_status.mpr_state`), `tolerance_p()`, `expect_hhmm()`.
- **`/root/finance/clinic_money.py` `0a2085ca…`**: `_sms_early_p` is shown today only as an early text on the clinic card (line ~1562: *"Bank SMS this morning: ₹X … the match waits for it"*); the match itself ignores it.
- **`/root/finance/darpan_kal.py` `fd799a56…`** (THE SANJEEVNI CHAT'S FILE): consumes `standing()` and names the source `"pos"` — an SMS figure would wrongly read as a POS total there.
- **The MPR arrival:** `upi_statement.ingested_at` = when the server took the mail (the poller runs at :56 each hour). Use it, labelled *MPR mail taken HH:MM*. **Do not change the MPR reader** (`finance_upi.py`, `finance_app.py`).
- **History (measured, counts only):** 22 SMS business days since 17-Sep (clinic 6, Sanjeevni 16) — **all 22 equal the MPR's upi_txn total to the paise, 0 differ.** SMS at ~07:01–07:11 IST, MPR taken 07:56–16:56 IST next day. **But the phone posted on only 6 of 25 clinic MPR days, 16 of 25 Sanjeevni, 0 of 20 NK Pathology (lab)**, and no ICICI post was refused on the missing days — the phone sent nothing. The ledger must make that gap visible (§4 C).

## 3 · Pins — read each live file, check its md5 = the pin, a different byte = STOP that file and report
- Edited: `/root/finance/bank_standin.py` `a35d04f1badcb840d52ee0ea5afcf250`; `/root/finance/bank_sms.py` `7cdd0ac9ca64921507bd0c65ab6a0e99`; `/root/finance/clinic_money.py` `0a2085ca5392646521fc9796485ae5f0`.
- Edited, the Sanjeevni chat's, **counted edits for the source word and its label only**: `/root/finance/darpan_kal.py` `fd799a56cf212625cfaadce768d3431d`. If more than the source/label is needed there, STOP and report — do not widen.
- Read-only, must be unchanged at install: `darpan_app.py` `a55ecbed…`, `sanjeevni_approvals.py` `792f4a9a…`, `bank_mpr_status.py` `e1a72305…`, `finance_upi.py` `21eb2556…`, `owner_console.py` `2b985708…`, `finance_app.py` (pin it as read at build time).
- Before building, re-read the board `_numbers` claims is not possible from Claude Code — instead confirm in the repository that no newer kit under `deploy_kits/` names any of the four edited files after 15-Oct 01:35.

## 4 · The change
**A · `bank_standin.py` — one source of truth for the day's bank figure.**
- New pure read `bank_day(con, unit, d, now=None)` → `dict(source = 'mpr' | 'sms' | 'pos' | None, amount_p, sms_p, sms_at, mpr_p, mpr_at, diff_p, label, never)`. `sms_at` = the earliest `received_at` of that business day's SMS rows (HH:MM IST); `mpr_at` = `upi_statement.ingested_at` (HH:MM IST, date if not the next day); `diff_p = mpr_p − sms_p` when both exist.
- `standing()` keeps its contract for the POS figure and, **only while `bank_sms.standin_on` = 1**, returns the SMS figure when the MPR is not in, in the same dict shape (`amount_p, typed_by='bank SMS', typed_at=sms_at, confirmed_by='', by_owner=False, never, label`) **plus** `source='sms'`, `sms_at`. The POS dict gains `source='pos'`. Precedence per D729 (2): an SMS figure beats a confirmed POS figure.
- `day()`: `offer` is False while an SMS figure stands (no one is asked).
- `owner_items()`: one line per unit-day where SMS and MPR both exist and `abs(diff_p) > tolerance_p` — *"<Unit> <date>: Bank SMS ₹X (07:02) · MPR ₹Y (09:56) · difference ₹Z"*. Owner only. A day with the SMS standing and no MPR after `NEVER_AFTER_DAYS` reads *"MPR never received — Bank SMS ₹X stands"*.
- `on_change` hooks fire when an SMS figure starts standing and when the MPR replaces it, so `clinic_money.sync_flags` / darpan's day are worked again exactly as for S496.

**B · `clinic_money.py` — the clinic's pages.** Where the card draws the bank line (~1550–1575): with the SMS standing → *"Bank SMS 07:02: ₹X credited — the bank's MPR mail has not come yet; this figure stands until it does."*; after the MPR → the existing line plus *"Bank SMS 07:02 ₹X · MPR mail taken 09:56 ₹Y · difference ₹Z"* (₹0 shown as *"same"*). The existing `standin` branch must not call an SMS figure a *POS total*. `match_day` gains nothing new beyond reading `standin['source']`. Staff text in plain English as today; owner wording English.

**C · `bank_sms.py` — the owner's ledger `https://followup.dr-manoj.in/finance/bank-sms`.**
- The owner's box: the switch `bank_sms.standin_on` (ON/OFF, owner only, audited).
- The day table becomes, per unit (units read from the statement store, not assumed two), per business day (last 30): **SMS time · SMS ₹ · MPR mail taken · MPR ₹ · difference · what stands** (MPR / SMS / POS / nothing). A day with an MPR and no SMS reads **"SMS nahi aaya"**; a day with neither reads *"—"*.
- One summary line on top: *"Since <first SMS day>: N days with both — all equal"* (or *"N equal, M differ"*), and per unit *"SMS came on A of B days"*.
- No JavaScript (F-303), tables on first request, as the page is today.

**D · `darpan_kal.py` (Sanjeevni) — the source word only.** `online_source` = `sp.get('source', 'pos')`; the staff label shows the SMS case in the page's own Devanagari style, e.g. *"बैंक SMS 07:02"*, instead of the POS wording. Nothing else.

## 5 · Walk (`BUILD_NORM_v1.md`) — a made-up root, made-up `finance.db` (dated March 2027)
**No phone number and no real account digit in the walk — the number gate (F-185).**
- **(a)** switch OFF: `standing()`, `day()`, the clinic card, darpan's day and the ledger's figures are identical to the old files' (compare the dicts / HTML); the ledger shows the switch OFF.
- **(b)** switch ON, SMS in, MPR not in: `bank_day` source `sms`; clinic `match_day['standin']['source']=='sms'`, its card says *Bank SMS 07:02*; darpan's day `online_source=='sms'` with the SMS label; staff are **not** offered the POS field even after the expected time.
- **(c)** the MPR lands (insert `upi_statement` + `upi_txn` equal to the SMS): source `mpr`; both times and *same* shown; no owner line; the hooks fired.
- **(d)** MPR differs by more than the tolerance → exactly one owner line, on the owner's page only; a staff login's pages show no difference text.
- **(e)** no SMS, no MPR, past the expected time → the POS field is offered as today; a confirmed POS stands with source `pos`; an SMS arriving afterwards wins over it; the MPR wins over both.
- **(f)** the ledger: per-unit rows, *SMS nahi aaya* on an MPR-only day, the summary counts; a staff login is refused the page as today.
- **(g)** two SMS rows on one business day sum; `sms_at` is the earlier.
- **R · real-store copy (counts only):** on a copy of the live `finance.db` with the switch ON: the 22 SMS days give 22 *same*, 0 owner lines; report the per-unit "SMS came on A of B days" counts. Never print an amount per day in the report.
- **Negative control:** the old files fail (b)–(g).
- **Installer:** gates → pins → compile (both pythons) → rebuild by counted anchored edits on the live bytes (`make_s562.py`, in memory first, each anchor found exactly once) → walk + control → DRY → backups `.bak_S562_<from8>` (and `finance.db` by the sqlite backup API, as the rulebook says; this kit writes only the one setting row) → place → read-back md5s → the setting `bank_sms.standin_on=0` (INSERT OR IGNORE) → restart only the service(s) that import these modules → health (`/finance/healthz` 200) → read `https://followup.dr-manoj.in/finance/bank-sms` and the clinic money page as `manoj`, switch OFF. Rehearsed on a made-up root (green · ALREADY INSTALLED · red-after-placing restores). `SUMS.md5`; no `.json` in the kit. The number gate: `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`. Take and hold the server build lock per `CLAUDE.md`.
- **Housekeeping inside this install (the parent's standing item):** remove the earlier kits' scratch on the server — `/tmp/s554kit`, `/tmp/s554probe`, `/tmp/s561kit` — after checking each holds no secret and no number (list them, count only). If the delete is blocked, say so in the report; never a line for the owner.

## 6 · Install, publish, report
- After the install, read the two pages as `manoj` with the switch **off**, then report. **Do not switch it on.**
- Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (CLAUDE.md).
- Write `claude_code_briefs/REPORT_S562.md`: 2 plain lines on top (§0), then the proof — pins FROM → TO with full md5s, the walk counts, the old-file red count, the services restarted, the one undo line, the cost, and every decision you made where this brief is silent.

**NEVER:**
- write a money row, or change `upi_statement`, `upi_txn`, `day_entry`, `cash_movement`;
- change the MPR reader or the SMS door's acceptance rules;
- show a bank difference to a staff login;
- print, log or report an SMS text, an account digit beyond what the page already masks, a key, or a per-day amount in the report;
- edit `darpan_kal.py` beyond the source word and its label, or any other Sanjeevni file;
- switch the feature on.
