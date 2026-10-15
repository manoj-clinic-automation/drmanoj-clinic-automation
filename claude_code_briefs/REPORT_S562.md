# REPORT S562_BANK_SMS_STANDS_IN — the bank's SMS stands in (D729)

The bank's morning UPI SMS now fills the bank figure on the clinic's and Sanjeevni's day pages as soon as it arrives, marked with the SMS time. When the MPR mail comes it takes over by itself, and the page shows both figures, both times and the difference (which should be zero).

**Status:** installed and working, **switched OFF** as the brief asked. You switch it on yourself in your box at the top of https://followup.dr-manoj.in/finance/bank-sms ("Switch ON"). Until then every day page is exactly as before.

---

## For the chat — the proof

**Built and installed 15-Oct-2026 (IST, read from the box):** build lock taken 15:57:35 · install 16:02:32 → 16:03:04 · `clinic-finance` restarted 16:02:59 · read-back 16:03:24.
Installed from `/tmp/s562kit`; it is byte-identical to `deploy_kits/S562_BANK_SMS_STANDS_IN/` (all 7 md5s compared).

### Pins FROM → TO (md5 read back on the box after placing)
| file | FROM | TO (read back) | counted edits |
|---|---|---|---|
| `/root/finance/bank_standin.py` | `a35d04f1badcb840d52ee0ea5afcf250` | `fd635862c75e1ab44f770a6ffd79511a` | 16 |
| `/root/finance/bank_sms.py` | `7cdd0ac9ca64921507bd0c65ab6a0e99` | `053d4ccb85d64403daf9918a0ba6f46c` | 6 |
| `/root/finance/clinic_money.py` | `0a2085ca5392646521fc9796485ae5f0` | `7152cd3a7d3dcae6da2a9aee893064e7` | 7 |
| `/root/finance/darpan_kal.py` (the Sanjeevni chat's) | `fd799a56cf212625cfaadce768d3431d` | `a8e11c31b9c80c1b01e63e948418d4a4` | 2: the source word, the label |

The four FROM pins matched the brief exactly. Read-only files were at their pins at install: `darpan_app.py a55ecbed4bbe1230b24565b4185b8755`,
`sanjeevni_approvals.py 792f4a9af1728c76e8d5a656f5662421`, `bank_mpr_status.py e1a72305cca72b90afcaa6b61bda626d`, `finance_upi.py 21eb25560cbb4c5ac35adacf9d46f8d0`,
`owner_console.py 2b985708b1dc3239fafbb7f41e969e55`, `finance_app.py 87cc4266f9cd05f3633f23e1f36488a0` (pinned as read at build time).
No newer kit under `deploy_kits/` names any of the four edited files after 15-Oct 01:35. S556 (14-Oct) only mentions them, and the pins confirmed nothing had changed.

**Data step:** one row, `setting bank_sms.standin_on = '0'` (INSERT OR IGNORE; written now; read back `'0'`). No money row was written.
**Backups:** `/root/finance/finance.db.bak_S562_20261015_160232` (sqlite backup API, 0600); `bank_standin.py.bak_S562_a35d04f1`, `bank_sms.py.bak_S562_7cdd0ac9`,
`clinic_money.py.bak_S562_0a2085ca`, `darpan_kal.py.bak_S562_fd799a56` (beside each file).
**Services restarted:** `clinic-finance` only. After the restart: `/finance/healthz` 200 (local and public). `/finance/bank-sms` and `/finance/clinic/money` gave 302 without a login, which is the login gate and expected. Both services are active. The journal shows no Traceback, Import or Name errors since the restart; its one "[ERROR]" line is gunicorn's own "worker was sent SIGTERM" during the restart.
**Page look after placing** (the placed files copied, a copy of the live database, the real clock, signed in as `manoj`, switch OFF): `/finance/bank-sms` 200, showing "Bank SMS stands in for the MPR: OFF" with his "Switch ON" button, 3 unit tables, 90 day rows. `/finance/clinic/money` 200.

### The walk (`walk_s562.py`): 74 checks green
It runs the real finance app (Flask test client, a walk-only header session, a walk-only door key) on scratch copies, using made-up rows dated March 2027.
- **(a) switch OFF = today.** Eight pages are byte-for-byte the old files' pages, each rendered in its own child process on an identical copy: the clinic card as shavez, alisha and manoj (×2 days), Clinic money, Darpan's day (×2), and the owner's Kal card. `standing()`, `day()` and `owner_items()` give the old dicts. The ledger's SMS/MPR figures equal the old page's: 2 made-up cells, plus 53 real unit-days on the live store with the real clock. The ledger shows the switch OFF.
- **(b) switch ON, SMS in, no MPR.** A staff checker's POST is refused. His POST switches it on and is audited (`audit_log` row by manoj). The hooks re-worked both units' day. `bank_day` gives 'sms' with time 07:02. `match_day.standin.source` is 'sms'. The stored `mpr_missing` flag was cleared by the hook. The card says *"Bank SMS 07:02: ₹1,234 credited — the bank's MPR mail has not come yet"* and never "POS". There is no POS field after 10:00. Darpan's day shows `online_source` 'sms' with the label *"बैंक SMS 07:04"*, and the field is neither offered nor shown.
- **(c) the MPR lands equal.** The hooks fired for both units. Source is 'mpr', mail taken 09:56. The card reads *"Bank SMS 07:02 ₹1,234 · MPR mail taken 09:56 ₹1,234 · same."* There is no owner line.
- **(d) the MPR differs by more than the tolerance.** Exactly one line appears on his Clinic money page: *"Clinic Thu 04-Mar-2027: Bank SMS ₹5,000 (07:05) · MPR ₹5,200 (09:56) · difference ₹200"*. His own card shows the difference. Dr Bhawna's page, Shavez's and Alisha's cards, Shavez's ledger and Darpan's day show no difference text.
- **(e) no SMS, no MPR, past the time.** The POS field is offered as today, on the clinic card and on Darpan's form. His POS figure stands with source 'pos'. An SMS arriving afterwards wins ("Bank SMS 11:05", POS box gone; Darpan 'sms'). The MPR then wins over both, and the POS row is kept as "replaced".
- **(f) the ledger.** It has one table per unit of the statement store (Clinic, Sanjeevni, NK Pathology), 30 days each. An MPR-only day reads "SMS nahi aaya"; a day with neither reads "—". The summary lines match an independent count. Alisha and Darpan get 403 on the page, as today.
- **(g)** Two SMS on one day sum to ₹1,250, and the time shown is the earlier one (07:01).
- **M:** none of `day_entry`, `sale_item`, `cash_movement`, the counter sheet, Docterz or `darpan_kal_day` changed. `upi_statement`/`upi_txn` hold only the walk's own W562 rows.
- **R (copy of the live store, switch ON, real clock; counts only):** 23 SMS business days. 22 have both an SMS and an MPR: **22 same, 0 differ, 0 owner lines.** 1 (Sanjeevni) is standing because its MPR is not in yet. The SMS came on: **Clinic 6 of 24, Sanjeevni 16 of 24, NK Pathology 0 of 19** MPR days since 17-Sep. The brief counted 25/25/20; the window here is statement days from 17-Sep up to yesterday.
- **Staff-eye (S444 rule)** for shavez, alisha, darpan and manoj, with the switch both OFF and ON: every duty's tile is on its person's portal home, every door answers 200, and no due duty's marker is hidden by this kit (one marker gap is old; see below). Staff pages are under 150 KB and under 3 s. The ledger page took 0.03 s.
- **Negative control:** the same walk on the old files turns **every one of the 21 "C:" checks red** (26 of 62 checks red).
- **Rehearsal** (`rehearse_s562.sh`, made-up root, stub systemctl/journal): a forced red after placing put all four files back byte-identically (exit 1). The green run placed them, wrote the setting '0' and gave PAGE OK. Housekeeping removed a clean made-up folder and left one holding a phone-shaped number. The second run said ALREADY INSTALLED. The live files were untouched throughout.
- **Gates:** both pythons (`/usr/bin/python3`, `/root/wa/venv/bin/python3`) compile everything. SUMS passed. `NO_PHONE_NUMBERS.py` was clean on all 7 kit files. The kit has no `.json`.

**Housekeeping (the parent's standing item):** `/tmp/s554kit` (11 files), `/tmp/s554probe` (3) and `/tmp/s561kit` (7) were checked first: no secret-shaped file and no phone-shaped number. All three were removed.

**DUTY_MAP:** unchanged. This kit adds, moves or removes no staff duty: the POS figure was never a duty (S496), and the SMS asks nobody anything.

### Undo (one line, on the server)
```
\cp -p /root/finance/bank_standin.py.bak_S562_a35d04f1 /root/finance/bank_standin.py && \cp -p /root/finance/bank_sms.py.bak_S562_7cdd0ac9 /root/finance/bank_sms.py && \cp -p /root/finance/clinic_money.py.bak_S562_0a2085ca /root/finance/clinic_money.py && \cp -p /root/finance/darpan_kal.py.bak_S562_fd799a56 /root/finance/darpan_kal.py && systemctl restart clinic-finance
```
The setting row can stay; the old files never read it. Then check `/finance/healthz` 200 and read the md5s back.

### Cost
About **$8.5 of API credit** for the whole run (the session counter read $8.09 when this report was started).

### Decisions I made where the brief is silent
1. **The switch also gates `bank_day`'s 'sms' source.** With it OFF, the ledger still shows the SMS, but "what stands" never reads SMS.
2. **OFF means byte-for-byte.** With the switch OFF, `standing()` returns the S496 dict *without* the new `source` key. With it ON, a POS figure carries `source='pos'`. Darpan reads `sp.get('source','pos')`, so both states read right.
3. **A difference is the owner's alone.** The clinic card's "Bank SMS … · MPR …" line shows the difference only on his login. Other logins see "same" when the figures are equal, and no comparison line when they differ. On the ledger, the Difference column and the "N equal, M differ" summary are his alone. Shavez and Dr Bhawna (clinic checkers) used to see "differs by ₹" on the old ledger; they no longer do, per his 12-Oct ruling.
4. **Owner lines look back 30 days (no "Seen" button).** The SMS-vs-MPR lines look back 30 days (the ledger's window), with no "Seen" state, because the kit writes no new row. "MPR never received — Bank SMS ₹X stands" uses S496's own never-rule: a later MPR is in, or 3 days have passed.
5. **On a day the SMS stands, POS lines go quiet.** He gets no POS line for it ("waiting for you" or "never received"). A typed POS row is left as it is, not lapsed, since nothing is written. S496's sweep closes it when the MPR comes. A POS figure posted to the address directly on such a day is not refused, but it changes nothing because the SMS outranks it.
6. **When the hooks fire.** They fire when an SMS is stored with the switch on (the door calls `bank_standin.sms_landed`, fail-soft; the door's acceptance and answers are unchanged). They fire when he switches it (every SMS day of the last 30 without an MPR is re-worked). They fire when the MPR replaces an SMS (seen by the sweep on a page read). After a service restart, the first read only notes the state; page reads re-work the day, as S496 already does.
7. **Times are shown as `07:02`** when received on the morning after the business day, otherwise as `dd-Mon HH:MM`. The same applies to "MPR mail taken" (`upi_statement.ingested_at`; on a zero-UPI day with no statement row, the raw file's time).
8. **The clinic match flags an SMS that differs from Docterz.** If the standing SMS is beyond the tolerance from the online money Docterz expects, the match raises one `sms_diff` flag on the staff card. It is worded as the bank's SMS, never a POS total. This mirrors S496's `pos_diff` and today's bank-vs-Docterz flags; it is not an SMS-vs-MPR difference.
9. **How the ledger counts.** Per-unit coverage counts days whose MPR is in (since the first SMS day, before today). The ledger's MPR figure is the one the match uses: the `upi_txn` total, or the statement's parsed total when it has no rows.

### Outside the brief: noticed, not touched
- **Darpan's page does not draw the SMS label yet.** `darpan_kal.html` draws the stand-in label only when `online_source == "pos"`. With 'sms', Darpan sees the general "bank की report बाकी" badge, and the owner's view shows the Marg wording. The label "बैंक SMS 07:02" is in the data but not drawn. A one-line change in `darpan_kal.html` is needed, for the Sanjeevni chat; I did not touch it because the brief allows `darpan_kal.py`'s source word and label only.
- **Darpan's day re-decides only for 'pos'.** `darpan_kal._refresh_if_needed` (~line 609) re-decides an already-decided day only when the source is 'pos'. A Darpan day decided on Marg's figures before the SMS stood is therefore re-decided only when the MPR lands, which is today's behaviour. Widening it to 'sms' would have gone beyond the two allowed edits. For the Sanjeevni chat.
- **Shavez's duty marker is missing on his list page.** In the DUTY_MAP, `shavez.match_check`'s marker "first pass" is not on `/finance/clinic/match` when 2 or more days wait; the list page says "pehli jaanch". This is the same on the old files and is old, not caused by this kit.
- **Other checkers can see the phone's key.** The ledger page's "Phone setup" fold shows the phone's door key to every login allowed on the page (the clinic checkers too), not only the owner. This is unchanged and old.
- **The phone misses many days.** It posted on 6 of 24 clinic MPR days, 16 of 24 Sanjeevni and 0 of 19 NK Pathology. With the switch on, the SMS can only stand on days the phone actually sends. The ledger now shows the gap per unit.

**Lock and permissions.** The build lock was held from 15:57:35 until this report was written, and removed at 16:05:04 IST (its one file, then the empty folder).
One command was refused by the permission list: a single `rm -rf` of the lock together with my own scratch `/tmp/s562kit` and `/tmp/s562probe`. I did not respell it. Those two folders are left for the next kit's housekeeping, as with S554/S561. They hold the kit's own files, the probe scripts and the install log: counts and the walk's made-up figures only, no secret and no phone number.
