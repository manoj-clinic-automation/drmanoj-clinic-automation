#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s461.py -- S461_FINANCE_TIDY (session 292, 03-Oct-2026): four display/hygiene edits to finance_app.py.

Built from the real file (/root/finance/finance_app.py at 40aef4df, as S457 left it) -- every anchor below was read
there, each must be found EXACTLY as many times as stated, and the result is one predicted md5. Anything else: the
file is left byte-for-byte as it was and this exits 1.

  1  /finance/health -- a row's label, words and hint are escaped before they reach the page (S291 whole read, lead 1).
  2  --selftest -- its fake scans go to a throwaway folder, and what it made in temp is removed at exit even when it
     aborts: a whole copy of the live database was left in temp before (lead 6).
  3  the 14 print-only mounts record their failure in _MOUNT_FAILED, and the 'mounts' health row shows the reason
     (lead 7).
  4  the three unguarded ?days= parses answer the default instead of a 500.

Nothing here changes a figure, a row, a gate or who sees what.   usage: apply_s461.py <path to finance_app.py>
"""
import hashlib
import re
import sys

FROM = "40aef4dfe976a596c81be46da1fbb429"

EDITS = []          # (name, old, new, times)


def ed(name, old, new, times=1):
    EDITS.append((name, old, new, times))


# ------------------------------------------------------------------ 4 · ?days=
ed("days helper",
   'def rupees(',
   'def _days_arg(default, cap):\n'
   '    """S461: ?days= as a whole number from 1 to cap. Anything else is the default -- never a 500."""\n'
   '    try:\n'
   '        return max(1, min(int(cap), int(request.args.get("days", default) or default)))\n'
   '    except (TypeError, ValueError, OverflowError):\n'
   '        return int(default)\n'
   '\n\n'
   'def rupees(')
ed("days: orthotics",
   '    days_n = min(int(request.args.get("days", "90") or 90), 366)\n',
   '    days_n = _days_arg(90, 366)                                   # S461\n')
ed("days: the two day lists",
   '        a = (today() - dt.timedelta(days=int(request.args.get("days", "60")))).isoformat()\n',
   '        a = (today() - dt.timedelta(days=_days_arg(60, 3660))).isoformat()   # S461\n', 2)

# ------------------------------------------------------------------ 2 · selftest
ed("selftest cleanup function",
   '# ----------------------------------------------------------------- selftest\n\ndef selftest():\n',
   '# ----------------------------------------------------------------- selftest\n\n'
   'def _s461_selftest_cleanup(paths):\n'
   '    """S461: remove what a --selftest run made in temp. Registered with atexit, so a run that ABORTS cleans up\n'
   '    too -- before this an abort left a whole copy of the live database in temp. Only paths the run itself made\n'
   '    (mkstemp / mkdtemp) are passed in, and anything outside the temp folder is refused here as well."""\n'
   '    import shutil\n'
   '    import tempfile\n'
   '    _root = os.path.realpath(tempfile.gettempdir()) + os.sep\n'
   '    for _p in list(paths or []):\n'
   '        try:\n'
   '            if not os.path.realpath(_p).startswith(_root):\n'
   '                continue\n'
   '            if os.path.isdir(_p):\n'
   '                shutil.rmtree(_p, ignore_errors=True)\n'
   '            elif os.path.exists(_p):\n'
   '                os.remove(_p)\n'
   '        except OSError:\n'
   '            pass\n'
   '\n\n'
   'def selftest():\n')
ed("selftest globals",
   '    global DB_PATH, ALLOW_HEADER_AUTH, LEDGER_JSONL\n    import shutil\n    import tempfile\n',
   '    global DB_PATH, ALLOW_HEADER_AUTH, LEDGER_JSONL, SCAN_DIR     # S461: + SCAN_DIR\n'
   '    import shutil\n    import tempfile\n')
ed("selftest sandbox",
   '    shutil.copyfile(live_db, tmp_db)\n    DB_PATH = tmp_db\n',
   '    shutil.copyfile(live_db, tmp_db)\n    DB_PATH = tmp_db\n'
   '    # S461: the fake scans this run uploads went into the LIVE scan folder, and an abort left the database copy\n'
   '    # and the smoke folders in temp. Scans now go to a throwaway folder; everything made here goes at exit.\n'
   '    import atexit\n'
   '    _s461_scan_prev = SCAN_DIR\n'
   '    SCAN_DIR = tempfile.mkdtemp(prefix="smoke_scans_")\n'
   '    _s461_made = [tmp_db, tmp_db + "-wal", tmp_db + "-shm", SCAN_DIR]\n'
   '    atexit.register(_s461_selftest_cleanup, _s461_made)\n')
