# S454_BILL_REGISTER · part 4, the medical PC, corrected — P4C_REFUSAL_WATCHER

The brief's section 20 (read on 04-Oct-2026, before any delivery). **P4B's watcher (20ec1602) was never delivered; this one took its place.**
Delivered to Drive `ToMedical\_kit` on 04-Oct-2026 at 13:23:48 IST (the script's own clock line). The report is
`claude_code_briefs/REPORT_S454.md`.

## What and why

`marg_watch.py` S454 P4C is built from P4B's own bytes (20ec1602, in `../P4B_REFUSAL_WATCHER/`) by `make_s454p4c.py`: ten anchored edits, each
anchor exactly once.

**20.1 — a note that could not be sent is tried again (in P4B it was lost).**

- A refused text is *noted* only when the server has answered for it. That fact is a marker beside the kept text, `<stem>.note` (the stem its
  `.txt` and `.why.txt` share): one line, when and what. It is not a `.txt`, so the start's retry never offers it to the reader.
- What writes a marker: the server answered 2xx with its own JSON (*sent*); the server answered 400 or 413 (*refused by the server*, with the
  status); the reader took the text at a start's retry (*taken later*, no note); a text of the same kind was taken after it was kept
  (*overtaken*, no note); it is older than `CENSUS_DAYS` and still unsent (*expired*, logged).
- Nothing else ends a note. A dead line, 401, 403, 404, the off switch, a missing key, an answer that is not the server's own JSON: the note
  waits, with no marker.
- A waiting note is tried at every start (after the retry of the refused texts) and at every census, and at the moment its text is kept. It is
  built again through `note_of` from the kept text and its `.why.txt`. The three tries a minute apart stay inside one attempt. One attempt at a
  time for a text. When the line, the switch or the key says "not now", the rest of that pass is not sent either (it would meet the same answer).
- The first start on a PC: before the first sweep, every text already in `refused` gets the marker "kept before S454 -- no note sent", and the
  sentinel `_captured_txt\S454_NOTES_STARTED.flag` is written (also when `refused` is empty). With the sentinel there, a later start never does
  this again. Until the sentinel exists, no waiting note is sent (only the note of a text kept at that moment).
- Capture never waits on a note and never fails for one (its own daemon thread; every fault inside is swallowed and logged).
- **The marker is copied to Drive.** `share_refused` copies it beside the text and its reason, so the list in `FromMedical\refused_text` still
  agrees with `refused` and shows which notes are done. It takes 18 files now (the same six texts: text, reason, marker).
- The log says that notes are waiting, and why, once — not at every census (the log's tail is read on Drive).
- **The heartbeat is not changed.** Its writer is `medical_agent.py`, a file this brief may not touch. How many notes wait is read from the
  log's tail and from the markers on Drive.

**20.2 — the note never carries a line of the file.**

- "not a bill-wise sales statement (it begins: …)" leaves as "not a bill-wise sales statement".
- A reader's refusal leaves as "the reader refused it (line N)", or "the reader refused it" when it names no line.
- The `.why.txt` and the PC's log keep every reason whole. A run of six or more digits is still masked.
- Read for this: `_why_not` has eight other answers and none quotes the file. `marg_txt.py` (ed17bb76, not changed) raises `Refused` in 38
  places, many with a piece of a line, a supplier's name or a bill number; every one reaches the note through "the reader refused it: …", so
  none of it leaves.

`KIT_MANIFEST.txt` is P4B's, byte for byte (LF b8ff9568; Drive keeps it with CRLF, 9e754e5c): no word of its S454 comment had to change.
`marg_push.py` (566e189e) and `marg_txt.py` (ed17bb76) are not changed. No server file is changed: P4A's door takes the same note.

## The walk — `walk_s454p4c.py`

It loads a watcher in a scratch folder with a made-up `marg_push.py` and a made-up sender (urllib's `urlopen` replaced in the process), Drive's
folder stubbed. Nothing leaves the PC. Every check runs through `watch()`'s own start and census; a restart is a new process on the same folder.

```
python -B walk_s454p4c.py --p4c <P4C marg_watch.py> --p4b <P4B marg_watch.py> --reader <marg_txt.py> --work <a scratch folder>
```

**WALK_S454P4C GREEN — 36 of 36**, on manojz (Python 3.14.5) and on the server's Python 3.9.25 (the medical PC runs 3.11.9). Copy the files out of
`deploy_kits\` first and run with `-B`.

Negative controls, on what the code does:

- **P4B** goes red on check 1 (the note is lost), check 4 (the note waiting across a restart is never sent) and check 7 (the first line of the
  file, and the refused line of a sale statement, are in the reason).
- **The brief expected P4B to send a note for an old text (4) and for a taken text (5). It does neither:** it has no retry of notes at all. The
  walk prints that as it is. So that checks 4, 5 and 6 can be seen to fail, the walk builds **MUT** — P4C with section 20's three guards taken
  out by anchored edits (the first-start marking, "taken later", "overtaken"). MUT sends a note for each old text, for the taken text, and for
  the overtaken refusal.

## Delivery — `deliver_S454_P4C.ps1` (made from P4B's script)

The clock gate (IST, not before 04-Oct-2026 13:00), this folder's two pins, Drive's two pins, a stop if Drive holds P4B's 20ec1602, a
`.superseded` copy of each, place, md5 read-back, both put back on red.

Drive `ToMedical\_kit\marg_watch.py` 81145aa7 → **297cc3d9ff5edddc894390426bdc463a** · `KIT_MANIFEST.txt` 05fb3485 → **9e754e5c** (CRLF).
Backups on Drive: `marg_watch_S397.py.superseded`, `KIT_MANIFEST_S454P1.txt.superseded`.

**To undo:** copy `marg_watch_S397.py.superseded` over `marg_watch.py` and `KIT_MANIFEST_S454P1.txt.superseded` over `KIT_MANIFEST.txt` in
`ToMedical\_kit`; the agent installs them and restarts the watcher. The markers and the sentinel on the medical PC are plain files the S397
watcher never reads.

## Every part of kit S454_BILL_REGISTER, as installed

The kit's top `README.md` is frozen (its table stops at part 1B). This is the whole list. Times are IST, from each part's install log.

| part | folder | brief | installed |
|---|---|---|---|
| 1 | `P1_ORDER_SHEET_RECEPTION/` | §3 the order sheet (reader, road, loader) · §4 reception's screen · the settings · §7.5 cards | 03-Oct 12:24 (the reader to Drive 12:29) |
| 1B | `P1B_COMPARE_FIRST/` | part 1's comparison taken before its own paper orders (5 of 21) | 03-Oct 12:28 |
| 1C | `P1C_SHEET_PAGE_AND_PHONE/` | §17 the printed sheet carries the whole open order · the Reception phone card and test message | 03-Oct 15:36 |
| 1D | `P1D_TICK_GUARD/` | part 1's block below `order_rules.py`'s `__main__` guard: the cron's tick mended | 03-Oct 16:35 |
| 2 | `P2_PAIRING_REGISTER/` | §5 pairing · §6 Amir · §7 the owner's register · §8 Vendor payments · §12 the duty | 03-Oct 17:26 |
| 3 | `P3_SHELF_FIGURE/` | §9 the shelf figure, and why the system's list differs | 03-Oct 18:17 |
| 3B | `P3B_FIRST_DAY/` | §18 what the first afternoon showed | 03-Oct 19:39 |
| 5 | `P5_ITEMS/` | §11 the items check, and learning the suppliers' item names | 03-Oct 20:03 |
| 4A | `P4A_REFUSAL_DOOR/` | §10.2 the server takes the medical PC's note | 03-Oct 20:28 |
| 4B | `P4B_REFUSAL_WATCHER/` | §10.1 the watcher's note, first build | **never delivered** (§20) |
| 4C | `P4C_REFUSAL_WATCHER/` | §20 the corrected watcher | 04-Oct 13:23 to Drive `ToMedical\_kit` |

## Files

- `make_s454p4c.py` — the anchored patcher (P4B's file → P4C's).
- `marg_watch.py` — the built file, 297cc3d9.
- `KIT_MANIFEST.txt` — P4B's bytes.
- `walk_s454p4c.py` — the walk.
- `deliver_S454_P4C.ps1` — the delivery.
- `KIT_ID.txt`, `SUMS.md5`.
