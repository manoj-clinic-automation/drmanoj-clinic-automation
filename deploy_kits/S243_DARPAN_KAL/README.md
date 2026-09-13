# S243_DARPAN_KAL -- Darpan's morning page: "Kal ka hisaab"

Built 13-Sep-2026 (S243) to the owner's ruling of the same day and his answers to the design's
open points (design: `S243_DARPAN_DAY_DESIGN.md`). **Design decisions honoured:** rides on the
D354 auto-applied day and never files one · two inputs only · the server checks his reason ·
excess = owed back to him, no reason asked · a "received" tap that may come later (amber, never
red) · no deterrent line anywhere · no kharcha reason · Rs 50 day line, Rs 2,000 month cap ·
`procedure_customer_name` setting reserved for the word he will give · no new patient field.

## What Darpan sees -- `/finance/darpan/kal` (Hindi, phone-first)

| line | from |
|---|---|
| कल की बिक्री (Marg) | `sale_item` bills net of credit notes, + parked review bills (`v_day_attribution.in_review_p`) |
| − घर / प्रोसीजर की दवा | `sale_item.home_med=1` (the S194 ingest tag) ∪ `day_noncash_bill` heads ∪ bills whose customer text matches setting `procedure_customer_name` (blank until he gives the word) |
| − Online (UPI/card) | `upi_txn` for the day when its `upi_statement` is in (badge "bank से"); else Marg's own non-cash modes, badge "bank की report बाकी", re-decided when the statement lands |
| = इतना cash होना चाहिए | the difference of the three |
| **कितना cash दिया?** · **किसको दिया?** | his two inputs; Dr Manoj / Dr Bhawna |

Match (≤ Rs 50, setting `darpan_kal.tolerance_p`) → "✓ हिसाब मिल गया", day complete. Short → the
rupees and five reasons (घर/प्रोसीजर दवा printout में नहीं · online payment POS पर नहीं दिखा · वापसी
नकद दी · कल दूँगा/कल दिया · और कुछ + दो शब्द). More → "✓ लिख लिया · ₹X ज़्यादा", recorded in
`darpan_kal_owed`, shown to him under "आपको वापस मिलना है" until the owner marks it returned.
Second section **कल की वापसी**: the count, and only the flagged returns opened (money verdicts
from `finance_returns_audit`, `returns.large_p`, desk flags), five answers each.

**Money landing.** The handover is ONE `cash_movement (out, party=<recipient>, reference '[kal] D -> party')`
on the day's own `day_entry` -- the same record `/finance/darpan/api/handover` writes -- so
`v_cash_ledger`, `/finance/api/cash-position` and the doctors' ledgers stay one arithmetic.
Re-typing before "received" updates the same row. No `day_entry`, `day_line`, `sale_item`,
`day_noncash_bill` or `cash_custody_event` is ever written (walk-proved).

## The server's checks (`check_reason`, verdict per reason in `darpan_kal_check` with evidence)

| reason | confirmed | not confirmable (his word stands) | contradicted → owner |
|---|---|---|---|
| home/proc not in print | a home/proc bill (or their sum) ≈ the gap | such bills exist, sum differs | no such bill on the day |
| online not on POS | a settled txn against a bill rung cash (`upi_match status='cash'`) or any `upi_txn` ≈ the gap | statement not in yet | statement in, nothing of that size; or the gap is a surplus |
| return refunded in cash | a `return_visit closure='cash'` slip with no CN ≈ the gap | slips/CNs exist, none match | no slip and no CN on the day |
| carried | the next two days return it | not yet | 2 days passed, not returned |
| other | -- | always | -- |

States: `waiting_report` (no report yet; claim kept, decided when the day is applied) · `open`
(short, reason not yet chosen) · `complete` · `explained` · `needs_owner`. Repeat patterns
(`patterns()`, computed fresh on the card): same reason ≥3× in 30 days · last ≥5 differences all
short · "carried" open >2 days · shortfalls > `darpan_kal.month_cap_p` (Rs 2,000).

## Who sees what

* **Darpan (maker):** the Hindi page, yesterday by default, any date by the picker.
* **Dr Bhawna (viewer, named in `darpan_kal.recipients`):** the same URL shows only the days
  handed to HER, one button "मिला · received". She cannot open or stamp Dr Manoj's days (walked).
