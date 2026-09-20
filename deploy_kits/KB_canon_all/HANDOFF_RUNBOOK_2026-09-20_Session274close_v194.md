# HANDOFF RUNBOOK — v194 — written at the S274 close, 20-Sep-2026 (the Sanjeevni project)

*Supersedes v193 (S272). §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the boundary with the parent · §5 what needs him. The Book v1.6 describes the pharmacy system; this runbook says how to work in it.*

## §0 · WHAT HAPPENED

D567's seven items were the mandate; **six are live by 09:44 IST, the seventh (the Book) is this close.** Five kits installed from the owner's one line each (one kit, S334, published and then restored itself at its own gate and was rebuilt as S337). Live now: Shavez's morning tile with the spine's certificate as its tick and the owner's overdue line (S337); refused exports kept in quarantine when they carry no person's detail, with a server-side rescan (S336); the spine on the health page through `spine_state.json` and two legs (S338); ordering rehearsed nightly against the spine into a file, scored a week later, not switched (S341); near-expiry read nightly from Marg's own export with a witness and cross-checked from the spine (S343). Nothing touched `finance_app.py`, `portal.py` or `tile_grants.json`; one parent data file (`freshness_legs.json`) moved and is declared; three cron lines added and declared. `NUMBERS_PROTOCOL_v1` ran for the first time with two chats open and held on five collisions.

## §1 · MENTAL MODELS TO CARRY

1. **The door's VERIFIED is structure; the spine's reading is the certificate.** A file that turned up is *aa gayi*; a file whose totals re-add under the certified reader is a tick. Never let the first look like the second.
2. **"No person's detail" is measurable, and the two numbers every Marg export carries are furniture.** The shop's `Phone :` line and Marg's footer are in every file; exempt exactly those, refuse everything else with a 6–9 ten-digit run or a sale-family word.
3. **A rule the owner has not approved is rehearsed, in a file that says so, before it touches a screen.** The order rehearsal writes NOT AN ORDER in its second line and scores itself; his sitting fills `order_rules.json`.
4. **A count the code actually runs beats the count a decision remembers.** The nightly gate is 13; D566's 14 was the acceptance run. `spine_state.json` records the number that ran.
5. **A kit's own login-gated URL proves nothing to curl.** Prove a placed module by importing it with the service's python. (F-573, the second time.)
6. **Compile on copies.** `py_compile` inside a kit folder is how `__pycache__` reaches `deploy_kits\` (F-574, F-538).
7. **A correction to a canon file after its row is written is a new row.** F-578: the Register's hash moved at 08:10 and the manifest row and pin header did not.
8. **The one counter holds.** Five pinned writes lost to the other chat this morning and every one re-read and took the next number; nothing was minted from memory.

## §2 · THE LIVE BACKLOG (Sanjeevni)

- **Watch:** seven nights of `gate 13/13` (D566/D572) from 20-Sep — read `spine_state.json` or the health page; the first `order_rehearsal` score lands 27-Sep; the first near-expiry answer lands with the October expiry export (F-576).
- **Mine, no owner step:** the certificate lag on Shavez's tile (door → spine reading) measured from the first real morning, 21-Sep; if it is hours, the cure is the door running the reader at take time (a kit, his call). The category-list signature to the VPS `signatures.json` (`b2dcb211` → manojz's `a987a08e`) — the first real rescue for S336's rescan.
- **His sitting, when he wants it:** the buying rules and the four lists (`order_rules.json`); who opens the order; the wording on Shavez's tile.
- **After count #1 closes (his step 2), untouched until then:** the 22 renames, the four salt rows, count #2 rungs 4–6, the four hub defects (Book §14.1).
- **Rung 4 (screens onto the spine), after the seven nights and his word:** ordering first, Amir's pages and stock-now, returns / Darpan / claim queue, the stock-check screens last.

## §3 · INSTALL DISCIPLINE — added this session

- An installer's health gate: `/finance/healthz` 200 · the page 302/401 · **the placed module imported by the service's python answers its `KIT`** — never a login-gated `api/healthz`.
- `py_compile`, the selftest and the walk run on copies in `/tmp`; the kit folder is never written to after it is sealed. The `find __pycache__` runs before the copy into `deploy_kits\`.
- A kit that touches a parent-owned data file (`freshness_legs.json`) applies it with a pinned, idempotent applier that refuses a moved pin, backs up beside the file, and names the new hash on the board for the parent's pin check.
- A cron line is added by `crontab -l | … | crontab -` after a dated backup of the whole crontab beside the kit's files, tagged with the kit name, declared on the board.
- The rescan wrapper releases the collector's lock before re-taking: the door locks itself per call (the selftest caught BUSY on the first run).

## §4 · THE BOUNDARY WITH THE PARENT

Declared this session, for the parent's next open: three root cron lines (`# S336_QUARANTINE` 06:25, `# S341_ORDER_REHEARSAL` 23:58, `# S343_NEAR_EXPIRY` 23:57); `freshness_legs.json` `0e56aa9e → 9dfbef9c` (two legs appended); `clinic-finance` restarted twice. Still owed by the parent: `code_bundle.py` to carry `root/finance/spine` (`*.py`, `*.json`, `spine_compare_latest.txt`) and the state backup to carry `spine.db` + `readings/`. The parent's S273 was open the whole session (S332 … S345); no shared file was touched by both.

## §5 · WHAT NEEDS HIM

One double-click: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — the S274 canon. Nothing on the box depends on it. Everything else this session was his one line per kit, all done.
