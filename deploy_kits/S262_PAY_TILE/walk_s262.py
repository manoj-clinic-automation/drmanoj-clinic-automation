#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s262.py -- the S262 walk. Reads the PATCHED portal.py and the NEW
tile_grants.json as bytes and proves, against the file it was patched FROM,
that exactly one tile was added, in the right section, with the right address,
and that not one other tile moved.

    python3 -B walk_s262.py --file <portal.py> --before <portal.py.bak> --grants <tile_grants.json> [--grants-before <old>]
"""
import argparse
import ast
import io
import json
import os
import py_compile
import sys
import tempfile

OK = 0
BAD = 0


def ck(cond, label):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % label)
    else:
        BAD += 1
        print("    FAIL  %s" % label)
    return bool(cond)


def _val(node):
    """A literal where the source has one; otherwise a stable stand-in for the
    expression itself, so two files can still be compared exactly."""
    try:
        return ast.literal_eval(node)
    except Exception:
        return "\u00abexpr\u00bb " + ast.dump(node)


def _shallow(node):
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_shallow(e) for e in node.elts]
    if isinstance(node, ast.Dict):
        d = {}
        for k, v in zip(node.keys, node.values):
            d[_val(k)] = _shallow(v)
        return d
    return _val(node)


def literals(path):
    """TILES, _TILE_GROUP and GROUP_ORDER, read out of the source -- no import.
    TILES carries real expressions (bool(...), config names), so each value is
    taken as a literal where it is one and as its own expression where it is not."""
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id in ("TILES", "_TILE_GROUP", "GROUP_ORDER"):
                out[t.id] = _shallow(node.value)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--grants", required=True)
    ap.add_argument("--grants-before", default=None)
    a = ap.parse_args()

    NAME = "Vendor payments"
    URL = "/finance/purchase/page/pay"

    # ---- 1. it is still python -------------------------------------------
    fd, cf = tempfile.mkstemp(suffix=".pyc")
    os.close(fd)
    try:
        py_compile.compile(a.file, cfile=cf, doraise=True)
        ck(True, "the patched portal.py compiles")
    except Exception as e:
        ck(False, "the patched portal.py compiles (%s)" % e)
    finally:
        try:
            os.remove(cf)
        except OSError:
            pass

    new = literals(a.file)
    old = literals(a.before)
    ck("TILES" in new and "_TILE_GROUP" in new, "the tile list and the section map are both readable")
    nt, ot = new["TILES"], old["TILES"]
    ng, og = new["_TILE_GROUP"], old["_TILE_GROUP"]

    # ---- 2. exactly one tile was added -----------------------------------
    ck(len(nt) == len(ot) + 1, "exactly one tile was added (%d -> %d)" % (len(ot), len(nt)))
    names = [t.get("name") for t in nt]
    ck(names.count(NAME) == 1, "the new tile is there, once: %s" % NAME)
    ck(len(names) == len(set(names)), "no two tiles share a name")

    added = [t for t in nt if t.get("name") == NAME]
    tile = added[0] if added else {}
    ck(tile.get("url") == URL, "it points at %s" % URL)
    ck(tile.get("roles") == ["doctor"], "in code it is the doctor's alone (roles %r)" % (tile.get("roles"),))
    ck(tile.get("live") is True, "it is marked live")
    ck(bool(tile.get("desc")), "it carries a description")
    ck(bool(tile.get("icon")), "it carries an icon")

    # ---- 3. where it sits -------------------------------------------------
    try:
        i = names.index(NAME)
        ck(names[i - 1] == "Marg Purchases", "it sits straight after Marg Purchases")
    except ValueError:
        ck(False, "it sits straight after Marg Purchases")
    ck(ng.get(NAME) == "Money & Accounts", "it is in Money & Accounts")

    # ---- 4. NOT ONE OTHER TILE MOVED -------------------------------------
    def shape(ts):
        return [(t.get("name"), t.get("url"), tuple(t.get("roles")) if isinstance(t.get("roles"), list) else t.get("roles"), t.get("live")) for t in ts]
    ck([s for s in shape(nt) if s[0] != NAME] == shape(ot),
       "every other tile is unchanged -- same name, address, roles and order")
    og2 = dict(og)
    ng2 = dict(ng)
    ng2.pop(NAME, None)
    ck(ng2 == og2, "not one other tile changed section")
    ck(new.get("GROUP_ORDER") == old.get("GROUP_ORDER"), "the section order is untouched")

    # ---- 5. portal's own import-time rule ---------------------------------
    missing = [t.get("name") for t in nt if t.get("name") not in ng]
    ck(not missing, "every tile maps to a section (portal refuses to start otherwise)%s"
       % ("" if not missing else " -- missing: %r" % missing))
    badg = sorted(set(ng.values()) - set(new.get("GROUP_ORDER") or []))
    ck(not badg, "every section named is a real section%s" % ("" if not badg else " -- %r" % badg))

    # ---- 6. the grants file ----------------------------------------------
    try:
        g = json.loads(io.open(a.grants, encoding="utf-8").read())
        ck(True, "tile_grants.json is valid JSON")
    except Exception as e:
        ck(False, "tile_grants.json is valid JSON (%s)" % e)
        g = None

    if g:
        ck(g.get("version") == 17, "it is version 17")
        users = g.get("users") or {}
        holders = sorted(u for u, v in users.items() if NAME in (v.get("extra") or []))
        ck(holders == ["shavez"], "granted by name to shavez and nobody else (%r)" % (holders,))
        masked = sorted(u for u, v in users.items() if NAME in (v.get("mask") or []))
        ck(not masked, "it is masked from nobody")
        stale = sorted({n for v in users.values()
                        for n in (v.get("extra") or []) + (v.get("mask") or [])
                        if n not in names})
        ck(not stale, "every name this file grants or masks is a real tile%s"
           % ("" if not stale else " -- stale: %r" % stale))
        if a.grants_before and os.path.exists(a.grants_before):
            ob = json.loads(io.open(a.grants_before, encoding="utf-8").read())
            ob.pop("_note", None); ob.pop("version", None)
            nb = json.loads(io.open(a.grants, encoding="utf-8").read())
            nb.pop("_note", None); nb.pop("version", None)
            nb["users"]["shavez"]["extra"] = [x for x in nb["users"]["shavez"]["extra"] if x != NAME]
            ck(nb == ob, "nobody else gained or lost a single tile")

    print("")
    print("%d ok, %d failed" % (OK, BAD))
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
