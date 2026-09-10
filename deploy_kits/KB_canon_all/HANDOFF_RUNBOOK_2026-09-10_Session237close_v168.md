# HANDOFF RUNBOOK — v168 — at the S237 close, 10-Sep-2026

**Supersedes v167 (S236 close).**

## 0 · WHAT HAPPENED

Two calendar days, one compaction. Three kits built and installed on the VPS; **the ledger app itself
was not touched.** The session began on the Marg export and the certificates and became, from the
owner's detour onward, the longest single piece of work this project has done on staff money.

**August's salary is finalisable.** ₹401,100 owed across six staff, reconciled line by line against
the ₹411,800 the system showed at the start. Darpan is ₹374,000 of it, now held in three accounts
that never pool.

**Twenty-five faults minted, F-389 … F-413. Five are the assistant's**, and F-411 is the one that
matters: I reasoned three times from a file I had not hashed against the manifest, and told the owner
that features he uses daily were never built.

## 1 · WHERE THINGS STAND

**Canon:** Archive **v1.84** · Register **v5.87** · Fault Register **v2.69** (F-0 … F-413) ·
**START_HERE_SESSION_238** · `CANONICAL_MANIFEST.md` · `MD5SUMS_ALL.txt`. Next free **D447 · F-414**.

**Installed on the VPS this session:** `S237_CERT_WATCH` (rev 1 live; **rev 2 with the corrected
10/4-day thresholds is published and NOT yet installed**) · `S237_SALE_BILL` · `S237_LEDGER_STATEMENT`.

**In the repository, published, NOT installed:** `deploy_kits\S236_DISCOUNT\` (T1, unchanged since
S236) · **`deploy_kits\S237_CERT_WATCH\` rev 2**.

**Changed on the VPS by the owner:** the CyberPanel renewal cron, weekly → daily, logging to
`/root/cyberpanel_renew.log`; crontab backed up to `/root/crontab.bak_S237` first. Four staff-ledger
entries: Darpan's ₹15,000 with a schedule, the ₹14,000 contra'd, Shivani's two duplicates and
Surendra's one reversed.

## 2 · WHAT TO START ON

**⭐ `S237_BUILD_BRIEF.md` §2 — the staff-ledger worklist.** The owner's instruction at the close:
*"this chapter is closed as the first thing in the next session."* It is ordered and it is complete:
the reconciler first, then the six corrections that have no route through the application, then the
two functions to read before anything is built, then the five system changes.

**Two of those corrections are time-critical.** `schedule_due_cum()` counts elapsed months
cumulatively less what has been recovered. Darpan's ₹15,000 carries `2026-08:7000, 2026-09:8000`;
**if August's ₹7,000 is not in the book before the September close, September reaches for the whole
₹15,000.**

Then the Marg work — the vendor's new columns, unmeasured since the export was proven unchanged and
the *printed invoice* was what moved.

## 3 · THE TRAPS THIS SESSION EARNED

- **⭐ Hash a file against `CANONICAL_MANIFEST.md` before reasoning from it. Every time.** No
  exception for the obviously named folder — that is exactly where the fossil lives (F-411, F-403).
- **The service's `ExecStart` is the only authority on which file runs.** A `find | head -1` is a
  guess wearing a command's clothes.
- **A file's own version history can lie by omission** — `staff_ledger.py` documents to v3.0 and runs
  at v3.6 (F-404).
- **A library call returning an empty container on failure is invisible to a fixture** —
  `ssl.getpeercert()` returns `{}` unverified, and fifty green checks said nothing (F-389).
- **Read the layer that acts, not the layer under it** — CyberPanel renews at 15 days; acme.sh's 30
  is irrelevant here (F-391).
- **A close that collects less than it should must say so.** August took ₹5,000 of ₹13,000 in silence
  (F-396) — the root of the whole chapter.
- **One field, one meaning.** `contra_of` means two opposite things and that alone makes the raw
  ledger unreadable (F-401).
- **The device shell mounted nothing, again, all session.** Stage → container → commit → verify md5.

## 3b · ⚠ THE PUBLISH MAY REFUSE, AND IF IT DOES THE REFUSAL IS THE FINDING

**F-413:** five ten-digit numbers that do not look like test values — one with a patient name and
a clinic ID beside it — sit in the inherited `KB_History_Archive`, and **v1.84 is a new file, so
the F-185 gate inside `PUBLISH_ALL.bat` sees the whole of it.** They were not masked: masking
inherited text breaks the Archive's pure-append proof, and repairing published history is a ruling,
not a tidy-up. **If the publish refuses, that refusal text is F-413 and the owner's ruling is what
unblocks it** — mask in place and record the broken proof loudly, or freeze at v1.84 and mask a
v2.0 forward.

## 4 · THE BOUNDARY

**No clinic screen changed behaviour this session.** The statement page, the salary page and the
close were all read and none were modified. Every ledger correction identified is either the owner's
own GUI action or waits for the reconciler, which does not exist yet.

**The largest open item is not a defect.** Darpan's interest-free tranche of ₹180,000 carries no
schedule; nothing collects against it while the ₹174,000 loan runs, which on today's terms means it
does not begin to move until roughly mid-2030. **That is a terms question for the owner.**

---
*HANDOFF_RUNBOOK v168 · S237 close · 10-Sep-2026.*
