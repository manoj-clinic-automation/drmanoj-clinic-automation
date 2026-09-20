# S270 BUILD BRIEF — the Sanjeevni close of 20-Sep-2026, and the mandate for the next session

*Written 20-Sep-2026, 01:06 IST (clock read). S270 opened 18-Sep 14:09 IST. This is a LIGHT close: the papers, the board and this brief are written; the canon increment (§6) is carried to the next Sanjeevni close, which appends it there. Next Sanjeevni session: **S272** (the board's nextFree of 19-Sep; the board wins). Read this brief, not START_HERE_SESSION_270 in the clone, which was S268's brief for this session and is now history.*

---

## 0 · THE OWNER'S MANDATE FOR THE NEXT SESSION — his words, 20-Sep

> "Analyse the Marg exports and all the flows in our system, and the Sanjeevni architecture, and the faults identified. My concern was to build a very solid spine on the basis of which a single source of truth remains … run all this and find the best way forward, and report to me in a human-readable format, short and precise, and give me the architecture part — can we move forward with a very, very solid base."

And, from 19-Sep: **re-confirm the S270 verification on Fable 5.1** (this session was moved to Fable 5.1 at its very end; the verification itself ran on the earlier model).

So the next session's whole job, in order:

1. **Phase 0** as the Sanjeevni start prompt says: claim S272 on the board (F-509); the nightly reports; a fresh clone and the canon gate; the Sanjeevni pins against the bundle.
2. **Re-confirm the verification on Fable 5.1.** Re-extract the newest nightly database and bundle from `D:\Downloads\_kbtools\vps_code\`, re-run `verify_all.py` from `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S270\evidence\audit\` against the 117 inputs named in `evidence\S270_INPUT_MANIFEST.csv` (md5 each), and state whether every figure in the reference document §4–§6 still holds. Any change is a new dated section in the reference document, never an edit of the old one.
3. **The architecture.** Read the Book v1.4 (§2–§7), the contract (§1, §4), the reference document (§5 faults, §8 gate) and S270_WHAT_IS_LEFT. Trace every Marg export from the counter PC to every table and screen that reads it. Then design the spine as the single source of truth: what it holds, what feeds it (only Marg's exports, through the certified readers), what reads it (every lane), and the order of the switch-over. Write it as `S272_SPINE_ARCHITECTURE.md` in the working papers and the project. **Plan only; no code until the owner says so.**
4. **Report to him in a few short lines**, not the paper: can we move forward on a solid base — yes/no, what the base is, what he must rule on.

---

## 1 · WHAT S270 DID

| paper | what it settles | where |
|---|---|---|
| `MARG_REPORT_CONTRACT_v1.md` (md5 f04ad990) | every report type read individually: grammar, witness, authoritative fields, clip width, frequency, and a deliberate failure each; §6 eight findings, unminted | working papers S270 · project |
| `MARG_EXPORT_LIST.md` v2 | who exports what, how often (Shavez daily pair; Amir purchases; owner salt weekly, category + item list monthly) | same |
| `SHAVEZ_MORNING_TILE_PLAN.md` | plan only, approved in concept 18-Sep; nothing built | same |
| `S270_MARG_DATA_AUDIT.md` A–G | the read-only audit of the server's core data against the certified readers | same |
| `S270_THE_33_ITEMS.md` | the roll-forward residue with the owner's annotations; §D the reconciliation decision | same |
| `S270_CORE_DATA_VERIFICATION_REFERENCE.md` (md5 0a7bd78f) | **THE SOLE REFERENCE**: result, inputs with md5, method, 18 faults (§5), the 29 reconciliation items (§6), decisions (§7), **§8 the gate the spine must pass**, re-run steps (§9) | same |
| `S270_WHAT_IS_LEFT.md` (md5 1c9e2180) | the plain-language list of what is unbuilt, half-built or parked, by area, with the recommended order (spine → ordering → Shavez tile → expiry/returns → stock defects) | same |
| `evidence\` | `contract_harness.py`, `mutate.py`, `clip.py`, `sweep.py`, `final.py`, `dump.py`, `results.json`, `mutations.json`, `clip.json`, `register.txt`, `S270_INPUT_MANIFEST.csv` | working papers only |
| `evidence\audit\` | `verify_all.py` + `verify_all.json` (the final re-run), `roll.py`, `sale.py`, `sl.py`, `union.py`, `auth.py`, `sweep.py`, `contract_harness_final.py` | working papers only |

**The result, in one line:** sale bills 752/752 exact; purchase bills 509 exact; the 06-Sep count baseline 373/373; the stock roll-forward 31-Mar → 17-Sep exact on 324 of 358, 5 owner-explained, 29 to reconcile (≈ Rs 5,400 more, ≈ Rs 6,400 less). Faults: 72 sale bills never loaded (04-May, 27-May, A000425); 8 misread lines; 5 purchase returns stored as purchases; 21 salts read as SANJEEVNI MEDICOS and renewed nightly; MRP fact = median sale price; DOLOGESIC SP ×2 under one name; 6 clipped sale names ambiguous (Rs 79,970); 16 purchase bill numbers shared across suppliers; 11 negative stocks in Marg.

**The owner's decisions this session (his words are the spec):** ETOZOX 90 and DOLOGESIC SP were his additions · units are **strips and tablets**, never packs · **Marg is not touched**: the spine opens at Marg's 31-Mar closing, applies every export, books one dated reconciliation entry per unexplained item so the spine equals Marg on every date · the purchase/ordering flow he dictated on 04-Sep is settled but has never been used (0 orders in two weeks) and is second after the spine.

## 2 · THE ONE LIVE CHANGE

`D:\Downloads\margsync\MargPull\signatures.json` on manojz: the CATEGORY_WISE_ITEM_LIST signature added (`dating: file_mtime`, header identical to the salt list, no end marker). Backup `signatures.json.bak_S270_b2dcb211`; new md5 **a987a08e626ec210045e8f644536af99** (read back 20-Sep). Both 18-Sep category exports re-filed VERIFIED at the 14:21 rescan. **The VPS copy `/root/marg_ingest/signatures.json` is still b2dcb211 — the two copies differ until the next kit carries it there** (the Book §3.1 hand-sync problem, third occurrence). Nothing else live was changed. No kit was built or claimed.

## 3 · THE GATE THE SPINE MUST PASS (reference §8, restated)

All 3,888 sale bills and 509 purchase bills present, each with a direction · purchase bills keyed by supplier + number + date, numbers kept as text · items keyed by name + packing · the 29 reconciliation entries booked and dated · stock equals Marg's closing on 358 of 358 items on every export date · the 06-Sep count baseline untouched · every reader certified (can fail, and was made to fail) · built offline, walked against the real nightly database, installed by the owner's one line.

## 4 · STANDING RULES CARRIED

Plain language, English in chat, Hindi on staff pages · one step at a time · full-file replacements · F-185 · nothing live rebuilt without his OK · build offline → `py_compile` (python) → he installs · F-509 board is the lock · F-510 clock times read · F-511 no git in the PC shell · F-512 kits in scratch · F-537 list KB_canon_all just before writing canon · D549 the 22 renames wait for count #1 · the 06-Sep count is not disturbed · **his step-2 answers are his, at his own time — never prompt** · his deferred items (close August, the first cheque, bank details for three suppliers, gross beside net) are named only when urgent.

## 5 · NUMBERS

From the board, 19-Sep (S269 parent close): **next free D557 · F-550 · A-D25 · kit S324 · Session 272.** The clone's Fault Register v2.96 ends at F-549. The board wins if later.

## 6 · OWED AT THE NEXT SANJEEVNI CLOSE (carried from S270, not done here)

- `MARG_REPORT_CONTRACT_v1.md` and `S270_CORE_DATA_VERIFICATION_REFERENCE.md` into `KB_canon_all\` with manifest rows and MD5SUMS rows.
- Mint the faults: the 8 findings of contract §6 and the reference §5 items not already numbered (F-527 covers the returns; F-536 the salt heading), from F-550 onward, board read first.
- The Register: the manojz `signatures.json` pin a987a08e (and the VPS copy still b2dcb211, stated as a known divergence).
- This brief into `KB_canon_all\` as `S270_BUILD_BRIEF.md`; the Archive entry; the board's Sanjeevni plan section refreshed (A10c, D534).
- The cloud workspace of S270 is gone with the session: nothing was in it that is not in `evidence\`.

## 7 · WHERE THINGS ARE

- Working papers: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S270\` (eight papers + `evidence\`).
- Project knowledge (this project): the seven papers under `claude/`, this brief as `claude/S270_BUILD_BRIEF.md`.
- The nightly database and bundle: `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` and `code_nightly.tar.gz` (copied 05:05 daily).
- The Book: `claude/SANJEEVNI_SYSTEM_BOOK_v1_4_S268.md` (current per the manifest).
- The board: `https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk` — keys `S270_progress`, `S270_close`.

---
*S270_BUILD_BRIEF · light close 20-Sep-2026 01:06 IST · the canon increment is carried to the next Sanjeevni close (§6) · the next session's mandate is §0.*
