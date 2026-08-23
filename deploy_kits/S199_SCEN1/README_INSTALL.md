# S199_SCEN1 — deduction SCENARIO tool (read-only; NOT a live-service change)

One new analysis file. Touches nothing live: no service, no database write, no
existing file replaced. Reads punches + staff_master + the Staff Register DB
read-only and writes two scenario files beside itself in /root (off-repo, F-31).

## Install + run (one line each, on the VPS)

    cp /root/deploy/repo/deploy_kits/S199_SCEN1/att_scenario.py /root/att_scenario.py
    /root/wa/venv/bin/python3 /root/att_scenario.py 2026-08

Then open /root/scenario_2026-08.html (or read scenario_2026-08.csv).

## What it shows, per staff, on the real August punches (month-to-date)

1. NEW policy at August's ramp slabs (marks limit 8) — itemised
2. NEW policy at September's STRICT slabs (limit 5) on the SAME data
3. OLD flat system: Rs.1/late-minute + day-salary per absent beyond 3
4. Dress / I-card: full computed value, own table, waive-none/half/all totals
   (DISCRETIONARY — never added into the mandatory totals)

Constants for the old system are at the top of the file if practice differed.
Nothing in these files is applied to pay — D332 keeps August preview-only.

## Pin

att_scenario.py md5 = 4dc05e332cec8b713f77efb3e284ca18 (new file; deliberately NOT Register-pinned —
analysis tool, no live service reads it; record at the S199 close)
