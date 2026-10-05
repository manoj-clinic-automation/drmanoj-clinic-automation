# S486_replay — the replay the buying model was chosen on (S295, 05-Oct-2026)

Read-only study on the nightly copy of `finance.db` (`D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` of 05-Oct, unpacked to `~/fn.db`).
`load.py` builds, per medicine, the daily sales, the effective purchase lines and the day-end stock (Marg's closing of 04-10 rolled back by
purchases and sales); `sim.py` runs a policy day by day over the shop's real sales from the real stock of 03-May; `final.py` prints `RESULT.txt`.
No person's name or number is read or written. FIXED in these scripts is a re-implementation of the engine's rules, not the engine's code;
`replay_s486.py` in the kit replaces the re-implementation with the kit's own pure functions (brief S486, B.0a and walk B.9.7).
