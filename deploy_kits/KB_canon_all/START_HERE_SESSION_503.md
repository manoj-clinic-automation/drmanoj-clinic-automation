# START HERE — SESSION 503 — written at the S502 close (the Sanjeevni chat), 22-Nov-2026 12:4x IST

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. Live from S502: **S926** (11:34) — the flow page's section "Not delivered, out of stock and substitutes" (one row per medicine + dealer, history, the shelf stock and ledger inline, the identity question, the doors); **S927** (12:38) — the Hub's Needs-you in three tiers, every line opening inline. The paper of S502: `S502_SUBSTITUTE_FLOW_ANALYSIS.md` (canon). The mock-ups:

```
https://claude.ai/artifact/8Uv76hsSWFG3HTvHEBDqg1
```
```
https://claude.ai/artifact/UvcwHAqo1rKtfq9ii7gsP2
```

1. **The open:** `OPEN_ROUTINE_v1` — never `git` in the device shell; code, tools and walks on disk in `03_WORKING_PAPERS\S503\` from the first byte (F-1553), only database copies in `/tmp` (removed at the close); compile with `PYTHONPYCACHEPREFIX` under `/tmp`. Session **503 (RESERVED at the S502 close)** — take it by ONE `db_str_replace` on `board/_numbers` `session_note` whose `old_str` is the end of S502's READY line (`S502 CLOSE READY.`). **Never `db_get` the whole board** (F-1571, F-1558). Numbers: probe `kit_next > 928` (a miss means S928 is free), list `deploy_kits/`, append the TAKES line, then the pinned integer write. Figures at this close: `D1042 · F-1585 · A-D120 · kit S928 · session 504`. The day's checks (`python D:\Downloads\_kbtools\day_open.py --read`, only when the page is not today's) — **the 23-Nov bundle must confirm 12 DECLARED-PENDING pins** (S925 3, S926 3, S927 5, and slip_log.py + check_screens.py from earlier); remind him once of the packs page (D713).
2. **Before telling him anything is open, read its state** (F-1545): the canon's live list; the medical PC's heartbeat `D:\Downloads\margsync\medical_SendToClinic\heartbeat.txt`; the built-in browser, `whoami` first.
3. **FIRST WORK — the stock plan re-run with Fable (D1037, his word):** `S501_STOCK_PAGES_CONSOLIDATION.md` read whole; add F-1579 (the ordering lane keys the 22 ticked orthotic renames by their OLD names — `item_alias.resolve_map` maps new → old for the count and stock lanes; the order sheet should carry Marg's current name). Then build in the Runbook §2B item 0 order, the Stock check page to mock-up v5 `https://claude.ai/artifact/XzqcBUHoroPyTt7xG8bNea`. Read `stock_figure.py`, `stock_app.py`'s record and `purchase_app.py` whole before patching.
4. **Then S928 — the remaining Needs-you panels** (`hub_panels.py`: Darpan's lines, Marg details, returns, the days lines, the expiry taps; "Accept Marg's figure" on vouchers; a Seen list he can reopen). Read `hub_panels.decorate()` and the lines' writers first.
5. **Read S926's first days** (read only): `order_flow_word` — his word on VFER 500 (the "Yes — same medicine" tap pending at this close), the keeps rows; Darpan's block.
6. **List to him (one line each, his to order):** VFER 500's one tap · Amir's seven Ask-Amir lines · Ram Singh's Stock Register button for Shavez · PARKED: AutoHotkey, the order list.

**Kit pattern reminders:** a module's load proven by its line in the service log since the restart (F-1554, F-1582), never a gated page — 302 is the gate; a new file name per version through `device_commit_files`, md5 read back (F-1581); `rm` refused in connected folders — no `set -e` across it; S761's `_S761_PLAIN` must list any new line field (F-1583); a walk gates only on what the kit changes (F-1555); Needs-you in a walk with `NEEDS_YOU_WITHOUT_S408=1` (F-1560); a Flask walk uses one connection (F-1573); no dialogs on his pages (F-1464); patient DB copies stay in the device VM `/tmp`.

**Close:** `CLOSE_ROUTINE_v1` — copy `03_WORKING_PAPERS\S502\close_parts\close.json`, change what changed; `close_build.py` then `--place`; one board batch; project knowledge gets the entry point, the brief, the close report; the publish named once.
