> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG / MEDICAL-PC DOCUMENT POINTERS

## "I found an old Marg document. Is it still true?"

**Find it in the tables below.**
If it is listed, **it is not current** — the row tells you what to read instead, where that
document is, and which section of the master carries the content.
**If it is not listed, and it is not in `S203_MARG_RETIREMENT_LIST.md` §1, it is current.**

**The one-line answer for almost everything:** read
**`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md`** — repo
`deploy_kits/S203_MARG_CANON/`, md5 `579ea885e440e76af73de3ecc4542d71` — §0.1 first, which tells you
which document class owns which kind of fact.

**Session 203 · 26-Aug-2026.** Every md5 below was computed with `md5sum` on this machine in this
session. Nothing was deleted (F-23); every retired document is retained with a banner at its top.
No `git` command was run (F-131). No token value read or printed.

> **⚠ The master is v3, not v4.** `S203_MARG_PRECEDENCE_MAP.md` was written against **v2**
> (`fc3058d92570fd12bbdb1d472270b7c9`) and `S203_MARG_RETIREMENT_LIST.md` against **v1**
> (`57d12c8c46dd633a318f096344d02709`). Both still name their own generation as "the master".
> **v3 wins**; where those two documents cite a master section number, check it against v3 — the
> numbering moved once (see row 10 below).

---

## A · RETIRED AND SUPERSEDED — banner added, in `deploy_kits/S203_MARG_CANON/`

`md5 now` = the file **after** its banner was prepended today. The **`md5 before`** column is what
`S203_MARG_RETIREMENT_LIST.md` §1 and the old `SUMS.md5` recorded; those citations are now stale by
one banner, which is expected and is why both values are here.

