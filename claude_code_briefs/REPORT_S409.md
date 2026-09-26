# REPORT_S409 — S409_SCAN_LANES (whoever holds the paper scans it: five lanes, a duplicate guard, late bills, pharmacy scans from 01-Sep)

**Owner of this kit: PARENT (the asset app).** Two Sanjeevni edits declared (the scan-from date in `purchase_app.py` / `porders.py`).
Installed on srv1746119 on **26-Sep-2026**, installer stamp 09:39:18 IST, done 09:44:22 IST, verified 09:45:03 IST (times read from
the log and the probe). Every pin re-read live first (09:08 IST, after S407). Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **The five choices on the scan screen, as the staff see them:** *Clinic bill — asset or consumable* · *Pharmacy purchase — Sanjeevni* ·
  *Lab purchase — NK Pathology* · *Dr MK expense* · *Other document — not a bill*. Only a clinic bill goes to the approval list; the other
  four are filed as a scan and a stamp (the pharmacy one still matches Marg as before). The same address: https://followup.dr-manoj.in/scanapp/intake
- **Who opens on which head:** Sukhveer on *Lab purchase*, Awdhesh on *Clinic bill*, Darpan on *Pharmacy purchase*, you on *Dr MK expense*,
  everyone else on *Clinic bill*. You change any of these with one tap on a small card, **/scanapp/lanes** (linked from the Purchases list).
- **What happens on a double scan:** if the same capture is sent again (a double tap, the same file), the server rejects it at once and the
  slip says in Hindi, large: *"Yeh bill pehle B-0123 par scan ho chuka hai — wahi number likho"* — the first number. A straight re-scan of
  the same paper (a PDF of it, a second flatten) is caught the same way but goes **amber** for the checker with two taps, *Duplicate* /
  *Not duplicate*, because a different bill printed on the same form can look the same to a camera. When the OCR then reads the same
  vendor, bill number and amount as an earlier scan, the bill is rejected as a duplicate on its own; a same-form bill with a different
  number clears itself. Approving a bill whose vendor, number and amount are already approved is refused, naming the stamp.
  **One honest limit, measured on the box:** a re-shot with a visible tilt is not seen by the picture check; the OCR check is what catches it.
- **Other things now on:** a bill can be moved between lanes with one tap (an approved bill never leaves the clinic lane); a bill scanned
  in a later month than its own date carries *late — belongs to <month>* (S408 files it there); the Purchases page shows this month's
  scans per lane; and **pharmacy bill scanning now counts from 1st September** — the *Bill scan karo* list and the red list no longer show
  August. The unscanned list drops from 108 to what is due from September.
- Proved on copies of both databases with crafted papers and crafted logins; the live scans were not touched.

