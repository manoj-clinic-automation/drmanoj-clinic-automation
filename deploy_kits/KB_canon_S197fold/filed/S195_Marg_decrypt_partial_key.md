# S195 — Marg decryption: THOROUGH NEGATIVE, retire remote decryption

Two background workflows attempted the crack (21 Aug). Corrected verdict below —
it supersedes the earlier optimistic "crackable via crib-drag" note.

## What the thorough attempt found (workflow we14ro2tl)
Four independent attacks over all 27,246 records and all 7 co-encrypted `*.c18`
files:
1. per-column printable/charset attack; 2. space-pad / null-pad fill hypotheses +
brute single-byte fill; 3. cross-file CHAR-witness union (global key) — pinned only
54/256 columns; 4. DBF zero-crib + displacement-chain reconstruction.
**All failed on the record fields.** Decisive negatives, under the header-verified
partial key and every derived key:
- **0** occurrences of bill numbers (A00nnnn / CN00nnn) anywhere in any 256-phase.
- **0** occurrences of "2026" (dates) in any phase; **no** all-digit columns.
- Field descriptors do NOT decode to valid VFP types (dbfread: "Unknown field type").
- Record columns are coded/binary (~73% dominant byte, ~110 uniques per column) —
  NOT space-padded ASCII, so field-type charset pinning has no target.
- **All 7 files share an identical 19-byte header prefix despite sizes 809 B … 13 MB.**
  Under simple XOR of a standard DBF the prefixes would differ (per-file date,
  record count, header length). Identical prefixes falsify "XOR-of-standard-DBF".

## Conclusion
It is confirmed there is a 256-byte repeating XOR *period* (autocorrelation), but
the plaintext under it is NOT a standard DBF — Marg applies a fixed wrapper +
per-record/non-XOR transform (bsVault → Chilkat). Only byte0 (0x30) and rec_len
(256) ever "verify", and those are consistent with coincidence/wrapper, not a real
decrypt. **Remote decryption from the files alone is not tractable** with known
methods. The only realistic remaining route is a **runtime debugger dump of the
key AND algorithm from MARGWIN.EXE/bsVault on the Marg PC** — heavy, uncertain RE.

## Decision (recommended): RETIRE remote decryption
Method A's only value-add over Method B was avoiding the GUI. But **Method B (the
report export) already yields bill-wise sales WITH item/drug lines, daily** — which
is exactly the item-level feed the Marg-independent dashboard needs. So put full
weight on the report-export pipeline (AHK auto-generate → guard-and-send → ingest).
Keep the encrypted samples (manojz `…\_to_delete\margdata\*.c18`) + these findings
on file only in case a hands-on debugger session is ever done. Do not spend more
remote effort on the cipher.

Workflows (resumable, for the record): `marg-dbf-decrypt-wf_e765f56d-53e.js`,
`marg-dbf-decrypt-finish-wf_728a2ed1-88d.js`.
