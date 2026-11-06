# S711_TRACK_FIXES — S388 (Sanjeevni), 06-Nov-2026

**Why.** (1) S710's live read (06-Nov 07:5x): on a PC the scan viewer showed the bill full width, but the card's own buttons (*This one is right*,
the dealer, the rescan chips) sat below the frame, behind the Previous / Next bar. (2) The owner, 07:59: *"one bill where you have asked to change
dealer … scanned obliquely … AA distributors was read as AA1 or I … it is not listing AA distributors in that option … only limited options …
a rescan is also not available."* The live read: B-0239, saved as A.A. PHARMACEUTICALS, read as A.A.I.PHARMACEUTICALS (a reading that names no
known dealer); the pick list was the 7 days' order dealers plus the saved dealer LAST, cut at 6 — six dealers that week cut it off; the card had no
rescan chips. (3) F-1121, F-1120, F-1123 (S387's reviews).

| file | from | to | what |
|---|---|---|---|
| `/root/finance/order_track_page.py` | b6181b62 | TO_PINS | the PC viewer two columns (bill left, words and buttons right, always in view; phones unchanged); the wrong-dealer card: "could not be read clearly (read as …)" when the reading names no known dealer, **"<saved> is right (as saved)"** first, the week's dealers (8), **Other dealer** = every dealer of a Marg bill or an order with a search box, **Send back for rescan**; a scan already with reception is not asked twice; every pick through the one door, the reply with **Undo**; *Dealer changed (7 days)* with Undo |
| `/root/finance/porders_s454.py` | 1bc312dd | TO_PINS | F-1121: the dealer core makes no tie of its own — it removes the wrong dealer's tie (and the arrival only that tie made) and runs the S454 tie (`order_sheet.tie_pass`, its own rules); each change kept in `s711_dealer_change` (made on first use) with what it replaced; `_s711_dealer_undo` + `/api/s454/s711/dealer/undo`; F-1123: `rescan_list` gives the asks their whole shape when assets.db cannot be opened |
| `/root/finance/order_sheet.py` | 1bba95ab | TO_PINS | F-1120: `tie_pass` never ties a scan picked as the copy (`s708_scan_pick`) |

Unchanged: `order_track.py` (S628's readers), the old pages (`?old=1`), `/api/s454/dealer_fix` (the old page's door). A read still writes nothing.
S708's one rule changed on purpose: a paper whose dealer IS read may now be set by the owner / Shavez to another dealer of the lists (walk_s708 4.3).

**Proofs.** walk S711 38 ok (with S708's walk 69 ok, its only red 4.3) on the rebuilt files; control on the live files 6 ok, 32 red. Chromium
(`js_s711.py`, kept in the working papers): 1366×768 and 1920×1080 — the bill left (718 / 1024 px), the buttons right and on screen without scrolling,
*Other dealer* searchable; phone 390 unchanged; on S710's page the PC checks go red. Live-shape read on a copy of the 05-Nov nightly database: every
page 200 for the owner and Shavez, `?old=1` 200 with the scan app unreachable (F-1123's road), 28 dealers in the full list, A.A. PHARMACEUTICALS
resolves to itself, nothing written. Undo never removes a person's tie, never runs over an order the S454 tie made from the bill, claims its row
atomically (a second tap is refused), never overwrites a dealer answered another way since, and says so when the old order has since taken another scan; a failing tie pass is rolled back.
Cold review R1: SAFE TO INSTALL (two Undo edge cases — fixed and tested, 3.7c / 3.7d); R2 on the fixes: SAFE TO INSTALL (its four small points also fixed: a later answer, the viewer copy of the list, a fresh read at the claim, the message). Installer rehearsed on a made-up server tree
(DRY, a forced red at [7/7] puts all three back, the install, ALREADY INSTALLED, a changed live file STOPS, a tampered kit STOPS).

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s711kit && cp -rp /root/deploy/repo/deploy_kits/S711_TRACK_FIXES /tmp/s711kit && bash /tmp/s711kit/install_S711_TRACK_FIXES.sh
