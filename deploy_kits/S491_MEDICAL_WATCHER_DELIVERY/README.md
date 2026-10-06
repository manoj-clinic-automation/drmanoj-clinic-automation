# S491_MEDICAL_WATCHER_DELIVERY — S488's watcher, delivered on today's pins

**Project:** Sanjeevni. **Made by:** the Sanjeevni chat (session 296, 06-Oct-2026). **Touches:** Drive `ToMedical\_kit\marg_watch.py` and `KIT_MANIFEST.txt` — and through them the medical PC's `D:\SendToClinic\marg_watch.py`. Nothing on the server, nothing on manojz.

## Why a kit of its own

`S488_DATES_AND_WAITS` packed `marg_watch.py` S488 (part E: a refused text with a person's detail stays off Drive) with `deliver_S488.ps1`, pinned to Drive as S480 left it (`marg_txt.py` 14b75012, manifest ea2b437a). The same afternoon `S490_ORDER_SHEET_PACKING` moved both (7fa5136d, 95a1dc5f). `deliver_S488.ps1` would refuse, by design, and **must never be run** — its manifest would also put the reader's md5 line back to S480's. A published kit folder is frozen, so the delivery is made again here.

## What is in it

| file | |
|---|---|
| `marg_watch.py` | `0a78ae15be60d8a0293b96ecfa38f35b` — byte-identical to `deploy_kits\S488_DATES_AND_WAITS\marg_watch.py` |
| `KIT_MANIFEST.txt` | S490's manifest plus S488's comment block, nothing else: LF `e06e9a3e290e956e65540a0032b80a03`, on Drive (CRLF) `d557f9346b089e039f2a48b781bd6933` |
| `deliver_S491.ps1` | the same delivery as a script; today it answers ALREADY DELIVERED |

## The chat's read of the watcher before it went (the brief's condition)

- Function-level compare of 58b54f37 against 0a78ae15: **changed** `share_refused`, `selftest`; **added** `_may_leave`, `_read_or_none`, `_share_put`, `_safe_why`, `_withhold`, `_share_sweep`, `_s488_share_cases`; **removed** none. Capture, the notes, the retry and `main` are untouched.
- `_may_leave` fails closed (any exception, an unknown kind, a binary or oversized text → the body stays on the PC); the three patterns are the server's `phi_scan.py`'s; the admitted kinds are PURCHASE, SALT, CATEGORY, ITEMS, VALUATION, EXPIRY, STOCK.
- `share_refused` is called only inside `publish_diagnostics`' own try / except — a fault there cannot stop capture.
- The file's `--selftest`: SELFTEST OK, 61 checks, beside the reader S480 **and** beside the reader S490 (run by the chat; Claude Code ran it on manojz).
- manojz runs no copy of this watcher against Drive (`MargPull\marg_watch.py` is the 13 KB file of 25-Aug, without `share_refused`), so the sweep has no second writer to argue with.

## How it was delivered — 06-Oct-2026, 15:39:22 IST

By the chat, through the file tools, after the owner approved the Drive folder (his PowerShell had answered *"the -File parameter does not exist"* for `deliver_S490.ps1`, though the file stood at that path; the cause was not found). The steps were the script's: every FROM pin read first (`marg_watch.py` 58b54f37, manifest 95a1dc5f, `marg_txt.py` 7fa5136d, `marg_push.py` 566e189e) → backups `marg_watch_S480.py.superseded` and `KIT_MANIFEST_S490.txt.superseded` written and read back → the manifest, then the watcher, each guarded by the file's last-seen time → both read back at their TO values.

S490 was delivered the same way at 15:37 IST (`marg_txt_S480.py.superseded`, `KIT_MANIFEST_S480.txt.superseded`).

## What to expect on the medical PC

The agent installs the reader and the watcher at its next kit check and restarts the watcher. At its start the watcher offers the reader every text refused in the last three days (S397) — so the order sheet refused at 13:48 on 06-Oct is read by reader S490 and sent. On its first diagnostics pass the new watcher sweeps Drive's `FromMedical\refused_text`: bodies that may not leave are removed (Drive's bin keeps them 30 days) and every `.why.txt` becomes the safe two lines.
