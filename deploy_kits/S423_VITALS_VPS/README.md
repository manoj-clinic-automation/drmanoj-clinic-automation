# S423_VITALS_VPS — Vitals & Plan on the server · session 284 · 27-Sep-2026

**The owner's word (D589, 20-Sep):** Vitals & Plan to the VPS — *every screen and all existing ledgers kept, patient data on the VPS disk off Drive as Case Pack, the PC copy the fallback.* **F-598:** the tool never moved; its tile was PC-only, so on his phone it simply was not there.

## What moves, and what does not change
| piece | on the server | note |
|---|---|---|
| the page | `/root/wa/vitals/vitals_page.html` = the PC's `fcedae30`, **byte for byte** | served at `https://followup.dr-manoj.in/portal/vitals`; its two calls (`/lookup`, `/save`) are pointed at `/portal/vitals/…` as it is served |
| the engine | `/root/portal/clinic_writer.py` = the PC's `0ad6d9f4`, unchanged | BMI, IDs, ledgers, bilingual PDFs — the proven code |
| the Hindi font | `/root/portal/NotoSansDevanagari-Regular.ttf` (`f4ae6809`) | beside the engine, as on the PC |
| the ledgers | `/root/wa/vitals/vitals_ledger.csv`, `plan_ledger.csv` (0600) | the PC's 14 + 14 July rows carried **once** by the assistant through the doctor-only import route, so IDs continue at `…000015` |
| the PDF archive | `/root/wa/vitals/plan_archive/<year>/<UID>/…` | new visits; the 22 July PDFs stay on the PC (`D:\clinic_writer\plan_archive`) with the PC tool |
| patient lookup | the Case Pack's two stores, read-only: `finance.db patient_ref` + `console.db patients` | replaces the PC's tracker CSVs on C: |
| access | the Case Pack's own gate (the doctor, `PORTAL_CASEPACK_USERS`) | Dr Bhawna stays masked from the tile, as today |
| the tile | *Vitals & Plan* → `/portal/vitals`, section **Clinic**, no longer PC-only | same name, so every grant and mask still applies |
| the PC tool | untouched — `D:\clinic_writer\open_vitals.bat` still works | the fallback |

`portal.py` gets three anchored edits (tile, section, mount beside the Case Pack) on the bytes read whole this session (`912a1d82` → `626838cd`). New code: `vitals_portal.py`. Restarts `clinic-portal`. `reportlab` is added to the portal's venv if absent. Backup `portal.py.bak_S423_912a1d82`; RED after placing → restored and the new files removed.

## Proof
`walk_s423.py` — 27 checks, fake patient stores, the real page and engine: the page served with exactly its two calls rewritten and otherwise identical; the gate on every route; lookup (one UID, two UIDs → pick-list, master-only → pending, unknown/blank); the import (wrong header refused, 14 + 14 in, a second import and any import after a save refused, 0600); a save (`V/P-2026-000015`, BMI by the engine, two real PDFs under `plan_archive/2026/<UID>/`, relative paths, `Entered_By` = the login, `Source_Face` = `vitals-vps`); a new patient filed under `pending`; a broken page answered 500, never half-served; and the patched `portal.py` (tile, section, one mount after the Case Pack behind its gate).

## Install — one line on the VPS (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S423_VITALS_VPS/install_S423_VITALS_VPS.sh
```
