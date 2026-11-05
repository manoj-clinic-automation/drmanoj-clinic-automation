# S708_TRACK_REDESIGN — S387 (Sanjeevni), 05-Nov-2026 · D830

**The owner (05-Nov 09:41 IST, D830):** the tracking page *"collapsible sections with clear headers, PC and mobile, far less scrolling; the
incomplete flows finished; for a bill scanned twice a way to pick the good scan; after the blurry / cut scans are deleted by their buttons,
the good ones stay visible"*. On the mock (artifact HvynwvX7xuPZCSsJBauBg6, 17:50 IST): *"looks ok, can be refined, add scroll up button,
collapsed default, expand all, collapse all button at top, scans that open shd be big enough for proper viewing in pc screen — build
accordingly; also need reception flow for their work generated frm this page"*.

| file | from | to | what |
|---|---|---|---|
| `/root/finance/porders_s454.py` | 5de2a4b8 | TO_PINS | `/s454/track` and `/s454/rescan` call the new module (`?old=1`, or a failure of the new page, = the S619 / S618 pages as now); S628's dealer door made callable (`_s708_put_dealer`, the same code); the seven S708 doors; reception's home row counts the papers too |
| `/root/finance/order_track.py` | 9010a012 | TO_PINS | `Ctx`: a scan picked as the copy (`s708_scan_pick`) is never usable and heads to the kept one; a family's clearer scan is never a picked copy; `usable(ignore_bad)`; `same_paper(asked_too)` — a pair one of whose scans was sent back stays a pair |
| `/root/finance/order_track_page.py` | — | TO_PINS | NEW: the two pages and the doors' logic; three tables of people's entries, made on first use |

