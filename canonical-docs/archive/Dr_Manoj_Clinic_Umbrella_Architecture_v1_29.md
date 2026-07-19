# Dr. Manoj Clinic — Umbrella Architecture · v1.29 (DELTA over v1.28)

**Applies over:** `Dr_Manoj_Clinic_Umbrella_Architecture_v1_28.md`.
**Session:** 75 · 2026-07-05 · **CODE CHANGED.**

This delta amends the Track-1 hosting model. Everything in v1.28 not amended here stands.

---

## Amendment 1 — Track-1 write-path is PC-LOCAL (was VPS)

v1.28 §2–§4 described the plan+vitals write-path as a VPS-hosted Flask+OLS tool. **That
is superseded for this tool.** The write-path now runs on the **clinic PC**:

- **Why:** the two source CSVs already live on the clinic PC (the follow-up tracker
  writes them; Drive syncs them out). Putting the writer where the data already is means
  patient data does not spread to a second machine, and matches the "one writer, one
  front door" design now that only the doctor enters vitals.
- **Data path (as owner stated it):** *backend data lives on the PC, then syncs with
  Drive; code + docs go to Git + Drive.*
- The VPS remains home for the Track-2 live systems (WABA bridge, portal, attendance,
  follow-up receiver, call-hook). Only the Track-1 write-path moved to the PC. (D136)

## Amendment 2 — one front door (staff BP page retired)

v1.28 §3 described "two front doors, one vitals writer" (owner page + staff BP-only
page). **The staff BP-only page is retired** (D135): the owner alone enters vitals; staff
hand him a physical vitals record. The design collapses to **one front door → one vitals
writer → one vitals_ledger.** The single-writer / complete-derived-fields guarantee is
unchanged.

## Amendment 3 — PDF archive home = clinic PC (was VPS)

v1.28 §4 put `plan_archive/` on the VPS. **Storage home is now the clinic PC** (D137),
then Drive sync. The archive STRUCTURE is unchanged and still locked:
`plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`; new
patients → `pending/<Clinic_Id>_<mobile>/…`. **PDF engine = reportlab** (D138) —
pure-Python, text-faithful, durable on Windows.

## Build status

**`clinic_writer.py` BUILT + INSTALLED + VERIFIED on the clinic PC** (Python 3.14.5;
self-test 20/20; md5 `d4e20a51ead1aada8c07bead2b504100`). It is the write-path library:
`write_vitals` + `write_plan` + `archive_pdf` + read-only `lookup_uid_by_clinic_id`.
The Step-5 front-end (next) will import these functions.

**Repo layout:** the writer sits in its OWN top-level Git folder `clinic_writer/`, separate
from `followup-tracker/` — two distinct systems, demarcated from the start (matches
`C:\clinic_writer\` on the PC). Kit correction, same session; code unchanged.

## Decisions carried / added (Track 1)
…D132–D134 (v1.28) stand, with **D133 amended by D137** and **D121/D122 amended/resolved
by D136** · **D135** staff page retired · **D136** PC-local write-path · **D137** PC
storage home · **D138** reportlab PDF engine. Next free: **D139.**
