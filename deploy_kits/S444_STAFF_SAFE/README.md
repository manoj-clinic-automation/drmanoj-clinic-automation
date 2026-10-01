# S444_STAFF_SAFE — the system remembers so the staff need not (D647 · D648 · F-669 F-670 F-671 F-672)

**Sanjeevni project + the portal (PARENT'S, declared) · session 283 · 01-Oct-2026 · brief `claude_code_briefs/S444_STAFF_SAFE.md` ·
runs after the parent's S441–S443 (installed 01-Oct 09:19–09:20 IST).** Staff pages in Hindi (Roman script), the owner's in English.
S438_COUNT_BOOK stays held.

## What the owner said (01-Oct)
"Staff tend to forget things and then issues crop up again and again — rectify this properly." And later: "it was finalised earlier
that everything populates in his portal, in his work … Decide how to proceed — in this and in other builds."

## What was built
**3.1 One sign-in name (F-669) — `clinic_sso.py` (PARENT'S).** `make_token` stores, and `verify_token` returns, the name in small
letters with no spaces around it (`norm_user`). "Amir", "AMIR", " amir " all sign in as `amir`; a token issued earlier as "Amir"
reads as `amir` in the portal, the finance app and the asset app the moment the services restart — nobody signs in again.
`portal.login()` also passes the normalised name. Before the switch the installer proves no live name depends on case
(`names_s444.py`: the user store's names, `tile_grants.json` users, `unit_role`, the asset app's lane logins and users, the
`pend_mark` and sale-check actors) and STOPS on one that does. "Signed in: <login>" is one quiet line on Amir's pages, the salts
page, Shavez's "Aaj ki reports", his stock board, and inside the S440 BACK bar of Purchase orders.

**3.1/3.2 The portal home — `portal.py` + `tile_grants.json` v31 (PARENT'S).** `users.amir.home = /finance/amir`: his FIRST `/portal`
of a sign-in goes there (302; remembered per sign-in — the token's issue time — in the cookie `clinic_portal_home`); `/portal?all=1`
("Sab tiles" at the foot of each of his steps) shows his tiles as before. A staff login shown nothing but the tiles every staff login
gets by role sees "Is naam par koi kaam set nahi hai — sahi naam se sign in kijiye" and a big **Sign out**; its own punch page
(Meri attendance) stays. Today that is `sandeep`, `surendra`, `vikky` (no scan or form use on the box; parvesh is inactive).

**3.3 Amir's bill line; "my own entry" (F-670) — `amir_day.py`.** Under each bill on step 5: "Marg: ₹X · Kaagaz (scan|paper): ₹Y ·
mil gaya / farq ₹Z / scan nahi hua" — Marg's amount from the newest export carrying the bill; the paper's through the S439/S440
link (`purchase_bill.scan_bill_id` → `purchase_scan_state.paper_amount`, else the scan's read total through `purchase_app`'s
read-only door to assets.db). A seventh answer **"Meri entry galat thi — Marg mein theek kar di"** (`self`) raises NO claim (and
settles one already open on that bill as `amir_own_entry`), waits in the flagged list as "Marg ki agli export ka intezaar", and clears
ITSELF when a later bill-wise export carries the bill at the paper's amount (±₹1) — with no scan, at an amount other than the one he
flagged — audited once in `purchase_audit` ("S444 auto: Marg = kaagaz" / "S444 auto: Marg ki rakam badli"). Never holds a day open.
**KEDAR 195 (27-Sep)**, by the owner's ruling: claim #1 settled `amir_own_entry` by "S444 rule", the answer `self` (`apply_s444.py`).

**3.4 The salt list (F-671) — `amir_day.py`, `amir_salts.py`, `reports_tile.py`.** While salt ticks are newer than the last VERIFIED
SALT WISE ITEM LIST: one red card "Ek export aur: SALT WISE ITEM LIST — Excel mein (text nahi)" (with the S243 prompt's words) on step 6,
the close screen ("Aaj nahi aayi to Shavez kal subah nikalega") and the salts page; named in `_left()` as words — the gate steps are
unchanged, Din band stays open to him. Shavez's row reads "N din se baaki" (days since the last verified list), red.

**3.5 The owner's lines — `sanjeevni_approvals.py` (block 15) → `amir_day.needs_you_lines`.** English, each with who and since when,
each gone by itself: (a) "Salt list not received for N days — M salt corrections unproven (Amir / Shavez …)" once owed
`amir.salt_owed_days` (2); (b) "Amir's own correction on <supplier> bill <no> not yet seen in Marg after N exports" (`amir.self_exports`, 2);
(c) "Claim for Darpan open N days: <supplier> bill <no> Rs X" (`amir.claim_open_days`, 7); (d) "Count vouchers waiting: N (orthotic M)
— Amir has not opened them in N visits" (`amir.voucher_visits`, 2; a visit = a day of `amir_day`; a touch = he opens the board or
enters a voucher); the duty map's ORPHAN duties (no door) from `DUTY_MAP.json`; and a report the door refused today. The four counts
are `setting` rows (seeded INSERT OR IGNORE).

**3.6 Amir's one door (F-672) — `amir_day.py`, `stock_app.py`.** Step 6 is **"Marg sudhar"**: (a) "Stock voucher baaki: 7 orthotic,
30 dawa — kholiye" per count with vouchers made and not marked entered (the board's own rule: the newest `stock_voucher_entered` row
wins), opening his board at the vouchers; (b) "Naam badlo: N naam" — only once the S437 proof is green (asked only when no voucher
of the count is open; kept 10 minutes); (c) the salt work as before. (a)/(b) also stand at the top of every other step and in the
close screen's list; nothing blocks Din band. The board carries a BACK bar to `/finance/amir` and the signed-in name, and remembers
each opening (`stock_board_open`; the checker's own look is marked and never counts as his). No new tile.

**3.7 The duty map — `claude_code_briefs/DUTY_MAP.md` + `DUTY_MAP.json`; `CLAUDE.md` gains two rules.** One table per person;
the JSON's duties carry a read-only `due_sql`, the door and its marker. The check runs on every read of Needs-you (not in
`stock_watch.py`'s 06:30 run — that file is not in the brief's declared touch list); only an orphan duty (no door) raises a line,
a duty with a door does once it carries `"raise": true`.

## Calls made where the brief left room
- The orphan-duty check runs on each read of the owner's Needs-you, read-only, not in stock_watch's 06:30 job (stock_watch.py is not
  in the declared touch list); the lines are the same and never older than the page.
- A "no work set" login keeps its own Meri attendance tile. "Always-on" = tiles a staff login gets by role; "work" = any tile granted
  by name.
- The salt list counts VERIFIED lists only (the brief's "last verified"); "N days" = since that list (the brief's twelve days).
- Count vouchers live: **37** (7 orthotic — 4 ISSUE + 3 RECEIVE, 30 lines — and 30 dawa; 201 lines). The brief's 39 counts a voucher
  once per section.
- The medical PC's refused TEXT notes stay on the PC and in Drive (FromMedical\refused_text) — the server never sees them; the line
  names what the server's door refused.
- The walk signs in with its own random secret and its own user store written into scratch portal folders: the live secret and the
  live password store are never copied.

## Pins (FROM read on the box 01-Oct-2026 21:26 IST → TO; built by `make_s444.py` from the live bytes, every anchor exactly once)
| file | FROM | TO |
|---|---|---|
| /root/portal/clinic_sso.py (PARENT'S) | 2bc6ba15e52512d3f866536e758079ed | 6344e09c07c0506924d19824d5604b3a |
| /root/portal/portal.py (PARENT'S) | 626838cdf624446f90ac3061a79b6523 | ba61e35a9a2a2722d19304d791e255ca |
| /root/portal/tile_grants.json (PARENT'S, v30 → v31) | acc9cc1bad61b3f9a77f6f4f56b15476 | 392e6d89b09bcc7127cc541224771206 |
| /root/finance/amir_day.py | 068a3988e296f6579e2e780b2e4f623b | 2b497142efdb1a3d1b84e9f05cbf59ac |
| /root/finance/amir_salts.py | 8d6ef482573e56ae8676712a82a2a563 | d8d9ba772650a4d804add6953790d14d |
| /root/finance/reports_tile.py | 2798436712be69eb3c4486a0913e38f4 | 8a9870414cf299b0396bec4bc937ef04 |
| /root/finance/sanjeevni_approvals.py | 3999c4ced7aaf098eeeb00d696014cab | d2c550401ebfb7716126d24a09fae78f |
| /root/finance/stock_app.py (S437's TO, read live) | 4f2625c0a88e450c88e0b23d499d6fa8 | c0120fb67c78105fe797982fcb6ab644 |
| /root/finance/porders.py (S441's TO) | af4a6f57b6c7522784fdb53d6233d50b | 3620b374a8fb3ac4988b8e6525795f84 |

READ ONLY: `purchase_app.py` a51fe90e. Not changed: `porders.html` (the signed-in line is put into the bar as the page is served),
`stock_amir.html` (the BACK bar likewise), `finance_app.py`, `stock_watch.py`, crontab. Data: finance.db (backed up first) — four
`setting` rows; KEDAR 195's claim and answer; the additive tables `amir_self_wait` and `stock_board_open` on first use.
**Restarts every service that imports clinic_sso:** clinic-portal, clinic-finance, assetapp, attendance-dashboard, staff-register,
staff-ledger.

## Proof
`walk_s444.py` — the REAL portal, finance app and asset app in one process per side over scratch copies (backup API); its own rows
keyed W444, dates from today; the NEW side (the kit's nine files) against the OLD side (the box as it is, the negative control).
60 checks: the name check (green on the live stores, STOP on a crafted capital name); sign-in typed four ways, the home redirect,
`?all=1`, an old "Amir" token read as `amir` by all three apps, the no-work login; **the staff-eye walk** for amir, shavez, alisha,
shivani and reception (every duty's tile on the home, every due duty's door shows its marker); the voucher card on all seven steps,
one voucher entered lowers it, the board's BACK and visit record, renames only on a crafted green proof (walk-only patch); the bill
line's states; `self` → no claim, waits, (b) after 2 exports, clears at the paper's amount / a changed amount, audited once; KEDAR
195 by the rule and cleared by a crafted export at ₹17,959; the salt card, Shavez's days, Din band still allowed, (a) at its
threshold; (c), the refused report, the orphan duty; "Signed in" in the Purchase-orders bar; the negative control.
`walk_old_s444.py` — S246 / S245 / S244, S243 and S241's walks copied to scratch beside the patched amir_day; adjustments A1–A7 named
(A1–A3 the answers S285 and S444 added; A4, A5, A7 already red before S444 — S246, S244, S368; A6 the brief's own salt-in-_left);
S241's selftest of amir_day asserts the design S244/S245 replaced — the same eight reds before and after S444, no other.
`walk_s440_s444.py` — S440's walk with A8, A9 (both moved by the parent's S441, both red before S444), against S440's own backups.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S444_STAFF_SAFE/install_S444_STAFF_SAFE.sh
```
Undo: put back the nine `.bak_S444_<from8>` files, restart the six services, healthz 200, read the md5s back. The data (the four
settings, KEDAR 195's settled claim and `self` answer, the two additive tables) is data: `finance.db.bak_S444_<stamp>` only if the
owner asks for it to be reversed — say so first.
