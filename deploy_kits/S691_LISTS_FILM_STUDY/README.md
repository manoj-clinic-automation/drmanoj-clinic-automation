# S691_LISTS_FILM_STUDY — Paid from Docterz, film size on the rate page, the film log's count and bills

*The parent, session 374, 01-Nov-2026. The owner's words, 06:32–06:56 IST: "when Docterz matches the slip exactly then what's the utility of shavez's manual ticks" · "Done button not required" · "21 March is also from last financial year, why keep it?" · "it shd mention number of bills with a from date" · "When adding x-rays film size option and number of films for the study are also missing, it's required also" · "Build now please".*

## What it gives him

1. **His X-ray & procedures page** (`/finance/slips/lists`). Paid now comes from the Docterz report, never from the room's tick, which was retired on 24-Oct (D775). The match is per patient, day and kind: the slip lines' total against that day's Docterz charges.
   - **Equal:** Docterz's mode — Cash, UPI, Card, or "Paid (two ways)". Following his 13-Oct ruling, the words "split payment" never appear.
   - **Different:** "Docterz ₹X for the day", in amber.
   - **Report in, no charge for that patient:** "Not in Docterz", in amber.
   - **No report for that day yet:** "Docterz not in yet".
   - **Line total zero:** "Free".

   The summary says "N lines not matching Docterz". The day chips read "1 film" and "14 films". "Size not set" links to his rate page.
2. **His X-rays & procedures rate page** (`/finance/clinic/sheets`). Every X-ray line shows its film (8×10 × 1, or "film?" when no size is set yet). Tapping the line gives size, films per study (1–6) and both sides on one film. **A new X-ray cannot be added without its film size.** The data is kept in one place: the film log's own table `xf_study`, through `xray_film.set_study`. The film log's separate per-study setting is now just a link to this page.
3. **The film log** (`/finance/slips/film/log`).
   - **Bills:** only film bills of this financial year are listed (from 1 April), under the line "N film bills since 1 Apr 2026 (this financial year)", with a link "All film bills — Scan App" for him only.
   - **The count:** it now counts every billed X-ray slip again. It used to count only slips with the room's Paid tick, which meant no films at all since 28-Oct.
   - **The staff X-ray list:** shows Paid as Docterz shows it. Staff see "Docterz mein alag raqam" and no rupee figure.

## What it changes on the box

| file | from | to |
|---|---|---|
| `/root/finance/owner_sheets.py` | baa7ccc4 | the film on every X-ray line; the Add row asks for the film size; route `/film` |
| `/root/finance/xray_film.py` | c08a1016 | set_study, docterz_paid, fy_start; every 'ok' slip counted; the bills card |
| `/root/finance/clinic_lists.py` | 6118ef4d | Paid from Docterz; "films"; links to the rate page |

No new table, no data step, no portal change. Restarts **clinic-finance** only. It reads `slip`, `slip_item`, `owner_service`, `clinic_day_line` and `xf_*`. It writes only `xf_study` rows, and only when he saves a film.

## Who reaches what

These are unchanged:
- The rate page and its film are for manoj only (clinic checker plus OWNER_SHEET_USERS, unset = manoj).
- The lists page is for manoj only.
- On the film log, the English pages are for the checkers and the Hinglish ones for the staff. The Scan App link is shown to him alone.

## Proof

- **Walk:** `walk_s691.py` runs the real finance app on a copy of the database, with made-up rows only (W691 IDs, days in Nov-2027): 66 of 66 green. That is 44 inner checks, plus the builder re-run byte for byte, plus 19 mutants caught.
- **Control:** on the live files, 25 checks are red.
- **Cold review:** round 1 found SAFE, with corrections. All of them are built: the "split" wording, the day-total wording, no rupee figure for staff, and no Docterz read inside the film count. Round 2 found SAFE, with two corrections, both built: Docterz-only rows also say "Paid (two ways)", and Shavez's Excel carries no rupee figure.

## Install

The publish first. Then one server line, inside the window 04:00–23:30 IST:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s691kit && cp -rp /root/deploy/repo/deploy_kits/S691_LISTS_FILM_STUDY /tmp/s691kit && bash /tmp/s691kit/install_S691_LISTS_FILM_STUDY.sh
```

**Undo:** the installer prints its own one-line undo, which puts the three backups `*.bak_S691_<from8>` back and restarts clinic-finance.

No patient name, number or secret is in this kit (F-185).
