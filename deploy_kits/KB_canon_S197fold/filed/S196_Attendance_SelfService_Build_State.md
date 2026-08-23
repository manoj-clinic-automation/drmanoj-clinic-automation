# S196 — Attendance self-service + machine late minutes — BUILD STATE

> **STATUS AT THE S196 CLOSE (appended):** BOTH kits INSTALLED GREEN the same day — `S196_ATT1` (register `--init` + all 12 usernames mapped clean + both selftests green + service restarted) and `S196_ATT2` (PWA with the real clinic-logo icons). **LIVE PINS: `staff_register.py` = `9087954c8a4a891e8cdd848d6a9d48b2` (v0.4) · `att_month_report.py` = `9ab98313bbda7ae5555fb4b5a5a82c4b` (v2.6).** Seven staff logins live; system in production. The text below is the build-time record, kept as written.

**23 Aug 2026 · kit `S196_ATT1` delivered into the repo working tree · NOT yet installed (pins below become live only when the installer runs GREEN on the box).**

## ⚠ Finding to mint at the close (F-160 candidate — F-135/F-141 family)

The kit was first written to `D:\dr-manoj-git\deploy_kits\` — **one level OUTSIDE the git working tree**, which is `D:\dr-manoj-git\drmanoj-clinic-automation\` (as `PUBLISH_ALL.bat`'s own `REPO_DIR` line states). The path was assumed from the connected-folder root instead of read from the publisher. PUBLISH_ALL therefore pushed only the genuinely pending S195 files and the VPS pull had no kit ("No such file or directory" at install). **Remedied same hour:** the six files were `mv`-ed into `drmanoj-clinic-automation\deploy_kits\S196_ATT1\` over the device bridge and **every md5 re-verified byte-identical after the move**. Rule: *the publish destination is read from the publisher's config, never assumed from a folder root.* Leftover empty `D:\dr-manoj-git\deploy_kits\` folder is harmless (bridge cannot delete). *(Minted at the S197 fold as **F-160**.)*

## Owner rulings this session (candidate decision — suggest D334 at close)

1. Staff logins for all remaining staff EXCEPT Arjun; created by the owner in `/portal/users`, role **staff**: awdhesh, pravesh, ranjeet, sukhveer, sandip, vikki, surendra — **owner reports all users added (pre-install)**. Existing logins (alisha, shivani, shavez, darpan) get the self view automatically.
2. "My biometric" shows **today only** — today's date + today's punch times, nothing else. No punch history to staff (management-leakage ruling).
3. **Mark-me-present**: same-day only · refused if the machine already has a punch · one per day · reason required · **the SERVER receipt time IS the punch time** (phone clock never trusted; delaying costs exactly what late punching costs) · checker (shavez) verifies, never his own · **counts only on Dr Manoj's approval** (SR_PRESENT_APPROVERS) · board shows "#N this month" per staffer. Staff punch OUT on the machine as usual — request=in-punch, machine=out-punch, departure/OT logic unchanged.
4. **≥60-min machine late auto-fill** in the day grid (the ID/uniform entry grid): exact minutes in a loud read-only badge, server-computed, stored in `daily_register.late_minutes`; the form cannot supply or override it. **Sundays included** (D253 roster transcribed). Sub-60 shows quietly ("in 09:35 · 5m late").
5. PWA path confirmed: page is mobile-first; self sessions permanent ~180 days (`SR_SELF_SESSION_DAYS`), portal deactivation still cuts instantly; manifest/service-worker is a later additive kit (no data caching, no push for now).

## Build provenance (D188)

Both sources hash-verified against the KB Register pins BEFORE editing — repo bytes == live pins (`staff_register.py cef76859…` S164; `att_month_report.py e64cad19…` S153). Frozen attendance core untouched (D251); att_month_report is the sanctioned additive layer; **no portal.py change** (repo copy is stale vs the S195 pin `ff089807…` — deliberately not touched; staff-role tiles already point at register URLs, and the register now routes self users).

## Pins (candidate → live on install)

| file | was (gate) | becomes |
|---|---|---|
| `/root/staff_register/staff_register.py` | `cef768594bee5360a388e66028456495` v0.2 | `c2059ea1e0157da6cbf820502f4925a3` v0.3 → `9087954c…` v0.4 (ATT2) |
| `/root/att_month_report.py` | `e64cad19d135618dec1413553e6bdc80` v2.5 | `9ab98313bbda7ae5555fb4b5a5a82c4b` v2.6 |

Kit ID `S196_ATT1 ba7127b165d76b1d6e51f3e503854677`. Schema additive only: new table `present_request`; new columns `staff.username`, `daily_register.late_minutes`. Service restarted: `staff-register` only.

## Mechanism notes

- New register role **self** (portal-verified login mapped to a staff row via `staff.username`, else unambiguous first-name; `--map-usernames` CLI seeds it and prints the table, SKIPs ambiguity loudly). Self reaches only `/register/me` + request POST; every other page redirects or refuses.
- **v2.6 fold**: att_month_report reads APPROVED `present_request` rows read-only (`ATT_REGISTER_DB`, fail-soft to exact v2.5 behaviour) and appends each as a synthetic punch at `req_ts` → presence, late bands, review-file loop, departure pairing all identical to a real punch. Grid marks the day `in*` with a legend line.
- Grid late display/store recomputes server-side on every save; register display can only SURFACE divergence from the report, never cause it (report reads punches directly).

## Verification (offline; VPS venv re-runs in the installer)

- `py_compile` + `pyflakes` clean on both (one pre-existing warning in v0.2 selftest, untouched).
- `staff_register --selftest` GREEN incl. new cases: machine late 74' weekday / 61' roster-Sunday / OFF-Sunday / minutes-exempt-0 / de-dup; form cannot override stored minutes; self page today-only + no other staff; request one-per-day; punch-blocks-request; own-verify refusal; approver-only decide (maker 403); reject note reaches staff; feed-down refuses loudly.
- `att_month_report --selftest` GREEN incl. new cases: approved request → present + 70' → LATE60 + review-loop row + `10:10*` grid + legend; pending request changes nothing; register DB gone → exact v2.5 picture.
- **Installer rehearsed end-to-end on a fake tree: steps 1–9 GREEN; negative test: a drifted live file → refused at step 1, nothing moved.** `bash -n` clean (F-126). Post-move md5s on the owner's disk re-verified byte-identical.

## Owed / next

- Owner: re-run `PUBLISH_ALL.bat` → VPS `cd /root/deploy/repo && git pull && bash deploy_kits/S196_ATT1/INSTALL_S196_ATT1.sh` (users already created; usernames must match step-7's printed mapping — if the master spells "Vicky", the username is `vicky`; tell Claude about any SKIP line). **[Done — see status at top.]**
- Close: pins into KB Register live-file table · `live_pins.txt` regen (A8) · mint the policy decision (suggest D334) · mint the delivery-path finding (F-160 candidate) · S193–S195 canon fold-in debt still stands (unrelated to this kit). **[All done at the S197 fold.]**
- Later kit (small, additive): PWA manifest + icon for `/register/me`. **[Done — S196_ATT2, live.]**
