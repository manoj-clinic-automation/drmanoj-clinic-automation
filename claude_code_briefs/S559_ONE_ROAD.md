# S559_ONE_ROAD — one easy road through the scan app (brief for the build runner, Agent SDK, the API credits)

*Written 14-Oct-2026 by the Scan App project (session 315). Kit **S559** claimed on the board `_numbers` (v423 → v424)
with its PLANNED line (D646). The owner, 13:13–13:17 IST: "the flow is very confusing … do all what is required for a
proper easy flow so that all that is built is useful." This file is the whole scope. Run by
`D:\Downloads\_kbtools\agent_build\run_build.py S559_ONE_ROAD`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** Kit in
`deploy_kits\S559_ONE_ROAD\`, report `claude_code_briefs\REPORT_S559.md`, then stop. The Scan App chat checks it; the
owner publishes and pastes one server line. Nothing live placed or restarted; no live row written.

## 0 · What a read-only walk of every route found (13:2x IST, as the owner)
- The owner enters from the portal tile *"Asset Register — Clinic assets & AMC"* → `/scanapp/`. Its top menu: Dashboard ·
  Assets · Renewals · **Drafts** · Staff · **Purchases** · Vendors · Admin · account · Logout.
- **The sorting desk is in no menu and not on the home page** (reached only via "Spend this month" → The month →
  "‹ Sorting desk", or Purchases → "Clinic papers to sort" → "Sorting desk →"). Bills awaited, the Implant ledger and the
  papers page have no menu entry either; **the desk's own pages carry no menu**, only "‹ Sorting desk" links.
- **"Drafts" in the menu is the old asset-drafts inbox** (`/drafts`, empty) — not the papers waiting; the owner reads it as
  the waiting papers.
- **Every paper row** (Purchases `/bills`, the papers list `/papers`, the ledger, the month) **opens the old bill page**
  `/bills/<id>`, which has **no scan on it** — the PDF is one more click — and cannot set a paper's place.
- The desk **cannot be opened on a given paper** from a link.
- **Two routes each** for the month (`/papers/month`, `/purchases` vs `/desk/month`) and Bills awaited (`/papers/challans`
  vs `/desk/awaited`); Purchases carries two links to The month.
- The old bill page shows a **captured** paper as **"approved"** (B-0016: the list says captured, its page a green
  "approved" badge — the badge labels any non-draft as approved).
- Purchases' **"← BACK" goes to the portal**, not the scan app home.
- Drafts filter (status=draft) = 12; the desk's waiting = 14 (it also holds an approved but unsorted paper and an
  unread Other-document paper) — two different meanings of "waiting" side by side.

## 1 · Read first
`claude_code_briefs\S551_SORTING_DESK.md` (v4), `S555_DESK_CORRECTIONS.md`, `S557_MACHINE_PAGES.md` and their reports —
every rule and NEVER still binds. **Copy `deploy_kits\S557_MACHINE_PAGES\`'s kit shape exactly** (installer `S559_*`
variables; rehearsal's refusals and five outcomes; walk isolated before import incl. `CLINIC_PORTAL_DIR`,
`FINANCE_LOCAL_URL`, `SHARED_LIB_DIR`; walk and control in separate processes; made-up rows, injected `today`).
`deploy_kits\KB_canon_all\BUILD_NORM_v1.md`.

## 2 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/asset_register.py` **`9e94b11c1a55eee6fdb22b9862b6db44`** (S557)
- `/root/assetapp/sorting_desk.py` **`91a04674e27de3fbfc7602403403c821`** (S557)
- `/root/assetapp/clinic_papers.py` **`058c9bcb5a4973f8a15984b645ff57d7`** (S551)
- `/root/assetapp/asset_machine.py` **`66c37197ae7c0d63874e213d52e7b9e5`** (S557)
- `/root/assetapp/scanner_widget.js` **`1143c77b13ae62652d4d961a92b9a9ab`** (S545) — **item 10 only**, inside the
  intake-only branches; the seven surfaces walked.
- Read only: `claude_reread.py` `d9b75e78…`, `claude_reader.py` `3894dc23…`.

## 3 · What to build (items 1–9: owner and manager pages only — **reception's intake, slip and its own menu are NOT changed**; item 10: the scanner's Adjust/Save fix, urgent)

