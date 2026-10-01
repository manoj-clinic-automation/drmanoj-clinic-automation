# REPORT S444 — S444_STAFF_SAFE (D647 · D648 · F-669 F-670 F-671 F-672) · installed 01-Oct-2026 22:08 IST · published

## For the owner
- **Sign-in is fixed:** whatever is typed — "Amir", "AMIR", " amir " — it is now the same login `amir` in every app, and the
  login Amir's PC already had now reads as `amir` too (no new sign-in needed). Six services were restarted for this: the portal,
  the finance app, the scan app, attendance, staff register and staff ledger — all back up.
- **What Amir sees on opening the app:** it goes straight to "Amir ka kaam" (his tiles are under "Sab tiles"). At the top of every
  step a red card: **"Stock voucher baaki: 7 orthotic, 30 dawa — kholiye"**; one tap opens his stock board (it now has a BACK button
  to his day). Step 6 is now "Marg sudhar". Under each bill he sees Marg's amount beside the paper's ("mil gaya" / "farq Rs X" /
  "scan nahi hua"), and a new answer "Meri entry galat thi — Marg mein theek kar di" that raises no claim and clears itself.
- **KEDAR 195 (27-Sep):** by your ruling, Darpan's claim #1 (Rs 17,716) is settled as Amir's own entry. The bill waits as
  "Marg ki agli export ka intezaar" (Marg Rs 17,716, paper Rs 17,959) and clears itself when an export shows Rs 17,959. October's
  daily exports start from 1-Oct, so a September bill appears again only if September is exported; otherwise you get one line after
  two exports, and Amir taps "Theek hai".
- **Salt list:** it arrived today at 12:34, after all 43 salt ticks, so nothing is owed now. From now on, if it is owed, Amir sees a
  red card and Shavez's page shows the days it is late.
- **Your Needs-you list:** no new lines today (nothing is late yet). From now on these appear by themselves and go away when fixed:
  the salt list late (2+ days), Amir's own correction not seen in Marg after 2 exports, a claim for Darpan open 7+ days, the count
  vouchers not opened in 2 of Amir's visits, any duty with no screen, and a report refused the same day.
- **Duty map:** every staff duty is now listed with the screen that shows it. Nine duties have no screen (below, for the chat).
  It works: every change was tested on a copy of today's records (60 of 60), and checked again after it went live.

https://followup.dr-manoj.in/portal
https://followup.dr-manoj.in/finance/amir/day
https://followup.dr-manoj.in/finance/approvals

## For the chat

**Kit** `deploy_kits/S444_STAFF_SAFE/` (12 files: `make_s444.py`, `amir_block_s444.py`, `stock_block_s444.py`, `names_s444.py`,
`apply_s444.py`, `walk_s444.py`, `walk_old_s444.py`, `walk_s440_s444.py`, `install_S444_STAFF_SAFE.sh`, `README.md`, `KIT_ID.txt`,
`SUMS.md5`). Plus `claude_code_briefs/DUTY_MAP.md`, `claude_code_briefs/DUTY_MAP.json` (NEW), two rules in `CLAUDE.md`
("Every duty has a door"), and one exact-path line in `.gitignore` (`!claude_code_briefs/DUTY_MAP.json` — the blanket `*.json` rule
would have hidden it; not named in the brief, needed for the publish). Ran on the box from `/tmp/s444go` — byte-identical to the
repository's kit (`diff -r` after the publish). Build lock taken 22:07:21 IST (owner S444_STAFF_SAFE), held through the install and
this report.

