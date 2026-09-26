# RETIRED -- 26-Sep-2026, S282, on the weekly auditor's finding AF-23 (21-Sep-2026)

This folder held a copy of `portal.py` whose access-control path still carried the fault closed on the box at S239
(F-98 / AF-12: the 10-year device cookie opening the surgical case pack without login). The live file, pinned in the
current `live_pins_*.txt`, has the fix; this copy never did, and nothing in the tree marked it as superseded -- so a
future patcher rebuilding from it would silently reopen the fault. F-472 stands: no patcher is built from anything but
the real file read whole from the box.

**Retired in place, nothing deleted:** the bytes are at `portal.py.RETIRED_S282_AF23` (md5 2cc42372867bad90a9cec455f81bcd10) for the record.
The live portal is `/root/portal/portal.py` on the VPS; its current pin is in `deploy_kits/KB_canon_all/live_pins_*.txt`.
