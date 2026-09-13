#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
salts_refresh.py -- S243_SALTS_REFRESH: Marg's fresh SALT WISE ITEM LIST reaches the salts page by itself.

Runs ON THE VPS (cron, every 10 minutes, 08-22). Until S243 the table purchase_salt_marg -- the "Marg confirms
N done in its list of <date>" line on /finance/purchase/page/salts -- was loaded only by push_salts.py on the
owner's PC. Since S240 every Marg export reaches the server through the one door and a SALT_WISE_ITEM_LIST,
carrying no patient identity, is KEPT in the server archive:

    /root/marg_ingest/archive/SALT_WISE_ITEM_LIST/<YYYY-MM>/SALT_WISE_ITEM_LIST_DEFAULT__<as-on>__<stamp>__<md5-8>.XLS

(marg_router.canonical_name: type_variant __ date __ YYYYmmdd-HHMMSS capture stamp __ md5[:8] . original ext).
This tool takes the NEWEST such file (by the stamp in its name, else its mtime), reads item -> salt exactly as
push_salts.read_marg_salt_list does (same rows, same as-on rule: the stamp's date), and POSTs the same
marg_items / marg_as_on / marg_md5 payload to the finance app's own machine door:

    POST http://127.0.0.1:8106/finance/purchase/api/salts      header X-Finance-Marg: <FINANCE_MARG_TOKEN>

The handler (purchase_app.api_salts -> _store_marg_salts) REPLACES purchase_salt_marg whole and stamps every row
with marg_as_on; the page shows MAX(as_on). No `tasks` key is sent, so Amir's DONE ticks and the doctor's
answers (purchase_salt_task) are never touched. The token is read from the systemd drop-in and never printed.

    --once      apply only if the newest archive file differs from the last applied one (cron mode; silent no-op)
    --force     apply regardless
    --dry-run   read and count, send nothing (prints counts only, no item names)
    --verbose   also say when nothing changed

State: /root/finance/salts_refresh.state.json (last applied file name, md5, as-on, rows, time, server reply).
Exit 0 ok / unchanged; 1 server refused; 2 nothing to send (no file, no token, unreadable, too few rows).

Paths for a mock: env SALTS_REFRESH_ROOT prefixes every default path (archive, ingest dir, drop-in, state);
--archive= --ingest= --dropin= --state= --url= --file= --min-rows= override singly.
"""
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.environ.get("SALTS_REFRESH_ROOT", "")
DEF_INGEST = ROOT + "/root/marg_ingest"
DEF_ARCHIVE = ROOT + "/root/marg_ingest/archive"
DEF_DROPIN = ROOT + "/etc/systemd/system/clinic-finance.service.d/marg_token.conf"
DEF_STATE = ROOT + "/root/finance/salts_refresh.state.json"
DEF_URL = os.environ.get("SALTS_REFRESH_URL", "http://127.0.0.1:8106/finance/purchase/api/salts")
TYPE_DIR = "SALT_WISE_ITEM_LIST"
MIN_ROWS = 100                      # a list this short is a truncated export; the handler would wipe the table with it
STAMP_RE = re.compile(r"__(\d{8})-(\d{6})__")
ASON_RE = re.compile(r"__(\d{4}-\d{2}-\d{2})__")


def _now():
    return dt.datetime.now().replace(microsecond=0)


def read_token(dropin=DEF_DROPIN):
    """FINANCE_MARG_TOKEN from the systemd drop-in written by install_m1a.sh:
    [Service] / Environment=FINANCE_MARG_TOKEN=<token>. Returned, never printed."""
    try:
        with io.open(dropin, "r", encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^\s*Environment=\s*\"?FINANCE_MARG_TOKEN=([^\"\s]+)\"?\s*$", line)
                if m:
                    return m.group(1)
    except OSError:
        return None
    return None


def stamp_of(path):
    """Capture stamp 'YYYYmmdd-HHMMSS' from the archived name, else from the file's mtime (the door sets it)."""
    m = STAMP_RE.search(os.path.basename(path))
    if m:
        return "%s-%s" % (m.group(1), m.group(2))
    return dt.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y%m%d-%H%M%S")


def find_newest(archive=DEF_ARCHIVE):
    """The newest kept SALT_WISE_ITEM_LIST in the server archive, across its month folders."""
    hits = []
    for pat in ("*.XLS", "*.xls", "*.XLSX", "*.xlsx"):
        hits += glob.glob(os.path.join(archive, TYPE_DIR, "*", pat))
        hits += glob.glob(os.path.join(archive, TYPE_DIR, pat))
    hits = sorted(set(hits), key=lambda p: (stamp_of(p), os.path.basename(p)))
    return hits[-1] if hits else None


def as_on_of(path):
    """The list's date: the capture stamp's date (push_salts' rule), else the name's __YYYY-MM-DD__, else mtime."""
    base = os.path.basename(path)
    m = STAMP_RE.search(base)
    if m:
        return "%s-%s-%s" % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8])
    m = ASON_RE.search(base)
    if m:
        return m.group(1)
    return dt.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def _sheet(path, ingest=DEF_INGEST):
    """Open sheet 0 with the vendored reader (/root/marg_ingest/marg_report + its xlrd), as marg_door does."""
    if ingest and ingest not in sys.path:
        sys.path.insert(0, ingest)
    try:
        import marg_report as MR                       # noqa: E402
        return MR._open_sheet(path)
    except ImportError:
        import xlrd                                    # noqa: E402  (same reader, direct)
        return xlrd.open_workbook(path).sheet_by_index(0)


