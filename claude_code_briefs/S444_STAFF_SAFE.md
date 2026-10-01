# Claude Code brief — S444_STAFF_SAFE (the system remembers so the staff need not: one sign-in name whatever is typed, a one-job login opens on its job, Amir's bill screen shows what the server already knows and has a "my own entry" answer, the salt list cannot be silently forgotten, every slip becomes one line for the owner)

Written 01-Oct-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S444 · decisions D647, D648 · faults F-669, F-670, F-671, F-672** (claimed on
the System Board, v138–v139). Runs AFTER the parent's S441–S443 (installed 01-Oct 09:19–09:20 IST) — **porders.py/html and tile_grants.json moved
there: read live.** S438_COUNT_BOOK stays HELD. Staff pages Hindi (Roman), owner pages English.
Touches, **DECLARED, the parent's:** `/root/portal/clinic_sso.py` (one change), `/root/portal/portal.py` (home + the empty-login line),
`/root/portal/tile_grants.json` (data: one `home` key). Sanjeevni: `amir_day.py`, `amir_salts.py`, `reports_tile.py`,
`sanjeevni_approvals.py` (the Needs-you hook), `stock_app.py` (the Amir board's BACK and the pending-voucher read), `CLAUDE.md` + NEW `claude_code_briefs/DUTY_MAP.md`, `porders.py` (one "signed in" line in the S440 BACK bar only), `purchase_app.py` READ ONLY
(the scan's amount through the S439/S440 link).

## 1 · The owner's words (01-Oct)
"Staff tend to forget things and then issues crop up again and again — rectify this properly." On the morning's events: Amir's PC showed a
different app from his phone under the same login (the owner signed in himself, in Chrome, after clearing all data, and in incognito);
Amir had corrected a wrong rate he typed on a KEDAR bill, "the prompt he got was confusing", and he entered one answer; the salt Excel had
to be taken on the PC.


Later the same day (F-672, D648): "After so much coding this is a very big lapse — it was finalised earlier that everything populates in his
portal, in his work. It is very difficult to hand him a link every time he comes. I have been asking you to check each and every product
thoroughly; these are operational products and hassles keep coming up. Decide how to proceed — in this and in other builds."

## 2 · What the chat read (01-Oct, the server's own log and the code) — REPORT the same facts first
- **F-669 — one person, two sign-in names.** `portal.login()` checks the password with `clinic_users.verify_password(STORE, user, pw)`,
  which looks the user up by `_norm(user)` = `strip().lower()`; it then signs the session with `clinic_sso.make_token(user, …)` — the name
  **as typed**. `clinic_sso.verify_token` returns `payload["u"]` unchanged and every app trusts it (`portal._sso_user`,
  `finance_app.py` ~220, `asset_register.py` ~624). Grants (`tile_grants.json` users), masks and `unit_role` are keyed in small letters. Typed
  "Amir" → password accepted → session "Amir" → no grant, no mask, no unit: no "Amir ka kaam", the masked tiles back. The phone's box
  (`autocapitalize=none`) always sends "amir". The web log of 01-Oct: the PC loaded `/portal` five times 09:13–09:15 and never reached
  `/finance/amir`; the phone did all the work (08:55–09:32).
- **F-670 — no answer for "my own mistake".** `amir_day.REASONS` offers Theek hai · Kam maal aaya · Deal nahi mili · Discount kam · Supplier
  galat likha · Aur koi baat — all supplier faults, and every one but Theek hai/Supplier raises an `amir_claim` for Darpan. Amir had typed a
  wrong rate for one item of **KEDAR 195 (27-Sep)** and corrected it in Marg; he answered "Aur koi baat" (09:10:57) → claim #1, Rs 17,716,
  open in Darpan's queue. The bill's scan B-0091 reads Rs 17,959; Marg's export of 09:00 carried Rs 17,716 (before his correction). The bill
  line never showed him the paper's amount.
- **F-671 — a step nobody owns.** The last verified SALT_WISE_ITEM_LIST is of 19-Sep; 43 salt ticks are waiting for it (01-Oct). Amir's step 6
  and Shavez's "Aaj ki reports" (`reports_tile._salt_row`) both show it as due — for twelve days — and nothing reached the owner. Marg's
  TEXT export of this list is not read anywhere (marg_txt knows only the bill-wise sale and the closing stock): it must come as Excel.

- **F-672 — a duty with no door.** The count's **39 Marg vouchers (201 lines; 7 orthotic: 4 ISSUE + 3 RECEIVE, 30 lines)** wait on Amir's
  stock board `/finance/stock/page/amir?count=1`; `stock_voucher_entered` has 0 rows (nightly of 01-Oct) and the web log of 01-Oct shows Amir
  never opened that board — "Amir ka kaam" (`/finance/amir`, his only work tile) never mentions it. The 22 orthotic renames (gated on the
  proof, S437) and live orthotic ordering both wait on these vouchers.

## 3 · The build (D647, D648)

### 3.1 One sign-in name (F-669) — `clinic_sso.py`, PARENT'S, declared
- `make_token`: the name stored is `user.strip().lower()`. `verify_token`: the returned `user` is `strip().lower()` too — so every session
  already issued as "Amir" becomes "amir" at once, in every app that reads the cookie, without anyone signing in again.
- `portal.login()`: passes the normalised name (belt and braces); nothing else in the form changes.
- **Before switching, the installer proves no live name depends on case:** every name in the clinic_users store, `tile_grants.json` users,
  `unit_role`, `lane` logins (S409), `pend_mark`/`sale_check` actors — all already small letters; if any is not, STOP and report it, place
  nothing.
- **"Who is signed in" on the staff pages:** the portal home already prints `who.user (role)` — keep. Add one quiet line "Signed in: amir" to
  Amir's pages (`amir_day._page`, `amir_salts`), to Shavez's reports page, and inside the S440 BACK bar of Purchase orders (right side, small).
- **A login with no work set:** when `_visible_sections` returns nothing but the always-on tiles, the portal says in Hindi "Is naam par koi
  kaam set nahi hai — sahi naam se sign in kijiye" with a big **Sign out** button, instead of a page of unrelated tiles.

### 3.2 A one-job login opens on its job — `portal.py` + `tile_grants.json`, PARENT'S, declared
`tile_grants.json` gains an optional `users.<name>.home` (data edit, version +1, by name); seed **amir → `/finance/amir`**. `portal.home()`:
a login with `home` is sent there (302) on its first `/portal` of a sign-in; `/portal?all=1` (a link "Sab tiles" on his pages) shows the
tiles as today. Nobody else gets a `home` in this kit.

### 3.3 Amir's bill line shows what the server knows; "my own entry" answer (F-670) — `amir_day.py`
- Each bill block on step 5 shows, under the supplier and number: **"Marg: Rs X · Kaagaz (scan): Rs Y"**, read through the S439/S440 link
  (`purchase_bill.scan_bill_id` → the paper amount S440 stores, else the scan's read total; READ ONLY). Equal within Rs 1 → green "mil gaya";
  apart → red "farq Rs Z"; no scan → "scan nahi hua".
- A seventh answer **"Meri entry galat thi — Marg mein theek kar di"** (reason `self`): raises NO claim; the bill moves to the flagged list
  as "Marg ki agli export ka intezaar"; it **clears itself** (disposition `ok`, audited "S444 auto: Marg = kaagaz") when a later BILLWISE export
  carries the bill at the paper's amount (±Rs 1); with no scan, when a later export carries a different amount from the one flagged — else it
  stays and he taps Theek hai. It never holds a day open (S246 rule for flagged bills).
- **KEDAR 195 (27-Sep), by the owner's ruling of 01-Oct** — Amir's own entry, corrected: claim #1 settled at install (`settled_outcome
  'amir_own_entry'`, by "S444 rule", audited) and the disposition becomes `self`; it clears itself on the next export that shows Rs 17,959.

### 3.4 The salt list cannot be silently forgotten (F-671) — `amir_day.py`, `amir_salts.py`, `reports_tile.py`
- Whenever salt ticks are newer than the last verified salt list, Amir's step 6 and the close screen (step 7) carry one red card: **"Ek export
  aur: SALT WISE ITEM LIST — Excel mein (text nahi)"**, with the Marg menu path as the S243 prompt already words it. It lists in `_left(w)` but
  does **not** block "Din band" (an Excel failure must not trap him); the close card says "Aaj nahi aayi to Shavez kal subah nikalega".
- Shavez's "Aaj ki reports" row for the salt list (`_salt_row`, exists) gains the days it has been owed ("12 din se baaki") and stays red.

### 3.5 Every slip becomes one line for the owner — `sanjeevni_approvals.py` (the existing Needs-you hook)
Four lines, English, each with who and since when, each disappearing by itself when put right: (a) **"Salt list not received for N days —
M salt corrections unproven (Amir / Shavez)"** after 2 days; (b) **"Amir's own correction on <supplier bill> not yet seen in Marg after 2
exports"**; (c) **"Claim for Darpan open N days: <supplier bill> Rs X"** after 7 days; (d) **"Count vouchers waiting: N (orthotic M) — not opened in 2 of Amir's visits"**; and, from 3.7's check, any other orphan duty in DUTY_MAP; and **a report the medical PC refused** (the watcher's refused-text note, e.g. 30-Sep sale, line 52 `***`) named the same day. Settings for the three day counts; nothing else on the
page moves.


### 3.6 Amir's one door: everything he owes is on "Amir ka kaam" (F-672) — `amir_day.py`, `stock_app.py`
- Step 6 is renamed **"Marg sudhar"** and carries, from the system's own state, in this order: **(a) Stock voucher** — per open count, the
  vouchers not yet marked entered, orthotic first ("Stock voucher baaki: 7 orthotic, 32 dawa — kholiye"), the button opening his stock board;
  **(b) Naam badlo** — only when the proof is green (S437 gate unchanged), with its count; **(c) Salt** — as today. Each line disappears when
  its work is done. The same card also stands at the top of whatever step he is on while any (a)/(b) is open, and in the close screen's list.
- It does **not** block "Din band" (a short visit must still close); a count's vouchers not touched for **2 of his visits** become an owner
  Needs-you line (3.5 d): "Count vouchers waiting: N (orthotic M) — Amir has not opened them in 2 visits".
- His stock board's BACK goes to `/finance/amir`; the board is reachable only through this door (no new tile).

### 3.7 The duty map and the staff-eye walk (D648) — `CLAUDE.md`, NEW `claude_code_briefs/DUTY_MAP.md`
- **DUTY_MAP.md**: one table per person (Amir, Darpan, Shavez, Alisha, Shivani, Reception, Bhati, Sukhveer, the owner) — every recurring duty,
  the system state that says it is due, the screen on that person's own home that carries it, and the Needs-you line if it is missed. Build it
  by reading the live tiles (`tile_grants.json`, `unit_role`) and every pending-work table the Sanjeevni modules keep; list any duty that has
  **no door** as a finding in the report (do not invent doors for the parent's modules — name them for the parent).
- **CLAUDE.md** gains two rules for every later kit: (1) a kit that adds, moves or removes a staff duty updates DUTY_MAP.md; (2) **the staff-eye
  walk** — the walk renders the home of every login the kit affects, as that login (a walk-only session on the scratch copy), and asserts each
  pending duty of theirs is visible there; a kit is not done until it passes.
- **The nightly orphan-duty check**: one job (in `stock_watch`'s 06:30 run, no new cron) reads DUTY_MAP's machine part (a small JSON beside it:
  duty → query → allowed days → owner line) and raises 3.5's Needs-you lines; nothing else.

## 4 · Pins — read live after S441–S443: portal.py 626838cd, clinic_sso.py 2bc6ba15, tile_grants.json acc9cc1b (v30, S441), porders.py
af4a6f57 / porders.html 7a6799ae (S441), amir_day.py 068a3988, stock_app.py (S437's TO — read live), amir_salts.py 8d6ef482, reports_tile.py 27984367, sanjeevni_approvals.py
3999c4ce, purchase_app.py a51fe90e (READ ONLY). **Restart every service that imports clinic_sso** — find them on the box (grep the unit
files and the apps), at least `clinic-portal`, `clinic-finance`, `assetapp`; name each in the report.

## 5 · Walk (scratch copies; rows keyed W444*) — including the staff-eye walk of 3.7 for amir, shavez, alisha, shivani, reception
Amir's door: with the live count's 39 vouchers open, every step of his day shows the card with 7 orthotic first; marking a voucher entered on the board lowers the count; renames appear only on a crafted green proof; the Needs-you (d) line appears after 2 crafted visits and vanishes when one voucher is entered · DUTY_MAP.md lists each person and the JSON check raises a line for a crafted orphan · Sign-in: "Amir", "AMIR", " amir " each get a session named amir — the portal shows his tiles and sends him to `/finance/amir`; `/finance/amir`
and the asset intake admit him; an old token minted as "Amir" (crafted with the live secret's walk copy) now reads as amir in all three apps;
`?all=1` shows the tiles; a login with no work sees the Hindi line and Sign out; the pre-install name check passes on the live stores and
STOPS on a crafted capital name · Bill line: the three states (mil gaya / farq / scan nahi hua) with the right figures; `self` raises no claim,
waits, clears on a crafted export at the paper amount (audited once), stays on a crafted export at the old amount; the no-scan case clears on
a changed amount; KEDAR 195's claim settled by the rule and its bill waiting · Salt: the card on step 6 and 7 when ticks are newer than the last
list, absent when not; close still allowed; Shavez's row shows the days · Needs-you: (a)(b)(c) appear at their thresholds and vanish when
cleared · S241/S243/S246 walks and S440's re-run green (assertions on REASONS and the bill block adjusted, each named) · negative control (old
files: "Amir" gets no grant; no paper amount; no `self`; no Needs-you line) · dates from today.

## 6 · Done means
Kit `deploy_kits\S444_STAFF_SAFE\` · installed · published · `claude_code_briefs\REPORT_S444.md` — owner lines first: sign-in fixed in one
sentence (and the services restarted), what Amir now sees on opening the app, KEDAR 195's state, the salt list state, Amir's voucher card as he will see it, the Needs-you lines live
today; **the duty map's no-door findings**; ending with `https://followup.dr-manoj.in/portal`, `https://followup.dr-manoj.in/finance/amir/day` and
`https://followup.dr-manoj.in/finance/approvals`.
