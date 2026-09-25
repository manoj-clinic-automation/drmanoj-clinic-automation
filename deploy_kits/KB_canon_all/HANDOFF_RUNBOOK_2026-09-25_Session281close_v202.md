# HANDOFF RUNBOOK — v202 · written at the S281 close (the Sanjeevni project), 25-Sep-2026

*Supersedes v201 (the parent's S279 close) as the current runbook. Same shape: §0 where things stand · §1 the mental models · §2 the backlog in the owner's order · §3 what is live and where · §4 the rules that bind · §5 what to read first. **The parent's S282 was open beside this close** (taken 09:34 IST); its backlog is v201 §2, carried whole in §2B below and not touched by this close.*

## 0 · WHERE THINGS STAND

**Four days, fourteen kits live, every one from the owner's own line or his agent's own read-back.** On the VPS: 04-Sep settled as Marg's 18 bills, ₹23,875, and a machine-filed day now follows Marg's later exports until it is approved (S367, D602); the approvals page is one tree — Needs you, Days, Cash, Bank, Returns, Month, and Checks folded at its foot (S368, D603); a purchase bill marked Wrong can be cleared when Marg's re-export agrees (S371); both bank accounts sit on the page, ICICI counted from the bank's own August closing balance, both balances bold at the top of Bank (S375, S377, S378; D604); and August's payment papers print as one pack — covering letter with the cheque number, NEFT annexure, payment sheet, each with a signature block (S380, D605). On the medical PC: Marg's saves to the pen drive's top level are watched (S381); one agent runs for whichever Windows account is signed in, SET or the staff's `user` (S387, S388); with Office broken, Marg's one-click TEXT export carries the bill-wise sale to the server as the same `.XLS` Marg's Excel makes (S389, S390 — live 20:02:04 IST 24-Sep); and the watcher now writes what it saw and why it refused anything into Drive `FromMedical`, readable when manojz is unreachable (S395, S396, S396.1). **24-Sep's sale is on the server** (captured 07:27:00, VERIFIED 07:27:03, 25-Sep) — the first attempt had been Marg's SUMMARY layout, which the reader rightly refused.

**Built and proved, not installed:** `S397_STOCK_TEXT` — the whole-stores closing stock read from Marg's text export (PROVE_S397 GREEN 14/14: the spine's own reader and the router take it as they take Marg's Excel; the same 378 items on the same rows; 23-Sep closing − 24-Sep sales = 24-Sep closing on every item). **It waits for his OK** (D615). The 24-Sep stock text is kept on the medical PC and in Drive; S397's watcher offers it again at its first start.

**One thing over the line:** drift 6 on the medical PC's `marg_watch.py` — every change built by an `apply_*.py` from the exact live bytes and self-tested, but read it whole before the change after S397. **Frozen:** S386 (refused itself 7/8 on the machine; S387 carried it).

## 1 · TEN MENTAL MODELS (v201's, with three of this session's)

1. **The board is the lock** — and this close met it: the parent took 282 and S398 while the close was being written; the write was re-read and re-pinned (v89).
2. **A kit is a kit.** Scratch, proven on the real bytes, his double-click or his agent's install, read back, pinned.
3. **A clock time is read, never estimated.**
4. **The PC shell works** (unreachable through the early morning of 25-Sep; answering again at 09:27:42 IST, the device's own timestamp, in time for this close) — still no git in it.
5. **Full-file replacements, or anchored patches proven in scratch — and a file with five or more anchored patches is read whole before the next.**
6. **The Sanjeevni chat's files are its own; a parent file it must touch is declared on the board first** (`finance_approvals.html` at S368 … S378).
7. **NEW · The medical PC can be reached without manojz.** Drive `ToMedical\_kit` in, Drive `FromMedical` out (heartbeat, census, watcher log, refused texts) — and every upload is downloaded back and hashed before it is swapped into place.
8. **NEW · A Marg export is judged by what is inside it, never by its name or where it landed.** Marg writes `user_<id>.txt` then `report.txt`, saves to `E:\` when it likes, and offers a SUMMARY and a DETAIL under one menu.
9. **NEW · A converted report is proven against Marg's own Excel of the same kind, and — when no same-day pair exists — by the day's movement: yesterday's closing, less the day's sales, is today's.**
10. **A feed that cannot parse something says so where a person — or the assistant — reads it** (F-620, after F-624).

## 2 · THE BACKLOG, IN HIS ORDER

### 2A · The Sanjeevni project (this close)

1. **Install S397 on his OK** — through Drive `ToMedical\_kit`, in two steps: `marg_txt.py` `38d85298` + `KIT_MANIFEST.txt` `8230562e` first; `marg_watch.py` `81145aa7` only after the heartbeat shows `marg_txt 38d85298`. Each upload downloaded back and hashed before the swap. Then **confirm the 24-Sep stock reaches the server** (STOCK_CLOSING 24-Sep VERIFIED) — the watcher offers the kept copy at its start.
2. **The Sanjeevni Book v1.9** — the text route, the agent guard, the census in `FromMedical`, the approvals tree, the two bank accounts.
3. **The vendor-ledger reconciliation** once the bulk NEFT for August is confirmed by the Yes Bank statement.
4. **The ICICI statement reader and the statement shelf** — a drop box, identified by content, one place per account per month (F-615's durable half).
5. **The monthly pack for Amir** — the NEFT sheet and both statements.
6. **The spine's seven clean nights (27-Sep)** and the switch of the Sanjeevni doors to it; **Shavez's first real morning** on his tile.
7. Carried small: F-612 (his Yes Bank CSV); the category signature `b2dcb211 → a987a08e`; the rung-4 paper; an F-number for the `__pycache__` lesson (never run python inside a repository folder on manojz); the `MD5SUMS_ALL` backup row; retire the parent's S377 handover draft.

### 2B · The parent (v201 §2, carried whole; S282 is working it)

0. `slip_log.py` and `portal.py` read whole (drift 5) · 1. the contacts build (D614) · 2. F-630 · 3. F-631 · 4. D590 steps 2–3 · 5. the rest of D589's order · 6. owed by the Sanjeevni chat: F-607 fname mask in `api_yesbank_statement`, F-606 format string, F-599 resync on statement arrival. **Nothing new is named to the parent by S281.**

## 3 · WHAT IS LIVE AND WHERE — the Sanjeevni files that moved (pins in Register v5.122 §S281)

VPS: `/root/finance/day_resync.py ddbb12eb` · `sanjeevni_day.py 5d16eff5` · `darpan_kal.py 1958ee7c` · `sanjeevni_approvals.py 7ab5fec6` · `finance_ui/finance_approvals.html 750f89e0` (the parent's, declared) · `finance_ui/finance_approvals_old.html 6c668ccc` (the fallback) · `purchase_app.py 9ad50878`. Medical PC `D:\SendToClinic\`: `marg_watch.py ce64bb31` · `marg_txt.py 76b5eb5d` · `MARG_TXT_LIVE.txt 4bb3fd36` · `agent_guard.py b8b5a900` · `START_AGENT.cmd c58946c3` (each account's Startup `MargAgent.cmd`) · `ENABLE_AGENT_THIS_ACCOUNT.bat e00db276`. Drive `ToMedical\_kit\KIT_MANIFEST.txt 8c8ac555`. **Switches:** `D:\SendToClinic\_off\AGENT_OFF.txt` stops the guard; `MARG_WATCH_OFF.txt` stops capture; deleting `MARG_TXT_LIVE.txt` holds every text.

## 4 · THE RULES THAT BIND — unchanged, plus this session's

Everything in v201 §4 stands. Added: **an upload through the Drive connector goes in under a temporary name, is downloaded back and hashed, and only then swapped into its real name** (S396, S396.1); **a converted Marg report reaches the server only after it is proven against Marg's own export of that kind** (S389 parity, S397 roll-forward); **a text route is held by default and goes live by a switch file, set only after the install is confirmed** (S390); **a kit that restarts a process whose new behaviour needs a second file delivers that file first and waits for the machine to confirm it** (S397's two steps).

## 5 · WHAT TO READ FIRST AT THE NEXT OPEN

The Sanjeevni chat: `START_HERE_SESSION_283.md` · `S281_BUILD_BRIEF.md` (project knowledge) · the Archive v1.119 §S281 · the Fault Register v2.107 §7.41. The parent: `START_HERE_SESSION_282.md`, unchanged.

---
*HANDOFF_RUNBOOK v202 · S281 close (the Sanjeevni project) · 25-Sep-2026 · VPS pins read from the 24-Sep 01:35 bundle; medical-PC pins from manojz's mirror of `D:\SendToClinic`; every time read from a clock or a program's own line.*
