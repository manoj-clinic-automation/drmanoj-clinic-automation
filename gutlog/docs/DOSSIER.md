---
title: "GutLog v3 - Reference Dossier"
subtitle: "Personal health diary - sole reference document"
author: "Built for Dr. Manoj Agarwal"
date: "21 July 2026"
toc: true
toc-depth: 3
geometry: margin=2.2cm
fontsize: 11pt
colorlinks: true
linkcolor: teal
---

\newpage

# 1. At a glance

| | |
|---|---|
| **Tool** | GutLog v3 - single-file Flask + SQLite personal health diary |
| **For** | Dr. Manoj Agarwal (orthopaedic surgeon, Bareilly UP); IBS-mixed |
| **Live URL** | https://health.dr-manoj.in (private, password-gated) |
| **Server** | Hostinger VPS `srv1746119`, CyberPanel / OpenLiteSpeed |
| **Runs as** | `gutlog.service` -> `gunicorn -w 2 -b 127.0.0.1:8020 app:app` |
| **Code** | `/root/gutlog/app.py`, ~1710 lines, no external app modules |
| **Data** | `/root/gutlog/health3.db` (SQLite) + `/root/gutlog/uploads/` |
| **Deps** | flask, gunicorn, werkzeug (Python 3.9 venv) |
| **Monitored by** | `clinic-watchdog.service` (morning all-ok / down-alert) |

This document is the **sole reference** for GutLog. It describes what the tool
is, every screen, the complete data model, all seeded reference data, the full
API, the design system, deployment, operations, security, and the decision log.

\newpage

# 2. Purpose & clinical context

GutLog exists to turn a clinician's own day-to-day symptoms into a clean,
timestamped dataset that reveals patterns a memory cannot.

**Patient context.** Dr. Agarwal has **IBS-mixed** (functional gut pain;
organic workup negative at AIIMS under Prof. Ahuja). Management is dietary
(low-FODMAP titration), behavioural (sleep, stress, tea/coffee reduction),
and pharmacological (as-needed antispasmodics/analgesics, a neuromodulator
course, occasional transdermal buprenorphine). He is also post total hip
replacement (right side) and has cervical issues, so neck/back/hip pain are
tracked alongside gut symptoms.

**What the tool is for.**

- Log gut and musculoskeletal symptoms fast, at end of day or as episodes.
- Track meals against two axes that matter in IBS: **FODMAP load** (symptom
  driver) and **protein** (a deliberate 57 g/day target during diet change).
- Run a structured **food-testing** workflow that promotes foods to
  *cleared* or *trigger* over time.
- Keep a **per-dose** medicine ledger (not daily yes/no) so dose frequency,
  timing clusters, and effect can be analysed over months.
- Hold labs, reports, prescriptions, and consult notes in one place.
- Review everything as trends and export any stream as CSV for a clinic visit.

**Design intent.** One uniform, timestamped ledger from day one - so every
future analysis is a single query, with no "pre-v3" special cases.

\newpage

# 3. Architecture

- **One file.** The entire app - Python backend, HTML, CSS, and JavaScript -
  lives in `app.py`. Pages are served with Flask `render_template_string`.
  No build step, no framework beyond Flask, no external JS/CSS at runtime.
- **SQLite.** A single `health3.db` file beside the app. The schema is created
  on first run; `_migrate()` adds any later columns idempotently.
- **Auth.** Single login password (set on first run), hashed with Werkzeug.
  Session cookie is HTTPOnly + SameSite=Lax, and Secure in production. Five wrong
  attempts trigger a 60-second lockout. A **session epoch** (random token in
  `settings.auth_epoch`, copied into each session at login and re-checked on
  every request) lets the owner **change the password** and **sign out all
  other devices** from the in-app Account page - no restart, no data touched.
  A separate **owner key** (`settings.owner_hash`, Werkzeug-hashed) gates every
  Account action, so a person who knows only the login password can use the
  diary but can neither change the password nor lock anyone out.