1. **One menu, everywhere the owner or a manager goes** — the scan app's top bar and **the desk's four pages** (which have
   none today) carry the same bar, in this order:
   **Sorting desk (N)** · The month · Bills awaited (N) · Implant ledger · Machines · Renewals · All papers · Vendors ·
   Admin · account · Logout.
   - *Sorting desk (N)* → `/desk`; N = the desk's own waiting count (the same function the desk uses — never a second
     count). Shown to a manager only while `desk.on` is on; otherwise the item is hidden for him.
   - *Bills awaited (N)* → `/desk/awaited`; N = awaiting challans the person may see.
   - *Implant ledger* → `/desk/implants`. *Machines* → `/assets` (the old "Assets"). *All papers* → `/bills` (the old
     "Purchases", retitled *All papers* on its page too).
   - **Out of the menu:** *Drafts* (`/drafts`, the asset-drafts inbox — still reached from the Assets page's existing
     "Scan first (Drafts)" link and from Admin) and *Staff* (`/staff` — reached from Admin). Their pages keep working.
   - One small helper builds the bar for every page (no copy-paste of the list); the desk pages, which render their own
     full-width HTML, call the same helper. It must fit one line at 1366 px; at phone width it wraps.
2. **The home page** (`/scanapp/`) opens, above everything else, with one card: **"N papers waiting — Open the sorting
   desk"** (a big button), and under it one line: *Bills awaited N · Implant ledger · The month*. When N is 0: "No paper
   waiting." The rest of the home page stays as it is.
3. **The desk opens on a given paper:** `/desk?open=<id>` (and `?open=B-0125`) loads that paper in the middle and right
   panels, exactly as picking it in the list does (the same permission rules: never pharmacy; Personal only for the
   owner; an unknown or refused id → the desk opens normally with one grey line "That paper can't be opened here").
4. **Every paper row leads to the desk.** On *All papers* (`/bills`, every filter), the papers list (`/papers`), Bills
   awaited, the implant ledger, the month page and the machine pages' *its paper* links: a **non-pharmacy** paper's link
   goes to `/desk?open=<id>`; a **pharmacy** paper's link keeps the old bill page (the desk never shows pharmacy).
   The papers list's separate "Open it" link goes the same way.
5. **The old bill page `/bills/<id>`** (kept — the manual path, and every pharmacy paper):
   - shows **the scan inline at the top** (`<iframe>` of `/bills/<id>/file`, full width, about 70% of the window's height;
     a plain "Open the file" link stays under it);
   - for a non-pharmacy paper, a button **"Open on the sorting desk"** → `/desk?open=<id>`;
   - the status badge tells the truth: *draft* → "Waiting", *captured* → "Filed", *approved* → "Accepted",
     *rejected* → "Set aside" (today any non-draft reads "approved").
