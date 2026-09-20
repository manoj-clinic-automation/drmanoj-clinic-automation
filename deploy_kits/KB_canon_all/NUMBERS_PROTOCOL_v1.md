# NUMBERS PROTOCOL — v1 · S272 · 20-Sep-2026 · binding for both projects

**Why.** Three times in four days two chats took the same numbers: F-534 (S267 vs S266), F-570 (S324 … S330 with no claim), and the S272 close finding its "next free kit" already spent by S273 minutes after it was written. The owner's word: *"develop a system so that I don't have to be alert for this."*

**The system: one counter, one place, one atomic write.** The System Board's database holds a single document, `board/_numbers`:

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk    → collection board · document _numbers
```

It carries `session_next · kit_next · D_next · F_next · AD_next` and a `claims` log. **Every number is taken there and only there, by a version-pinned write:** read the document (it returns its `version`), write it back with `if_version` = that version, taking the number(s) needed and moving the counter past them, and appending one line to `claims` (session · IST clock read · what was taken). **If the pinned write fails, another chat took it first: re-read and take the next.** The database refuses the second writer; two chats cannot take one number.

**When (both projects):**
1. **The session number — the FIRST act of every chat**, before the board is read for anything else (this replaces "the board wins if later"; there is nothing to compare any more).
2. **A kit number — before the scratch folder is named** (F-515), and never from a listing of `deploy_kits/`.
3. **D and F numbers — before the first canon file of a close is written** (F-534 stands: list `KB_canon_all` too, for the file versions).
4. **The close** writes the claims it used into its close note and the Register's four lines; the Register's end-marker and the manifest footer then *record* what `_numbers` said — they are never the source.

**What is retired:** "next free from the parent's START_HERE_SESSION_###, then the board" (Sanjeevni prompt §3 row 1 and §4) becomes "next free from `board/_numbers`, pinned". `_claude_status.nextFree` stays as a human-readable mirror written by the close, never read to mint.

**Seeded at S272:** session_next 274 (reserved for the Sanjeevni chat; either project's next chat after that takes 275) · kit_next 334 · D_next 568 · F_next 573 · AD_next 25.

**For the parent's next START_HERE_PROMPT / SANJEEVNI_START_HERE_PROMPT revision and END_OF_SESSION_PROMPT v17:** paste the four "When" lines above into Phase 0 and A0 respectively. Until then this file is the rule and both projects' `START_HERE_SESSION_###` name it.
