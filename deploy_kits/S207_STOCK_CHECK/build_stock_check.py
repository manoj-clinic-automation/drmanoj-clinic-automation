#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""build_stock_check.py — regenerate the staff stock-check page from the archive.

S207. Reads the newest Marg exports out of MargArchive and writes a single
self-contained HTML file that runs on a phone with no server and no install.

    python3 build_stock_check.py [ARCHIVE_DIR] [-o OUT.html]

Exit 0 = written.  1 = a real failure.  2 = the archive is not reachable.

WHY IT IS A GENERATOR AND NOT A HAND-MADE FILE
    The owner asked for it to "keep this updated with latest data". A page
    edited by hand goes stale the day after it is written and nobody can tell
    by looking. This reads whatever is in the archive today, so refreshing the
    count sheet is one command after any new stock export.

THE ONE RULE THAT MATTERS IN HERE
    Marg's UNIT LABEL is not trusted. 27 orthotics -- arm slings, clavicle
    braces -- are labelled TAB. in the item master. The PACK SIZE decides
    whether a thing is counted in strips or in pieces, and nothing else does.
    That rule is in units.py, in the reconciliation, and now here.

AND THE F-235 GUARD
    A category-filtered export (orthotics only, 81 rows) carries the SAME
    store name, the SAME as-on date and a byte-identical header to the full
    377-row one -- Marg records no category marker anywhere. So the full
    universe is taken as the LARGEST export for the newest date, never the
    latest file, and the filtered one is used only to flag which items are
    orthotic.
