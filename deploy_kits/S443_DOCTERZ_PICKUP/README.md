# S443_DOCTERZ_PICKUP — the Docterz export from the reception PC, on the server

**Session 287 (parent), 01-Oct-2026 · D645 · plan `S286_NEXT_BUILD_PLAN.md` §C·1.**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S443_DOCTERZ_PICKUP/install_S443_DOCTERZ_PICKUP.sh

- The Drive folder **Clinic Records / Docterz exports** (`1JjWcfk_7IzSBQUbLlbNWPvf96LGcjjDt`, drmka.ortho) was made at S287 and
  shared **read-only** with the box's service account (patient-mirror@…). Reception's Chrome saves its downloads there.
- Every 15 minutes: files known by **content** (consultation report: *Consultation Date* + *Mode Of Payment*; follow-up log:
  *Appointment ID* + *Mobile No*); the day from the content; one current export per kind and day; newest wins; **fewer rows =
  quarantined** and shown; bytes kept on the box only (`/root/finance/docterz_exports/`, mode 600/700), never in the repo.
- The owner's money page: a red line when the last working day's consultation export is not in by 10:00 (Sunday closed);
  it clears itself when the export lands. The page side ships in S442's `clinic_money.py` (fail-soft until this kit is in).
- **Not here:** the follow-up tracker's move — it keeps live ledgers on the PC (patient master, visit / follow-up / call /
  revenue ledgers, concessions, manual procedures) and staff forms write them; moving it is a cut-over, put to the owner first.
