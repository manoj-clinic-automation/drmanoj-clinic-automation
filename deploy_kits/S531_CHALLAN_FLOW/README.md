# S531_CHALLAN_FLOW — a challan kept as "goods received, bill awaited", joined to its bill, then deletable (D689 item 2)

*Scan App project, S306, 11-Oct-2026. The owner's mock-up (artifact WJztiYt5bpWnpxDmpQVfwh, folds 1, 5, 6, 7) as he left
it — his one edit: amber after 15 days. Built by BUILD_NORM_v1 (D704). Installed after S530 (it pins S530's bytes).*

## What the kit does
**At the counter (staff):** one big button under the lane line on the bill intake, **📄 CHALLAN HAI?** — one tap before
Save when the paper is a challan: it turns amber (*✔ CHALLAN — bill baad mein*), the lane line ends *· CHALLAN*, the hint
says a second tap undoes it; after every Save the button goes back to normal by itself, so a forgotten tap can never mark
a run of bills. The stamp slip says *CHALLAN — bill baad mein aayega; kaagaz par yeh number likho; bill aaye to yahi
number batao.* A plain bill: nothing to touch. The basic (no-scanner) upload carries the same field.

**The record:** three additive columns on `bills` (the app's own migration at start): `doc_kind` 'challan',
`challan_state` awaiting / joined / closed / deleted, `challan_of` the bill. A challan never counts as a purchase: it is
out of the papers-to-sort list, the consumables month and the sections. **On the pharmacy lane** a challan is handed
over as `kind='Challan'` (not 'Pharmacy'), status captured, `doc_kind='challan'` — the Sanjeevni side's register and
matcher (`kind='Pharmacy'`) do not take it for a scan to pair; that side reads challans when it chooses to; the scan app
never joins a pharmacy challan (S465's join refuses that lane).

**The owner / Shavez:** `/scanapp/papers/challans` — **Bills awaited**: every awaiting challan with its supplier, date,
age, amount; amber from 15 days (setting `d710.challan_amber_days`); bills of the same supplier scanned since are named;
*Bill nahi aayega — close it* closes one that will never get a bill (kept as a record). When a bill of the same supplier
is scanned (first two words of the name; within 60 days; amount within a tenth when both are read), **its to-sort card
and its own page say "This may be the bill for challan B-…"** with one button: *Yes — join B-… into this bill* — S465's
join, one PDF (bill first, challan after), the challan a page of the bill, state *joined*; undo as before. Then, on the
challan's page, **Delete the challan**: state *deleted*, the reason names the bill, **its own file is MOVED to
`uploads/_deleted_challans/` — never removed** (its picture is inside the bill's PDF when the join merged it), its stamp
number stays reserved. Delete is refused before the join. The owner's fold *Where each paper stands* and the papers
page's head carry *Bills awaited (n)*.

**The widget (shared by seven surfaces):** two edits inside S441's inlineStamp block only — a queued upload snapshots
the upload fields at Save and the send (and every retry) uses the snapshot — so the button's reset after Save, or a
lane/month change, can never alter an upload that retries later. The other six callers never queue (inlineStamp is the
intake's alone): unchanged.

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/assetapp/asset_register.py` | `d3f1b64e` (S523) | `PIN_TO_asset_register.txt` — backup `.bak_S531_d3f1b64e` |
| `/root/assetapp/clinic_papers.py` | `c60e043c` (S530.1) | `PIN_TO_clinic_papers.txt` (S531.1) — backup `.bak_S531_c60e043c` |
| `/root/assetapp/scanner_widget.js` | `cd9c6e60` (S523) | `PIN_TO_scanner_widget.txt` — backup `.bak_S531_cd9c6e60` |
| `/root/assetapp/assets.db` | — | backed up `assets.db.bak_S531_<stamp>`; three columns added at start |

Edits (counted, anchored, by `make_s531.py` on the box): widget W1–W3; app A1–A11 (columns; the field through both
intake doors; the mark; the button, its hint and the lane line; the basic form's field; the reset after Save; the slip;
the scan reply; the badlo link as one word); papers C1–C8 (the block: Bills awaited, close, delete, the join marks, the
cards; challans out of every count; the routes; the version; the fold and the head link).

## Proof
`walk_s531.py --browser` — the app with the three built files on a copy of the real database, through its own doors and
in headless Chromium against a live copy of the app: **39 of 39 green** (the columns; the intake's button, field and
script; a clinic challan and a pharmacy challan land marked, a plain bill untouched; the Sanjeevni-shaped query does not
see the pharmacy challan; the slip; Bills awaited with amber and the hand-over note; the challan out of the to-sort list;
the bill's card and page offer the join; join → joined, undo → awaiting, delete before the join refused, delete after →
deleted with the file moved and the number kept; close; the month page; every old door; the live database untouched;
in the browser: one tap sets the field and the line, a chosen photo becomes a page, Save resets the button at once and
the upload queued before the reset still lands as a challan, the next scan is a plain bill, no page error). On the LIVE
files: 4 red (the control). Three screens read at phone width by an independent agent; its two notes (the orphaned
*badlo*, the hint after the tap) taken in. The installer rehearsed on a made-up root: DONE · ALREADY INSTALLED · drift
refused · red-after-placing restored.

## Install (the owner's one line, after his publish — S530 must be installed first)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S531_CHALLAN_FLOW/install_s531.sh
```
## Undo (one line)
```
cp -p /root/assetapp/asset_register.py.bak_S531_d3f1b64e /root/assetapp/asset_register.py && cp -p /root/assetapp/clinic_papers.py.bak_S531_c60e043c /root/assetapp/clinic_papers.py && cp -p /root/assetapp/scanner_widget.js.bak_S531_cd9c6e60 /root/assetapp/scanner_widget.js && systemctl restart assetapp
```
The three columns stay (additive; nothing in the old files reads them).
