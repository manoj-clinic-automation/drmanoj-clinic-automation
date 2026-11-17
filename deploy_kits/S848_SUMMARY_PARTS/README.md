# S848_SUMMARY_PARTS — a dealer's month summary sent in parts adds up (17-Nov-2026, Sanjeevni session 473)

**Why.** The owner's question at 11:16 IST about scan B-0332: L.K. Drug House sent October in **two** summary papers — B-0296 (₹3,656,
dated 15-Oct, no printed name) and B-0332 (₹9,178, 31-Oct, no printed name). Together ₹12,834 = Marg. The month-end check let only the
newest summary of a dealer speak, so L.K. read "₹3,656 short" (bills 90058 and RT092205, which are on the first paper) and October's lock held.

**Now** (`scan_register.py` only; read only, as S750): for one dealer and one month, when every paper is read, each lists bills, and **no
bill or credit appears on two papers**, the papers are parts — their lines, figure and totals add up; the newest paper's id speaks for the
scan; the opened line says "The dealer sent this month in 2 papers: B-0296 · ₹3,656 (open) + B-0332 · ₹9,178 (open) — added together".
Any overlap (a revised or repeated summary), or a paper not read: the newest speaks, exactly as before. One paper: unchanged.

**File:** `/root/finance/scan_register.py` f0bb05cd → TO (whole file; `make_s848.py` from the FROM bytes, two exact anchors + one block).
**Proof:** `synth_s848.py` 10/10 (T1–T6 the rule; E0–E2 on a copy of the database with made-up papers of L.K.'s real October: in parts →
agrees; a newer complete paper → the newest alone); the control on the live file red (2 FAIL). walk_s750 / walk_s753 / walk_s755 give the
same last line on the live and the new file. On the box the installer adds **R1: L.K.'s live October agrees** (copies of finance.db and
assets.db) and runs the three walks old-vs-new.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S848_SUMMARY_PARTS/undo_s848.sh`.