6. **One meaning of "waiting" for the owner.** On *All papers*, the header's "12 pending" link and the **draft** filter
   are relabelled: the header shows **"N waiting on the desk →"** (the desk's count, linking to `/desk`); the status
   filters read *Not accepted yet (draft) · Filed (captured) · Accepted (approved) · Set aside (rejected)*.
7. **One route each:** the menu and every in-app link point to `/desk/month` and `/desk/awaited`; links to the old
   `/papers/month`, `/papers/challans` and `/purchases` are removed from menus, toolbars and the home page (the item links
   on a bill page that go to `/purchases?item=…` go to the month page's item instead, if it has one; otherwise they stay).
   **The old pages stay reachable by their address** with their "Replaced by…" banners (the manual path). *All papers*'s
   toolbar carries **one** link to The month.
8. **"← BACK"** on *All papers* and the owner/manager pages goes to the scan app's home (`/scanapp/`), not the portal.
   Reception's intake keeps its own back.
9. **Small things from the last live read (fold in):** the Assets page's Zone filter lists "Unassigned" twice → once;
   machine pages, Renewals and All papers show dates as **dd-mm-yyyy** (the same helper the desk uses), storage unchanged;
   a machine whose cover lives only in its old record (`contract_type` set, no cover rows) reads in the cover line
   **"Covered (old record): <contract_type> — <provider>"** instead of "No cover"; Renewals' *Kind* column shows the
   reminder's own label kind (Warranty / AMC / Licence / Insurance / Other) instead of "Warranty" for every row
   (read how it is decided; fix it in one place); the service form's fixed sentence "Preventive maintenance is covered
   under the AMC — no charge." shows **only** when the machine has a live AMC/CMC cover.

10. **URGENT — one paper, two stamps (the owner, 13:40 IST: reception's Alisha adjusted a Variety Stationers challan and got
    a new stamp beside the old one, two scans on the screen).** Cause, read in `/root/assetapp/scanner_widget.js`
    (`1143c77b`): while a page's **Adjust** stage is open, the green **Save** (`#camsave`, and `#savebtn`) stays live.
    Tapping Save before *"Theek hai"* runs `doSave()`'s `inlineStamp` branch (≈ line 999): it queues the **un-adjusted**
    page (stamp 1), empties `pages`, `clearSrc()` sets `adjustIdx = -1` — **but leaves the Adjust stage on screen** with
    its "✔ Theek hai — page 1" label. Her next tap on that button runs `addPage()` → `adjustIdx < 0` →
    `addCaptured(warp())`, a **new** page from the stage's canvas; the next Save queues it — **stamp 2, the same paper**.
    (Yesterday's B-0159 / B-0160 fit the same path.) **The fix, inside the intake-only branches** (`cvScanOn` /
    `inlineStamp`, which only the scan app's intake sets):
    - **Save while a page is being adjusted applies the adjustment first** (`adjustDone()`), then saves once — one tap,
      no question (staff flows are friction-free);
    - `doSave()`'s `inlineStamp` branch always **closes the stage** (`resetShot()`-equivalent: hide `#stage`, reset
      `#addpage`'s label, `adjustIdx = -1`, `adjustImg = null`) after queueing;
    - `addPage()` / `addWhole()` do nothing while the stage is a stale Adjust stage with no page under it (never a page
      from a leftover canvas);
    - a second guard in `enqueue()`: the same page data queued twice within 10 seconds is queued once.
    **The widget is SHARED BY SEVEN SURFACES** (two scan-app, five finance-app): every change sits inside `cvScanOn` /
    `inlineStamp` code that only the scan app's intake sets; **walk the finance app's five surfaces unchanged** (load the
    widget with each surface's own config, as S545's walk did — read `deploy_kits\S545_*` for how) and say so in the
    report. FROM pin `/root/assetapp/scanner_widget.js` **`1143c77b13ae62652d4d961a92b9a9ab`**. Also list in the report —
    read only, from the box — today's Variety Stationers papers scanned at reception (stamp, time, pages, lane, status),
    so the owner can set aside the extra one on the desk; **never change them**.

## 4 · Never
Everything in S551 v4 §5, S555 §3, S557 §4, and: change reception's intake, slip or reception's menu; delete a page, a
route or a row (the old pages stay reachable); change the portal's tile (the parent's file — the report carries one line
FOR THE PARENT: rename the tile *"Asset Register — Clinic assets & AMC"* to *"Scan app & assets"*); touch `packs.py`,
`scanner_widget.js` outside item 10's intake-only branches, any finance or Sanjeevni file, the DUTY_MAP; write a real row; place; restart; publish; push; print a
person's name, a phone number, a key or a token.

## 5 · Walk, control, installer, rehearsal, kit, report (BUILD_NORM_v1 — S557's shape)
- **Walk** (isolated, made-up rows): the menu on every owner/manager page incl. the four desk pages, in order, with
  correct counts (desk N equal to the desk's own list length; Bills awaited N); *Sorting desk* hidden for a manager while
  `desk.on` is off; *Drafts* and *Staff* absent from the menu and their pages still 200 for the owner; the home card and
  its count; `/desk?open=<id>` for a clinic paper (loaded), a pharmacy paper and a Personal paper for a manager (refused
  with the grey line), `?open=B-xxxx`; every row link on `/bills` (each filter), `/papers`, Bills awaited, the ledger, the
  month page and a machine page → `/desk?open=` for non-pharmacy, old page for pharmacy; the old bill page has the iframe,
  the desk button (not for pharmacy) and the four true badge words (incl. a captured Other-document paper → "Filed"); the
  relabelled header and filters; no link to `/papers/month`, `/papers/challans`, `/purchases` in any menu/toolbar/home;
  those pages still 200 with banners; BACK → `/scanapp/`; reception's intake HTML byte-identical in its words and links;
  the item-9 fixes each; **item 10** — drive the widget headless (as S545's walk does): capture → Adjust → tap Save
  while adjusting → exactly ONE item queued, holding the ADJUSTED page, the stage closed; Adjust → Theek hai → Save →
  one item; Save → tap the old stage button → nothing added; the same pages queued twice in 10 s → one; the finance
  app's five surfaces load and save exactly as before (byte-identical behaviour outside the intake branches); the S557
  (41), S555 (19) and S551 (87) walks still green on the new files.
- **Control:** red on the live (S557) files, with named checks for items 1–9 red.
- **Installer** `install_s559.sh` (S557's order and safety; no database change — if one is needed, stop and report;
  `/healthz` 200 and `/desk` 302; ALREADY INSTALLED; restore on failure; undo with `\cp -p`, a printf format `'\\cp -p'`).
- **Rehearsal** `rehearse_s559.sh` — the five outcomes on a made-up root.
- **Kit** `deploy_kits\S559_ONE_ROAD\` — the usual files, SUMS, `.gitignore` last-match-wins, the contact-number gate.
- **Server line** (README): `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S559_ONE_ROAD/install_s559.sh`
- **Report** `claude_code_briefs\REPORT_S559.md`: 3–5 plain lines on top — *how the owner now goes from the portal tile to
  sorting a paper, click by click*; then pins, counted edits, the walk/control counts printed into the log, the three
  earlier walks, the rehearsal, gates, the line FOR THE PARENT, the cost. Last line: **nothing installed, nothing
  published.**

**If anything cannot be done as written, stop at that point, write what was done and why, and end.**
