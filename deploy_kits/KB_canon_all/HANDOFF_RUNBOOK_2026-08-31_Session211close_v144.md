# HANDOFF RUNBOOK — v144 · written at the S211 close, 31-Aug-2026

> **S211 closed PARTIALLY, by the owner's instruction.** The chat was long and at risk of
> freezing: *"if full closeout is risky here due to chat window limitations, then do as best,
> but with utmost data safety."* §5 lists everything owed. **Do not assume the usual close ran.**

---

## §0 · WHAT HAPPENED

A live fault, then a long piece of forensics that ended somewhere better than it started.

**The Remove button** failed with "remove failed — network" and was three faults deep: a `.catch`
that threw away the server's answer and printed a guess; a missing patience wrapper; and,
underneath, a CHECK constraint that admits only `pending/applied/rejected/superseded` while the
code wrote `dismissed`. All three fixed. Errors now quote the server's own words.

**D355 — identity by lookup.** The owner's ruling: *"instead of generating a confidence level,
match them with data and come out with answers."* Bills are matched against the patient master,
falling back to the visit record. Built and live. The purpose is two things only: tag a sale and
a sale return to a patient, and make the counter's gap visible daily to him and to Darpan.
*"Only feedback and information should be sufficient."*

**D356 — the full mobile.** *"Why truncate the patient mobile number, it's for clinic internal
use, my console… will be used by WABA, 360 degree etc."* F-86's last-4 masking is reversed on the
VPS. **F-185 is untouched: still no number at all in the repository.**

**The item-anomaly detector, and the case that set it.** A June bill surfaced where 20 tubes of an
ointment were billed and 2 given, hidden until now by a Marg stock adjustment the owner has since
blocked. *"I feel analytics can reach and flag such issues too."* It can. Bill A001988, 30-Jun,
against an item that had sold once before, in ones.

**The money model, proven.** See §2. This is the durable result of the session.

---

## §1 · MENTAL MODELS — the ones that changed

**The outlier must never be inside the yardstick that judges it.** This mistake was made three
times in one session. Twice a caller computed the item norms ONCE over the whole period and handed
the same ruler to every day, so the June ointment saw its own four lines, its ceiling became 20,
and 20 is not eight times 20. **The fix was not another threshold: `scan_day` no longer accepts a
norms argument at all.** Every flagged row now carries the yardstick it was measured against, so no
caller ever needs the norms table. *The door is gone, so the mistake cannot be made.*

**A rehearsal that exercises the library but not the calling shape is blind.** All three
recurrences lived in caller scripts and every rehearsal stayed green. The rehearsal now walks
day-by-day exactly the way the probes do — and that new check failed on its first run and caught a
wrong bill id.

**Validate with the real parser, never a lookalike.** A hand-written regex silently dropped a ₹690
orthotic whose long name ran into the pack column with a single space. The production parser is
token-based and has no such defect. *A lookalike parser measures the lookalike.*

**Prove it offline before spending his attention.** Four publish-and-run cycles went on one bug
and he called it — *"is this ping pong for your forensics layer??"* The assistant's shell has no
network and no key to the VPS, which makes offline proof more important, not less. The Marg
archive on his own PC settled the largest question of the session with zero VPS queries.

---

## §2 · THE MARG MONEY MODEL — settled, do not re-derive

`amount_p` in `sale_line_item` is **the RATE PER PACK, not the line amount.**

    line amount = (strips + loose / pack_size) x rate
    non-strip packs (5GM, 2ML, 1*1):  qty x rate
    bill GROSS  = sum of line amounts
    a credit note prints GROSS negative — magnitude + direction (D314)

Measured with `marg_report.read_report` — the ingest's own parser — over
`D:\Downloads\margsync\MargArchive\SALE_BILLWISE\`:
**374 bills with item lines, 373 reproduce their printed gross exactly (99.7%)**, 29 of them
credit notes, one unreconciled by ₹33.65 and deliberately left unresolved.

**A bill whose lines do not sum to its printed gross is itself a flag.** Cheap, and stronger than
trusting either number alone.

Two figures were withdrawn on the strength of this: **₹1,33,514** (compared `sale_item.mode`,
which nobody fills, instead of `day_line`, Darpan's typed declaration) and **₹38,157** (a sum of
rates, which is not money). The 123-orphan count stands; its value must be recomputed.

Paper: `claude/S211_MARG_MONEY_MODEL_PROVEN.md`.

---

## §3 · THE LIVE BACKLOG — the S212 order

1. **THE SUMP — sale returns on the panel.** *"It is the sump which NEEDS TO BE ON CONSTANT
   RADAR."* Source them from the **item lines**, not `sale_item`, which misses 123 orphan returns.
2. **Item anomaly on the panel** — proven, 6 flags in 133 days.
3. **The API must pass both through** — `day_report()` already returns them; the route drops them
   at the `jsonify`. One anchored patch, MARK `S211 (day gaps api r2)`.
4. **D356 deploy** — re-push the patient master, then the VPS sync; it also fills the collision
   `kind`, unset on all 17.
5. **Mint F-247…F-258** from `S211_CANDIDATE_RULINGS.md`.
6. **Check 27-Aug** — that day's file is .xlsx and the reader takes .xls only. It is folded into
   the first S212 command.

**The panel shape, stated many times:** ONE card. No duplication of what the console already
shows. No links. All data on the page. Collapsed, expandable to granular detail.

---

## §4 · INSTALL DISCIPLINE

Unchanged, plus two earned this session:

- **Never run a writing `git` command against the mounted repo.** Even `git status` leaves an
  `index.lock` the assistant's shell cannot delete. Use `git --no-optional-locks`; move strays into
  `_to_delete\`, which is already gitignored.
- **`PUBLISH_ALL.bat` sweeps stale locks itself** (the S195 block). Read the batch file before
  asking the owner to do its job — that ask was made this session and was unnecessary.
- Set `PYTHONDONTWRITEBYTECODE=1` before running python in his trees and `__pycache__` never
  appears. It appeared four times before this was adopted.

---

## §5 · THE BOUNDARY — what this close did NOT do

**Done and verified:** build brief (project knowledge + Cowork) · session kits copied,
**45 files md5-verified against the live folder, 0 mismatches** · `MANIFEST.md5` rebuilt after the
sweep, **450 rows, all green** · `00_INDEX.md` · `OWNER_TODO_LIVE` · `START_HERE_SESSION_212` ·
sweep folders with `WHY_SAFE.txt` per drive root · Notion session log.

**OWED, every one repeated in `OWNER_TODO_LIVE`:**

- KB History Archive append · Fault Register minting (twelve rulings) · KB Register ·
  `CANONICAL_MANIFEST` · live pins · VPS clone pull · canon snapshot folder · reduction tranche
- **SSD mirror and cold kit — `F:\ClinicBackup` was NOT CONNECTED.** `device_list_dir` returned
  *"Could not stat"*. Not the usual does-not-mount: not connected at all. **Ask for it by name at
  the start of S212.** The cold kit is due.
- The publish — four files staged, gates green, awaiting his double-click.

Project knowledge measured at the close: **1,397,721 of 2,000,000 bytes — 69.9%.**
No tranche moved; the cap is not pressing and the session's remaining room was spent on safety.

---
*HANDOFF_RUNBOOK v144 · supersedes v143 · S211 close, 31-Aug-2026.
Next free: **D357 · F-247 · Session 212**.*
