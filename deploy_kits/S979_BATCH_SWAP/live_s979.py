#!/usr/bin/env python3
"""live_s979.py -- S979_BATCH_SWAP: the proof on COPIES of the live database, and the read after the install (counts and item names only).
  cd CODE && live_s979.py run COPY.db SPINE ARCHIVE OUT.json   the watch's own run (this folder's expiry_watch.py) on a COPY; the lists dumped
  live_s979.py compare OLD.json NEW.json                       the old and new runs' lists and batches identical; the new one has the cases
  cd /root/finance && live_s979.py read LIVE.db                read only: the cases, the owner's section, Darpan's card"""
import json
import os
import sqlite3
import sys

os.environ.setdefault("ORDER_PUSH_STUB", "/dev/null")        # a run on a copy never pushes (it never does; belt and braces)
_ME = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [os.getcwd()] + [p for p in sys.path if os.path.abspath(p or ".") not in (_ME, os.getcwd())]   # the folder's files, never the kit's


def dump(db, out):
    con = sqlite3.connect(db)
    q = lambda sql: [list(r) for r in con.execute(sql)]       # noqa: E731
    rid = con.execute("SELECT MAX(id) FROM stock_expiry_run").fetchone()[0]
    d = dict(lines=q("SELECT section, part, k20, item, batch, expiry, units, pack, info FROM stock_expiry_line WHERE run_id=(SELECT MAX(id) FROM stock_expiry_run) ORDER BY section, seq"),
             batches=q("SELECT k20, batch, expiry, units, printed, sold, bought, new, pack FROM stock_batch_now ORDER BY k20, batch, expiry"),
             run=q("SELECT ok, export_as_on, counts FROM stock_expiry_run WHERE id=%d" % (rid or 0)),
             cases=q("SELECT k20, old_batch, old_expiry, paper_units, new_batch, state FROM expiry_swap_case ORDER BY k20")
             if con.execute("SELECT 1 FROM sqlite_master WHERE name='expiry_swap_case'").fetchone() else None)
    con.close()
    json.dump(d, open(out, "w"))
    return d


def main(a):
    if a[0] == "run":
        import expiry_watch as EW                             # noqa: PLC0415 -- this folder's
        logs = []
        rc = EW.run(a[1], a[2], a[3], log=logs.append)
        d = dump(a[1], a[4])
        sw = [l for l in logs if "batch_swap" in l or "batch swap" in l]
        print("RUN rc=%s ok=%s lines=%d batches=%d cases=%s swaplog=%s" % (rc, (d["run"] or [[0]])[0][0], len(d["lines"]), len(d["batches"]),
                                                                       "none" if d["cases"] is None else len(d["cases"]), (sw[-1] if sw else "-")[:160]))
        return 0
    if a[0] == "compare":
        A, B = json.load(open(a[1])), json.load(open(a[2]))
        print("LIVE-SHAPE same_lists=%s same_batches=%s old_cases=%s new_cases=%s items=%s" % (
            A["lines"] == B["lines"], A["batches"] == B["batches"], "none" if A["cases"] is None else len(A["cases"]),
            "none" if B["cases"] is None else len(B["cases"]), ",".join(c[0] for c in (B["cases"] or []))[:200]))
        return 0
    if a[0] == "read":
        import batch_swap as BS                               # noqa: PLC0415
        con = sqlite3.connect("file:%s?mode=ro" % a[1], uri=True)
        try:
            rows = BS._rows(con)
            st = {}
            for c in rows:
                st[c["state"]] = st.get(c["state"], 0) + 1
            v = BS.darpan_view(con)
            h = BS.owner_section(con)
            print("READ ok=True kit=%s cases=%d states=%s ask=%d bills=%s red=%d section=%s items=%s" % (
                BS.KIT, len(rows), json.dumps(st, sort_keys=True), len(v.get("ask") or []), len((v.get("bills") or {}).get("ids") or []),
                len(BS.needs_you(con) and [1] or []), h.startswith('<details class="s979">'), ",".join(c["item"] for c in rows)[:200]))
            return 0
        except Exception as ex:                               # noqa: BLE001
            print("READ ok=False %s: %s" % (type(ex).__name__, str(ex)[:160]))
            return 1
        finally:
            con.close()
    print("usage: run | compare | read")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
