# S723_PC_KITS_CURRENT — the PC setup kits kept current by themselves · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** Every night your PC checks each setup kit on the *Clinic PCs* page against what that PC really runs, repacks a kit that has fallen behind, and has the same night's rehearsal prove it; your usual publish carries it to the server.

## Why
- **D803** (the owner, 29-Oct): *"find a way how to keep them current automatically"*; **F-1048** (open): the medical kit is not refreshed by later kits; the board, 06-Nov 08:48 IST: *"Clinic pc tiles - the pc etc setup files stay uptodate - build was planned but it's pending"*.
- Read at S390 (an independent read-only survey): the **medical** kit (packed 11-Oct, S526) carries `marg_watch.py` 0a78ae15 and `marg_txt.py` 7fa5136d; that PC runs **a009d2fd** and **aa7baee5** (S679, live 29-Oct 17:30). The **reception** kit equals the reception PC's pinned files; the **manojz** kit restores from the nightly state zip by design; the two phones' templates match their records.

## What it is
`D:\Downloads\_kbtools\pc_kits_current.py`, run by `NIGHTLY.bat` just **before** the kit rehearsal (the nightly is the assistant's own; nothing on the server, nothing for the owner to run).
- **medical:** each `payload/<file>` against the PC's mirror of `D:\SendToClinic` (`D:\Downloads\margsync\medical_SendToClinic`), cross-checked with the newest live pin and, when Drive is mounted, `ToMedical\_kit\KIT_MANIFEST.txt`. A file behind is **repacked**: only its bytes change, every other member is copied byte for byte in the same order, `MD5SUMS.txt` is rewritten in its own shape, the new zip is proved, `KIT_INFO.txt` (kit_md5 · packed · version) follows — the page serves a kit only while the two agree.
- **reception:** its files against the reception PC's live pins — **report only** (that PC's bytes are not on this PC).
- **Refused, the kit left as it is:** the mirror older than 26 hours; a file whose mirror copy is not its newest pin, or that has no pin; Drive's manifest naming another md5; a kit not whole to begin with.
- After a repack the rehearsal's report is moved aside, so the same night's rehearsal re-proves the kit on Windows. Report: `D:\Downloads\_kbtools\PC_KITS_CURRENT_LATEST.txt`. Members are only ever those the kit already has (`token.txt` is never packed).

## Proven
`walk_s723.py` **26 of 26** on made-up kits, mirrors and pins (LF and CRLF sums): repacked with every other member byte-identical in order, MD5SUMS proving every member, KIT_INFO following, no secret packed, the rehearsal report moved aside, a second night CURRENT and untouched; left as packed for a stale mirror, a mirror copy that is not its pin, a file with no pin, a kit not whole; `--dry` writes nothing; reception behind is reported only. Control: **20 red**. On a copy of the real repository at S390: medical BEHIND → REPACKED (2 members + MD5SUMS changed, the rest identical, sums whole), then CURRENT.

## Undo
Remove the one `pc_kits_current.py` line from `D:\Downloads\_kbtools\NIGHTLY.bat` (or move the script away — the line runs only while the file is there). A repacked kit's old bytes are in the repository's history and in `D:\Downloads\_kbtools\_pc_kits_before\` (the last one).