ed("selftest ledger folder",
   '    _f6_ledger_dir = tempfile.mkdtemp(prefix="smoke_ledger_")\n',
   '    _f6_ledger_dir = tempfile.mkdtemp(prefix="smoke_ledger_")\n'
   '    _s461_made.append(_f6_ledger_dir)                             # S461\n')
ed("selftest renewals folder",
   '    _rn_dir = tempfile.mkdtemp(prefix="smoke_renewals_")\n',
   '    _rn_dir = tempfile.mkdtemp(prefix="smoke_renewals_")\n'
   '    _s461_made.append(_rn_dir)                                    # S461\n')
ed("selftest teardown",
   '    DB_PATH = live_db\n    try:\n        os.remove(tmp_db)\n    except OSError:\n        pass\n',
   '    DB_PATH = live_db\n    SCAN_DIR = _s461_scan_prev                                    # S461\n'
   '    try:\n        os.remove(tmp_db)\n    except OSError:\n        pass\n')

# ------------------------------------------------------------------ 3 · mounts
ed("mounts row: the reason",
   '            add("mounts", "Parts of the finance app that did not load", "bad",\n'
   '                "%d of %d did not load: %s" % (len(_mf), _all, ", ".join(_mf)),\n'
   '                "Every other page keeps working. The reason is in the journal of clinic-finance.")\n',
   '            _why = "; ".join("%s: %s" % (_n, _w)                   # S461: the stored reason, shown\n'
   '                             for _n, _w in (globals().get("_MOUNT_FAILED") or []))[:400]\n'
   '            add("mounts", "Parts of the finance app that did not load", "bad",\n'
   '                "%d of %d did not load: %s" % (len(_mf), _all, ", ".join(_mf)),\n'
   '                "Every other page keeps working. " + (("Why: %s. " % _why) if _why else "")\n'
   '                + "The full reason is in the journal of clinic-finance.")\n')

MOUNT_RE = re.compile(
    r'^except Exception as (_ex_[a-z]+):( +# noqa: BLE001)\n'
    r'    print\("([a-z_]+) NOT mounted: %s" % \1, file=sys\.stderr\)\n', re.M)
MOUNT_N = 14


def mounts(src):
    n = [0]

    def rep(m):
        n[0] += 1
        return ('except Exception as %s:%s\n'
                '    _MOUNT_FAILED.append((\'%s\', repr(%s)[:200]))   # S461: as the thirteen above it\n'
                '    print("%s NOT mounted: %%s" %% %s, file=sys.stderr)\n'
                % (m.group(1), m.group(2), m.group(3), m.group(1), m.group(3), m.group(1)))
    out = MOUNT_RE.sub(rep, src)
    return out, n[0]


# ------------------------------------------------------------------ 1 · /finance/health
ed("health: escape helper",
   '    def _delink(txt):\n        return re.sub(r"</?a\\b[^>]*>", "", txt or "")\n',
   '    def _delink(txt):\n        return re.sub(r"</?a\\b[^>]*>", "", txt or "")\n'
   '\n'
   '    # S461: a row\'s words are TEXT. The Reception PC row carries words that PC supplies, and a hint that named\n'
   '    # "<the medical address>" was swallowed by the browser as a tag. Everything is escaped; the one thing a hint\n'
   '    # may still carry is a whole, plain link to a page of this site.\n'
   '    def _hx(txt, links=False):\n'
   '        s = html_escape(txt)\n'
   '        if links:\n'
   '            s = re.sub(r"&lt;a href=&quot;(/[A-Za-z0-9_./#?=%-]*)&quot;&gt;(.*?)&lt;/a&gt;",\n'
   '                       r\'<a href="\\1">\\2</a>\', s)\n'
   '        return s\n')
ed("health: the row",
   '        hint = _delink(c["hint"]) if linked else c["hint"]\n',
   '        hint = _hx(_delink(c["hint"])) if linked else _hx(c["hint"], links=True)   # S461\n')
ed("health: label and words",
   '                 % (cc, cicon, c["label"], c["detail"],\n',
   '                 % (cc, cicon, _hx(c["label"]), _hx(c["detail"]),            # S461\n')
ed("health: the culprits line",
   '    sub = ((" &#183; ".join(h.get("culprits") or [])) + " &#183; "\n',
   '    sub = ((" &#183; ".join(html_escape(x) for x in (h.get("culprits") or []))) + " &#183; "   # S461\n')


def apply(src):
    for name, old, new, times in EDITS:
        got = src.count(old)
        if got != times:
            raise SystemExit("!! anchor '%s' found %d time(s), expected %d - nothing written" % (name, got, times))
        src = src.replace(old, new)
    src, n = mounts(src)
    if n != MOUNT_N:
        raise SystemExit("!! %d print-only mounts found, expected %d - nothing written" % (n, MOUNT_N))
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s461.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d edits + %d mounts; %+d bytes)"
          % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), MOUNT_N, len(out) - len(raw)))


if __name__ == "__main__":
    main()
