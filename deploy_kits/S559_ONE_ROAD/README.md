# S559_ONE_ROAD — one easy road through the scan app (D646 claim, S315)

**Why.** The owner, 14-Oct-2026 13:13–13:17 IST: *"the flow is very confusing … do all what is required for a proper easy flow
so that all that is built is useful."* And at 13:40 IST: reception adjusted a Variety Stationers challan and got a second stamp
beside the first.

**What it does (owner and manager pages only — reception's intake, slip and menu are not changed).**
1. **One menu bar** on every owner / manager page and on the desk's four pages (and the one-line page a manager sees while the
   desk is off): *Sorting desk (N) · The month · Bills awaited (N) · Implant ledger · Machines · Renewals · All papers ·
   Vendors · Admin · account · Logout.* One helper builds it (`_s559_bar`). N = `len(sorting_desk.waiting(...))`, the very
   function the desk lists with; Bills awaited N = `len(awaiting_challans(...))` for that person. *Sorting desk* shows to a
   manager only while `desk.on` is on. *Drafts* and *Staff* are out of the menu (Assets and Admin reach them; Admin gains a
   Staff card). The title links home. One line at 1366 px; wraps at a phone's width (browser walk W).
2. **The home page** opens with *"N papers waiting — Open the sorting desk"* and *Bills awaited N · Implant ledger · The month*
   (*"No paper waiting."* at 0). Nothing else on the page moves.
3. **`/desk?open=<id>`** (or `?open=B-0125`) opens that paper on the desk, by the desk's own rule (`_visible`: never pharmacy,
   Personal only for the owner); refused / unknown → the desk opens normally with *"That paper can't be opened here"*.
4. **Every paper row leads to the desk** (All papers every filter, the papers list incl. *Open it*, Bills awaited, the ledger,
   The month, a machine's *its paper* and *From bill*): non-pharmacy → `/desk?open=<id>`; pharmacy → the old bill page. For a
   manager while the desk is off, rows keep the old bill page (the desk would only say it is off), and the papers page's
   *Change / Open it* keeps `/papers/<id>`, his sorting page (S559_FIX1 B1; walk L8).
5. **The old bill page** shows the scan inline (an iframe, 70% of the window, *Open the file* under it), *Open on the sorting
   desk* (not for pharmacy), and the true badge: *Waiting · Filed · Accepted · Set aside*.
6. **All papers** (the old *Purchases*): *"N waiting on the desk →"* (the desk's N) and the filters *Not accepted yet (draft) ·
   Filed (captured) · Accepted (approved) · Set aside (rejected)*.
7. **One route each:** menus, toolbars and the home page link `/desk/month` and `/desk/awaited`; All papers' toolbar has one
   link to The month. `/papers/month`, `/papers/challans`, `/purchases` stay reachable by address with their banners. The bill
   page's item links to `/purchases?item=…` stay (The month has no per-item place to go to).
8. **BACK** on All papers → the scan app's home (`/scanapp/`).
9. **Small things:** Zone *Unassigned* once (it filters every Unassigned zone); dd-mm-yyyy on the machine page, Renewals and All
   papers (the desk's `_dmy`; storage unchanged); *"Covered (old record): <type> — <provider>"* when the cover lives only in the
   old record; Renewals' new *Kind* column (one helper, `_s559_kind`); the PM sentence only under a live AMC / CMC.
10. **The scanner (`scanner_widget.js`), intake-only branches:** Save while a page is being adjusted applies the adjustment
    first and saves once; the inlineStamp Save always closes the stage; on the intake (smart outline + auto page) a leftover
    stage never makes a page; the same pages queued twice within 10 s are queued once. S559_FIX1: a late-loading Adjust image
    never reopens the stage after Save (a generation counter, C1); deleting an earlier page while a later one is adjusted
    keeps the adjustment on that page, and Save never puts one page in twice (C2). The finance app's five surfaces and the
    asset page set neither branch — proven byte-identical in load and save (browser walk S).

**Files.**

| File | FROM → TO | edits |
|---|---|---|
| `/root/assetapp/asset_register.py` | `9e94b11c` → `20ef7bc6` | 34 counted (+ the helpers block `s559_ar_block.txt`) |
| `/root/assetapp/sorting_desk.py` | `91a04674` → `a59fa38d` | 11 counted |
| `/root/assetapp/clinic_papers.py` | `058c9bcb` → `80e3cd8d` | 7 counted |
| `/root/assetapp/asset_machine.py` | `66c37197` → `0caec41e` | 4 counted |
| `/root/assetapp/scanner_widget.js` | `1143c77b` → `1128ac97` | 9 counted |

- **Read only, pinned:** `claude_reader.py` `3894dc23`, `claude_reread.py` `d9b75e78`.
- **No database change.** A safety backup `assets.db.bak_S559_<time>` is still taken (backup API). Only `assetapp` restarts.
- **Not touched:** reception's intake / slip / menu (walk K1: byte for byte, but the widget's own `?v=` file-time stamp),
  `packs.py`, the finance and Sanjeevni side, the portal's tile, the DUTY_MAP.

**Install (server), after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S559_ONE_ROAD/install_s559.sh
```

`DRY=1` before `bash` stops after the walks. The installer needs the S557, S555 and S551 kits beside it (their walks are the
regression). It ends with `/healthz` 200, `/desk` 302 and the served widget carrying `S559.1`; any red after placing restores.

**Undo (server):**

```
\cp -p /root/assetapp/asset_machine.py.bak_S559_66c37197 /root/assetapp/asset_machine.py && \cp -p /root/assetapp/sorting_desk.py.bak_S559_91a04674 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/clinic_papers.py.bak_S559_058c9bcb /root/assetapp/clinic_papers.py && \cp -p /root/assetapp/scanner_widget.js.bak_S559_1143c77b /root/assetapp/scanner_widget.js && \cp -p /root/assetapp/asset_register.py.bak_S559_9e94b11c /root/assetapp/asset_register.py && systemctl restart assetapp
```

**Proof (14-Oct-2026, FIX1 round, on the box in /tmp only, and in headless Chrome on the PC).**
- `walk_s559.py`: **43 checks, all green** on the built files (made-up rows, made-up logins, made-up today 15-Jun-2031).
- The control on the live (S557) files: **36 RED, every named check** (W2, M1–M6, H1–H2, O1–O4, L1–L6, L8, B1–B3, F1–F2, N1,
  N3, K2, Z1, D1, C1, R1, P1, J1, J2, J3). On the first S559 build's `clinic_papers.py` and widget: L8, J1, J3 red.
- Regression on the new files: S557 41/41, S555 19/19, S551 87/87. S557's unchanged-pages baseline is taken from the S559 build
  without `asset_machine.py`; S551's walk runs from a `/tmp` copy with three counted lines (`s551_lines_s559.py`: its S555 date
  line; H2's row link now `/desk?open=`; H3's second "Consumption" link now absent). The frozen kits are not edited.
- `walk/` (browser, `walk_results.txt`): **20 of 20** — V (the widget compiles in V8: node --check's equivalent, no node here);
  item 10's four scenes with the live widget as the control (it shows the reported fault: un-adjusted page queued, stage left
  open, the next tap a second paper); FIX1's scenes E (C1) and F (C2), each red on the first S559 build (`--prev`); the seven
  surfaces; the bar's fit.
- `rehearse_s559.sh`: **five outcomes** — green · ALREADY INSTALLED · forced red restored · `/desk` 404 restored · `/desk` 200
  restored.
