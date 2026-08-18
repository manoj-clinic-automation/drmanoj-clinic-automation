# TPA Network Tariff — Verification & Ingestion Brief
## Dr. Manoj Agarwal Clinic, Bareilly · Session 19 · 30 June 2026

> **Purpose of this document.** It is the complete, self-contained instruction set
> for a *separate background chat (same project)* to verify a set of insurance-TPA
> orthopaedic tariff scans against an unverified AI transcription, and produce one
> clean, trustworthy dataset for later ingestion into the Surgical Estimate system.
>
> **Why this exists.** A previous AI (Gemini) transcribed 10 scanned TPA tariff PDFs
> into JSON. The source PDFs are **image scans with NO text layer**, so that
> transcription could not have been machine-verified — it was visual guesswork and
> is **not yet trusted**. This data will eventually feed a surgical cost-estimate
> tool, so accuracy is **safety-critical**: a wrong rate could cause under-billing
> or a wrong promise to a patient.

---

## 0. Hard rules for the verification chat (read first)

1. **The source PDFs have no text layer.** `extract_text()` returns empty. They
   MUST be read **visually** — rasterize every page at **≥150 DPI** and read the
   image. Do not rely on text extraction; it will return nothing.
2. **Do not trust the Gemini JSON.** Treat it as a *claim to be checked*, never as
   a source. Verify every procedure name, every code, every rupee figure, every
   column label, and every condition footnote against the actual scan.
3. **When a digit or word is not clearly legible, mark it `[UNREADABLE — verify
   manually]`. Never guess a number.** A blank is safer than a wrong rate.
4. **Preserve column structure exactly.** Several TPAs price by room category or
   tier (e.g. Single AC / Twin / General Ward; Tier 1/2/3; L1-L3-L4 vs L2). Keep
   every column; do not collapse them into one "rate".
5. **Preserve every condition/footnote.** "Implants excluded", "implants bundled",
   "LOS cap", "Category A only" etc. materially change the real cost. Capture them.
6. **No PHI, no secrets.** This is tariff reference data only — there is no patient
   data here. Keep it that way.

---

## 1. Source files to verify (the 10 originals)

Upload these exact files to the verification chat. **Do NOT** use the Gemini export
as a source — it is the thing being checked.

| # | File | Pages | Size (bytes) | MD5 (integrity) |
|---|---|---|---|---|
| 1 | `ADITYA BIRLA.pdf` | 2 | 81051 | `13130c9e2ddc74e8d39e9886750b4d0e` |
| 2 | `BAJAJ ALLIANZ.pdf` | 1 | 82170 | `44c411a4d446ee6bab98b73888ddea1a` |
| 3 | `FHPL 2025.jpg` | (image) | 172345 | `b45460a3487d7d356b790f79ce8c156e` |
| 4 | `IFFCO TOKIO TPA.pdf` | 2 | 170447 | `b37b8b00dd616da48d840eb0c3dfa307` |
| 5 | `MAX BUPA HEALTH TPA (1).pdf` | 2 | 175554 | `ce51b912ba21672878c24babd42f283e` |
| 6 | `PARAMAOUNT TPA.pdf` | 1 | 23091 | `d1ca73c948fb92fbcfbf9c8cc492d09d` |
| 7 | `RELIANCE GENERAL INSURANCE.pdf` | 1 | 80424 | `2a86147943294c8d9be66b5609db92b9` |
| 8 | `RELIGARE GRAMIN.pdf` | 4 | 514617 | `8ec3a54d150e121c41d541403eb7655e` |
| 9 | `SBI GEN TARIFF.pdf` | 2 | 297099* | `297dab847e72d60660a49c6867cbe4c9` |
| 10 | `STAR HEALTH.pdf` | 2 | 73757 | `b4f66a8bc7006840c501add56ccaffe5` |

*All 10 live inside the zip `TPA_Packages_2022_DTH-20260630T031218Z-3-001.zip`,
folder `TPA Packages 2022 DTH/`. (SBI size shown as listed in the archive.)

**Note:** "DTH" = Dhanwantari Tomer Hospital. These are *that hospital's*
contracted rates with each TPA, dated 2022 (FHPL sheet is a 2025 image).

---

## 2. What the Gemini JSON claims (the thing to check)

Gemini produced **65 procedure rows across 10 TPAs**. Row counts per TPA:

| TPA | Rows in Gemini JSON | Smell test |
|---|---|---|
| IFFCO TOKIO | 4 | ⚠ Thin. TKR listed at **₹12,000** — implausibly low vs every other source (₹48k-₹180k). Strongly suspect a misread or fabrication. |
| MAX BUPA | 2 | ⚠ Very thin for a tariff PDF — likely incomplete. |
| FHPL 2025 | 10 | Mixed ortho + urology; multi-tier (L1/L3/L4 vs L2 + cap). Check column mapping. |
| PARAMOUNT | 3 | ⚠ Thin; "Category A only" condition — confirm scope. |
| SBI GENERAL | 15 | Largest set; room-category columns. Check MCL rate `56676` (oddly precise). |
| ADITYA BIRLA | 5 | Coded; 3 room columns; implants excluded. |
| RELIGARE GRAMIN | 7 | Codes look inconsistent (`100003` vs `00005` vs `00012`) — verify code digits. |
| BAJAJ ALLIANZ | 7 | 3-tier; implants bundled. |
| STAR HEALTH | 5 | LOS caps + room columns. |
| RELIANCE GENERAL | 7 | **Identical numbers to BAJAJ** — verify this is real, not a copy-paste error by Gemini. |

