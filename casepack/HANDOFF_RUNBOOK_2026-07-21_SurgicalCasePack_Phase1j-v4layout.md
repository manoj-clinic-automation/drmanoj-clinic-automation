# HANDOFF RUNBOOK — Surgical Case Pack / Consent
**Date:** 2026-07-21  **Track:** Surgical Case Pack + Consent (website project)  **Phase:** 1j → **1j-v4layout** (§0 closed)
**Predecessor:** HANDOFF_RUNBOOK_2026-07-20_SurgicalCasePack_Phase1j.md

---

## §0 — What happened this session

**Goal:** Port the confirmed **v4 print layout** (`Consent_Layout_PREVIEW_v4.html`) into the live consent tool (runbook §0). **Status: DONE.**

### File-version discovery (important)
- The project's **live file is `casepack_page.html`** (was 271 KB; now 272 KB after edits). It has all Phase 1i/1j content (`csPrintHTML`, `csGenerate`, `csLastMeta`, and every `CS_*` wording constant).
- The other file in the project, **`Surgical_Estimate_Finder_Phase1d.html` (180 KB), is a STALE leftover** — internally "Phase 1b", none of the consent engine. **Do not edit it. It should be deleted from project knowledge.**
- Phone + PC files remain **byte-identical** (one artifact, two names), per the deploy rule.

### The 7 changes ported (all from §0)
1. **New 3-line letterhead header, repeating on every printed page** — t1 title, t2 credentials, t3 = `मरीज: NAME (AGE वर्ष) · RELM RELN · निवासी RES` (left) + `दिनांक: DATE` (right).
2. **Removed in-body duplicate** title + doctor line (killed page-1 doubling).
3. **Removed** the "दिनांक व समय …" line and the standalone "स्थान: बरेली" line (date now header-only).
4. **Removed per-page footer** (clean last page); per-page identity carried by the repeating header (accepted browser-print limitation: header shows on all pages except a solo last page).
5. **Rebuilt end-signature blocks** as two side-by-side `.endsig` boxes, each with a dashed `.sig-box` on top; removed witness headings, per-block "दिनांक ___", and the "गोला करें / who signs" line.
6. **Address split:** single "पूरा पता / मोबाइल:" → **पूरा पता:** (label + one blank line) + separate **मोबाइल नं.:** line.
7. **Added doctor's dashed signing box** (`.cs-attest .dr-box`) to the attestation (doctor's explicit request this session). Kept continuity line, `CS_ATTEST` wording, and the auto `@bottom-center` "पृष्ठ X / Y" page number untouched.
- **Bonus fix:** added `#printArea .docprint .cs-doc td/th{border:none}` so the consent prints borderless like v4, while OT/estimate tables keep their borders.

### Data plumbing
- **निवासी reuses the existing form field** `cs_res` (line ~357). Only gap was that `csLastMeta` didn't carry it → added `res:_res||''` so the header can render निवासी. No new input, no staff change.

### Exact code touch-points (in `casepack_page.html`)
- CSS: replaced old `.cs-rhead/.cs-rfoot` block with `.cs-rhead .t1/.t2/.t3` + `.endsigs/.endsig/.sig-box` + `.cs-attest .dr-box` styles; swapped the print `tfoot` rule for the borderless `.cs-doc td/th` override.
- `csPrintHTML()`: new 3-line `head`; deleted `foot`; removed `<tfoot>` from the table return.
- `csGenerate()`: `var html='';` (title removed); date/time+place line removed; end-sig loop rebuilt; `dr-box` appended to attest; `res:_res` added to `csLastMeta`.

### Verification
- `node --check` on the single 214 KB `<script>` block → **valid syntax**.
- Paren "−1" is pre-existing (literal parens in Hindi labels); identical in original — not introduced by edits.
- Braces/brackets balanced. Both output files **md5 `1db68fa0441068bafd471edc02ea0767`** (identical).

### Files delivered (this session)
- `casepack_page.html` — PC/app file (exact name required by `casepack_app.py`).
- `Surgical_Estimate_Finder_Phase1j_v4layout.html` — phone file, byte-identical. (Rename/relabel as you prefer.)

---

## §1 — Mental models to carry forward
- **`casepack_page.html` is the single source of truth** for the consent/case-pack tool. Phone file = same bytes, different name. Ignore/delete the stale `Surgical_Estimate_Finder_Phase1d.html`.
- **Title/letterhead is print-only.** On screen the generated consent starts body-first (no title). This is expected v4 behaviour, not a bug.
- **`CS_ATTEST` wording is locked.** Layout/box changes around it are fine; text edits need explicit OK.
- **Deploy = full-file replacement of both copies**, done by the doctor after a Ctrl+P self-preview (untick "Headers and footers").

---

## §2 — Open backlog / next steps

**Pending doctor decisions:**
- [ ] **Attest redundancy:** the locked `CS_ATTEST` line still prints "…हस्ताक्षर: ____ दिनांक/समय: ____" AND the new dashed box sits below it. Trim the inline text so only the box remains? (Wording change — awaiting OK.)
- [ ] **Deploy:** not yet live. Doctor to preview a test THR (Ctrl+P → Save PDF, check page-2-onward header repeat + clean last page), then replace both live copies.

**Default-next candidates (doctor to choose):**
- **OT list** — start with the Mephentine/Termin duplicate.
- **Phase 1k** — new consent content (e.g. extension-of-surgery clause); design + fresh preview first.
- **HBP-2022 ingestion.**

---

## Close-out checklist status (vs END_OF_SESSION_PROMPT 8 steps)
1. Summary → **done** (§0 above).
2. Master KB append → **not in this session's context**; ready-to-paste KB section text available on request when the KB file is loaded.
3. Runbook → **this file**.
4. Umbrella Architecture → **no change** (no new D-series decision; no module status change — a layout port within an existing module).
5. API Quick-Ref → **no change** (no API behaviour touched).
6. GitHub commit → see below.
7. Project-knowledge swaps → see below.
8. Cold-backup zip → not assembled here (single-track session; the two HTML files + this runbook are the deliverables).

### GitHub commit message
```
Consent: port confirmed v4 print layout into live case-pack tool (Phase 1j-v4layout)

- New 3-line repeating letterhead header (title/credentials/patient+निवासी+date)
- Remove in-body duplicate title, time line, स्थान line, and per-page footer
- Rebuild end-sign blocks as side-by-side dashed sig-boxes; split पता / मोबाइल
- Add doctor dashed signing box to attestation
- Add निवासी (res) to csLastMeta; consent table now borderless in print
- node --check clean; phone + PC files byte-identical (md5 1db68fa0…)
```

### Project-knowledge swaps (delete old → upload new)
- **Delete:** `Surgical_Estimate_Finder_Phase1d.html` (stale, misleading).
- **Upload/replace:** `casepack_page.html` (new), this runbook.
- (Optional) upload `Surgical_Estimate_Finder_Phase1j_v4layout.html` as the phone copy of record.

*Notion: handled live, not part of this close-out.*
