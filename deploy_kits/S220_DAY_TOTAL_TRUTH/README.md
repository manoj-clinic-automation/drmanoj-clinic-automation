# S220_DAY_TOTAL_TRUTH — the day's Marg money, told once, on both screens (F-281 · F-282)

**Found by the owner, 02-Sep 22:40 IST, on the first day through the S220 system:** the portal read
*"Marg — total 17,674 · variance 30 ✓"*, Darpan's card read *"Din ki sale 15,614"*. Read from the code and
the live db, both were wrong and the declared cash (17,644) was right:

| | what | figure |
|---|---|---|
| **F-281** `finance_app.py` | Marg total = `sum(amount_p)` over sale rows — fetches `service`, ignores it; the return (stored positive, S180) is **added** | 16,644 + 1,030 = 17,674 |
| **F-282** both screens | 7 bills parked for review (a name, no clinic ID, confidence 0.5) are not sale rows — **their ₹2,030 was in neither total** | card 15,614 |
| the truth | 16,644 − 1,030 + 2,030 | **17,644 = declared** |

`v_day_attribution` has known both facts since S180 (it subtracts returns and carries `in_review_p`);
neither screen read it. Now both do — one source, one rule (D349). Darpan's card also names the parked
bills under the sale (*bina pehchaan ke bill (7) — ₹2,030*, Hindi, staff page) so the identity owed is
visible, not hidden.

**Proven:** selftest 9/9 through the real card API on a copy of the live db (a day with parked bills, a day
with a return); browser render 4/4 in Chromium; finance_app anchor matched exactly once on the S218 bytes
and compiles.

**Recorded, not fixed here (candidate):** the ingest's 0.70 confidence gate parks every named bill without
a clinic ID — 7 of 27 on 02-Sep. D355 says identity by lookup, never a generated confidence; the parked
money is now counted, but the parking itself is a design question for the Marg backlog.

| file | what |
|---|---|
| `patch_finance_app_margtotal_s220.py` | finance_app.py — 1 anchor |
| `patch_darpan_card_review_s220.py` | darpan_app.py — 2 anchors |
| `patch_darpan_card_html_s220.py` | darpan_card.html — 1 anchor |
| `selftest_daytotal_s220.py` | 9 checks |