"""
import argparse, collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE"))
DEF_ARCHIVE = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
DEF_OUT = os.path.expanduser("~/mnt/Downloads/margsync/_analysis/STOCK_CHECK.html")
FILTERED_MAX = 200          # an export smaller than this is a filtered subset


def expiry_key(e):
    """'6/28' -> (2028, 6). Unparseable sorts last, never first — an unknown
    expiry must never be presented to staff as the one to sell next."""
    m = re.match(r"(\d{1,2})\s*/\s*(\d{2,4})", (e or "").strip())
    if not m:
        return (9999, 99)
    mm, yy = int(m.group(1)), int(m.group(2))
    return (2000 + yy if yy < 100 else yy, mm)


def as_on_key(s):
    """Marg writes dd-mm-yyyy, and comparing that as TEXT is quietly wrong:
    "31-03-2026" > "27-08-2026" because "31" > "27". This scan was scoped to
    two month folders and so never met the problem; push_snapshot.py scanned
    them all and picked March over August on its first real run. Same key, both
    places. An unreadable date sorts FIRST and can never win."""
    t = (s or "").strip().replace("/", "-").split("-")
    if len(t) == 3:
        try:
            d, m, y = (int(x) for x in t)
            if y > 1900 and 1 <= m <= 12:
                return (y, m, d)
        except ValueError:
            pass
    return (0, 0, 0)


def newest_full(archive, months=None):
    """The largest WHOLE STORES export for the newest as-on date. See F-235."""
    import marg_stock as MS
    best = None
    pat = os.path.join(archive, "STOCK_CLOSING", "*", "*")
    for p in glob.glob(pat):
        try:
            r = MS.read_closing(p)
        except Exception:
            continue
        if r.get("store") != "WHOLE STORES":
            continue
        k = (as_on_key(r.get("as_on")), len(r["rows"]))
        if best is None or k > (as_on_key(best.get("as_on")), len(best["rows"])):
            best = r
    return best


def orthotic_set(archive, months=("2026-08",)):
    """Items in the ORTHOTICS category, from the filtered export if one exists."""
    import marg_stock as MS
    out = set()
    for mo in months:
        for p in glob.glob(os.path.join(archive, "STOCK_CLOSING", mo, "*")):
            try:
                r = MS.read_closing(p)
            except Exception:
                continue
            if r.get("store") == "WHOLE STORES" and len(r["rows"]) < FILTERED_MAX:
                out |= {x["item"] for x in r["rows"]}
    return out


def batches(archive):
    """{item: {batch: earliest expiry seen}} from every purchase export."""
    import marg_purchase as MP
    bat = collections.defaultdict(dict)
    for p in sorted(glob.glob(os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.XLS"))):
        try:
            rep = MP.read_purchase(p)
        except Exception:
            continue
        for r in rep["rows"]:
            b = (r.get("batch") or "").strip()
            if not b:
                continue
            e = (r.get("expiry") or "").strip()
            prev = bat[r["item"]].get(b)
            if prev is None or expiry_key(e) < expiry_key(prev):
                bat[r["item"]][b] = e
    return bat


def build(archive):
    full = newest_full(archive)
    if full is None:
        return None, "no WHOLE STORES closing export found"
    orth = orthotic_set(archive)
    bat = batches(archive)
    items, seen = [], set()
    for row in full["rows"]:
        n = row["item"]
        if not n or n.upper() in ("DESCRIPTION", "TOTAL") or n in seen:
            continue
        seen.add(n)
        bs = sorted(bat.get(n, {}).items(), key=lambda kv: expiry_key(kv[1]))
        items.append({"n": n,
                      "p": row["packing"] or "1*1",
                      "s": int(row["pack_size"] or 1),
                      "u": (row["unit"] or "").strip(),
                      "q": int(row["units"] or 0),
                      "o": 1 if n in orth else 0,
                      "b": [[k, v] for k, v in bs[:8]]})
    items.sort(key=lambda x: x["n"])
    return {"as_on": full.get("as_on"), "items": items}, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="regenerate the staff stock-check page")
    ap.add_argument("archive", nargs="?", default=DEF_ARCHIVE)
    ap.add_argument("-o", "--out", default=DEF_OUT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    if not os.path.isdir(a.archive):
        print("ARCHIVE NOT REACHABLE -- %s" % a.archive)
        print("Connect the Downloads folder, or pass the archive path as argument 1.")
        return 2
    data, err = build(a.archive)
    if err:
        print("FAILED: %s" % err)
        return 2
    tpl = os.path.join(HERE, "stock_check_template.html")
    with open(tpl, "r", encoding="utf-8") as fh:
        t = fh.read()
    if "__STOCK_DATA__" not in t:
        print("FAILED: the template has no __STOCK_DATA__ placeholder")
        return 1
    body = t.replace("__STOCK_DATA__", json.dumps(data, separators=(",", ":")))

    # ---- the page has to be able to rebuild ITSELF -------------------------
    # Sharing a count means publishing a new version of this artifact, and a
    # publish hands over a COMPLETE document. So the page carries its own
    # source, base64'd, with two holes in it: one for the shared counts and
    # one for the source itself. Filling the second hole with the same base64
    # string reproduces the carrier exactly, so version 40 is still able to
    # publish version 41.
    #
    # The head/body split is real, not decorative: a <title> left in the body
    # is not reliably honoured, and without the viewport meta the whole thing
    # renders at desktop width on a phone -- which is the only width that
    # matters here.
    cut = body.find("</style>")
    if cut < 0:
        print("FAILED: the template has no </style> to split head from body")
        return 1
    cut += len("</style>")
    head, rest = body[:cut], body[cut:]
    full = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            + head + "\n</head>\n<body>\n" + rest + "\n</body>\n</html>\n")
    import base64
    skel = base64.b64encode(full.encode("utf-8")).decode("ascii")
    # COUNT=1, and it matters. Python's str.replace() replaces EVERY
    # occurrence, and each token appears twice: once as the carrier the data
    # goes into, and once inside the JavaScript line that refills that carrier
    # when the page republishes itself. Replacing both turned
    #     skel.replace("__SHARED__", ...)
    # into
    #     skel.replace("{"e":{}}", ...)
    # and the whole script died with "missing ) after argument list" -- the
    # gate rendered no buttons at all. The carrier comes first in the file, so
    # a count of 1 hits the right one.
    html = body.replace("__SHARED__", '{"e":{}}', 1).replace("__SKEL__", skel, 1)
    if html.count("__SHARED__") != 1 or html.count("__SKEL__") != 1:
        print("FAILED: expected exactly one surviving token of each (the JS "
              "that refills them); got %d SHARED, %d SKEL"
              % (html.count("__SHARED__"), html.count("__SKEL__")))
        return 1
    for tok in ('id="SHARED" type="application/json">__',
                'id="SKEL" type="text/plain">__'):
        if tok in html:
            print("FAILED: the %s carrier was not filled" % tok)
            return 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    n = len(data["items"])
    print("stock as on %s" % data["as_on"])
    print("  items           : %d" % n)
    print("  holding stock   : %d" % sum(1 for i in data["items"] if i["q"] > 0))
    print("  orthotic        : %d" % sum(i["o"] for i in data["items"]))
    print("  with batches    : %d  (multi-batch %d)"
          % (sum(1 for i in data["items"] if i["b"]),
             sum(1 for i in data["items"] if len(i["b"]) > 1)))
    print("  written         : %s  (%d bytes)" % (a.out, len(html)))
    return 0


def selftest():
    n = [0]

    def ck(cond, msg):
        n[0] += 1
        if not cond:
            print("check %d FAILED: %s" % (n[0], msg))
            raise AssertionError(msg)

    ck(as_on_key("27-08-2026") > as_on_key("31-03-2026"),
       "August beats March -- dd-mm-yyyy compared as TEXT gets this backwards")
    ck(as_on_key("28-08-2026") > as_on_key("27-08-2026"), "and later in the month wins")
    ck(as_on_key("rubbish") == (0, 0, 0), "an unreadable date sorts first, never wins")
    ck(expiry_key("6/28") == (2028, 6), "a two-digit year expands to 2028")
    ck(expiry_key("12/2027") == (2027, 12), "a four-digit year is taken as-is")
    ck(expiry_key("") == (9999, 99), "an unknown expiry sorts LAST, never first")
    ck(expiry_key("rubbish") == (9999, 99), "so does an unparseable one")
    ck(expiry_key("3/28") < expiry_key("6/28"), "March beats June in the same year")
    ck(expiry_key("11/27") < expiry_key("1/28"), "and a year boundary is handled")
    tpl = os.path.join(HERE, "stock_check_template.html")
    ck(os.path.isfile(tpl), "the template sits beside this script")
    with open(tpl, "r", encoding="utf-8") as fh:
        t = fh.read()
    ck("__STOCK_DATA__" in t, "the template carries the data placeholder")
    ck(t.count("__STOCK_DATA__") == 1, "exactly once")
    ck("isStrip" in t and "it.s > 1" in t,
       "the strip test is on PACK SIZE, not on Marg's unit label")
    ck("nn=v=>" in t or "const nn" in t, "the negative-quantity clamp is present")
    ck("batches add to" in t, "the batch-sum reconciliation is present")
    ck("NOT COUNTED: " in t, "the report summarises uncounted items, never lists 368")
    ck("localStorage" in t, "progress survives the page being closed")
    ck("__SHARED__" in t and "__SKEL__" in t,
       "the template carries the two holes the page refills when it republishes")
    ck(t.count("__SHARED__") == 2,
       "__SHARED__ appears twice: the carrier, and the line that refills it")
    ck('claude.use("artifact")' in t, "the page asks for the artifact capability")
    ck("READONLY" in t and "not_writer" in t,
       "a view-only viewer is told so, instead of being shown a failure")
    ck('c==="conflict"' in t, "a conflict is handled as routine, and never retried")
    ck("function merged()" in t and "function unshared()" in t,
       "shared and local counts are merged newest-wins, and the gap is countable")
    import re as _re
    ids = set(_re.findall(r'\bid="([A-Za-z0-9_-]+)"', t))
    wanted = _re.findall(r'getElementById\("([A-Za-z0-9_-]+)"\)', t)
    missing = sorted({w for w in wanted if w not in ids})
    ck(not missing,
       "every id the script reaches for exists in the markup; missing: %s" % missing)
    ck(t.count("shareBadge()") >= 3,
       "the share badge refreshes on render AND on every count, not once at load")
    ck("const shareBtn=document.getElementById" in t.replace("  ", ""),
       "shareBadge looks the button up itself -- it runs before any outer const exists")
    body = t.split("<script>")[-1]
    declared = set(_re.findall(r'(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)', body))
    # a comma-separated declaration only names the first one after the keyword:
    #   const bill=..., bdate=..., start=..., sameBtn=...;
    declared |= set(_re.findall(r',\s*([A-Za-z_$][\w$]*)\s*=', body))
    declared |= {"window","document","localStorage","JSON","Math","Object","String",
                 "Number","Array","Date","console","navigator","setTimeout","alert",
                 "claude","atob","btoa","Uint8Array","TextDecoder","isNaN","parseInt",
                 "DATA","SHARED","PEOPLE"}
    used = set(_re.findall(r'^([A-Za-z_$][\w$]*)\.addEventListener', body, _re.M))
    undeclared = sorted(used - declared)
    ck(not undeclared,
       "no top-level listener is hung on an identifier that does not exist: %s" % undeclared)
    ck('id="whoC"' in t and 'id="whoE"' in t,
       "the gate asks who COUNTED and who is ENTERING, separately")
    ck('"Darpan","Shavez","Amir","Alisha"' in t.replace(" ", ""),
       "the four named people are Darpan, Shavez, Amir, Alisha")
    ck("Someone else" in t, "and anyone else can be typed in on the day")
    ck('id="same"' in t, "'same person' is one tap, since it is the common case")
    ck("cby:S.cby,eby:S.eby" in t.replace(" ", ""),
       "every entry records BOTH people, not just one")
    print("BUILD_STOCK_CHECK SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
