# S281_PAPERS_SORT — the shelf reads the right Register again

**Session 261 · 17-Sep-2026 · manojz only · ALREADY APPLIED — nothing to run.**

## The fault (F-506)

`build_papers_index.py` (S277) takes "the newest KB Register" as the last name in a
**string** sort of `KB_Register_v5_*.md`. `v5_99` sorts after `v5_100` and `v5_101`, so
from the S260 close onward the shelf's corpus quietly used **v5.99, a superseded
Register**, while printing it on the page as if it were the newest. The figure it
produced (205 of 406) happens to be the same either way this session — the fault is
that the corpus line said one thing and the folder held another, and nobody would
have noticed until a Register moved a paper's citation.

Same family as F-491: a tool whose output looks right while reading the wrong input.

## The repair

One line: the sort key is now the number after `v5_`. Everything else is byte-identical
to S277's file.

## What was done, and where

- `D:\Downloads\_kbtools\build_papers_index.py` replaced through the file tools at S261;
  the S277 bytes kept beside it as `build_papers_index.py.bak_S261_dfcf659c`.
- `D:\Downloads\_kbtools\SUMS.md5` row for the file updated to the new hash so the
  installed folder's own gate reads green; `S277_SUMS.md5` is the S277 kit's frozen
  record and is left as published.
- `PAPERS.bat` is unchanged and needs nothing.

## The figure at S261

`406 papers, 205 never referred to` (50.5 %) · corpus: `00_INDEX.md` 29 % ·
`CANONICAL_MANIFEST.md` 32 % · `KB_Register_v5_101_S261close.md` 19 %.
Last trustworthy reading before this: S257, **193 of 375 (51.5 %)**. It fell — by one point.
