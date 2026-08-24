# S199 LIVE PIN RECORD (recorded as they moved, F-97)

| File | Chain (S199) | Final pin | Kit |
|---|---|---|---|
| `/root/att_scenario.py` (NEW) | `4dc05e332cec8b713f77efb3e284ca18` → `5c4ff00910fcc1cbdcc92e6dc63eb7ff` → **`4dcd19bc02675a07cf0a77fadff6605b`** | v2 | S199_SCEN1 → SCEN3 |
| `/root/staff_register/staff_register.py` | `9087954c8a4a891e8cdd848d6a9d48b2` → `c1fede9f723454d4fe8e01e1a45cc111` → `c9fd063dd3ef53d3eda681aaa344a318` → `d5819b954d23b79a28fa568ea63cc4ff` → **`124c6eb2c5dc03055c70ac427c8347bb`** | v0.7 | SCEN2 → FLOW1 → FLOW2 → FLOW3 |
| `/root/staff_register/salary_engine.py` | `5514918067243e3f39e7074144ee7db4` → `ca37c615a421d984bb2d8a2f89782ca2` → **`bedd468ee7b89b8f0c130d215a42b6d1`** | — | SALFIX → FLOW2 |
| `/root/staff_register/salary_policy.py` (NEW) | `e8cdd22307a59bf6850b43a39680ebd2` → `8cba90f4e08f677dc5329794857dcbed` → **`7f86cc8702b9fa48940e31a5ed2869d4`** | v1.3 | FLOW1 → FLOW2 → FLOW3 |

New stores (deliberately NOT pinned — data, not code): `salary_policy_settings.json` (+ audit
jsonl) · `hold_ledger.jsonl` · lazy tables `pack_approval`, `month_remark` in staff_register.db ·
August dress migration executed (backup `staff_register.db.bak_S199_dress_20260824_060906`).
Owner-side, OUTSIDE the repo (all-staff salary data / drafts): `Salary_Scenario_Playground_S199.xlsx`
+ `_v2` · `Staff_Attendance_Notice_DRAFT{,_v2,_v3}.docx` · `Salary_Sheet_Print_Format_DRAFT.docx`.
All installs gated (D317 chain), every base recovered/verified by hash; two toolchain faults caught
offline (a decorator-eating replace harness — route-200 selftests; a heredoc quote break); no incident.
