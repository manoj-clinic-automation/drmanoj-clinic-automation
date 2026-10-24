#!/usr/bin/env python3
"""make_s638.py -- kit S638_EXPIRY_WATCH: builds the TO files from the FROM bytes by anchored edits (each anchor exactly once, else stop),
and places the two new / whole files.

    python3 -B make_s638.py --finance /root/finance --marg /root/marg_ingest --portal /root/portal --out <dir> [--pc <dir with marg_txt.py>]

--pc builds the medical PC's reader too (FROM S604 e8a60d9d), from its Drive copy or D:\\SendToClinic -- the server's install does not.
Every output lands in <out> under its own relative path; nothing outside <out> is written."""
import argparse
import hashlib
import importlib.util
import os
import sys

FROM = {
    "finance/sanjeevni_approvals.py": "792f4a9af1728c76e8d5a656f5662421",
    "finance/darpan_kal.py": "6159b75b09257d5087111f6aebac611a",
    "finance/darpan_kal.html": "81dbb26a02043562bac6476326d9b9ed",
    "finance/amir_day.py": "2c99c29eff254c9abfe1374b2e3f8ba3",
    "finance/porders_s454.py": "647f29255e849e11afd4221b050b215b",
    "finance/supplier_msg.py": "4e3911a79096a6c0ba48f2b0e698ed1e",
    "finance/bank_sms.py": "aa5278403ec85c898d808486e4c3cde3",
    "finance/finance_ui/finance_approvals.html": "b32da7ffe605ce2440414febb8cf7bce",
    "finance/spine/near_expiry.py": "627a3915727fce3595c2fdfb11b8f01a",
    "portal/tile_grants.json": "6498a9169ff5e088cbdff46317a4e00f",
    "marg_ingest/signatures.json": "21604e0fa84f0403e1a86e7584c3a1bd",
}
FROM_PC = {"medical/marg_txt.py": "e8a60d9df79ed9fb763e2be4c4f23d4f"}
EDIT_FILES = {
    "finance/sanjeevni_approvals.py": "edits_sanjeevni_approvals.py",
    "finance/darpan_kal.py": "edits_darpan_kal.py",
    "finance/darpan_kal.html": "edits_darpan_kal_html.py",
    "finance/amir_day.py": "edits_amir_day.py",
    "finance/porders_s454.py": "edits_porders_s454.py",
    "finance/supplier_msg.py": "edits_supplier_msg.py",
    "finance/bank_sms.py": "edits_bank_sms.py",
    "finance/finance_ui/finance_approvals.html": "edits_finance_approvals_html.py",
    "portal/tile_grants.json": "edits_tile_grants.py",
    "marg_ingest/signatures.json": "edits_signatures.py",
    "medical/marg_txt.py": "edits_marg_txt.py",
}
WHOLE = {"finance/spine/near_expiry.py": "near_expiry.py"}           # replaced whole (FROM pinned above)
NEW = {"finance/expiry_watch.py": "expiry_watch.py"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(kit, name):
    spec = importlib.util.spec_from_file_location("s638_" + name[:-3], os.path.join(kit, name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def apply(src, edits, label):
    s = src.decode("utf-8")
    for i, (a, b) in enumerate(edits):
        n = s.count(a)
        if n != 1:
            sys.exit("STOP %s edit %d: anchor found %d times (must be 1): %r" % (label, i + 1, n, a[:120]))
        s = s.replace(a, b)
    return s.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--marg", required=True)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--pc", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    roots = {"finance": a.finance, "marg_ingest": a.marg, "portal": a.portal, "medical": a.pc}
    want = dict(FROM)
    if a.pc:
        want.update(FROM_PC)
    for rel, pin in want.items():
        top, rest = rel.split("/", 1)
        src = open(os.path.join(roots[top], rest), "rb").read()
        if md5(src) != pin:
            sys.exit("STOP %s: md5 %s is not the FROM pin %s" % (rel, md5(src), pin))
        if rel in WHOLE:
            out = open(os.path.join(a.kit, WHOLE[rel]), "rb").read()
            how = "replaced whole"
        else:
            out = apply(src, list(load(a.kit, EDIT_FILES[rel]).EDITS), rel)
            how = "%d edits" % len(load(a.kit, EDIT_FILES[rel]).EDITS)
        dst = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(out)
        print("BUILT %-44s %s -> %s (%s)" % (rel, pin[:8], md5(out), how))
    for rel, n in NEW.items():
        b = open(os.path.join(a.kit, n), "rb").read()
        dst = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(b)
        print("BUILT %-44s NEW      -> %s" % (rel, md5(b)))


if __name__ == "__main__":
    main()
