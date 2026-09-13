# S243 BUILD BRIEF — the night the VPS was emptied and Sanjeevni got its book

*12/13-Sep-2026. One brief instead of the twelve papers and eleven kits: the shortest complete path into what S243 did.*

## The session in one line

Study from evidence, not from the plans → the VPS emptied of 495 dead files and fenced → Sanjeevni mapped into
twelve sections → the owner's rulings turned into eleven kits, all live by 09:30, every one installed from a
single line with rollback proven and every page read back as every role.

## What changed, in the order it landed

| # | kit | what it did | pins |
|---|---|---|---|
| 1 | `S243_RETIRE` | 495 residue files → `/root/_retired/S243_2026-09-13_0007/` (undo kept; 12 held) | — |
| 2 | `S243_SALTS_REFRESH` | salt-wise list refreshes itself from the server archive, every 10 min (D489) | `salts_refresh.py` d7994e38 |
| 3 | `S243_AUTOAPPLY` | sale reports apply on arrival; duplicates superseded; OFF switch (D488) | `finance_app.py` 72bc8323→f002defb |
| 4 | `S243_WATCHDOG_FINANCE` | 14 units guarded incl. `clinic-finance` | `clinic_watchdog.py` 389afcfe→35e40626 |
| 5 | `S243_CODE_BUNDLE` v1.2 | nightly code copy to Drive 01:35; secrets excluded by the repo gate's heuristic | `code_bundle.py` 27e42d0d |
| 6 | `S243_SCREEN_FIXES` | `/finance/purchase/` → hub; `/finance/daily` checker → Review (D486) | `purchase_app.py` ad1fc004 · `finance_app.py` →4cd8f966 |
| 7 | `S243_SNAPSHOT_SOURCE` | computed stock → `stock_expected`; Marg-only `stock_snapshot`; 1,119 rows restored (D490) | `stock_app.py` 0b965da4→aa6d9cd9 |
| 8 | `S243_DARPAN_KAL` | Darpan's prefilled day; owner card; Bhawna recipient (D491) | `finance_app.py` →f93f7430 · hub →7dbb5e56 |
| 9 | `S243_REPORTS_TILE` | Shavez's "Aaj ki reports"; hub line (D495) | `finance_app.py` →dae5fd90 · `portal.py` →4bb6bde0 · grants v13 |
| 10 | `S243_AMIR_VISIT` | salt-export prompt; "Amir's visit — what was done"; F-455 fixed | `amir_day.py` ae2c8939→bf7d9826 |
| 11 | `S243_CA_AND_NUMBERS` | corrections read-only; monthly accountant report; health informational; full numbers on returns desk (D492/D493) | `finance_app.py` →912398e9 · hub →aa79b181 · `returns_desk.*` |
| 12 | `S243_DARPAN_TILE` | "Kal ka hisaab" tile for Darpan | `portal.py` →06f1b378 · grants v14 0efad736 |
| — | `S243_LIVE_CAPTURE` | records: 215-row fingerprint of the live code; byte-exact copy private | — |

## The three things worth knowing next time

**1 · The live code is in hand.** `code_nightly.tar.gz` (Drive, nightly) and the private zip carry every live
file byte-exact. Base every `finance_app.py` patch on the capture; gate installers on lineage markers plus
`count==1` anchors — six kits stacked on that file in one morning that way, each proven on the bytes as they
would be after the previous one.

**2 · Three refusals, all correct.** A stale watchdog pin, a too-strict secret filter, a token at the wrong door
— each installer stopped with nothing changed. The lesson each time was the same: read the code (or the record)
that produced the refusal before touching the box.

**3 · The owner's words are the spec.** Darpan's notebook subtraction is the screen, line for line. The one
line the assistant added — a deterrent notice — the owner struck: *the data surfacing there is the deterrent.*

## The rulings that now govern Sanjeevni (Book §13)

Apply is automatic · no cash↔UPI corrections in Marg (CA) · full numbers on staff desks · Drive mirror keeps
PHI · everything PC-side moves to the VPS · Shavez generates the morning reports · Amir is a distinct role ·
Darpan's cash: ₹50 day line, ₹2,000 month cap, excess owed back to him, received tap by owner/Bhawna.

## Owed

F-456 key rotation (with MyOperator) · D493 phase 2 (mobile at Apply) · F-458 gate fix · F-450/453/454 pin
rows · F-451 cron · procedure-medicine word · claim tab · Phase 3 items in Book §11.4 · delete `_retired` after
a cycle (owner).
