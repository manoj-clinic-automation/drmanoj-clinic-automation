# S825_ARRIVALS_BY_THE_BILL — a scanned bill counts as arrived only what it carries (Sanjeevni; built S455, rebuilt S457, 14-Nov-2026) · F-1220 (D883, D976)

**The fault.** When a bill scan is tied to a purchase order, the stock figure (`stock_figure.scan_lines`) presumed that EVERY open line of that order had arrived — the bill's own items were never read. The owner's *Arrived but not in Marg* mixed presumed arrivals with real ones (Yuvika's sizes; Kedar's FLACORT 6, which Kedar had said no to), and the engine counted them as stock until Marg's purchase entry.

**The kit (three files, rebuilt on the box from the live bytes by `make_s825.py`, exact counted anchors):**
- `/root/finance/order_track.py` — `size_of()` reads the size words a name prints (SMALL/MEDIUM/LARGE = S/M/L, EXTRA LARGE = XL, XXX = XXXL, 2XL = XXL; a letter after a number — 10'S — is a count; an initial before the first word — L.S. BELT — is no size; UNIVERSAL no size). The tracker's matcher `name_score()` gives 0 when both names print different sizes; `match_lines()` also refuses, for an **Orthotics** item, a size printed on one side only. On the real data: Orthotic item pairs that matched across sizes 229 → 57 (the 57 are one item spelt two ways or another brand); the 316 medicines: no change; the 104 learnt dealer spellings: no pair lost.
- `/root/finance/stock_figure.py` — `s825_bill_judged()`: for each scan-tied open line, whether the bill **tied to its order** carries it (the scan's clearer copy, usable as the tracker counts usable, as Claude read it), by the tracker's own matcher. `scan_lines()` leaves out a line the bill does not carry.
- `/root/finance/order_rules.py` — on the count basis such a line stays **on order** (on the way), so the engine does not propose it again.
- Not judged — the old reading stands: a tied scan not read yet, a scan to redo, a scan older than `order.track_since`, the scan store unreachable, any failure. READ ONLY (it calls nothing that writes; checked on a read-only connection). No database change; no screen changes its layout; the tracker's own "on bill / not seen" notes become stricter about sizes.

**Left as it was, and said so:** the quantity counted is still the ordered packs (a bill's quantity is not trusted for units); `purchase_app._in_transit` (the snapshot fallback) is untouched; a medicine missing from the bill because the matcher does not recognise its spelling (TENDOZAC TABLET 10'S, MAGMAG SACHET 15GM) is judged *not carried* — the safe side: it stays on order, so the engine does not propose it again. It stays on order only within the on-order window (`order.on_order_days`, or the supplier's interval + lead under S644); an order older than that, still unanswered in Marg, is counted nowhere until Marg's purchase entry (as any unanswered order already was).

**Known limits (the review's should-fixes, S459):**
- **Orthotics, a size printed on one side only:** a bill that prints the size apart from the name (a size column) reads as "no size" — the line is then judged *not carried* and stays on order (the safe side; the tracker's note says "not seen"). The 229 → 57 measure is on the store's real names.
- **The fresh tracker context per call** (`order_rules._s825_not_carried`): the engine calls it a few times a run, never per item; `proof_s825.py` times the on-order read on the box and prints it on the PROOF line, old and new.
- **`order_sheet._s619_pick`** (which waiting order a scan belongs to) uses the same matcher: an orthotic scan now names fewer lines across sizes, so a doubtful tie is not made — the order stays "sent" (on the way), never wrongly "received".
- **The tables fallback** (`order.engine_source = tables`; the live setting is `spine`): `purchase_app._in_transit` counts a tied order's lines as arrived from its "received" mark, so there a not-carried line of an item with no shelf count would be counted twice (in transit and on order). Not the live path; to be settled before the fallback is ever switched on (Runbook §2B).

**Bench.** `walk_s825.py` (a copy of the 14-Nov database, made-up tied orders and scan store): 27 checks green on the new files; its control on the live files 15 red. `proof_s825.py` on the box's own databases (read-only) lists every scan-tied open line before and after. `rehearse_s825.sh` on a stand-in root.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s825kit && cp -rp /root/deploy/repo/deploy_kits/S825_ARRIVALS_BY_THE_BILL /tmp/s825kit && bash /tmp/s825kit/install_S825_ARRIVALS_BY_THE_BILL.sh

**Undo:** the installer prints the one line (the three backups `*.bak_S825_*`).
