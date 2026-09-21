# HANDOFF RUNBOOK — v200 · written at the S280 close (the Sanjeevni project), 21-Sep-2026

*Supersedes v199 (the S275 close) as the current runbook. Same shape: §0 where things stand · §1 the mental models · §2 the backlog in the owner's order · §3 what is live and where · §4 the rules that bind · §5 what to read first.*

## 0 · WHERE THINGS STAND

**The pharmacy's cash is one calculation, and the owner can read any day at a glance.** In one day (21-Sep 08:02 → ~16:0x IST) four kits went live: the Yes Bank statement PDF read and self-proved (S360); `sanjeevni_cash.py`, the one cash calculation, anchored on the 17-Aug count and proven against both physical counts (S361); the pool of Dr Bhawna and Dr Manoj recorded as he runs it, an approved day's cash gone to it, the two deposits their own record (S363); and the day panel — sale → bills → medicines, returns, UPI, without cash, Cash received, where it went, checks in words (S365). He approved every September day and called it *"meaningfully corrected"*.

**Owed to him, in his order:** his Yes Bank CSV still refused (F-612, OPEN), the ₹200 of 04-Sep, the rest of the approvals page (D591), then the carried spine work.

**The clock that still runs:** D566/D572 — seven consecutive nights of `gate 13/13` from 20-Sep.

## 1 · NINE MENTAL MODELS (the eight of v199, plus one)

1. **The board is the lock.** Five kit claims today; one (S364 → S365) caught only because the board was read (F-611).
2. **A kit is a kit.** Scratch, gated, his double-click, his one line, read back, pinned.
3. **A clock time is read, never estimated** (F-609 found one that was not).
4. **No git in the PC shell.**
5. **Full-file replacements, or anchored patches whose predicted bytes are proven in scratch first.**
6. **The parent's files are touchable, but only declared.** Three moved today: `finance_app.py`, `finance_approvals.html`, `finance_workbench.html`.
7. **A placed module is proven by importing it**, never by curling its login-gated route.
8. **A surface that says "none" is making a claim.**
9. **NEW · One figure, one calculation.** Before a screen shows money, find whether `sanjeevni_cash.py` already computes it; if so, read it; if not, add it there and prove it against the counts. Four drawer figures were four arithmetics (F-610).

## 2 · THE BACKLOG, IN HIS ORDER

1. **F-612 · his Yes Bank CSV** — find his files, try the PDF for him, then make the CSV usable with dates asked on the page (F-112 kept).
2. **The ₹200 of 04-Sep** — find the bill, put it to him in one line.
3. **D591's remainder** — Needs-you strip, sections, the audit page one link away.
4. **The spine's seven nights** · Shavez's first real morning · the category signature · the rung-4 paper.
5. **Owed to the parent:** `api_yesbank_statement` fname mask (F-607); `finance_upi.py` format string (F-606); resync on statement arrival (F-599).
6. **Not touched, by his standing rule:** the stock-check screens until count #1 closes; any screen onto the spine before the seven nights.

## 3 · WHAT IS LIVE AND WHERE — the Sanjeevni files that moved today

`/root/finance/finance_yesbank.py 825016c0` · `sanjeevni_cash.py 8e58691b` · `sanjeevni_day.py 7f6ea583` · `darpan_app.py 2c22822d` · `darpan_kal.py 19b9c0e8` · `darpan_month.html cee5478b` · **the parent's, declared:** `finance_app.py 70cff498`, `finance_ui/finance_approvals.html 6c668ccc`, `finance_ui/finance_workbench.html 601d5a77` · five new `cash_*` tables · `setting darpan_kal.log_from`. Backups `.bak_S36x_<from8>` beside each placed file; `finance.db` backed up before each seed. No crontab change.

## 4 · THE RULES THAT BIND — unchanged, plus today's

Everything in v199 §4 stands. Added: **a kit asks for any system binary in its own first step** (F-608); **the owner does not log August or September by day — approval is the record** (D598); **every Sanjeevni cash figure comes from `sanjeevni_cash.py`** (D600).

## 5 · WHAT TO READ FIRST AT THE NEXT OPEN

`START_HERE_SESSION_281.md` · `S280_BUILD_BRIEF.md` §0 · the Book v1.8 §6.7 and §10.7 · the Fault Register §7.39 (F-612 is the open one).

---
*HANDOFF_RUNBOOK v200 · S280 close · 21-Sep-2026 · every figure read from the installers' own output on the box, the live day panel in the browser and the commit stamps in `.git/logs/HEAD`.*