- **Serving.** gunicorn (2 workers) binds `127.0.0.1:8020`; OpenLiteSpeed
  reverse-proxies `health.dr-manoj.in` (TLS) to it. Runs under systemd as
  `gutlog.service`.
- **Client.** Mobile-first single page: a bottom tab bar swaps five sections;
  a floating Save button dispatches to the active screen's endpoint. All state
  is posted as JSON to `/api/*`; the server always recomputes derived totals.

\newpage

# 4. The five tabs (functional walkthrough)

The bottom navigation is: **Log - Meals - Meds - Files - Review**.

## 4.1 Log
Opens on the **completion-ring strip** (Day / Meals / Protein / Meds / Vitals)
with a **streak counter** in the gradient header; tapping a ring jumps to that
section. Three segments:

- **Day** (one row per date, re-saving updates it):
  - *Symptoms* - a tap-all-that-apply grid (bloating, gas, urgency, loose
    stools, incomplete evacuation, constipation, nausea, fatigue, feverish,
    eye burn/water, low mood, high stress). Nothing tapped = a clean day.
  - *Gut pain 0-10* with a conditional **site** picker: Left iliac fossa,
    Right iliac fossa, Hypogastrium, Left flank, Right flank, Umbilical,
    Diffuse, Other.
  - *Stools* count + *Bristol* type (1-7).
  - *Tea* and *Coffee* steppers (colour-warn as counts climb; taper target
    2-3 tea/day).
  - *Sleep*, *Walk / Treadmill / Meditation* minutes, free-text notes.
- **+ Episode** (a timed within-day event, own severity + duration):
  Gut (pain spike / urgency / cramping / bloating wave), Neck (neck pain /
  neck + radiculopathy), Hip (hip pain, with left/right/both - right = THR
  side), Back (back pain / low back pain).
- **Vitals**: BP (systolic/diastolic), pulse, **temperature (deg F)**,
  weight, waist, notes. BP weekly; weight/waist monthly.

## 4.2 Meals
- **Day totals** banner: protein-vs-57g bar + today's FODMAP load.
- **Picker**: search the 87-food library (each dot-coloured by FODMAP) or tap
  favourites; items drop into a **basket** with +/- quantity. The basket shows
  this meal's protein/kcal/fibre, a FODMAP-load meter, and the projected
  day protein total. Slot = Breakfast/Lunch/Dinner/Snack, with date+time.
- **New food, just in time**: if a search finds nothing, an inline form adds
  the food (name, portion, protein, kcal, fibre, FODMAP) and drops it straight
  into the meal.
- **Manage food library** (sub-screen): the full 87+ list grouped by category,
  with filters (All / Favourites / Comfort / Triggers), star-to-favourite, and
  edit/delete. Add new foods with a category picker.
- **Food test** (segment): on a deliberate test day, record one food, portion,
  symptoms within 24 h, severity, and a **verdict**. A *Tolerated* verdict
  writes the library status to `cleared`; *Trigger* writes `trigger` -
  the food map updates itself.

