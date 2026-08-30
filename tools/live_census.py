#!/usr/bin/env python3
"""
live_census.py -- what is ACTUALLY live on this box?

Read-only. Writes nothing, restarts nothing, touches no database.

WHY THIS EXISTS
  S211, 30-Aug-2026. `S210_DBPATIENCE` was recorded live in the session's own
  state document and was not installed; the owner's patch run answered
  `patched OK`, not `already_patched`. Nine kits were reported live on the
  strength of an installer that ran five. Nothing in the system could tell the
  difference between a kit that was built and a kit that was installed.

  This does. For every kit that patches a file, it asks the LIVE file whether
  that kit's MARK is in it. For every kit that ships a page, it asks which
  kit's bytes the LIVE page actually is.

USAGE
    /root/wa/venv/bin/python3 /root/deploy/repo/tools/live_census.py
    python3 tools/live_census.py --repo <repo> --live <root>      (offline test)
"""
import hashlib, os, re, sys

PAGES = {                      # shipped filename -> where it lives
    "finance_approvals.html": "finance/finance_ui/finance_approvals.html",
    "darpan_card.html":       "finance/darpan_card.html",
    "finance_workbench.html": "finance/finance_ui/finance_workbench.html",
    "finance_daily.html":     "finance/finance_ui/finance_daily.html",
}
MARK_RE = re.compile(r'^MARK\s*=\s*"([^"]+)"', re.M)
TGT_RE  = re.compile(r'(/root/[a-z0-9_/]+\.py)')


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main(argv):
    repo = "/root/deploy/repo"
    live = "/root"
    if "--repo" in argv: repo = argv[argv.index("--repo") + 1]
    if "--live" in argv: live = argv[argv.index("--live") + 1]
    kits = os.path.join(repo, "deploy_kits")
    if not os.path.isdir(kits):
        print("!! no deploy_kits under", repo); return 2

    patches, pages, missing = [], [], []
    for kit in sorted(os.listdir(kits)):
        d = os.path.join(kits, kit)
        if not os.path.isdir(d) or not re.match(r"^S2\d\d_", kit):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if fn.endswith(".py"):
                try: src = open(p, encoding="utf-8", errors="replace").read()
                except OSError: continue
                m = MARK_RE.search(src)
                if not m: continue
                t = TGT_RE.search(src)
                if not t: continue
                mark, tgt = m.group(1), t.group(1)
                rel = tgt[len("/root/"):] if tgt.startswith("/root/") else tgt.lstrip("/")
                lp = os.path.join(live, rel)
                if not os.path.isfile(lp):
                    patches.append((kit, mark, tgt, "NO SUCH LIVE FILE")); continue
                ok = mark in open(lp, encoding="utf-8", errors="replace").read()
                patches.append((kit, mark, os.path.basename(tgt),
                                "live" if ok else "** NOT INSTALLED **"))
                if not ok: missing.append("%s -> %s" % (kit, os.path.basename(tgt)))
            elif fn in PAGES:
                lp = os.path.join(live, PAGES[fn])
                if not os.path.isfile(lp):
                    pages.append((kit, fn, "NO SUCH LIVE FILE")); continue
                pages.append((kit, fn, "IS LIVE" if md5(p) == md5(lp) else "-"))

    print("=" * 72)
    print("PATCH KITS -- is this kit's mark in the live file?")
    print("=" * 72)
    for kit, mark, tgt, st in patches:
        print("  %-22s %-28s %-18s %s" % (kit, mark, tgt, st))

    print()
    print("=" * 72)
    print("PAGE KITS -- which kit's bytes IS the live page?")
    print("=" * 72)
    seen = {}
    for kit, fn, st in pages:
        seen.setdefault(fn, []).append((kit, st))
    for fn, rows in sorted(seen.items()):
        hit = [k for k, s in rows if s == "IS LIVE"]
        absent = all(s == "NO SUCH LIVE FILE" for k, s in rows)
        note = (", ".join(hit) if hit else
                "not on this box" if absent else
                "** matches NO kit -- live page is off-lineage **")
        print("  %-26s %s" % (fn, note))
        if not hit and not absent:
            missing.append("%s matches no kit" % fn)

    print()
    if missing:
        print("!! %d THING(S) THE RECORD MAY CALL LIVE AND ARE NOT:" % len(missing))
        for m in missing: print("   -", m)
    else:
        print("ALL CLEAR -- every kit mark is in its live file, every page matches a kit.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
