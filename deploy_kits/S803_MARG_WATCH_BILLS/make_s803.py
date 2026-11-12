#!/usr/bin/env python3
"""make_s803.py FINANCE_DIR KIT_DIR OUT_DIR -- kit S803_MARG_WATCH_BILLS (S438, 12-Nov-2026, the Sanjeevni chat).
sanjeevni_approvals.py: from its FROM pin, ONE change -- init() also mounts marg_billwatch, fail-soft (the three lines of init's body are
    replaced by KIT_DIR/block_s803_mount.txt; the anchor must stand exactly once).
owner_notice.py: from its FROM pin, the S803 block (KIT_DIR/block_s803_owner_notice.py) put BEFORE the command-line guard, which stays
    the last thing in the file (F-1207) -- nothing else in it changes.
finance_ui/finance_approvals.html (the Sanjeevni Hub): from its FROM pin, ONE line added -- in "Go to", under the Purchase bills link, a link
    to the Marg watch (the anchor line must stand exactly once).
marg_billwatch.py: NEW, the kit's whole file.
Refuses unless the three live files are at their FROM pins and marg_billwatch.py is not there yet."""
import hashlib
import os
import shutil
import sys

FROM = {"sanjeevni_approvals.py": "569c5ee4caa2692708be82c7967d2813", "owner_notice.py": "537b7c321116304baff676cec8e98fb0",
        "finance_ui/finance_approvals.html": "6a4178ea61d46c5df99a1af5d5d45e03"}
HUB_ANCHOR = '        <a href="/finance/purchase/page/scans">Purchase bills — in Marg · scanned · differences</a>\n'
HUB_NEW = '        <a href="/finance/sanjeevni/marg-watch">Marg watch — bills changed after their day</a>\n'
NEW = ("marg_billwatch.py",)
SA_ANCHOR = "    _db, _require, _unit = db_getter, require_fn, unit\n    app.register_blueprint(bp)\n    return bp\n"
ON_GUARD = 'if __name__ == "__main__":'


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, kit, out):
    os.makedirs(out, exist_ok=True)
    for n, pin in FROM.items():
        if not os.path.isfile(os.path.join(fin, n)):
            print("REFUSED: %s is not in %s" % (n, fin))
            return 2
        got = md5(os.path.join(fin, n))
        if got != pin:
            print("REFUSED: %s is %s, not %s" % (n, got[:8], pin[:8]))
            return 2
    for n in NEW:
        if os.path.exists(os.path.join(fin, n)):
            print("REFUSED: %s already exists in %s" % (n, fin))
            return 2
    s = open(os.path.join(fin, "sanjeevni_approvals.py"), encoding="utf-8", newline="").read()
    if s.count(SA_ANCHOR) != 1 or "marg_billwatch" in s:
        print("REFUSED: sanjeevni_approvals.py -- init()'s three lines stand %d time(s), or an S803 mount is already there" % s.count(SA_ANCHOR))
        return 2
    s = s.replace(SA_ANCHOR, open(os.path.join(kit, "block_s803_mount.txt"), encoding="utf-8", newline="").read())
    with open(os.path.join(out, "sanjeevni_approvals.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    o = open(os.path.join(fin, "owner_notice.py"), encoding="utf-8", newline="").read()
    at = o.rfind("\n" + ON_GUARD)
    if o.count("\n" + ON_GUARD) != 1 or "# ---- S803 (" in o or not o[at + 1:].strip().endswith("sys.exit(main())"):
        print("REFUSED: owner_notice.py -- the command-line guard is not the one last thing in the file, or an S803 block is already there")
        return 2
    o = o[:at + 1] + open(os.path.join(kit, "block_s803_owner_notice.py"), encoding="utf-8", newline="").read() + o[at + 1:]
    with open(os.path.join(out, "owner_notice.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(o)
    h = open(os.path.join(fin, "finance_ui", "finance_approvals.html"), encoding="utf-8", newline="").read()
    if h.count(HUB_ANCHOR) != 1 or "/finance/sanjeevni/marg-watch" in h:
        print("REFUSED: finance_approvals.html -- the Purchase bills line stands %d time(s), or a Marg watch link is already there" % h.count(HUB_ANCHOR))
        return 2
    with open(os.path.join(out, "finance_approvals.html"), "w", encoding="utf-8", newline="") as fh:
        fh.write(h.replace(HUB_ANCHOR, HUB_ANCHOR + HUB_NEW, 1))
    for n in NEW:
        shutil.copyfile(os.path.join(kit, n), os.path.join(out, n))
    print("built sanjeevni_approvals.py %s -> %s · owner_notice.py %s -> %s · finance_approvals.html %s -> %s · marg_billwatch.py NEW %s"
          % (FROM["sanjeevni_approvals.py"][:8], md5(os.path.join(out, "sanjeevni_approvals.py"))[:8], FROM["owner_notice.py"][:8],
             md5(os.path.join(out, "owner_notice.py"))[:8], FROM["finance_ui/finance_approvals.html"][:8], md5(os.path.join(out, "finance_approvals.html"))[:8],
             md5(os.path.join(out, "marg_billwatch.py"))[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
