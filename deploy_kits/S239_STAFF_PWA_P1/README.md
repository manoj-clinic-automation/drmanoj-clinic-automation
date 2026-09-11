# S239_STAFF_PWA_P1 — the staff app, phase 1

**Owner, 11-Sep-2026:** launch the app for Shavez, Shivani and Alisha; Darpan too. Add the Call Tracker. In the
Sanjeevni/Marg tiles only Vaapsi is active now. Docterz tiles are confusing — remove the extra ones. Hold
Attendance and Staff Register from all staff for the time being.

## What each phone shows after this (rendered from the live portal code, pin 7bc59115, with this file)
| login | Clinic | Money & Accounts |
|---|---|---|
| shavez | Call Tracker · Forms & Downloads · Asset Register · Scan Purchase | Vaapsi Desk · Docterz Revenue |
| shivani | Call Tracker · Forms & Downloads · Scan Purchase | Vaapsi Desk · Docterz Revenue |
| alisha | Call Tracker · Forms & Downloads · Scan Purchase | Vaapsi Desk · Docterz Revenue |
| darpan | Forms & Downloads · Scan Purchase | Daily Sale · Vaapsi Desk |

Owner and Dr Bhawna: unchanged. Amir: keeps his three purchase tiles; Attendance/Staff Register held.

**Withdrawn Docterz tiles** — Daily Collection, Clinic (S182 hand entry) and Docterz daily collection (S223
register card): **zero entries in `finance.db`** (nightly of 07-Sep). Pages and books untouched.

**Page gates already let each one in:** `returns.desk_users` = darpan, shavez, alisha, shivani, bhawna;
clinic maker rows = shavez, alisha, shivani; Darpan is the medical maker.

**Call Tracker** opens the existing Apps Script page; it asks the person's own key once and remembers it on
that phone (`clinicDashKey`). No key is in this kit.

## Install (VPS, one line)
`bash /root/deploy/vps_deploy.sh S239_STAFF_PWA_P1` — gate v8, backup `.bak_S239_v8`, swap, read back, and a
list of every portal login with a flag on any staff login the hold does not cover.