**What was read first (21:26:56 IST, read-only)** — the brief's §2 facts, as the box showed them:
- F-669: `portal.login()` verifies by `_norm(user)` and signed the session with the name as typed; `clinic_sso.verify_token` returned
  `payload["u"]` unchanged. Grants, masks and `unit_role` are small letters. (The finance gate's `roles_for` already compares
  `lower(username)`, so `/finance/amir` admitted "Amir"; the portal's grants did not.)
- F-670: `amir_claim` #1 open — KEDAR PHARMACEUTICAL 195 (27-Sep), Rs 17,716, reason `other`, raised by amir 01-Oct 09:04:03; answer
  09:10:57. purchase_bill id 535 (one row per bill: each export moves its amount and `bw_md5`), newest export 01-Oct 08:58:32, scan
  B-0091 linked EXACT, total Rs 17,959; no S440 paper amount on it.
- F-671: the newest VERIFIED SALT_WISE_ITEM_LIST is of **01-Oct 12:34:43** (received 12:34:47), after all 43 ticks (26-Sep 09:58 →
  01-Oct 09:30). So the list is NOT owed today; the brief's "twelve days" was true before 12:34.
- F-672: count #1 — **37 Marg vouchers** (28 ISSUE + 9 RECEIVE; **7 orthotic — 4 ISSUE + 3 RECEIVE, 30 lines**; 201 lines), made from
  27-Sep 12:59, `stock_voucher_entered` 0 rows. The brief's 39 counts a voucher once per section it carries. Amir is a medical
  viewer (the board admits viewers).
- The refused-text note of the medical PC (e.g. 30-Sep sale, line 52 `***`) is written by `marg_watch.py` to Drive
  `FromMedical\refused_text\` (S396.1); nothing brings it to the server (no `mi_file` row, no pipeline-status field).
- Services importing `clinic_sso` (grep of /root, retired copies excluded): clinic-portal (`portal.py`, `tracker_pass.py`),
  clinic-finance (`finance_app.py`), assetapp (`asset_register.py`), attendance-dashboard (`att_dashboard.py`), staff-register
  (`staff_register.py`), staff-ledger (`staff_ledger.py`). ring-hook does not.

**Live files, FROM → TO (each md5 read back on the box after placing; again by the repository's installer: ALREADY INSTALLED)**
| file | FROM | TO |
|---|---|---|
| /root/portal/clinic_sso.py (PARENT'S, 5 anchored edits) | 2bc6ba15e52512d3f866536e758079ed | 6344e09c07c0506924d19824d5604b3a |
| /root/portal/portal.py (PARENT'S, 4 anchored edits) | 626838cdf624446f90ac3061a79b6523 | ba61e35a9a2a2722d19304d791e255ca |
| /root/portal/tile_grants.json (PARENT'S, v30 → v31, amir's `home`) | acc9cc1bad61b3f9a77f6f4f56b15476 | 392e6d89b09bcc7127cc541224771206 |
| /root/finance/amir_day.py (13 anchored edits + the S444 block) | 068a3988e296f6579e2e780b2e4f623b | 2b497142efdb1a3d1b84e9f05cbf59ac |
| /root/finance/amir_salts.py (1 edit + a small block) | 8d6ef482573e56ae8676712a82a2a563 | d8d9ba772650a4d804add6953790d14d |
| /root/finance/reports_tile.py (5 anchored edits) | 2798436712be69eb3c4486a0913e38f4 | 8a9870414cf299b0396bec4bc937ef04 |
| /root/finance/sanjeevni_approvals.py (the Needs-you hook, block 15) | 3999c4ced7aaf098eeeb00d696014cab | d2c550401ebfb7716126d24a09fae78f |
| /root/finance/stock_app.py (S437's TO read live; 1 edit + the S444 block) | 4f2625c0a88e450c88e0b23d499d6fa8 | c0120fb67c78105fe797982fcb6ab644 |
| /root/finance/porders.py (S441's TO; "Signed in" in the S440 bar only) | af4a6f57b6c7522784fdb53d6233d50b | 3620b374a8fb3ac4988b8e6525795f84 |

READ ONLY: `purchase_app.py` a51fe90e (its read-only door to assets.db). Not changed: `porders.html`, `stock_amir.html` (the signed-in
line and the board's BACK are put in as the pages are served), `finance_app.py`, `stock_watch.py`, `asset_register.py`, crontab.

**Backups:** `finance.db.bak_S444_20261001_220811` (backup API, 29,102,080 bytes) and `.bak_S444_<from8>` beside each of the nine
files (each read back at its FROM md5). **Restarted:** clinic-portal, clinic-finance, assetapp, attendance-dashboard,
staff-register, staff-ledger — all active since 22:08:51–52 IST.

**Health after placing (22:08–22:10 IST):** local finance healthz 200; `/finance/amir`, `/finance/porders` 302 (the login gate);
portal `/portal/health` 200, `/portal` 302, `/portal/login` 200; asset app login 200, `/intake` 302; attendance :8042 / 302, staff
ledger :8043 / 404, staff register :8044 / 404 — each the same as before the restart; nothing "NOT mounted"; no traceback in any
journal. Public 22:09:58: `/finance/healthz` 200, `/portal`, `/finance/amir/day`, `/finance/approvals` 302.

**The data step on the live database (`apply_s444.py`, 22:09 IST)** — settings added (INSERT OR IGNORE): `amir.salt_owed_days=2`,
`amir.self_exports=2`, `amir.claim_open_days=7`, `amir.voucher_visits=2`. KEDAR 195: answer `other` → `self` (by "S444 rule"),
claim #1 settled `amir_own_entry` by "S444 rule"; audited in `purchase_audit`: `amir_claim_settled` and `amir_self` (who "S444 rule
(owner, 01-Oct: Amir's own entry)"); waiting Marg Rs 17,716, paper Rs 17,959 (the scan's read total). Amir's card as he sees it:
"Marg sudhar — Stock voucher baaki: 7 orthotic, 30 dawa — kholiye · Ginti #1 · har voucher Marg mein daal kar uska number likhiye.
Din band karne se nahi rukta." Renames: not shown (vouchers open; the proof is "wait"). Salt list: not owed. **S444 Needs-you
lines live today: 0** — (a) nothing owed; (b) KEDAR 195 needs 2 bill-wise exports after 01-Oct 09:01 (the next Amir days);
(c) claim #1 settled, no other claim; (d) 1 of his visits (01-Oct) since the vouchers were made — the line comes on his 2nd visit if
he has not opened the board or entered one; the duty map's one live orphan (`amir.arrival_bill_entry`) is 0; no refusal today.
No W444 row on the live database (bills 0, claims 0, mi_file 0); `stock_board_open` 0 rows (made on first use).

**The walk — `walk_s444.py`, in the install: `WALK_S444 GREEN -- 60 of 60 passed`** (the real portal, finance app and asset app in
one process per side, over scratch copies made with the backup API; its own rows keyed W444; dates from today; sign-in on the walk's
own random secret and own user store — the live secret and password store never copied):
- *0 the name check:* live stores green (users 15, grants 15, unit_role 12, lane logins 4, asset users 3, pend_mark / sale-check
  actors 0); a crafted `unit_role` 'W444Amir' → STOP, exit 3, named.
- *1 sign-in:* "Amir", "AMIR", " amir ", "amir" → token `u`='amir'; first `/portal` 302 → `/finance/amir`; next 200 with his tiles;
  `?all=1` shows "Amir ka kaam" and "amir (staff)". A token minted pre-S444 as "Amir": portal → `/finance/amir`, finance whoami
  'amir', asset app 'amir'; `/finance/amir` 303 into his day; intake 200. A login with no work: the Hindi line, Sign out, only
  "Meri attendance".
- *2 the staff-eye walk (DUTY_MAP.json):* amir 7 duties (due: bills 5, own correction 1, vouchers 37 — each door shows it; first
  `/portal` → `/finance/amir`); shavez 5; alisha 6; shivani (Alisha's queue, `shared`) 6; reception 4 (due: bill scans 23, scan
  questions 11, order arrival 1) — every tile on the home, every due duty's door shows its marker.
- *3 Amir's door:* count #1 37 open (7 orthotic, 30 dawa) read from the box; steps 1–7 all carry "Stock voucher baaki: 7 orthotic,
  30 dawa", "Signed in: amir", "Sab tiles"; step 6 "Marg sudhar"; one ortho voucher entered (POST 200) → 6 / 30; the board: BACK
  → `/finance/amir`, "Signed in: amir", openings recorded [amir 0, manoj 1 (checker)]; every voucher entered + the real proof → no
  rename, no voucher line; a crafted green proof (walk-only patch) → "Naam badlo: 22 naam" on step 6 and atop step 2; line (d) after
  2 visits (01-10 real + 28-09 crafted) → "Count vouchers waiting: 37 (orthotic 7) — Amir has not opened them in 2 visits"; gone
  once one voucher is entered.
- *4 the bill line:* W444A "Marg ₹1,000 · Kaagaz (scan) ₹1,000 · mil gaya"; W444B "farq ₹100"; W444C "scan nahi hua"; W444D the
  S440 paper amount wins: "Kaagaz (paper) ₹4,100 · farq ₹100"; the seventh answer on every bill.
- *5 self:* W444D/E answered `self` → kept, no claim; exports at the old amount → still waiting; after 2 → line (b) ×2; an export at
  the paper's amount clears D ("S444 auto: Marg = kaagaz", audited once, still once after a second page load); no scan, changed
  amount clears E ("S444 auto: Marg ki rakam badli"); line (b) gone.
- *6 KEDAR 195:* claim #1 settled `amir_own_entry` by "S444 rule", answer `self`; step 5 shows "Marg ₹17,716 · Kaagaz (scan) ₹17,959 ·
  farq ₹243" and "Marg ki agli export ka intezaar"; a crafted export at ₹17,959 clears it, audited once.
- *7 salt:* the box today → no card; a crafted tick → red card on step 6, step 7 (with "Aaj nahi aayi to Shavez kal subah
  nikalega") and the salts page; Shavez's row "0 din se baaki", red, "Signed in: shavez"; Din band still offered (gate 2,4,5,6);
  line (a) absent at 2 days, present at 0; a verified list after the tick → card, line and owed days gone.
- *8:* claim open 8 days → "Claim for Darpan open 8 days: KEDWALK444 PHARMA bill W444F Rs 12,345 (raised by amir 23-09)", the 3-day
  one not; settled → gone; a refused file → "Report refused today: SALE_BILLWISE at HH:MM — … line 52 (***)"; the crafted map's
  orphan duty raised, the coded one not.
- *9:* Purchase orders — "Signed in: alisha" inside the S440 bar; the bar once, "← BACK" once.
- **Negative control (the box as it is, same rows):** "Amir" → session 'Amir', no redirect, no "Amir ka kaam"; the old token reads
  'Amir' in finance, no grant; no Hindi line (Forms, Scan Purchase, Attendance, Meri attendance, Staff Register shown); no paper
  amount, no `self`, no card; `self` not kept; no S444 Needs-you line; claim #1 still open; no salt card or days; no BACK bar on the
  board, no "Signed in" on Purchase orders.

**Earlier walks re-run on the patched files (in the install)** — each COPIED to scratch beside the patched file; the kit folders
are not edited. Baseline = UNADJUSTED on the box as it is (already red before S444): S246 40/41 (G2), S245 51/53 (A8, F2), S244
62/62, S243 67/70 (healthz kit, step-4 tick, hub call), S241 selftest_amir_day 35/43, selftest_amir_salts 36/36.
Patched + adjusted: **S246 41/41 · S245 53/53 · S244 62/62 · S243 70/70 · S241 salts 36/36**; adjustments, each named:
- A1 (S246 G2), A3 (S245 F2): the answers are seven — S285 added `supplier`, S444 adds `self`. A2 (S245 A8): 4 bills × 7 radios.
- A4 (S243): S246 renamed the module's healthz kit. A5 (S243): S244 added a third check mark on step 4. A7 (S243): S368 moved the
  hub's `loadAmirVisit();` into `loadMargFold()`. — all three red before S444.
- A6 (S243): "_left() does not name the list" → S444's brief 3.4 names the salt list there as words; the gate (2,4,5,6) asserted.
- **S241 selftest_amir_day stays 35/43 — NOT adjusted:** it asserts S241's step-4/step-5 design, replaced by S244 (7 asserts: in
  transit, not missing; dobara only after the grace window; …) and S245 (`required` removed); the gate is "the same eight as before
  S444, no other" — met. S244's and S245's own walks (62/62, 53/53) carry those facts.
- **S440's walk 66/66** (on the box + S444 against S440's own `.bak_S440` files) with A8 (S441's `twin` group counted) and A9 (S441
  reworded the intake's "Kaise?" paragraphs; the fold and its text asserted) — both red on the box as it is before S444 (64/66).
- Also green on the built files: `clinic_sso --selftest` 25/25 (2 new S444 checks), `reports_tile` own selftest 40/40.

**Calls made where the brief left room** (each also in the kit's README)
- **The orphan-duty check runs on every read of Needs-you, not inside stock_watch's 06:30 run:** `stock_watch.py` is not in the
  brief's declared touch list (rule 9). Same lines, never staler than the page; read-only connection, SELECT/WITH only.
- **Only ORPHAN duties raise an owner line from the map** (the brief: "any other orphan duty in DUTY_MAP"). A duty WITH a door raises
  one once it carries `"raise": true` in DUTY_MAP.json — none does: switching them on now would add ~10 lines at once (see below).
- **"No work set"** = a staff login shown no tile granted by name. It keeps its own "Meri attendance". Today: `sandeep`, `surendra`,
  `vikky` (none ever submitted a scan on the asset app; `parvesh` is inactive). Doctor and manager roles are never "no work".
- **The home redirect is once per sign-in** (cookie `clinic_portal_home` = login + the token's issue time, path /portal, Secure,
  HttpOnly, 31 days). Amir's PC session (issued before S444) gets the redirect on its next `/portal`.
- **(d) "visit" = a day of `amir_day`; "touched" = he opens the board (a checker's look does not count) or enters a voucher.**
- **The salt list counts VERIFIED lists; "N days" = since that list** (the brief's twelve days), the 2-day threshold on the oldest
  unproven tick. The Marg menu path: the S243 prompt carries none ("Marg se SALT WISE ITEM LIST nikaalo"); those words are used.
- **Shavez's salt row** turns "due" (red, with days) whenever a tick is newer than the last verified list — also when an older list
  arrived the same morning (before, the row said "aa gayi" for the morning list).
- **The refused-report line names what the server's door refused today** (`mi_file` not VERIFIED / pc_verdict REFUSED); the PC's
  refused TEXT notes stay on the PC and in Drive.
- **KEDAR 195's disposition `by_user` reads "S444 rule"** (who changed it), the claim's `settled_by` "S444 rule".
- **The walk's sign-in uses its own random secret and user store**, not "the live secret's walk copy" — the same proof without
  handling the live secret.
- **Stock board "BACK" and Purchase orders' "Signed in" are inserted as the page is served** (`stock_app.page_amir`, `porders.page`),
  so `stock_amir.html` and `porders.html` (not named) stay untouched. Purchase orders is now served from the file's text with
  `Cache-Control: no-store` (was `send_file`), as S441 already did for the shared login.

**The duty map's no-door findings** (`DUTY_MAP.md`, built by a read-only pass over the live tiles, `unit_role` and every pending-work
table; 42 duties with a tested `due_sql`)
1. Darpan — Amir's supplier claims (`amir_claim`): no page Darpan can open reads it. *Sanjeevni* (amir_day; Kal ka hisaab or Stock
   milaan could carry it). Owner's line now exists (c).
2. Amir — pick a Sunday for the full count: only on his stock board (no tile; S444's card opens it only while vouchers are open).
   *Sanjeevni.*
3. Amir — key the bill for goods tapped as arrived: same board. *Sanjeevni.* (JSON line raised when due 3+ days; 0 today.)
4. Amir — fix lines from the stock traces (28 open): same board. *Sanjeevni.*
5. Reception phone — supplier NEFT messages not leaving (18 queued since 26-Sep 19:49): nothing on the reception home. *Sanjeevni.*
6. Reception login — holds clinic and checks maker seats but has no Docterz daily collection / Morning match / Check karein tile.
   *Parent's* (tile_grants.json).
7. Morning match — opens on yesterday only: 13 clinic days with no first pass and 2 waiting for Shavez open only by a typed address.
   *Parent's* (clinic_money).
8. Spine tasks (`marg_task`, 48 open since 07-Sep) — no page, no person. *Sanjeevni* (marg_spine).
9. **Found by the staff-eye walk:** Shavez — the same 18 supplier messages: his Vendor payments tile opens the CURRENT month
   (`/pay/2026-09`), which shows nothing of them; "Pending — baaki … Bhejo" is only on `/pay/2026-08`. *Sanjeevni* (purchase_app —
   READ ONLY here). The owner's line exists (supplier_msg).

**Anything I did NOT do, and why**
- Not in stock_watch's 06:30 run (see the calls). No owner line for duties that HAVE a door (the owner's call: one field per duty).
- S241's selftest of amir_day was not rewritten to S244's design (above).
- No page was opened under a real login (no password is entered from here); the live sign-in path was proven by the walk on the
  real code, and the live box was checked by the installer's probes and the figures.
- **One command was refused by the permission list:** a local PowerShell line that ended by deleting `__pycache__` folders with
  `Remove-Item -Recurse`. Not re-spelt: the local checks were re-run without creating any (`python -B`, `compile()` instead of
  `py_compile`).

**Outside the brief — noticed, not touched**
- **Doors that exist but the work is not done** (measured 21:50 IST): Vaapsi Desk jaankari 48 shelf checks + 30 name/ID disputes
  (2 answers ever) · counter sheet 28 clinic days unfilled (oldest 11-Aug) · Morning match 13 days no first pass, 13 staff flags ·
  Check karein 36 X-ray files with no clinic ID · Report baaki 16 X-ray photos not filed · bill scans 23 · physiotherapy received
  12 days · spot counts 4. Each becomes an owner line the day its duty carries `"raise": true` in DUTY_MAP.json.
- 7 counter returns from August (03–19 Aug) wait for your OK; the existing Needs-you line counts the current month only, so they
  never show (`sanjeevni_approvals._returns_pending`).
- `PUBLISH_ALL` publishes everything pending: this commit also carried files other sessions had written in the repository during
  this build — `deploy_kits/S445_RING_OUTCOMES_BACKUP/` (6 files), seven new `deploy_kits/KB_canon_all/` S287-close files and two
  changed ones there (`CANONICAL_MANIFEST.md`, `OWNER_TODO_LIVE.md`) — plus the brief `S444_STAFF_SAFE.md` itself. They were not
  written or changed by S444; the publish gate (F-100 / F-185) passed on the whole commit.
- `portal.py` line ~1406 carries an invalid escape (`"\/"`) that newer Pythons warn about — existing, untouched.
- The frozen S241/S243 walks leave temp folders in `/tmp` (`amirday_*`, `walk_s243_amir_visit_*`) — synthetic data; the 12 made by
  this build's runs were removed.

**After the publish (22:09–22:11 IST):** `PUBLISH_ALL` gate clean, commit `58c5020` on main, origin verified; on the box
`git pull --ff-only` → HEAD 58c5020 (22:09:58); the repository's kit SUMS 11 of 11 OK; `diff -r` repo kit vs `/tmp/s444go`
(what ran): byte-identical; `DUTY_MAP.json` in the clone = the one the install used; the repository's installer: "ALREADY
INSTALLED … all six services active · healthz 200"; no `__pycache__` in the repository's kits; the build's scratch in the server's
/tmp (the walks' copies of the two databases, the trial and probe folders) removed 22:10:30. The lock is released after this report
is published (second commit).

**Undo:** the nine `.bak_S444_<from8>` files back (`/root/portal/` clinic_sso.py, portal.py, tile_grants.json; `/root/finance/`
the six), `systemctl restart clinic-portal clinic-finance assetapp attendance-dashboard staff-register staff-ledger`, healthz 200,
md5s read back. The settings rows, KEDAR 195's settled claim and `self` answer, and the two additive tables are data:
`finance.db.bak_S444_20261001_220811` only if you ask for them to be reversed — say so first.
