# S315_READING_COMPARE — Claude's reading vs Sarvam's, on every scan (READ ONLY)

*Written 14-Oct-2026 by the Scan App project (session 315), at the owner's question of 08:08 IST: "You re-read all the scans
with the Claude API — what are the results, and how do they compare with Sarvam's?" No kit, no number. Run by
`D:\Downloads\_kbtools\agent_build\run_build.py S315_READING_COMPARE`.*

**READ ONLY. Nothing is written to the live database, no file is placed, no service is restarted, nothing is published,
no API call is made to Claude or Sarvam.** The only output is one report file on this PC.

## What to do

1. On the box (ssh as CLAUDE.md says), make a copy of the scan app's database with SQLite's backup API into
   `/tmp/s315cmp/assets.db` (the live path: read it from `systemctl show assetapp -p Environment --value`, `ASSETS_DB=`,
   never print the rest of that line; else `/root/assetapp/assets.db`). Work only on the copy; delete `/tmp/s315cmp/` at the
   end.
2. Read `/root/assetapp/claude_reader.py`, `claude_reread.py`, the S550 part of `asset_register.py` (`_bg_extract`,
   `_s550_claude`) and `/root/shared/sarvam_ocr.py` just enough to know: where Claude's reading is kept (`claude_reading`:
   `bill_id, at, model, ok, doc_kind, data, error`), where Sarvam's result is kept (the bill row's fields, any OCR
   status / raw text column, the `bill_items` rows, the audit lines that say who or what filled a field), and how to tell a
   field a **person** typed or corrected (edit / approve audits) from one a reader filled.
3. Compute, for every paper that has a `claude_reading` row:
   - **Coverage:** Claude read OK / could not read (with the error kinds), by lane; Sarvam had read it / not (status), by
     lane; papers neither could read.
   - **Field by field** — supplier, bill/challan number, bill date, total amount, number of item lines — for each: both
     agree · Claude only · Sarvam only · both read but differ. Compare sensibly (amounts to the rupee; dates as dates;
     supplier on the first two words, case and punctuation ignored; bill numbers ignoring spaces and case).
   - **Who was right, where a person settled it:** on papers where a person typed or corrected the field (or approved the
     paper after looking), score Claude's and Sarvam's values against the person's. Say how many papers this covers.
   - **Kind of paper:** Claude's `doc_kind` counts (bill / tax invoice / estimate / challan / quotation / other) against the
     paper's stored `doc_kind` and lane; handwritten counts; how Claude did on handwritten slips vs Sarvam.
   - **What Claude added:** the papers where Claude filled an empty field (the "4 filled in"), and which fields.
   - **The differences list:** for every paper where the two readers differ on number, date or amount: stamp (B-xxxx),
     lane, the field, Claude's value, Sarvam's value, and the person's value if any. Supplier names of businesses are fine.
4. Also: today's Claude call count and the daily limit, the model, and — if the code or logs keep it — tokens or cost.

## Never
- print or keep a person's name (patient, made-out-to), a phone number, a key or a token; never read `/root/.scanapp_secrets/`;
- write anything on the box outside `/tmp/s315cmp/`; restart anything; call any reading API; publish; push.

## The report — `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S315\READING_COMPARE.md`
Top: 5–8 plain English lines for the owner (how many papers, how often each reader got each field, who was right where a
person checked, what Claude does better or worse — handwritten slips, challans, dates, amounts — and one line on what
this means for keeping Claude after 17-Oct). Then the tables and the differences list. Last line: **read only — nothing
changed.** Do not put the report in the repository.
