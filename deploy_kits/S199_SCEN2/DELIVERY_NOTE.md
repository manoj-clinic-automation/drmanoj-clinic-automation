# S199_SCEN2 — Deduction Scenario, wired into the portal

## What it adds
A read-only **Deduction scenario** page inside your Staff Register app, reached
one click from the Salary page (a new pill), behind the **same manoj/bhawna
salary gate**. It shows, per staff, this month to date:
- the NEW policy at August's ramp slabs, itemised,
- the SAME behaviour at September's STRICT slabs,
- the OLD flat system (Rs.1/late-minute + day-salary per absent beyond 3),
- dress/I-card in their own table (full value + waive none/half/all totals).

Nothing is applied to pay. No existing route, database, or salary math is touched.

## Full flow from your portal
Portal home -> **Staff** group -> **Salary — approve & lock** tile
-> on the salary page, the **📊 Deduction scenario** pill (top row, beside
"Early-big") -> the scenario page. A "← Back to Salary" link returns you.
(Direct URL: `/register/salary/scenario`. Defaults to the current month; add
`?ym=2026-08` for a specific month.)

## Files (two), both currency-gated
| File | From | To | Base pin (must match live) | New pin |
|---|---|---|---|---|
| `staff_register.py` | S196 v0.4 | `/root/staff_register/staff_register.py` | `9087954c8a4a891e8cdd848d6a9d48b2` | `c1fede9f723454d4fe8e01e1a45cc111` |
| `att_scenario.py` | v1.0 (S199_SCEN1) | `/root/att_scenario.py` | `4dc05e332cec8b713f77efb3e284ca18` | `5c4ff00910fcc1cbdcc92e6dc63eb7ff` |

`att_scenario.py` v1.1 adds `render_document()` (returns the HTML as a string so
the web page can show it inline); the shell command still works exactly as before.

## Install (on the VPS, after PUBLISH_ALL + git pull)
    bash /root/deploy/repo/deploy_kits/S199_SCEN2/INSTALL.sh

The installer REFUSES unless the box holds the exact bytes above, backs both files
up (`.bak_S199_SCEN2_<ts>`), copies, re-verifies the hashes, runs the register
`--selftest` (restores on failure), then restarts `staff-register`.

## Proven offline
- `py_compile` + `pyflakes` clean on both files.
- register `--selftest` PASS with the new route (routes 200).
- end-to-end Flask render test: the route draws the real table (Asha/Vikram/Arjun,
  correct figures), the pill appears on the salary page, default month = current,
  and it fails soft to a friendly message if the attendance tool is unreachable.

## Pins for the S199 close
staff_register.py `c1fede9f723454d4fe8e01e1a45cc111` (Register-pinned; base 9087954c) ·
att_scenario.py v1.1 `5c4ff00910fcc1cbdcc92e6dc63eb7ff` (analysis tool, not Register-pinned).