def read_marg_salt_list(path, ingest=DEF_INGEST):
    """item -> salt from the salt-wise report, line for line the rule of push_salts.read_marg_salt_list:
    a salt is a line with only column A filled and no leading number; an item is 'N     NAME' under it.
    Returns (items, as_on)."""
    sh = _sheet(path, ingest)
    cur, out = None, []
    for r in range(3, sh.nrows):
        a = str(sh.cell_value(r, 0)).strip()
        pk = str(sh.cell_value(r, 1)).strip() if sh.ncols > 1 else ""
        if not a or a == "1.0":
            continue
        m = re.match(r"^(\d+)\s{2,}(.+)$", a)
        if m and cur:
            out.append(dict(item=m.group(2).strip(), salt=cur))
        elif not pk and not re.match(r"^\d", a) and a.upper() != "SALT WISE ITEM LIST":
            cur = a.upper()
    return out, as_on_of(path)


def build_payload(path, ingest=DEF_INGEST):
    """Exactly the marg_* keys push_salts.py sends (it rides /vendors with the work list; here they go alone
    to /api/salts, which accepts marg_items without tasks). source/host are informational; the handler
    ignores them."""
    items, as_on = read_marg_salt_list(path, ingest)
    md5 = hashlib.md5(io.open(path, "rb").read()).hexdigest()
    return dict(marg_items=items, marg_as_on=as_on, marg_md5=md5, source=os.path.basename(path), host="vps")