## For the chat
### Live files FROM → TO (md5 read back after placing; re-read 09:45 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/assetapp/asset_register.py (PARENT; S403's TO; v1.11.0 → 1.12.0) | 30b26d280c6cdf373774a94aae59f339 | df8c0e198d66b06645a2a389ce5bae1e |
| /root/finance/purchase_app.py (Sanjeevni, declared; S407's TO) | fdec7ec01d2ceb449aaa0a62956a7a0f | cdd4e9c069bc8ab78160349a11a4a4c7 |
| /root/finance/porders.py (Sanjeevni, declared) | 78d1712a69324a06c2894c19158cd834 | d08f59e2fb4e42e173f135f06da28787 |

Built on the box by `make_s409.py` from the live bytes (anchored edits, each exactly once). `scanner_widget.js` untouched; no portal /
grants change (the Scan Purchase tile already reaches everyone it should); `RECEPTION_OK` unchanged.

### What the kit does (decisions for the record)
- `bills.lane` (backfilled: Pharmacy → pharmacy, the 15 existing rows → clinic), kinds Lab / Expense / Document for the three new lanes,
  all `captured`; `/purchases` and every spend query keep `status='approved'` (asserted: a ₹99,999.50 lab row never enters the spend).
- **The fingerprint.** The asset app's python has no Pillow; the flattened first page is rendered small and grey by `pdftoppm` (PDF) or
  ImageMagick (image) and hashed in pure Python: a fine dHash (17×16, 256 bits, `bills.fp`) and a coarse one (9×8, 64 bits, `bills.fpc`).
  **Calibrated on the box** (crafted papers and eleven real uploaded scans): the same file 0/0 bits; a 4 % re-crop coarse 2–3; a PDF
  re-scan coarse 3–5; unrelated papers coarse 9+ (real scans median 32); **a re-shot tilted 0.5–3° lands at coarse 9–13, indistinguishable
  from unrelated papers.** So: fine ≤ 8 → rejected (the same capture); coarse ≤ 6 → amber `maybe` (a straight re-scan, or a different bill
  on the same printed form — never auto-rejected, the brief's "rejected at once" narrowed to what the picture can prove); the tilted
  re-shot is left to the OCR triple. This narrowing is the one departure from the brief's letter and it is deliberate: a genuine second
  bill must never be thrown away on a layout match.
- **The OCR triple** (vendor + bill number + total, case/punctuation-free, last 90 days, the oldest match = the original): exact → rejected
  `dup_of`; same vendor + total with the number unreadable on either side → amber `maybe`; an image amber whose number the OCR reads as
  different clears itself. `bill_approve` refuses a triple already approved and turns the bill amber. `dup_why` says which layer spoke.
- The slip: Hindi line + the first stamp; a clean slip polls `?json=1` for 30 s so a verdict arriving with the OCR replaces it.
- Re-lane `POST /bills/<id>/lane` (owner / manager), audited in the new `bill_audit`; `late_for` at capture, after OCR, on the checker's
  edit; `/lanes` card; the lane line on `/purchases`; `porders.scan_from` = 2026-09-01 read by both Sanjeevni lists; `_scans()` skips
  rejected rows so a pharmacy duplicate never reaches the Marg match.

### Backups · services · health · data
`/root/assetapp/assets.db.bak_S409_20260926_093919` · `/root/finance/finance.db.bak_S409_20260926_093919` · `asset_register.py.bak_S409_30b26d28`
· `purchase_app.py.bak_S409_fdec7ec0` · `porders.py.bak_S409_78d1712a`. Restarted `assetapp` and `clinic-finance` (both active; portal untouched).
healthz 200; the asset login page 200; `/scanapp/intake`, `/scanapp/lanes`, `/finance/porders`, the scan-links page 302 to a plain curl;
journal clean. After the restart the app's own `migrate()` added the eight columns and the two tables; the 15 live bills read lane
`clinic`; the four lane defaults seeded; `porders.scan_from` 2026-09-01; no W409 rows on either live database.

### The walk (walk_s409.py — the real asset app and the real finance app over scratch copies; crafted papers made with ImageMagick)
`WALK_S409 GREEN -- 24/24` (full output in this session's log): the backfill · the five lanes · only clinic in the queue · the spend
negative control · the five default lanes and the owner's card · the fingerprints (same 0; re-crop 3; unrelated 29; tilt 9 coarse / 58
fine) · the same image twice → rejected, the re-crop → amber, the tilted re-shot and a different paper → plain rows · the Hindi slip and
its JSON · a PDF re-scan → amber (42 fine / 3 coarse) · the triple rejects; near-miss amber against the original; a different number and
amount clean · the list's amber row with the two taps; Not duplicate / Duplicate stored and audited · approve refused, naming the stamp ·
re-lane both ways, audited; approved stays; reception 403 · late_for · S403's pre-fill · reception's reach · the lane line · the Sanjeevni
side (25-Aug hidden, 02-Sep shown, on both lists). **Negative controls** (the old files, the same papers): two drafts with two stamps for
the same image, no /lanes, no re-lane route, no Hindi line; the old finance side lists the 25-Aug bill. **Re-runs:** `WALK_S407 27/27` ·
`WALK_S406 27/27` · `WALK_S405 29/29` · `WALK_S404 65/65` · `WALK_S403 52/52` (its "new" asset app is this kit's) · `WALK_S400 63/63` · `WALK_S402 16/16`.
Eight earlier installer runs went red on the walk's own gates and on three real slips caught by them — the scans-page helper inserted
between a route decorator and its function (the route would have pointed at the helper), pdftoppm's output name, and the hash thresholds
(calibrated as above); nothing was placed by those runs.

### Outside the brief, noticed (not changed)
- Of the eleven real uploads sampled for the calibration, twelve pairs are byte-identical scans (the same paper uploaded again during
  testing); from today those would be caught at capture.
- The Sarvam OCR key sits on the `assetapp` unit's `Environment=` line (noted in REPORT_S407).

### Kit
`deploy_kits\S409_SCAN_LANES\` — make_s409.py, seed_s409.py, walk_s409.py, install_S409_SCAN_LANES.sh, README.md (owner = parent; the two
Sanjeevni edits named), KIT_ID.txt, SUMS.md5. Ran from `/tmp/s409kit/S409_SCAN_LANES` (md5sum -c OK; sibling kits linked from the clone);
the repository copy is byte-identical (verified after `git pull`). No `__pycache__`. NO_PHONE_NUMBERS gate: clean. Build lock held from
09:23 IST to the publish, then removed.

### Undo
Put back the three `.bak_S409_<from8>` files, `systemctl restart assetapp clinic-finance`, asset login 200, healthz 200, md5s read back.
The new columns, tables and rows are data and harmless; the two database backups only if the owner asks.