## 4.3 Meds
- **Buprenorphine patch card**: apply / remove, with a days-worn counter and a
  single-active constraint (can't apply a second while one is on).
- **Today so far**: doses already logged today, grouped per medicine with their
  times and a **+1 dose** repeat button.
- **PRN dose logging**: tap every medicine taken at one time (multi-select from
  the 15-item list, "+ Add medicine" for anything new), set the time, optional
  shared reason/effect, and log once - each medicine becomes its own
  timestamped `doses` row.
- **Courses** (segment): start a multi-day drug (duloxetine, paroxetine taper,
  nortriptyline, rifaximin, other) with a live **day counter**; end it with a
  response (helped fully/partly/none).

## 4.4 Files
- **Vault**: upload PDF/JPG/PNG (<=12 MB) with a date, type, and label; list,
  open, delete.
- **Labs**: add a result for any of 11 analytes; each shows the latest value,
  unit, and **next-due** date (red when overdue).
- **Consults**: log a visit - doctor (6 pre-loaded, add more), reason, advice,
  med changes, next visit.

## 4.5 Review
Range selector 30 / 90 / 180 days. SVG charts (no libraries): pain vs tea vs
coffee (line), FODMAP load (line), PRN doses/day (bars); a protein target
hit-rate bar; recent doses / episodes / patch-history tables; the cleared vs
trigger food map; and **CSV export links for all 11 streams**. Reminds you to
back up `health3.db`.

\newpage

# 5. Data model

15 tables. `created` is an ISO timestamp on every event table. Free-text notes
are capped (usually 500 chars). Symptoms are stored pipe-joined in `days.syms`.

| Table | Columns |
|---|---|
| **settings** | key, value  *(holds `pw_hash`, `seeded_v3`, `auth_epoch`, `owner_hash`)* |
| **days** | day (PK), syms, pain, pain_site, bristol, stools, tea, coffee, sleep, walk, treadmill, meditation, notes, updated |
| **library** | id, cat, item (unique), portion, protein, kcal, fibre, fodmap, status, tags, fav, note, created |
| **meals** | id, day, mtime, slot, items (JSON snapshot), protein, kcal, fibre, fscore, notes, created |
| **doses** | id, day, dtime, medicine, reason, effect, notes, created |
| **prnmeds** | id, name (unique), sort |
| **courses** | id, drug, start_day, end_day, response, notes, created |
| **patches** | id, strength, day_on, time_on, day_off, time_off, notes, created |
| **episodes** | id, day, etime, category, etype, side, severity, duration, notes, created |
| **vitals** | id, day, vtime, sys, dia, pulse, weight, waist, **temp**, notes, created |
| **foodtests** | id, day, food, portion, symptoms, severity, verdict, notes, created |
| **consults** | id, day, doctor, reason, advice, changes, next_visit, created |
| **doctors** | id, name (unique) |
| **labs** | id, day, analyte, value, created |
| **files** | id, day, ftype, label, stored, orig, size, created |

**Notes.**

- `meals.items` is a JSON snapshot of each chosen food (name, qty, per-unit
  protein/kcal/fibre, FODMAP letter). Totals (`protein/kcal/fibre/fscore`) are
  **recomputed server-side** from that snapshot, so editing the library never
  rewrites history.
- `meals.fscore` = sum of qty x FODMAP score (L=0, L-M=0.5, M=1, M-H=1.5, H=2).
- `doses` is append-only, one row per medicine per time - the basis for
  dose-frequency and time-clustering analysis.
- `patches` uses a single-active pattern (`day_off IS NULL` = currently worn).
- `files.stored` is a random UUID filename on disk; `orig` is the user's name.

\newpage

# 6. Seeded reference data

Seeding runs once, guarded by `settings.seeded_v3`.

## 6.1 Food library - 87 items
Category spread: A Grains 12, B Dals/legumes 10, C Soy/protein 6,
D Dairy/fats 7, E Sabzis 20, F Snacks/nuts 13, G Fruit 13, H Drinks/composites 6.

**Status semantics** (a food carries at most one):

- `cleared` (5) - proven tolerated: multigrain bread, paneer 50 g, makhana,
  rajgira laddu, garlic pearl.
- `trigger` (3) - proven to provoke, avoid: **flaxseed, cauliflower, mango**.
- `test` (6) - currently under trial: urad black (sabut), chickpea/chana,
  chana dal, lobia, paneer 75 g, apple (1/4).
- plain (73) - no verdict yet.

**FODMAP scale** shown as a colour dot and used for load maths:
L (green) 0, L-M 0.5, M (amber) 1, M-H 1.5, H (red) 2.

**Comfort tag** (surfaced in the Manage-Foods "Comfort" filter): Baskin Robbins
choc bar, Cadbury Nutties 40 g, Lays plain salted 20 g, rusk + butter.

**Protein target: 57 g/day.** ~18 items are flagged as favourites for the
quick meal picker (papaya, curd, guava, moong dal, jowar roti, soya chunks,
soy isolate, khichdi, smoothie, coffee-adjacent staples, etc.).

## 6.2 PRN medicines (15)
Colospa (mebeverine 135), Drotaverine 80, Paracetamol 500, Etoricoxib 60,
Allegra 180, Bilastine 20, Fluticasone nasal spray, Peppermint oil, Psyllium,
PEG, Cremaffin, Clonazepam 0.5, Zolpidem 5, ORS, Probiotic.
(*"+ Add medicine" appends any others on the fly.*)

## 6.3 Buprenorphine patch
"Zuprinor" = buprenorphine transdermal **5 mcg/hr**, tracked as its own entry
type (apply date/time, remove date/time, days-worn counter), not as a PRN dose.

## 6.4 Doctors (6)
Prof. Ahuja (Gastro), Dr. V.K. Srivastav (Psychiatry), Ophthalmology,
Orthopaedics, Physician, Other.

## 6.5 Lab analytes (11) with repeat interval
HbA1c (6 mo), FBS (6 mo), Creatinine (6 mo), Hb (12 mo), TSH (12 mo),
Vitamin B12 (12 mo), Vitamin D (12 mo), Ferritin (12 mo), LDL (12 mo),
Triglycerides (12 mo), CRP (on flare - no fixed due date).

\newpage

# 7. API reference (34 routes)

**Auth / pages**

- `GET/POST /setup` - first-run password creation
- `GET/POST /login`, `GET /logout`
- `GET/POST /account` - owner-key-gated: change password, sign out all other
  devices, create/rotate the owner key (login required)
- `GET /` - the single-page app (login required)

**Day & summary**

- `POST /api/day` - upsert the day row (symptoms, pain, tea/coffee, etc.)
- `GET /api/day/<day>` - read one day
- `GET /api/summary/<day>` - ring/streak/protein/patch summary

**Library**

- `GET /api/library` - all foods
- `POST /api/library` - add a food
- `POST /api/library/<id>` - edit a food (also toggles favourite)

**Meals**

- `POST /api/meals` - log a meal (server recomputes totals from item snapshot)
- `GET /api/meals/today/<day>` - meals for a date

**Doses (PRN)**

- `POST /api/doses` - log one row per selected medicine
- `POST /api/doses/plus` - +1 repeat of a medicine now
- `GET /api/doses/today/<day>` - today's doses grouped per medicine
- `GET/POST /api/prnmeds` - list / add PRN medicine names

**Patch / courses**

- `GET /api/patch`, `POST /api/patch` (action = on/off; single active)
- `POST /api/courses`, `POST /api/courses/end/<id>`, `GET /api/courses/active`

**Episodes / vitals / food tests**

- `POST /api/episodes`, `POST /api/vitals`, `POST /api/foodtests`
  (*a food-test verdict writes back the library status*)

**Consults / doctors / labs**

- `POST /api/consults`, `GET/POST /api/doctors`
- `POST /api/labs`, `GET /api/labs/status` (latest value + next-due)

**Files / delete / review / export**

- `POST /api/upload`, `GET /file/<id>`
- `POST /api/delete/<table>/<id>` - whitelisted tables only
- `GET /api/review?days=N` - everything for the trend view
- `GET /export/<table>.csv` - 11 tables (meals flatten items to "name xQ")

\newpage

# 8. Design system

- **Brand teal** `#0B6E6E` -> `#12907C` gradient; deep `#084F4F`.
- **Accents:** amber `#C8860A`, hip-purple `#7A4FBF` (patch), error `#B3372A`,
  ok `#2E7D32`.
- **Surfaces:** app bg `#EFF5F2`, card `#FFFFFF`, line `#D5E3DD`,
  chip `#E6F0EC`, muted ink `#5B7370`, ink `#1D2F33`.
- **FODMAP colour scale:** L `#2E7D32`, L-M `#7CA53A`, M `#C8860A`,
  M-H `#C2622B`, H `#B3372A`.
- **Signature elements:** the completion-ring strip + streak counter (Log tab),
  the gradient sticky header, and the live protein/FODMAP meters on Meals.
- System font stack; emoji glyphs as lightweight icons; `prefers-reduced-motion`
  respected; safe-area insets for iOS.

\newpage

# 9. Environment variables

| Var | Default | Purpose |
|---|---|---|
| `GUTLOG_DB` | `health3.db` beside app | SQLite path |
| `GUTLOG_UPLOADS` | `uploads/` beside app | file vault dir |
| `GUTLOG_SECRET` | sidecar file `<db>.secret` | Flask session key |
| `GUTLOG_INSECURE` | unset | `1` = allow non-HTTPS cookies + Flask debug (local only) |
| `PORT` | 8020 | dev-server port (gunicorn sets its own bind) |

# 10. Security model

- Password hashed with Werkzeug (`generate/check_password_hash`).
- Session cookie: HTTPOnly, SameSite=Lax, Secure in production, 30-day lifetime.
- Brute-force: 5 wrong tries -> 60 s lockout.
- Uploads restricted to `.pdf/.jpg/.jpeg/.png`, max 12 MB, stored under random
  UUID filenames; served only to an authenticated session.
- `/api/delete/<table>/<id>` accepts a whitelist of tables only.
- Single-user tool; there is no multi-account or role system by design.
- **Account management** (`/account`, login required, **owner-key gated**):
  change the login password, **sign out all other devices**, and create or
  rotate the owner key. Every action requires the owner key (`owner_hash`) -
  a private second secret, separate from the login password. So even someone
  who knows the login password cannot change it or lock the app; only the owner
  can. Password change and "sign out others" both rotate `settings.auth_epoch`,
  which invalidates every existing session on every device while keeping the
  acting device signed in. This replaces the old need to delete
  `health3.db.secret` and restart over SSH. None of these actions read or write
  diary data.
- **Owner key setup & recovery.** The owner key is set once, on the first visit
  to `/account` (a "Create your owner key" screen). Do this immediately after
  deploy - whoever sets it first owns it. If forgotten, reset it server-side
  (root): write a new `owner_hash` into `settings`, or
  `DELETE FROM settings WHERE key='owner_hash'` to re-expose the create screen.
  No restart needed; settings are read live.
- Deploying the epoch build logs every device out **once** (pre-existing
  sessions carry no epoch); a single re-login re-stamps them.

\newpage

# 11. Operations & troubleshooting

**Restart / status / logs**
```bash
systemctl restart gutlog
systemctl status gutlog          # want: active (running)
journalctl -u gutlog -n 30 --no-pager
```

**Confirm a deployed file is v3**
```bash
grep -c "health3.db\|seeded_v3" /root/gutlog/app.py   # >= 2
wc -l /root/gutlog/app.py                              # ~1710
```

**Common issues**

- *Login page won't accept password after a fresh DB* - it's asking you to
  *create* the password (fresh DB, first run), not enter an old one.
- *Locked out* - wait 60 s after 5 wrong tries.
- *A field's value didn't save* - numeric vitals/pain are range-validated;
  out-of-range values are stored as blank rather than rejecting the whole save.
- *Service failed on restart* - check `journalctl`; usually a syntax slip in a
  hand-edit. Restore from a `.bak` and re-apply.

**Migration** is automatic and idempotent - no manual `ALTER` needed; safe to
restart repeatedly.

# 12. Watchdog integration

GutLog is one of the always-on services guarded by `clinic-watchdog.service`
(`/root/wa/clinic_watchdog.py`). Its `SERVICES` list holds
`("gutlog.service", "GutLog health diary (web)", "systemctl restart gutlog")`,
so a stop triggers the same ntfy/email down-alert (with the fix command) and it
appears in the morning all-ok. Full method + verification in
`deploy/watchdog_entry.md`.

# 13. Backup & recovery

Back up, from `/root/gutlog`: **`health3.db`**, **`uploads/`**,
**`health3.db.secret`**. Use `deploy/backup_gutlog.sh` (SQLite `.backup` for a
consistent snapshot; 30-day retention) on a 1 a.m. cron. To restore: stop the
service, drop the three items back into `/root/gutlog`, restart. Losing only the
secret logs sessions out but loses no data.

\newpage

# 14. Decision log

- **Fresh start over v2 migration.** v2 held negligible data and a different
  shape (day-only meds, preset-text meals). A single uniform ledger from day one
  beats carrying "pre-v3" special cases through every future query. Old
  `health.db` left on the server, untouched.
- **Food library moved to the background** (behind the meal picker + a
  Manage-Foods screen) rather than being its own nav tab - keeps logging fast.
- **Per-dose PRN ledger** over daily yes/no - enables months of dose-frequency
  and timing analysis.
- **Tylenol = paracetamol 500 mg** (corrected from 650).
- **Zuprinor = buprenorphine 5 mcg/hr**, its own apply/remove entry type.
- **Protein target 57 g/day**; tea recipe 0.3 tsp sugar; coffee half cow-milk /
  half water, no sugar.
- **v3.0.1 patch:** temperature field (auto-migrated), richer gut-pain sites,
  Back episode group.
- **v3.1.0 - Account & multi-device sign-out.** Added an in-app Account page
  (`/account`) to change the password and sign out all other devices, driven by
  a new `settings.auth_epoch` token checked in `login_required`. Chosen over the
  prior SSH-only method (delete the session secret + restart) so the owner can
  self-serve; keeps the acting device signed in, touches no diary data, and
  reuses the existing Werkzeug hashing. Trade-off accepted: one forced re-login
  on the first deploy.
- **v3.2.0 - Owner-key lock on the Account page.** Added a second secret
  (`settings.owner_hash`) that gates every Account action - change password,
  sign out others, and rotate the owner key itself. The login password now only
  unlocks the diary; it no longer authorises control actions. This guarantees
  that only the owner can change the password or lock the app, even if the login
  password is shared or leaks - directly answering the "someone else changes it
  and forgets it" risk. Owner key is set once on first `/account` visit;
  forgotten-key recovery is a server-side `owner_hash` reset (owner is root).
  Deliberately *not* full multi-user: data is still a single shared diary; true
  per-user isolation remains a future v4.

# 15. Known open items & ideas

- **Fish** library row is a 100 g rohu-curry placeholder from the audit; refine
  portion/values to the actual dish if desired.
- **Lays** is set to *plain salted* (low); flavoured packs are noted as high
  FODMAP (onion/garlic) in the item note.
- **Temperature** is labelled deg F (98.6 placeholder) but stores any number;
  a deg C label/range swap is a one-line change if preferred.
- **Unified pain picker** (all body regions in one place) was offered as an
  alternative to the current Day-site + Episode split - not yet built.
- **Vitals are not charted** in Review yet (stored + exported only); a
  BP/weight trend could be added.

# 16. Kit manifest

```
gutlog/
  app.py                      the whole application
  requirements.txt            flask, gunicorn, werkzeug
  README.md                   orientation + quick start
  CHANGELOG.md                version history & decisions
  docs/DOSSIER.md             this document (sole reference)
  docs/DEPLOYMENT.md          deploy/runbook
  deploy/gutlog.service.example   systemd unit
  deploy/backup_gutlog.sh         daily backup script
  deploy/watchdog_entry.md        clinic-watchdog integration
```

*End of dossier.*
