# S562_BANK_SMS_STANDS_IN — the bank's morning SMS stands in for the bank (D729)

**Brief:** `claude_code_briefs/S562_BANK_SMS_STANDS_IN.md` (the parent, session 317, 15-Oct-2026). **Decision:** D729.

## What it does (for the owner)
The bank's morning UPI SMS (posted by MacroDroid) fills the bank figure on the clinic's and Sanjeevni's day pages as soon as it
arrives, marked with the SMS time — no confirmation by anyone. When the bank's MPR mail comes it takes over by itself, and the page
shows both figures, both times and the difference (which should be zero). A difference beyond the tolerance is one line for the
owner only, never for staff. **Installed OFF**: the owner switches it on in his box on `https://followup.dr-manoj.in/finance/bank-sms`.
With the switch off every day page is byte-for-byte what it was.

Order of the day's bank figure: **the MPR** (upi_statement / upi_txn) > **the SMS** (bank_sms_settlement) > **the owner-confirmed POS
total** (S496). The POS field is offered to staff only when neither the MPR nor the SMS is in by the expected time.

## Files — pins FROM → TO (built on the box by `make_s562.py`, counted anchored edits on the live bytes)
| file | FROM | TO | edits |
|---|---|---|---|
| `/root/finance/bank_standin.py` | `a35d04f1badcb840d52ee0ea5afcf250` | `fd635862c75e1ab44f770a6ffd79511a` | 16 |
| `/root/finance/bank_sms.py` | `7cdd0ac9ca64921507bd0c65ab6a0e99` | `053d4ccb85d64403daf9918a0ba6f46c` | 6 |
| `/root/finance/clinic_money.py` | `0a2085ca5392646521fc9796485ae5f0` | `7152cd3a7d3dcae6da2a9aee893064e7` | 7 |
| `/root/finance/darpan_kal.py` (the Sanjeevni chat's) | `fd799a56cf212625cfaadce768d3431d` | `a8e11c31b9c80c1b01e63e948418d4a4` | 2 (the source word, its label) |

Read only, must be at their pins: `darpan_app.py a55ecbed`, `sanjeevni_approvals.py 792f4a9a`, `bank_mpr_status.py e1a72305`,
`finance_upi.py 21eb2556`, `owner_console.py 2b985708`, `finance_app.py 87cc4266`.

- **bank_standin.py** — `bank_day(con, unit, d)` (source mpr | sms | pos | None; both figures, both times, diff); `standing()` returns
  the SMS figure (source 'sms') while the switch is on and the MPR is not in; `day()` offers nothing while the SMS stands;
  `owner_items()` adds `sms_diff` / `sms_never` (owner_only) and drops a POS line on a day the SMS stands; `owner_block_html()` draws
  the SMS lines for the owner's login only; the hooks fire when the SMS starts standing (`sms_landed`, `set_sms_on`) and when the MPR
  replaces it (`sweep`). The switch: setting `bank_sms.standin_on` (`sms_on`, `set_sms_on`).
- **bank_sms.py** — the ledger per unit (read from the statement store) × the last 30 business days: SMS time · SMS · MPR mail taken
  (upi_statement.ingested_at) · MPR · difference (owner's login only) · what stands; "SMS nahi aaya" on an MPR-only day; the summary
  "Since <first SMS day>: N days with both — all equal / N equal, M differ" and per unit "SMS came on A of B days"; the owner's ON/OFF
  box (POST, his login only, audited in audit_log). After the door stores a settlement SMS it calls `bank_standin.sms_landed` (fail-soft);
  what the door accepts and answers is unchanged. No JavaScript.
- **clinic_money.py** — the morning-match card: "Bank SMS 07:02: ₹X credited — the bank's MPR mail has not come yet; this figure stands
  until it does." while it stands; after the MPR "Bank SMS 07:02 ₹X · MPR mail taken 09:56 ₹Y · same." (a difference only on the owner's
  login). match_day reads `standin['source']`: an SMS figure is never called a POS total.
- **darpan_kal.py** — `online_source = sp.get('source', 'pos')`; the label "बैंक SMS 07:02" when the SMS stands. Nothing else.

**Data step:** one setting row `bank_sms.standin_on = '0'` (INSERT OR IGNORE). No money row is written by this kit or by the code it
places (no day_entry, cash_movement, upi_statement or upi_txn row is created, changed or removed).

**Restarts:** `clinic-finance` only.

## Install (on the server)
```
rm -rf /tmp/s562kit && cp -rp /root/deploy/repo/deploy_kits/S562_BANK_SMS_STANDS_IN /tmp/s562kit && bash /tmp/s562kit/install_S562_BANK_SMS_STANDS_IN.sh
```
`DRY=1` runs every gate and the walks and writes nothing. `bash rehearse_s562.sh` rehearses on a made-up root (red-after-placing
restore, green, ALREADY INSTALLED).

## The walk (`walk_s562.py`)
The real finance app on scratch copies, made-up rows dated March 2027 (W562 keys, made-up merchant tails, no phone number, no real
account digit): (a) switch OFF = the old files' pages and dicts byte for byte; (b) switch ON, SMS in → stands; (c) MPR lands equal →
"same", hooks fired; (d) MPR differs → one owner line, no staff difference; (e) POS offered with nothing in; SMS beats POS; MPR beats
both; (f) the ledger; (g) two SMS sum, the earlier time; M no money row; R the live store's counts; staff-eye for shavez, alisha,
darpan, manoj. `--expect-red` on the old files: every `C:` check red.

## Undo
```
\cp -p /root/finance/bank_standin.py.bak_S562_a35d04f1 /root/finance/bank_standin.py && \cp -p /root/finance/bank_sms.py.bak_S562_7cdd0ac9 /root/finance/bank_sms.py && \cp -p /root/finance/clinic_money.py.bak_S562_0a2085ca /root/finance/clinic_money.py && \cp -p /root/finance/darpan_kal.py.bak_S562_fd799a56 /root/finance/darpan_kal.py && systemctl restart clinic-finance
```
(the setting row may stay: the old files never read it.)