def load_state(state=DEF_STATE):
    try:
        with io.open(state, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(d, state=DEF_STATE):
    os.makedirs(os.path.dirname(state) or ".", exist_ok=True)
    tmp = state + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
    os.replace(tmp, state)


def post(url, body, tok, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def _opt(argv, key, default):
    """The LAST --key=value wins, so a trailing override beats an earlier one."""
    vals = [a.split("=", 1)[1] for a in argv if a.startswith(key + "=")]
    return vals[-1] if vals else default


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry-run" in argv
    force = "--force" in argv
    verbose = "--verbose" in argv
    archive = _opt(argv, "--archive", DEF_ARCHIVE)
    ingest = _opt(argv, "--ingest", DEF_INGEST)
    dropin = _opt(argv, "--dropin", DEF_DROPIN)
    state_p = _opt(argv, "--state", DEF_STATE)
    url = _opt(argv, "--url", DEF_URL)
    min_rows = int(_opt(argv, "--min-rows", str(MIN_ROWS)))
    when = _now().strftime("%d-%m-%Y %H:%M")
    head = "salts_refresh %s " % when

    path = _opt(argv, "--file", None) or find_newest(archive)
    if not path or not os.path.exists(path):
        print(head + "no SALT_WISE_ITEM_LIST in %s -- nothing to send" % os.path.join(archive, TYPE_DIR))
        return 2
    name = os.path.basename(path)
    md5 = hashlib.md5(io.open(path, "rb").read()).hexdigest()

    st = load_state(state_p)
    if not dry:
        st["checked_at"] = _now().isoformat()
        st["newest_seen"] = name
    if not force and not dry and st.get("md5") == md5 and st.get("ok"):
        save_state(st, state_p)
        if verbose:
            print(head + "unchanged: %s (md5 %s) already applied %s -- nothing sent" % (name, md5[:8], st.get("applied_at", "?")))
        return 0

    try:
        body = build_payload(path, ingest)
    except Exception as e:                                     # noqa: BLE001
        print(head + "file=%s could not be read (%s: %s) -- nothing sent" % (name, e.__class__.__name__, str(e)[:120]))
        if not dry:
            save_state(st, state_p)
        return 2
    items, as_on = body["marg_items"], body["marg_as_on"]
    salts = len({i["salt"] for i in items})
    if len(items) < min_rows:
        print(head + "file=%s as_on=%s rows=%d salts=%d -- fewer than %d rows, looks truncated; nothing sent (use --min-rows= to override)"
              % (name, as_on, len(items), salts, min_rows))
        if not dry:
            save_state(st, state_p)
        return 2
    if dry:
        print(head + "DRY RUN file=%s as_on=%s rows=%d salts=%d md5=%s -> would POST %s (nothing sent)"
              % (name, as_on, len(items), salts, md5[:8], url))
        return 0

    tok = read_token(dropin)
    if not tok:
        print(head + "file=%s as_on=%s rows=%d -- no FINANCE_MARG_TOKEN in the drop-in; nothing sent" % (name, as_on, len(items)))
        save_state(st, state_p)
        return 2
    try:
        code, reply = post(url, body, tok)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")[:200]
        except Exception:                                      # noqa: BLE001
            detail = ""
        print(head + "file=%s as_on=%s rows=%d -> server ERROR %s %s" % (name, as_on, len(items), e.code, detail))
        st.update(ok=False, last_error="HTTP %s" % e.code, last_error_at=_now().isoformat())
        save_state(st, state_p)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print(head + "file=%s as_on=%s rows=%d -> server unreachable (%s)" % (name, as_on, len(items), e.__class__.__name__))
        st.update(ok=False, last_error=e.__class__.__name__, last_error_at=_now().isoformat())
        save_state(st, state_p)
        return 1
    try:
        rj = json.loads(reply)
    except ValueError:
        rj = {}
    ok = bool(rj.get("ok")) and code == 200
    st.update(file=name, md5=md5, as_on=as_on, rows=len(items), salts=salts, ok=ok,
              applied_at=_now().isoformat(), reply=dict(status=code, ok=rj.get("ok"), marg_items=rj.get("marg_items"),
                                                        stored=rj.get("stored"), kept=rj.get("kept"), error=rj.get("error")))
    save_state(st, state_p)
    print(head + "file=%s as_on=%s rows=%d salts=%d -> server %s: %s marg_items=%s stored=%s kept=%s%s"
          % (name, as_on, len(items), salts, code, "ok" if ok else "ERROR", rj.get("marg_items"), rj.get("stored"), rj.get("kept"),
             "" if ok else " %s" % (rj.get("error") or reply[:120])))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
