# S221 BUILD BRIEF — the one document Session 222 reads instead of ten papers

**03-Sep-2026, 05:20 → 11:00 IST. THE SESSION THAT MADE A MAN'S ARRIVAL DO SOMETHING.**
Nine kits, eleven live files moved or created, **every pin predicted offline and read back
identical**. Amir onboarded end to end. Two of my own mistakes caught by measurement before they
reached anything, and F-142 repeated twice in one morning — in the project that recorded F-142.

## What is live now (pins at the S221 close)

| file | pin | carries |
|---|---|---|
| `finance_ingest.py` | `747b4a50` | **the D355 ladder at ingest** (F-283): clinic ID · full mobile · last-4+name · same-day Docterz, before the confidence gate. Mobile fingerprinted in memory, stripped from stored raw |
| `returns_desk.py` | `1dc1fd62` | Darpan's **jaankari** list — three lists, answers are evidence only |
| `returns_desk.html` | `6d98e1b0` | the Hindi card: one question a row, three buttons, full mobile, capped at six |
| `darpan_card.html` | `4a31f14e` | the directory became **his four job buttons**, registry-driven, scoped |
| `cards_registry.json` | `ded2f66e` | ownership per card, `who` field |
| `stock_app.py` | `4e929d0b` | the **audit finding** (sealed) · two prices · the **drift log** · purchase-due · viewer access |
| `stock_finding.html` | `99bf7a78` | the document: header, table, totals, print, signatures |
| `stock_drift.html` | `ffe7333c` | computed vs Marg over time · feed health · **purchase export owed** |
| `darpan_app.py` | `c98f0c24` | the corrections desk accepts `viewer` (Amir) |
| `push_snapshot.py` (manojz) | `7722c33a` CRLF | same-date exports: **the later-taken one wins** |
| `PUSH_STOCK_DAILY.bat` v2 · `PUSH_STOCK_NIGHTLY.bat` (manojz) | — | pinned baseline; a refusal can no longer print "Done"; one nightly job, 22:30 |

> **Eight of these pins are held in this close's record as 8-character prefixes only.** The full md5
> was read from the box at install and matched the offline prediction every time, but the full
> string is not in the record — so `live_pins_S221close.txt` marks those rows **PENDING**, not a
> pass, and the S222 open re-hashes and promotes them. A hash is never written from memory (A0).

## ⭐1-2 THE LADDER, PROVEN ON REAL DATA THE SAME MORNING

**7 parked bills → 3.** Day total held at ₹17,644, variance 0. **All four named by the FULL
MOBILE** — last-4 scored 0, the Docterz list scored 0. Had I built only what F-283 described, none
would have been named. The three refusals are correct: 285, 477 and 82 patients in the master fit
those names, and the one last-4 present matches nobody.

## MEASUREMENTS THAT CHANGED DECISIONS

- **78 % of pharmacy bills carrying a real patient were bought the day that patient visited**;
  2.3 % within three days. **D11's "days, not hours" is false for this pharmacy** — same-day beats
  the ±3-day window on both axes (more matches, half the ambiguity).
- **1,871 last-four values are shared; only 719 numbers are.** The full mobile separated 22 of 22
  remaining ambiguities.
- **The sale-day test** (`S221_SALE_DAY_TEST_RESULT`): 77 % of testable returns explain themselves.
  The method independently reproduced the audit engine's own nine NEVER BOUGHT, 1 Jun / 4 Jul /
  4 Aug. **Three credit notes, ₹2,878, survive scrutiny** — CN00169, CN00192, CN00193.
- **MRP ÷ cost: median 1.40 over 147 items**, 2 below cost — after finding that
  `sale_line_item.amount_p` is a *strip rate*, not an amount.
- Cost covers 187 of 376 items, MRP 180, **neither 156**.

## THE OWNER'S RULINGS (candidates for D367 — not minted; D367 is still free)

1. **Internal match only.** No question to Darpan on identity yet — *"low intent person; first get
   him to do sale returns, stock check, drawer management, then reassess."* Later refined:
   **send the questions, go soft on the answers** — recorded as evidence, silence costs nothing.
   This **supersedes** the S220 design's 2-day escalation and G6.
2. **Cards scoped by intended user**; the full directory moves to the owner's hub. Ownership set
   per card; stock count is *"two persons"*.
3. **Stock difference is an audit finding**: recover at MRP · unvalued never in a total · **LOG
   ONLY, never deducted** · line closes, recovery amount stays open · Marg vouchers scanned with
   dates · cost backfilled when M3 lands.
4. *"A blind sight is worse. When the system is in place its main purpose is deterrence."*
5. **The 54 never-in-the-feed bills: dropped** — *"why bother, it's revenue."*
6. **"history too"** — the whole-history re-join is approved; the tool is on the box.
7. **F-244 retire** (already executed at S211) · **§S205 struck** (settled 27-Aug).
8. **Amir: biweekly, ₹2,500 fixed retainer**, Emp Code 101, sunday_group B, minutes_exempt Y,
   allowed_offs 26 so absence cannot eat the retainer.

## THE FIRST THING SESSION 222 MUST DO

**The Vaapsi desk over-grant (F-296).** `viewer` IS the desk's key, so giving Amir viewer for his
corrections and stock work also opened the returns desk to him — a purchase man who can issue cash
refunds. **The owner caught it; I had written it into the walk as a PASS.** The cause is older than
Amir: S214's "named reception staff" was never named in code — the desk asks *"are you a viewer?"*,
never *"are you one of them?"*. **Anyone ever given viewer gets the returns desk.**

**The fix, designed and approved, not yet built:** an opt-in `returns.desk_users` setting. If set,
only those people plus maker/checker may open the desk; **if unset, nothing changes**, so
reception's access cannot break. Seed it with Darpan · Shavez · Alisha · Shivani. One live file
(`returns_desk.py`), its browser gate re-run (the page's standing rule since S214), and a walk that
proves Amir is refused and all four of them are not.

## OWED / NEXT

- `returns.desk_users` (above) — **first**
- the corrections page still draws the owner's ledger-check and transfer controls for a viewer;
  they refuse him safely, but they should be hidden
- Amir's joiner record needs CREDENTIALS_SENT and STAFF_MASTER ticked to close at 6/6
- the joiner page shows the WhatsApp text with **no way to send it** and **does not create the
  portal login** (F-295) — both cost real time today; a `wa.me` link and an adduser step are small
- run the whole-history re-join (`--from 2026-04-01 --apply`), the owner has approved it
- the spot-count bridge — **parked by the owner** until the drift log has a month or two
- ⭐1-3 Marg's user-wise register (parked) · M3 purchase tables (backfills loss-at-cost) · the
  M-series · Docterz Phase 1 · the August staff close · the scanner A5 vertical resize

## THE ELEVEN FINDINGS (F-286 … F-296 — nine are mine)

F-286 a rung dead in production and green in the walk (the walk built its own Row factory) ·
F-287 the full mobile nearly stored in `sale_item_review.raw_text` · F-288 a default that reached
back eleven weeks — 121 rows on a counter phone · F-289 a heading that rendered as "ग", caught only
by the browser · **F-290 the money labelled backwards** · **F-291 `| tail -1` swallowed a gate —
F-142 again** · F-292 a page that hard-coded `/stock` (the S209 fault) · F-293 a render test that
blamed the page for the stub's gaps · F-294 a pin predicted in LF, read in CRLF ·
**F-295 the joiner page shows a credential it never creates (the owner's)** ·
**F-296 the Vaapsi over-grant (the owner's), carried forward unbuilt**.

---
*Working paper, stamped at birth — 03-Sep-2026, Session 221 close.*
