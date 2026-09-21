# HANDOFF RUNBOOK — v199 · written at the S275 close (the Sanjeevni project), 21-Sep-2026

*Supersedes v198 (the parent's S278 close) as the current runbook. Same shape: §0 where things stand · §1 the mental models · §2 the backlog in the owner's order · §3 what is live and where · §4 the rules that bind · §5 what to read first.*

## 0 · WHERE THINGS STAND

**The pharmacy's money is true again, and the page that shows it is next.** In one night (20-Sep 21:55 → 21-Sep 05:5x) the approval figures were repaired in three live kits: UPI taken from the bank instead of frozen at report time (F-599), home and procedure medicine deducted again after a month of being counted as cash (F-600), a home/procedure return treated as goods back rather than a hole in the drawer (D594), and the hub card that had said "none" for five months reading the day books (F-601). The doctors can now log Darpan's daily cash themselves, one day or a backlog, and there is a month-wise table of sale · UPI · cash · − home · − procedure · = net cash.

**What is owed to him, in his order:** the Yes Bank statement upload (F-603, OPEN — it refuses both formats his bank gives him), then the approvals page rebuilt to D591/D592, then the log window back to 17-Aug (D593), then the carried spine work.

**The clock that still runs:** D566/D572 — seven consecutive nights of `gate 13/13` from 20-Sep. Nothing moved onto the spine tonight and nothing may before that clock and his word.

## 1 · EIGHT MENTAL MODELS (the seven of v194, plus one)

1. **The board is the lock.** Two chats, one number series, `board/_numbers` by pinned write. Held again tonight across five kit claims.
2. **A kit is a kit.** Built in scratch, gated, published by his double-click, installed by his one line, read back from the box, pinned in the shared Register.
3. **A clock time is read, never estimated.**
4. **No git in the PC shell.** Read `.git/logs/HEAD`, or clone in the cloud.
5. **Full-file replacements, or anchored patches whose predicted bytes are proven in scratch first.** Both used tonight; the anchored one refuses unless the hash it predicts comes out.
6. **The parent's files are touchable, but only declared.** Three of them moved tonight — `finance_app.py`, the hub page, `tile_grants.json` — each named on the board before the kit was built and each in the Register's §S275 table.
7. **A placed module is proven by importing it.** Never by curling its own login-gated route. Third occurrence tonight (F-602).
8. **NEW · A surface that says "none" is making a claim.** Check what it counts. The hub's home-medicine card counted a column with zero rows for five months and nobody asked why (F-601). The same instinct catches F-605: a check whose two sides are now the same source prints a pass forever.

## 2 · THE BACKLOG, IN HIS ORDER

1. **F-603 · the Yes Bank statement upload** — refuses PDF and CSV both; the tile's message is wrong. Read the door's code first; get his two real files. *S280's first job.*
2. **D591 · the approvals page rebuilt** — the day panel in his order, approve then log (D592), one drawer figure (F-604), the always-zero variance line gone (F-605), the audit apparatus moved to its own page.
3. **D593 · the log window to 17-Aug** — with `_pending_days` taught to skip days that already carry a `cash_movement`.
4. **The spine's seven nights** (D566/D572, from 20-Sep) · the first real morning on Shavez's tile · the category signature `b2dcb211 → a987a08e` · the rung-4 paper.
5. **Owed to the parent:** `finance_upi.py`'s literal format string (F-606); the autofile calling the resync when the statement lands, instead of waiting for the half-hour (F-599's root cause).
6. **Not touched, by his standing rule:** the stock-check screens and tables until count #1 closes; any screen onto the spine before the seven nights.

## 3 · WHAT IS LIVE AND WHERE — the Sanjeevni files that moved tonight

`/root/finance/day_resync.py a4e53adc` (cron `*/30 7-23 # S356_DAY_TRUTH_2`) · `darpan_kal.py 2072e290` · `darpan_kal.html 4f115f44` · `darpan_month.html c4e81f7c` · **the parent's, declared:** `finance_app.py 4a399f30`, `finance_ui/finance_approvals.html c940c46f`, `/root/portal/tile_grants.json` v24 `7296bbd2` · `setting noncash.home_words` / `noncash.proc_words`. Backups: `finance.db.bak_S356_20260920_221703`, `.bak_S357_20260920_222705`, and `.bak_S359_<from8>` beside each placed file.

**Frozen, never install (F-512):** `S355_DAY_TRUTH`, `S358_CASH_LOG`.

## 4 · THE RULES THAT BIND — unchanged, plus tonight's

Everything in v194 §4 stands. Added: **an installer may curl only a path listed in `PUBLIC_PATHS`** — every other proof is an import or a database read (F-602, the rule's third writing); **a word list the owner's staff generate belongs in the `setting` table, not in code** (D595); **approve first, log the cash after** (D592).

## 5 · WHAT TO READ FIRST AT THE NEXT OPEN

`START_HERE_SESSION_280.md` · `S275_BUILD_BRIEF.md` §0 · then the Book v1.7 §2.1, §6.4, §11.4 for the lanes that moved. The Fault Register §7.38 carries F-599 … F-606 in full; F-603 is the only one open.

---
*HANDOFF_RUNBOOK v199 · S275 close · 21-Sep-2026 · every figure read from the installers' own output on the box, the live pages in the browser, and the 20-Sep nightly database.*
