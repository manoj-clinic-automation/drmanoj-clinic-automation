# HANDOFF RUNBOOK — v182 · Session 261 close · 17-Sep-2026 IST

## §0 · WHAT HAPPENED

**One sitting, 06:38 → close. No live code changed on any machine's running path. No VPS pin moved. One
kit, `S281_PAPERS_SORT`, already applied on manojz. One fault, F-506. EOS-light.**

**1 · The S260 publish landed, and the clone proved it.** Commit `af73217` at 06:35 IST; the gate from
inside `KB_canon_all` read 575/575 with v2.84 / v1.97 / v5.100 present. A16b for S260: settled.
`device_bash` mounted all three folders for the first time since 8-Sep — including `F:`.

**2 · The pharmacy PC share was refusing, not the machine.** 146 pulls in a row had failed since
**15-Sep 10:20** after the counter account's Windows password was changed. The stored credential on
manojz no longer matched. The owner refreshed it with one `cmdkey` line (password typed by him, written
nowhere) and the 06:50 pull was clean. In that one pull: the 17-Sep 05:13 stock closing (as on 16-Sep,
438 items) captured, verified, archived and pushed with the computed figure; the 15-Sep and 16-Sep sale
exports accepted by the server; one 16-Sep 23:55 export refused (no signature) and kept in `_REFUSED`.
**The S260 "export reached no store" worry was the credential.**

**3 · D528 part 2 executed.** The Sanjeevni project's first session (S262) uploaded the 35 and proved
them by hash; this session deleted the same 35 here — **1,593,475 → 1,475,742**, the delta agreeing
with the new side to 3 bytes. The staging folder (116 files) rowed in `ClaudeCowork\MANIFEST.md5` by hand
(the 05:05 rebuild had walked before it existed): 2,945 → 3,061, 0 mismatches. Manifest §S261 block: the
35 with their md5; six existing rows tagged `project: sanjeevni`. Register v5.101 records it.

**4 · The shelf read, and F-506.** 406 papers, **205 never referred to (50.5 %)** — down from 51.5 % at
S257. The tool had been picking "the newest Register" by string sort and had read v5.99 since v5.100
existed. Fixed in one line, applied on manojz with a backup; source and proof in
`deploy_kits/S281_PAPERS_SORT/`. Nothing for the owner to run.

**5 · Numbers.** drift 0 · dead 1 · **stale 3, over the line** — the Sanjeevni Book, now the Sanjeevni
project's document and its first candidate job there · folders per the 05:05 report.

## §1 · MENTAL MODELS THIS SESSION EARNED

- **"Unreachable" is two facts.** The machine answering and the share refusing are told apart by one
  ping, and the pull script already does it — read the script's own facts before walking to a machine.
- **A password change on a machine breaks every stored credential that points at it.** When the owner
  says "I changed a login", the pull chain is the first place to look.
- **A "newest by name" pick over versioned files must sort on the number.** A string sort is right until
  the number gains a digit, and then it is wrong in silence (F-506; F-491's family).
- **Two sessions of one owner can run at once if they agree on a number and a board.** S261 here, S262
  there, both status lines on the board.
- **A nightly walk is a snapshot.** A folder created after 05:05 has no row until 03:10 tomorrow; the
  close rows it by hand when a survivor proof depends on it.

## §2 · THE LIVE BACKLOG — split by project (D528)

**Here, the assistant's:** D528 step 4 — the 75 evidence-only Sanjeevni papers out of this project over
later closes, each behind its `MANIFEST.md5` row (they have rows since 07:20) · F-498 second half ·
F-496 · the asset-register nightly backup that names no log · D525's seven never-fired checks + the UPI
check (the bundle carries `freshness_legs.json` since 17-Sep) · the F-384 sweep of the manifest's
historical blocks · the portal tile caption (with the next portal change) · `freshness_legs.json` on the
box differs from the Register (a config edit, found by the S262 pin check — record the box's bytes at the
next VPS-touching close).

**The Sanjeevni project's:** `SANJEEVNI_START_HERE_PROMPT_v1.1` (the shared-systems map) · the Book
v1.3 (F-493 §7.2; stale 3) · D524 · F-494 · Darpan's day-close · the refused 16-Sep 23:55 export (what
report was it?) · the tidy-up chain.

**His, deferred at his word:** `OWNER_TODO_LIVE.md`. Not chased.

## §3 · INSTALL DISCIPLINE

One file changed on manojz outside the canon folder: `D:\Downloads\_kbtools\build_papers_index.py`
(backup `.bak_S261_dfcf659c` beside it; `_kbtools\SUMS.md5` row updated; `py_compile` clean; run twice).
The credential refresh on manojz was the owner's own line. Every canon write was hashed after writing and
the gate re-run from inside `KB_canon_all`.

## §4 · THE BOUNDARY

The publish is the owner's double-click and is owed: v2.85, v1.98, v5.101, v182, START_HERE_263,
S261_BUILD_BRIEF, S261_CLOSE_REPORT, the pin list, the manifest, `MD5SUMS_ALL.txt`, `KIT_ID.txt`,
`deploy_kits/S281_PAPERS_SORT/`. The VPS deploy-clone pull (A8c) rides with it — one line, his. Nothing
on the VPS changes.
