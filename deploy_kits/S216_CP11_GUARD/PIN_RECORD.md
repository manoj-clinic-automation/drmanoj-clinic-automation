# S216_CP11_GUARD — live pin record
*Recorded at install, 01-Sep-2026 ~15:57 IST (F-97: as the pin moves, not at the close).*

| file on the box | before | after | == kit bytes |
|---|---|---|---|
| `/root/wa/casepack/casepack_page.html` | `903b915e…` (S215) | **`1e4d25d4…`** | **yes** |
| `/root/portal/casepack_portal.py` | `3146bdbf…` | `3146bdbf…` | unchanged — page-only kit |

Backup left on the box, named, not deleted:
`/root/wa/casepack/casepack_page.html.bak_S216_CP11_20260901_155717`

Owner-run selftest on the box: **32/32**.
Install one-paste: `cd /root/deploy/repo && git pull && bash deploy_kits/S216_CP11_GUARD/install_cp11.sh`

**Register action owed at the close:** move the `casepack_page.html` row
`903b915e…` → `1e4d25d4…` in the KB Register (v5.64 at the S215 close) and
regenerate `live_pins` after the manifest (A8).

**LIVE-SHAPE WALK: DONE, 01-Sep-2026, owner-run on the served page.**
Walk A (elective THR + polio `thr_fnf` → must refuse, correct in one click) —
**OK**. Walk B (plain THR, no fracture signal → must NOT block) — **OK**.
The kit is proven live. Nothing else is owed on step 1.

Owner observations at the walk, both already on the CP-1.1 list and NOT
regressions of this kit: the dropdown contrast (step 2) and the polio module's
heading-plus-fragments formatting (step 4).