**What changed for whom.** The owner and Shavez: every section folded on opening (remembered per tab), Expand all / Collapse all, the four
counts tappable, *To do now* with one line per kind of work, ▲ Top; *Not arrived* with Call and Goods arrived on each card (3 shown, the
rest behind *Show the other N*); *Came short* with what did not come; one **Scan problems** section — one bill scanned twice (both
pictures, *This one is right* on each, Undo; a rescan request on the copy is withdrawn), rescans (picture, why, with reception since when,
reception's "paper not found"), bills never scanned (arrived, in Marg or a day old, no scan: *Ask reception to scan it*), saved under the
wrong dealer (Change dealer when the paper is read; else the dealers of that week's orders to pick from). Every scan opens **on the same
page**: a side panel of ~62 % of a PC screen (the PDF itself, Zoom), full screen on a phone (its picture, *Open the full scan*); *Check all
scans one by one* steps through all of them with Next / Previous and each card's buttons. *Complete* now holds only orders that are really
complete (scanned, no other dealer's paper). Reception (*Phir se scan karo*): each card says what to find, the old scan, how to scan it,
who asked; *Scan karo*; *Kaagaz nahi mila* → shown on the owner's and Shavez's page; *Mil gaya*.

**Why the good scan disappeared (found by the walk):** a scan with an open rescan ask is "bad" to `Ctx.usable`, so the moment one copy of a
paper was sent back the pair was no longer a pair, and nothing showed the good copy. `same_paper(asked_too=True)` keeps such a pair on the
page until the good one is picked.

**One fact, one place:** every list is the existing reader's (`order_track.light_all / full_all / wrong_dealer / paper_dealer / same_paper`,
`porders_s454.rescan_list`); the new module draws them. People's entries: `s708_scan_pick` (undo = `undone_at`), `s708_paper_ask`
(withdraw = `withdrawn_at`; open only while the order still has no scan — worked out on every read), `s708_lost` (cleared = `cleared_at`).
Nothing is deleted. A read writes nothing. **Nothing is tied by itself (R2):** reception scans the paper and taps *Scan ho gaya*; the owner
or Shavez then sees the dealer's untied scans made since the ask and taps *This is its bill* (the server's own candidate list;
`order_sheet._tie`, how `paper_ask`), or *Send to reception again*. The ask closes when its order has a tied scan, by whatever door.

**Seen, not touched:** `claude_code_briefs/DUTY_MAP.json` `reception.rescan.due_sql` counts `scan_rescan_ask` only — reception's row now also
counts the paper asks (with the parent: a `due_sql` change re-runs the parent's REWRITE fit, F-1024). The S618 list (`?old=1`) raises
`KeyError: by_owner` when the scan app's database is unreachable (the new list does not).

**Cold review R1 (SAFE, seven should-fix — all built):** a "could not find" count stuck after the paper was scanned (only open work counts);
paper asks never closing and costing every home read (open = not withdrawn and the order untied; the home row is one COUNT; `tie_papers`
ties the paper reception scans to its order on the reads that already run the S454 tie, and on reception's list); Undo only in the tap's
reply (a 7-day *Clear scan picked* group with Undo — the good scan stays visible); two opposite picks at once (one open pick per scan);
the staff page's size not gated (the live read's Shavez figure is a gate; *Complete* shows the newest 60); a phone sees a PDF's picture only
(a filled *Open the full scan* button on phones; the live server serves the PDFs inline, no frame block); English refusals on staff screens
(one bilingual table). Minors built: *Kaagaz nahi mila* only for reception's logins; a non-object body refused; a picked copy off the
wrong-dealer list; duplicate paper asks refused.

**Cold review R2 (NOT SAFE — one blocker, built):** R1's automatic tie of "the dealer's next scan after the ask" took scans the S454 tie
holds back on purpose (an unsettled reading, an unread paper without reception's *Haan*, a rescan of another bill, a new delivery's bill)
and, the tie being unique, the true order could never get them. Removed: reception's *Scan ho gaya* + a person's *This is its bill*.
Also: reception's row and list are one set by one rule (`RECEPTION_PAPER`); a bill scanned three times can be resolved (a pick refused only
when the new keep is already a copy or the new copy already kept); phones make no PDF frame (the picture + *Open the full scan*);
`_s618_open_count`'s docstring says what it now counts. Seen, not touched: the cron's S454 tie can still give reception's old paper to a
newer waiting order of the same dealer (its own oldest-waiting rule) — the card then offers no candidate and *Send to reception again*.

**Cold review R3 (SAFE; should-fix built):** a scan-app copy of a picked copy heads to the kept scan (never usable); an ask on a
cancelled order is nobody's work; an ask whose order got its scan another way (Marg's link) is shown with Withdraw; the "which scan is
its bill?" card names the order's medicines and has its *To do now* line, plus Withdraw; the dealer door's reply names the order's date.
**Seen, not touched (to the fault register):** S628's dealer core moves a tie to the dealer's newest untied order of 7 days — S708's
dealer pick reaches it for unread papers (the reply now names the order); `order_sheet.tie_pass` does not read `s708_scan_pick`, so a
picked copy that is untied can still be tied to that dealer's next waiting order (as any untied duplicate can today); a person's tie has
no Undo (as S628's).
**Cold review R4 (SAFE):** the R3 fixes fuzzed 3000 runs against the live `Ctx` — with no pick, `head()` / `usable()` identical. Seen: an ask
whose order got its scan by Marg's link stays on reception's list until the owner or Shavez taps Withdraw on its card (the card says so).

**Proofs:** walk 70 ok on the rebuilt files; control 11 ok, 59 red on the live files (the 11 are the old pages, the refusal of Darpan, the
fallback, markup in a dealer name shown as text, nothing tied by itself, and S628's Change dealer unchanged); the page's script in Chromium at 1280 px and 390 px: 31 ok (`js_s708.py`, working papers);
the live read on a copy of the 05-Nov nightly database: the counts of the old and new pages agree (14 / 13 / 1), 63 KB against 178 KB (Shavez 62 KB).
Installer rehearsed on a made-up server tree: DRY, a forced red at [7/7] (everything put back), the install, ALREADY INSTALLED.

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s708kit && cp -rp /root/deploy/repo/deploy_kits/S708_TRACK_REDESIGN /tmp/s708kit && bash /tmp/s708kit/install_S708_TRACK_REDESIGN.sh

Gates before placing: SUMS, KIT_ID, the window, the live pins, the rebuild from live bytes to the TO pins, the walk (70 ok) on the rebuilt
files, the control (11 ok, 59 red) on the live files, the new pages drawn READ-ONLY on a copy of the live data with the live scans (owner,
Shavez, reception; no failure; the counts of the old and new order list agree; Shavez's page under 100 KB). Restarts clinic-finance. Undo is printed. The old pages:
`?old=1`.