**Two specific red flags to resolve first:**
- **IFFCO TOKIO TKR ₹12,000** — almost certainly wrong. Read that page carefully.
- **RELIANCE == BAJAJ (identical 7 rows)** — could be genuine (same rate card reused)
  or a Gemini duplication error. Confirm against both scans independently.

The full Gemini JSON is reproduced verbatim in **Appendix A** below for line-by-line
comparison.

---

## 3. The verification task (step by step)

For **each** of the 10 files:

1. Rasterize every page at ≥150 DPI and read it visually.
2. Transcribe the orthopaedic tariff table **exactly as printed**: every procedure,
   code, rate column, and footnote/condition. Include urology lines too if present
   (some sheets mix specialties) but tag specialty.
3. Open the matching block in the Gemini JSON (Appendix A).
4. Produce a **discrepancy log** for that TPA listing every difference:
   - rows Gemini missed,
   - rows Gemini invented,
   - wrong numbers (show printed value vs Gemini value),
   - mislabeled or collapsed columns,
   - dropped conditions/footnotes.
5. Assign a **confidence note** per TPA: `HIGH` (scan clear, fully read),
   `PARTIAL` (some cells unreadable), or `LOW` (scan too poor — needs human eyes).

---

## 4. Required outputs (what the verification chat must deliver)

1. **`TPA_Tariff_Master_Verified_v1.json`** — one clean unified dataset, structured
   per TPA, every rate column preserved, every condition captured, every uncertain
   cell marked `[UNREADABLE — verify manually]`. This is the file that will later be
   ingested into the Surgical Estimate system as raw reference data.
2. **`TPA_Verification_Discrepancy_Log_v1.md`** — per-TPA list of exactly what
   Gemini got wrong, plus the per-TPA confidence note.
3. A short **summary** at the top: total verified rows, total discrepancies found,
   which TPAs are `LOW` confidence and need the doctor's manual check.

**Schema guidance for the master JSON** (keep it simple and faithful):
```
{
  "dataset": "TPA Network Tariffs — Dhanwantari Tomer Hospital",
  "source_year": 2022,
  "verified_on": "<date>",
  "verified_against_source": true,
  "tpas": [
    {
      "tpa_name": "...",
      "source_file": "...",
      "confidence": "HIGH | PARTIAL | LOW",
      "conditions": "implants excluded / bundled / LOS caps / room-category-only ...",
      "rate_columns": ["<exact column labels as printed>"],
      "tariffs": [
        {
          "code": "<as printed or null>",
          "specialty": "Orthopedics | Urology | ...",
          "procedure_name": "<exact>",
          "rates": { "<column label>": <number or '[UNREADABLE]'> },
          "notes": "<footnotes / per-piece implant rules / etc.>"
        }
      ]
    }
  ]
}
```

---

## 5. After verification — Drive + Notion (the verification chat does this, not now)

Once the two output files are produced and the doctor has glanced at any `LOW`
confidence TPAs, the verification chat should:

**Google Drive** (account `drmka.ortho@gmail.com`):
- Upload both output files to: **`Dr. Manoj Agarwal | Practice Hub / 06 · Claude
  Workspace / Generated Documents`**.

**Notion** — add one row to the **Tech & Systems Register**
(`collection://e2e5e030-efc6-41a3-8f8a-70e808aaa5cb`):
- **Name:** TPA Network Tariff Dataset (10 insurers, DTH 2022)
- **Status:** Verified raw data — pending ingestion into Surgical Estimate
- **Note:** Scanned PDFs visually verified against Gemini JSON; discrepancy log
  produced; feeds the future Surgical Estimate rebuild. Source: Dhanwantari Tomer
  Hospital TPA contracted rates 2022 (+ FHPL 2025 image).

---

## 6. How this connects back to the build

This dataset is **reference data for the future Surgical Estimate web tool**, not a
standalone deliverable. The clinic's *own* package master and the **Ayushman**
package KB already exist and are separate. This TPA set adds the **private-insurer**
dimension (what each TPA pays for a given procedure), which lets the Surgical
Estimate tool eventually answer: "for a patient with insurer X, the approved
package rate for this procedure is ₹___, implants ___ (included/excluded)."

It does **not** change anything live. It is queued, not active.

---

## Appendix A — Gemini JSON (verbatim, to be checked — NOT a source of truth)

> The structured JSON Gemini produced is reproduced below exactly as received.
> Paste this, plus the 10 original files, into the verification chat.
> Every figure here is a *claim* awaiting confirmation against the scans.

*(Paste the full Gemini `unified_network_tariff_dataset` JSON block here when
starting the verification chat — it is already in the doctor's possession from the
Gemini export `.docx`. It is intentionally not re-typed here to avoid introducing a
second layer of transcription error; use the original Gemini export as the
comparison artifact.)*

---

*Prepared in Session 19 for a same-project background verification chat. This
document changes nothing live. Build focus for Session 19 remains the doctor-only
launcher portal.*
