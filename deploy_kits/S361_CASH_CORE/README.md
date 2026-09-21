# S361_CASH_CORE — kit README

**Project:** Sanjeevni (session 280, 21-Sep-2026) · **Part 1 of** S280_CASH_ARCHITECTURE_AND_MONTH_TABLE · **Touches a parent file:** no.

## What it does
Puts in place **one calculation** for where the counter's cash is — Darpan's drawer, Dr Bhawna, Dr Manoj, the bank — on any date, and the **month table** (sale · UPI · cash · home medicine · procedure · paid elsewhere · cash income · Marg's own sale beside it).

It starts from the **counted** position of 17-Aug-2026 (drawer 0 · Dr Bhawna 1,56,235 · Dr Manoj 18,963; the ₹20,000 August advance paid out of that clearing) and reads every handover from **both** registers (cash_movement and cash_custody_event), counting each once — the double model that produced four different drawer figures.

## What it writes
- `/root/finance/sanjeevni_cash.py` — NEW.
- `finance.db` — four NEW tables, nothing existing touched: `cash_anchor`, `cash_handover_cover` (which days each August handover paid for), `cash_bill_ruling` (20-Aug bill 2777 paid at the clinic counter — the owner's ruling of 21-Sep), `cash_period_close` (the ₹7 of 17–31 Aug, rounding). One transaction, committed only if the proof is green; the database is backed up first.
- **No screen changes and no restart** — nothing imports the module yet. Part 2 moves every cash screen onto it.

## Proof
- Against **two physical counts**: 17-Aug (the anchor, = cash_count 1,75,198) and **25-Aug (drawer 43,903 before that day's handover)**. August closes at drawer 7 · Dr Bhawna 2,98,155 · Dr Manoj 79,703.
- `selftest_s361.py` — builds a scratch database of August's **day totals only**, seeds and proves it, then breaks it seven ways (a handover in both registers, an anchor that does not add up, a missing handover, a ruling on the wrong bill, a day's cash changed afterwards, a day left uncovered, the pre-count advance). Three deliberately broken modules each fail it.
- Installer rehearsed: install · rerun ALREADY · a foreign file refused · a database whose count disagrees refused with nothing written.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S361_CASH_CORE/install_S361_CASH_CORE.sh
```
