# S201_HEALTH — the health page stops calling a queue an error

One file: finance_app.py d930b6b5bca59e7f52ce46f6b88332fd -> 024399775bfd14844f299b3dfac4bb47

**Three faults on one row, all found 25-Aug by reading the live database.**

1. **"This month vs Marg" compared two things that can never be equal.**
   books = `v_cash_ledger.revenue_p` (the WHOLE day) against
   `marg_net_sql(sale_item)` (ATTRIBUTED lines only). Any day with one
   low-confidence bill differed, so the row was **permanently red at `bad`** —
   and `bad` drives the portal tile. Exactly the wallpaper condition the S195
   flags-as-info ruling exists to prevent, applied to data_flag and never here.
   Now: books vs **attributed + queue**, which can actually reach zero.

2. **The differing-day list truncated at five and said nothing.** The sibling
   never-filed line right above it appends "and N more"; this one did not.
   24-Aug was differing and simply was not shown — it was found by arithmetic
   (books +12,964 vs Marg +10,539 while the listed five were unchanged), then
   confirmed in the code. Now it says so, asserted BOTH ways.

3. **They were never named for what they are: SALE BILLS WITHOUT A CLINIC ID.**
   The salesman enters three identifiers at the till — mobile, name and clinic
   ID (numbered from 1, now in the 7999s). A bill missing the ID cannot be
   linked to a patient, so it is parked for the Docterz cross-match. It is
   **not** missing from sales: `day_line` carries the whole day and
   `finance_ingest` cannot touch it (D313). New row at **`info`**:
   *"Sale bills without a clinic ID"*.

   **"low confidence" was the wrong word.** That threshold (0.70) was built for
   OCR, where the doubt is whether a scan was READ correctly. There is no OCR
   in this path. Measured over **192 bills across seven days**, every Marg bill
   scores either **0.95+** (an ID is present) or **0.50** (it is not) —
   nothing in between, ever. The threshold is a has-ID switch, not a judgement
   about reading, and any value between 0.51 and 0.94 behaves identically.
   **Nothing to tune; only the label was wrong.**

   Measured identifier capture: **73% of bills, 71.7% of turnover.**
   Best day 92% (22-Aug), worst 57% (21-Aug).

Offline differential on the seeded live-shape store, every imported module
hash-recovered to its live pin:
**573/682 -> 580/689, +7 exactly, fail set byte-identical (109 rows).**
Live projection: **683 -> 690.**

    cd /root/deploy/repo && git pull
    bash deploy_kits/S201_HEALTH/INSTALL_S201_HEALTH.sh
