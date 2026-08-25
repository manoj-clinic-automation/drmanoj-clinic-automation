# S201_A1FIX — the A1 "does your total match Marg?" warning has never fired. Fixed.

One file: finance_app.py 2c99b2c6c719091deada5603fc295c90 -> d930b6b5bca59e7f52ce46f6b88332fd

**The fault (auditor AF-2, 24-Aug — confirmed from the live bytes, 25-Aug).**
`_marg_total_for_date()` reads a staged push looking for days keyed
`business_date` / `net_p`. `api_marg_push`'s `days_payload` writes
`date` / `expect` / `lines_csv` / `items_csv`. **The reader can never match a
real staged push**, so the maker's save-time warning and its high-severity
`TOTAL_VS_MARG` flag have not fired once since S195.

**The fix.** Carry the two keys through. Both values are already in `d` — the
loop reads `d["business_date"]` on its first line and `d["net_p"]` two lines
later for the survey. **Purely additive**: the apply path reads only
date / expect / lines_csv / items_csv and ignores every other key, so replay
behaviour is byte-unchanged.

**Why the vacuous test did not catch it.** The push-path stub fabricated the
READER's key shape. The three new checks go through the real writer and then
call the real reader — asserting the rule, not a fixture.

Offline differential on the seeded live-shape store, every imported module
hash-recovered to its live pin (finance_ingest 6cb83302 · marg_report 6411a57d ·
staff_ledger acd7b538 · finance_yesbank 5dcbdd3a):
**570/679 -> 573/682, +3 exactly, fail set byte-identical (109 rows).**
Live projection: **680 -> 683.**

    cd /root/deploy/repo && git pull
    bash deploy_kits/S201_A1FIX/INSTALL_S201_A1FIX.sh
