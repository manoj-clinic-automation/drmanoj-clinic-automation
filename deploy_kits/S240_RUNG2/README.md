# S240_RUNG2 — T1 (the owner's discount rulings) + Rung 2 (the bill discount on its lines)

**Built 11-Sep-2026, Session 240, on the owner's "GO".** Nothing on any screen changes: Rung 3 — gross
becomes net, side by side — is the owner's word, later.

1. **T1** — the 93 rulings of 09-Sep (kit `S236_DISCOUNT`, published, never installed until now), with its
   own gate, backup and 43 selftests.
2. **Rung 2** — `sale_attribution.py`: each bill's discount is put on the line it belongs to, by the rulings.
   Lines valued by the spine's own money model (the line prints the rate per pack). A bill whose lines do
   not add up to its printed gross is not attributed. An unruled line is never given a discount it cannot
   be shown to carry — that money stays on the bill, counted.

**Install — one line on the VPS, after the publish:**

    bash /root/deploy/vps_deploy.sh S240_RUNG2

**Undo:** delete the two `# S240_RUNG2` cron lines; the three tables (`sale_line_discount`,
`sale_bill_attrib`, `sale_attrib_run`) are derived and read by nothing. T1's own undo line is printed by it.