| # | Old document | Status | Read this instead | Where the successor lives | Master v3 section carrying it | Successor md5 | md5 now | md5 before |
|---|---|---|---|---|---|---|---|---|
| 1 | `S195_FINAL_PINS.md` | **RETIRED** | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` (medical-PC pins) · `KB_Register_v5_54_S202.md` (VPS + manojz live-file table) | `deploy_kits/S203_MARG_CANON/` · `deploy_kits/KB_canon_all/` | **§3.2 Live pins** | `579ea885e440e76af73de3ecc4542d71` · `8fede84d7126e13fca17418e449f9d0a` | `e8dda44c8aa13af10513e3d1638ddb4e` | `c368c43fedb41786fcade130f0ea0931` |
| 2 | `S195_Close_Summary_FINAL.md` | **RETIRED** | `KB_History_Archive_v1_49_S202.md` **§S195** | `deploy_kits/KB_canon_all/` | *(history — the master carries no narrative)* | `06c6670a8a1155959e4f0961ad58e7c5` | `1e8b97efbebd4dc67fd8542d9ac3dc4d` | `b1bcdceec46223c08783782c56092824` |
| 3 | `S195_Marg_dbf_Encryption_Finding.md` | **SUPERSEDED** (23-Aug, by its own successor) | `S195_Marg_decrypt_partial_key.md` — the thorough negative | `deploy_kits/S203_MARG_CANON/` **and** `deploy_kits/KB_canon_S197fold/filed/` (identical) | **§4.3 The database is encrypted — reading it directly is RETIRED** | `3f83f1594fcb22e29b6aba0458e6574b` | `805f71d7bf5a1cc568dc9d896fdad4b2` | `17364d0b85feb7b98472078bb21f9c6c` — the state at the start of this pass, when it already carried the exemplar banner. Before **any** banner it was `c3f7d453f576218b104d069ea4e04b68`, recorded in `SUMS.md5.before_S203_master` line 24 |
| 4 | `S195_Email_Hardening_and_Marg_Guard_BuildState.md` | **SUPERSEDED** | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` (what is actually on the machine) · Archive §S195 (the e-mail half) | `deploy_kits/S203_MARG_CANON/` · `deploy_kits/KB_canon_all/` | **§3.1 What is on it** — the guard chain described is **not on the medical PC at all** | `579ea885e440e76af73de3ecc4542d71` · `06c6670a8a1155959e4f0961ad58e7c5` | `e1420f1190d40007b5cf3b6e54f9642c` | `4456995fcb9db746978722de1e0441df` |
| 5 | `S201_A1FIX_Live_Pin_Record.md` | **SUPERSEDED** | `KB_Register_v5_54_S202.md` **live-file table** (recovery recipe kept in `S201_PARKED_BACKLOG.md` §B) | `deploy_kits/KB_canon_all/` · `deploy_kits/S203_MARG_CANON/` | *(none — the master does **not** own VPS/manojz pins, §0.1)* | `8fede84d7126e13fca17418e449f9d0a` · `3083d35fb29b5565d2bebb4b6aeb2b26` | `88b7cee03dab3f7a7a077b5ee4cc5db3` | `c069cd4b36a604618cd5d2a4e47c0844` |
| 6 | `S201_Part0_Rescan_Record.md` | **SUPERSEDED** | `MARG_PIPELINE_REFERENCE_v1.md` **§7** · `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` **§3** | `deploy_kits/S203_MARG_CANON/` (both manifest-pinned Tier-1 CURRENT) | §2 for the chain; the procedure belongs to the two references | `97b3cf73f7f83c0860bde2d911596ff7` · `c2b5251f55762490ad219b8855a18dd8` | `66ace6c5d0551633e8cb1d25ff515b40` | `4247b6153f649f7607e8cace84bae7e0` |
| 7 | `S201_Part1_Capture_And_Agent_Record.md` | **SUPERSEDED** | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` | `deploy_kits/S203_MARG_CANON/` | **§3.3** how the agent starts (and the supervisor-kill trap) · **§3.4** delivering changes · **§3.2** the pins | `579ea885e440e76af73de3ecc4542d71` | `900920aa7ef18760894ca8984e3be771` | `8be4f6c758b2054e14861189c49c5b35` |
| 8 | `S201_Marg_Outbox_Never_Drained_Finding.md` | **SUPERSEDED — F-179 CLOSED** | `Fault_Action_Register_v2_41.md` (the only register of record for fault status) | `deploy_kits/KB_canon_all/` | **§7 Failure modes, by symptom** | `4883e3bdf08cba92da7597448e00f2da` | `4a1579db3d7dbcb03d153124d2c1aa07` | `d0adbd36217ad4922ef0474b2bdd5774` |
| 9 | `S201_Medical_Pipeline_Completion_Audit.md` | **SUPERSEDED BY MEASUREMENT** | `S203_MEDICAL_PC_PINS.md` — the first pins ever read off the medical PC | `deploy_kits/S203_CENSUS_BACKUP/` | **§3.1 / §3.2**; its "C: tree found 25-Aug" claim is **the error corrected at §9 #8** (it was 15-Aug) | `976a6f0ccc22318a603d055f81541f71` | `85a6bc7cac550a982711e8537c9f4c24` | `a0452bbb7491ac2adc909945df254ca1` |
| 10 | `S201_WHATS_LEFT_FOR_YOU.md` | **SUPERSEDED** | `OWNER_TODO_LIVE.md` — the living list, kept current by numbered step A10 | `deploy_kits/S203_MARG_CANON/` (un-manifested by design) | **§11 OPEN ITEMS.** *(The retirement list says "§6" — that was v1/v2 numbering. In v3, §6 is "How to know it is working".)* | `0f0645f1a78415d571c8fe867b8b0432` | `e53ce3548b753f8dffceb46404da8584` | `907ff59bb8d41c64117cac4d239a932a` |
| 11 | `S180_Marg_Feed_Feasibility.md` | **SUPERSEDED** — a route survey whose verdicts are spent | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` for the route that was built; the **still-unanswered vendor asks** are in `S180_Marg_Action_Register.md` V8/Q5 and `Marg_Report_Requirement_Sanjeevni.md` | `deploy_kits/S203_MARG_CANON/` | **§2 The chain, stage by stage** | `579ea885e440e76af73de3ecc4542d71` · `599d315625fdf3aca11fa9aa70e6f5b3` · `ee3cd2549948d6437ef75480d9dadec0` | `d9cabc4a27bb4401d0062a8bfb05635c` | `6db52a89106e17e17769f2d31be6f24d` |
| 12 | `S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` | **⚠ UNCERTAIN — treat as KEEP** | **No successor could be verified.** `S203_MARG_RETIREMENT_LIST.md` §1 row 12 retires it as "superseded whole by v2" — **no `…_Build_Contract_v2` exists anywhere in this repository** (searched by filename across the whole tree, 26-Aug), and §4 #1 records that the v1 was never read from project knowledge. Nearest current: `S179_Finance_LIVE_State` (design/D313, out of date on state) · `MARG_INGESTION_REFERENCE_v1.md` | `deploy_kits/KB_canon_all/` · `deploy_kits/S203_MARG_CANON/` | *(none — the master carries no build contract)* | `54cb25a88adc5692360341113a87a43e` · `4d603b727a91a7c782992f092fc949e3` | `3297bfbbbdf85090adfabe35b95987e2` | `f6de1a5eaa59f1c685caca988ad1a3b8` |
| 13 | `S203_MARG_MEDICAL_SYSTEM_MAP.md` | **SUPERSEDED** — written from the record; the master was written from the machine | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md`, which corrects three of its statements | `deploy_kits/S203_MARG_CANON/` | **§3.1** (AF-1 is armed on a file that is not on the machine) · **§4.2** (nothing runs a backup at all — it was never scheduled) · **§9 #2** (the `marg_report.py` copy runs on manojz). Its §5 D350 gap tables are **not** carried and stay in it | `579ea885e440e76af73de3ecc4542d71` | `7c8ea601adfe0128febe2a13c6be7c03` | `5221196a9e531416cc61aa77f5bc9f5b` |
| 14 | `S180_Marg_Feed_Transport_Design.md` | **⚠ PARTIAL — §2 only.** The rest is **KEEP and current** | §2's route ranking → master v3 **§2**. §3.4 (idempotent per-day upsert), §3.5 (self-checks), §3.6 (PHI), §3.7 are the **only home** of that material — do not retire them | `deploy_kits/S203_MARG_CANON/` | **§2** *(§2 only)* | `579ea885e440e76af73de3ecc4542d71` | `4c5b8b48c88d42b480ea8d66d9f508df` | `144a1a406851fec73f6885cfe514d97e` |
| 15 | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md.superseded_by_v2` | **SUPERSEDED — two generations** | `…_v3.md`. v1 lost §4.3 encryption, §4.4 the money rule + V7 truncation, and §4.5 the whole ingestion half; v2 added all three | `deploy_kits/S203_MARG_CANON/` | *(the whole document)* | `579ea885e440e76af73de3ecc4542d71` | `ffc51713065ac582a79087258fd08438` | `57d12c8c46dd633a318f096344d02709` |
| 16 | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v2.md.superseded_by_v3` | **SUPERSEDED** | `…_v3.md`. **v2 §4.3 and §11 item 12 assert the superseded optimistic decryption note** — v3 carries the thorough negative instead and adds §0.1, the precedence rule | `deploy_kits/S203_MARG_CANON/` | *(the whole document; §4.3 and §11 are the corrections)* | `579ea885e440e76af73de3ecc4542d71` | `e8c4886890a2620c9c037b4a7bee57ce` | `fc3058d92570fd12bbdb1d472270b7c9` |

---

## B · SUPERSEDED COPIES **OUTSIDE** `S203_MARG_CANON` — no banner, and two of them are **not the same bytes**

These are the copies a reader may actually open. **They were out of scope for the bannering pass
(which was scoped to `S203_MARG_CANON/`), so they carry no warning at their top.** Read this table
before trusting any of them.

| Old document | Repo path | md5 (hashed today) | Status | Read this instead |
|---|---|---|---|---|
| `S195_Marg_dbf_Encryption_Finding.md` | `deploy_kits/KB_canon_S197fold/filed/` | `2b4525492549a644ad97e3bb198d4137` | **SUPERSEDED.** Carries a 4-line supersession note at its *end* but **no banner at its top** | `S195_Marg_decrypt_partial_key.md` · `3f83f1594fcb22e29b6aba0458e6574b` · master v3 **§4.3** |
| `S195_Email_Hardening_and_Marg_Guard_BuildState.md` | `deploy_kits/KB_canon_S197fold/filed/` | `b60efae40f7ed732ba621967d4f700b6` | **SUPERSEDED**, no banner | master v3 **§3.1** · `579ea885e440e76af73de3ecc4542d71` |
| `S195_Marg_decrypt_partial_key.md` | `deploy_kits/KB_canon_S197fold/filed/` **and** `deploy_kits/S203_MARG_CANON/` | `3f83f1594fcb22e29b6aba0458e6574b` — **identical in both, verified** | ✅ **CURRENT. This is the winning document on encryption, not a retired one.** It was repo-only until this session | *nothing — this is what you read.* Pin it at the close (precedence map §6 #2) |
| `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` — the **operational** copy at `D:\Downloads\margsync\` on manojz | *(not in the repo — on the machine)* | `f02cd8bd…` — **not hashed by me**; cited from master v3 §9 | **STALE — it is the S201 version.** The copy you would actually open **does not contain the fix for the outage that produced it** | the canonical `c2b5251f55762490ad219b8855a18dd8` in `deploy_kits/S203_MARG_CANON/` |

> ### ⚠ The two `KB_canon_S197fold/filed/` copies are **not byte-identical** to their `S203_MARG_CANON` twins, and neither is a superset.
>
> Diffed today, before the banners were added:
>
> - **`S195_Marg_dbf_Encryption_Finding.md`** — the `filed/` copy is **3 lines longer**: it ends with
>   a supersession note naming `S195_Marg_decrypt_partial_key.md`. The `S203_MARG_CANON` copy did
>   **not** have it (it now has a full banner instead).
> - **`S195_Email_Hardening_and_Marg_Guard_BuildState.md`** — **each copy has content the other
>   lacks.** The `filed/` copy carries three later annotations the other does not (the
>   `e535c4f8…` live pin; *"Superseded by the medical-PC leg's portable-Python packaging"*;
>   *"Retired — encryption…"* on Method A). The `S203_MARG_CANON` copy carries a longer macro-steps
>   line the `filed/` copy does not.
>
> **A filename is not provenance (D188), and a same-named copy is not the same document (F-88).**
> **Owed at the close:** reconcile these two pairs deliberately — do not assume either side is the
> original.

---

## C · DECLARED SUPERSEDED BUT **MANIFEST-PINNED** — do NOT banner or retire until the manifest row changes

Editing or removing any of these before its manifest row is amended **breaks Phase 0 on the next
session** (F-184, F-107). The fix is a label change in the manifest, not an edit to the document.

| Document | md5 (pinned, verified today) | The conflict | What must happen, and when |
|---|---|---|---|
| `S195_Medical_Watcher_LIVE_Reference.md` | `885090ab946b61e7b5a990a14a190a15` | The manifest still labels it *"**SOLE reference** for the Marg capture pipeline"* while `MARG_PIPELINE_REFERENCE_v1.md` opens *"**Supersedes** `S195_Medical_Watcher_LIVE_Reference.md`…"*, and master v3 §0 supersedes it on every point where they differ. **Two canonical documents each claiming to be the reference** | **Strike the "SOLE reference" label on the manifest row at the close** — precedence map **C5**, `S202_PENDENCY_AUDIT` **N3**, both still open. Until then this document stays pinned and unbannered |
| `MARG_INGESTION_REFERENCE_v1.md` **§9 item 5** | `4d603b727a91a7c782992f092fc949e3` | §9 item 5 still calls `ingest.min_confidence` *"an owner decision"*; **D348 retired that question** hours later. **A ruling is amended only by a ruling** — a reference cannot keep a retired question alive | **Correct §9 item 5 in place as a struck line (F-23)**, not by deleting it. The rest of the document is current and is the **only** home of the ingestion half — master §4.5 defers to it |
| `MARG_PIPELINE_REFERENCE_v1.md` **§1 and §4** | `97b3cf73f7f83c0860bde2d911596ff7` | §1 says the watcher watches *"BOTH folders"* — it watches **three** roots (master §9 #3, measured). §4 lists **three** token copies — there are **five** (master §8) | Correct §1's root count and §4's token inventory at the close. **On the oldest open item, two lists of different lengths is worse than one wrong list** |
| `AUDITOR_SEED_v1.md` | `b4e349cbcf01547ff774a7c3c434bb21` | Still instructs the live weekly Auditor to continue the **F-series**, which S196 overrode | An **F-23 situation for the owner's ruling**, not a silent edit. Raise it; do not patch it |

---

## D · WHAT IS **NOT** RETIRED — the documents whose content lives nowhere else

Listed so this index cannot be misread as "everything old is dead". Each is the **sole** home of
what it carries; master v3 §10 names most of them "must be preserved, and are at risk".

`S180_Marg_Folder_Recon.md` (`f3393979354411105a253e2715fabe7b`) — the whole Marg data-layer
analysis · `S180_Marg_Daily_Sale_Button_Settings.md` (`3f46935784261a18f50da552d6fd31ee`) — **the
only recipe for regenerating the feed after a Marg reinstall** · `Marg_Report_Requirement_Sanjeevni.md`
(`ee3cd2549948d6437ef75480d9dadec0`) — the licence number and the unanswered vendor asks ·
`S180_Marg_Sample_Findings.md` (`2621975e30be0f66b59a8d842bb928e2`) — the C: tree, the column
variants, the text-cell credit-note trap · `AUDIT_RUN_2026-08-24_slice1.md`
(`17746ec35727c14e2c5b173c9235fce7`) — **the only place AF-3's scan command exists** ·
`S201_Part1_xlsx_Dependency_Removed.md` (`52fe31ae61f7a868927f8231b1537c98`) — the only proof
`xlsx_stdlib.py` is correct · `S201_Parts2_3_4_Record.md` (`e02af11363bd0f235493bb230e164150`) — the
per-type `end_marker` derivations · `S179_Marg_Sale_Report_Analysis.md`
(`da742177633bc023c7c19198b4774b4a`) — **the money rule's derivation; the master carries the rule
and not the proof** · `S180_Marg_Feed_Request_and_Flow.md` (`efef42c53049ec27758489d950398088`) —
**§4A, the sale-return correlation on nine real credit notes** (*not* in `…_Transport_Design`, whose
attribution in `S203_KB_CENSUS_PHASE12` row 51 and `S203_MARG_DOC_INVENTORY` §3 is wrong —
retirement list §0.3).

---

## E · STILL OWED — this index does not close these

1. **`deploy_kits/S203_MARG_CANON/` is not manifest-pinned.** Phase 0 does not verify it; `SUMS.md5`
   in the folder is the only check. **Pin it before anything is retired from project knowledge**
   (F-184).
2. **The repo may be unpublished.** `OWNER_TODO_LIVE` ⭐0 #3: the S202 close is committed locally
   only until `PUBLISH_ALL.bat` runs. **Until it does, the "second store" is one disk, not two** —
   which is the whole gate the retirement exercise rests on. `git status` was **not** run (F-131).
3. **Reconcile the two divergent `KB_canon_S197fold/filed/` pairs** (§B).
4. **The manifest label changes in §C** — none of them is done.
5. `S203_MARG_RETIREMENT_LIST.md` §1 and the pre-banner `SUMS.md5` now cite **pre-banner** md5s for
   the sixteen documents in §A. Expected, recorded in the `md5 before` column, and **the folder's
   regenerated `SUMS.md5` is the current authority.**

---

*S203 · 26-Aug-2026 · every md5 computed with `md5sum` in this session · no document deleted or
moved · banners prepended only inside `deploy_kits/S203_MARG_CANON/` · no manifest-pinned document
edited · no `git` command run (F-131) · no token value read or printed · no patient identifier
reproduced.*

---

> **VERSION NOTE, added 26-Aug-2026.** This was built against master **v3**.
> The current master is **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v4.md`**
> (md5 `df290c6f5cbb870af6c232db21bc2219`). Every section reference still resolves
> — v4 only ADDED section 2.1 and refreshed the section 2 chain table; it
> renumbered nothing. v3 is retained as `...v3.md.superseded_by_v4`.
