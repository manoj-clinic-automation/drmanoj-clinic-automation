"""make_s850.py <code dir holding the FROM files> <out dir> -- kit S850_MARG_IS_RIGHT: three files patched on exact anchors (each once), the
new marg_right.py beside them (copied from this script's folder). Every FROM file is checked against its pin first."""
import hashlib, os, shutil, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"scan_ask.py": "41adf66bceb6e7ef31f25181c8a2da71", "purchase_app.py": "b789e3791684743969bbf1d25e1b3f92",
        "item_ledger.py": "49768145965c2bbd81bdf56ab5ca9f74"}
P = {}
P["scan_ask.py"] = [(
    'VERSION = "S849-SCAN-ASK-1.0"',
    'VERSION = "S849-SCAN-ASK-1.1"                       # S850 (F-1440): a bill named by its number and its total'), (
    '    out.sort(key=lambda c: (-(c["agree"]), -int(c["tail"]), -int(c["total"]), c["gap"]))\n'
    '    for c in out:\n'
    '        c["best"] = False\n'
    '    if out:\n'
    '        top = out[0]\n',
    '    for c in out:                                          # S850 (F-1440): the number read AND the total within Rs 2 -- or, the paper\'s\n'
    '        c["numtot"] = bool(c["tail"] and (c["total"] or (not total_p and c["gap"] == 0)))   # total not read, the same date\n'
    '    out.sort(key=lambda c: (-int(c["numtot"]), -(c["agree"]), -int(c["tail"]), -int(c["total"]), c["gap"]))\n'
    '    for c in out:\n'
    '        c["best"] = False\n'
    '        c["why"] = "lines"\n'
    '    nt = [c for c in out if c["numtot"]]                   # ... name the bill, whatever the read lines say (B-0122 -> Marg bill 3499)\n'
    '    if len(nt) == 1:\n'
    '        nt[0]["best"] = True\n'
    '        if not (nt[0]["n_scan"] > 0 and nt[0]["agree"] == nt[0]["n_scan"]):\n'
    '            nt[0]["why"] = "numtot" if nt[0]["total"] else "numdate"\n'
    '    elif out:                                              # none, or several (duplicate Marg entries): the old rule\n'
    '        top = out[0]\n'), (
    '                      "every line read on the scan agrees in item, batch and rate" if best["n_scan"] else "its number or total agrees", twice))',
    '                      ("its bill number and its %s agree (%d of %d lines read on the scan agree — the scan misread the rest)"\n'
    '                       % ("total" if best.get("why") == "numtot" else "date (the paper\'s total was not read)", best["agree"], best["n_scan"])\n'
    '                       if best.get("why") in ("numtot", "numdate") and best["n_scan"] else           # S850 (F-1440)\n'
    '                       "every line read on the scan agrees in item, batch and rate" if best["n_scan"] else "its number or total agrees"), twice))'), (
    '        same_w = "dawai, batch aur rate same hain:" if best["n_scan"] else "bill number ya total same hai:"',
    '        same_w = (("bill number aur total same hai:" if best.get("why") == "numtot" else "bill number aur tareekh same hai:" if best.get("why") == "numdate"\n'
    '                   else "dawai, batch aur rate same hain:")   # S850 (F-1440)\n'
    '                  if best["n_scan"] else "bill number ya total same hai:")')]
P["purchase_app.py"] = [(
    '    return _page("Scan reading against Marg — %s" % _month_name(month), body)\n',
    '    _s850_js = ""\n'
    '    try:                                                       # S850 (D993 b-c, D995): the line verdicts and the corrections kept\n'
    '        import marg_right as _s850                            # noqa: PLC0415 -- beside this file\n'
    '        body += _s850.cards_html(con, month, request.script_root + _url_prefix)\n'
    '        _s850_js = _s850.JS\n'
    '    except Exception as _e850:                                 # noqa: BLE001 -- the page as it was before S850\n'
    '        print("S850 cards failed: %r" % (_e850,), file=_sys_s781.stderr)\n'
    '    return _page("Scan reading against Marg — %s" % _month_name(month), body, _s850_js)\n')]
P["item_ledger.py"] = [(
    '    L = ledger(con, sp, key, d1, d2, HR)\n',
    '    L = ledger(con, sp, key, d1, d2, HR)\n'
    '    try:                                                      # S850 (D993 d): each purchase line carries its scan line\'s verdict\n'
    '        import marg_right as _s850                           # noqa: PLC0415 -- beside this file\n'
    '        _s850.annotate_ledger(con, it, L)\n'
    '    except Exception as _e850:                                # noqa: BLE001 -- the ledger as before\n'
    '        print("S850 ledger verdicts failed: %r" % (_e850,), file=sys.stderr)\n'), (
    'esc(U.fmt(-e["u"])) if e["u"] < 0 else "", esc(U.fmt(e["bal"])), btn))',
    'esc(U.fmt(-e["u"])) if e["u"] < 0 else "", esc(U.fmt(e["bal"])), btn + (e.get("s850_html") or "")))')]
TAIL = {"purchase_app.py": '''


# ---- S850_MARG_IS_RIGHT (17-Nov-2026, Sanjeevni session 476; D993 b-c, D995): "Marg is right" on one line of "Scan reading against Marg" -----
@bp.route("/api/s850/line", methods=["POST"])
def api_s850_line():
    """The doctor's tap on a scan line of a bill whose totals differ: {a: scan id, k: line key, do: right | undo}."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
    b = request.get_json(silent=True) or {}
    try:
        sid = int(b.get("a") or 0)
    except (TypeError, ValueError):
        sid = 0
    if sid <= 0 or not str(b.get("k") or ""):
        return jsonify(ok=False, error="bad_request", message="Which line?"), 400
    con = _db()
    try:
        import marg_right as _s850                            # noqa: PLC0415
        ok, msg, code = _s850.tap(con, _who(u), sid, str(b.get("k")), str(b.get("do") or "right"))
    except Exception as e:                                    # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        ok, msg, code = False, "Not saved (%s)." % e.__class__.__name__, 503
    return jsonify(ok=ok, message=msg), code
# ---- S850 end ---------------------------------------------------------------------------------------------------------------------------
'''}
os.makedirs(OUT, exist_ok=True)
for n, pin in FROM.items():
    b = open(os.path.join(SRC, n), "rb").read()
    assert hashlib.md5(b).hexdigest() == pin, "%s is not at its FROM pin" % n
    t = b.decode("utf-8")
    for a, r in P.get(n, []):
        assert t.count(a) == 1, "%s: anchor not found exactly once: %r" % (n, a[:70])
        t = t.replace(a, r, 1)
    if n in TAIL:
        t = t.rstrip("\n") + TAIL[n]
    open(os.path.join(OUT, n), "wb").write(t.encode("utf-8"))
    print(n, hashlib.md5(t.encode("utf-8")).hexdigest())
here = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(OUT) != here:
    shutil.copy(os.path.join(here, "marg_right.py"), os.path.join(OUT, "marg_right.py"))
print("marg_right.py", hashlib.md5(open(os.path.join(OUT, "marg_right.py"), "rb").read()).hexdigest())