* **Owner (checker):** hub card **"Darpan -- needs you"** on `/finance/approvals#kalCard` --
  one English line per item: contradicted day (with the why), pattern, flagged return answered
  "other"/money flag, cash owed to Darpan (button "returned"), handover not yet received (amber),
  report not applied by 11:00. Each day line opens `/finance/darpan/kal/<date>?view=owner` -- the
  arithmetic, his inputs, the evidence, accept / ask Darpan / reject, received, and links to
  `/finance/api/day/<date>/full` and the returns card.

## Install (the owner's double-click publishes; then ONE line on the VPS)

```
bash /root/deploy/repo/deploy_kits/S243_DARPAN_KAL/install_S243_DARPAN_KAL.sh
```

Refuses unless `finance_app.py` is `f002defb…` **or already carries the S243_SCREEN_FIXES mark**
(that kit installs first and moves the pin; the patcher's count==1 anchor is the real guard, and the
ACTUAL from-pin is recorded in the `.bak_S243_<pin8>` name and the printout) and
`finance_approvals.html` is `cc349dd0…` (the 13-Sep capture). Writes `.bak_S243_f002defb` / `.bak_S243_cc349dd0`, patches to `.new`,
py_compiles, import-smokes under the unit's environment (the `darpan_kal` blueprint must be
registered), restarts, waits for healthz. Any RED → both files restored, new files removed,
service restarted. Re-run → ALREADY INSTALLED. **Predicted to-pins:** `finance_app.py`
`1aa9af6db1e625bc68402ff8a77c0248` from f002defb alone, `f93f7430b5c36449d520d41b6012ec3d` after
SCREEN_FIXES (4cd8f966) then this kit; hub `7dbb5e56a6564abbfebaa6f94cee484c`. **The installer also
seeds the recipients** (`manoj` → dr_manoj, `bhawna` → dr_bhawna, viewer role for `bhawna`) — idempotent,
never overwrites a hand edit — so nothing is left for the owner but the tile.

Rollback by hand:
```
\cp -f /root/finance/finance_app.py.bak_S243_<pin8 printed by the installer> /root/finance/finance_app.py && \cp -f /root/finance/finance_ui/finance_approvals.html.bak_S243_cc349dd0 /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
```

**Step 2 (GUI, owner):** repoint Darpan's portal tile to `/finance/darpan/kal` (tiles show, gates
decide -- no portal patch shipped; the new page links back to the old card, the old URLs stand).

**Recipients (done by the installer; re-runnable by hand with other logins if ever needed):**
```
/root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_DARPAN_KAL/seed_kal_recipients_s243.py /root/finance/finance.db manoj bhawna
```
It sets `darpan_kal.recipients` and adds `unit_role(medical, bhawna, viewer)` -- the S221/S222
precedent; the Vaapsi desk stays closed to her (`returns.desk_users` does not name her).

**After install, prove on the box (builds its own db, touches nothing live):**
```
FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_DARPAN_KAL/walk_darpan_kal_s243.py
```

## Files

| file | role |
|---|---|
| `darpan_kal.py` | the module: pages, api, arithmetic, checks, patterns, landing |
| `darpan_kal_schema.sql` | 5 tables + 4 settings, idempotent, run by `ensure_schema` on every request |
| `darpan_kal.html` | the one page: Hindi staff view · recipient view · owner English view |
| `patch_finance_app_darpan_kal_s243.py` | on-box patcher for both live files, `--selftest` |
| `install_S243_DARPAN_KAL.sh` | the installer (gates, pins, backups, smoke, healthz, rollback) |
| `seed_kal_recipients_s243.py` | names the recipients manoj/bhawna (run by the installer) |
| `walk_darpan_kal_s243.py` | live-shape walk, 72 checks incl. the rendered PAGE walk (maker, Dr Bhawna, anonymous, owner hub, no-report day) |
| `mock_install_darpan_kal_s243.sh` | the installer's five ROOT proofs (wrong pin, install, ALREADY, healthz rollback, SCREEN_FIXES lineage + seed) |

## Not built / open

* The "Claim" tab (amir_claim chase folding in) is a visible disabled tab slot only.
* The corrections desk is not touched here; its retirement to a monthly accountant report is a
  separate kit.
* Phase 2 (owner OK): let the check pass write `day_noncash_bill` rows for `home_med=1` bills so
  `v_cash_ledger.noncash_p` stops reading 0 on auto-filed days.
