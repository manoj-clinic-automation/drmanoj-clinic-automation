import re
p = "w/marg_watch.py"
s = open(p, encoding="ascii").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)
rep("def publish_diagnostics(roots, out):\n",
"""def share_refused(spool, fm, now=None):
    \"\"\"S396.1: a report the reader would not take, copied beside the census so it can be looked at
    without anyone going to the medical PC. Only what is already in _captured_txt\\\\refused (report
    text and its reason), only the last CENSUS_DAYS, at most 12 files; a copy of the same size is
    not written again.\"\"\"
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    if not os.path.isdir(src):
        return 0
    dst = os.path.join(fm, "refused_text")
    n = 0
    for name in sorted(os.listdir(src), reverse=True)[:12]:
        p = os.path.join(src, name)
        try:
            st = os.stat(p)
            if not os.path.isfile(p) or now - st.st_mtime > CENSUS_DAYS * 86400 or st.st_size > MAX_SHARE:
                continue
            os.makedirs(dst, exist_ok=True)
            q = os.path.join(dst, name)
            if os.path.exists(q) and os.path.getsize(q) == st.st_size:
                continue
            shutil.copyfile(p, q)
            n += 1
        except OSError:
            continue
    return n


MAX_SHARE = 5 * 1024 * 1024


def publish_diagnostics(roots, out, spool=None):
""")
rep("""            with open(os.path.join(fm, "marg_watch_log.txt"), "wb") as fh:
                fh.write(tail)
""", """            with open(os.path.join(fm, "marg_watch_log.txt"), "wb") as fh:
                fh.write(tail)
            if spool:
                share_refused(spool, fm)                        # S396.1
""")
rep("    publish_diagnostics(roots, out)         # S396\n", "    publish_diagnostics(roots, out, spool)  # S396\n")
rep("            publish_diagnostics(roots, out)\n", "            publish_diagnostics(roots, out, spool)\n")
rep("""        ck("...and only once, however often it is looked at",""",
"""        fmd = os.path.join(d, "FromMedical"); os.makedirs(fmd)
        ck("S396.1: a refused report is copied beside the census (text and reason), once",
           share_refused(sp2, fmd) == 2 and share_refused(sp2, fmd) == 0
           and sorted(f.endswith(".why.txt") for f in os.listdir(os.path.join(fmd, "refused_text"))) == [False, True])
        ck("...and only once, however often it is looked at",""")
rep('out("marg_watch S395 starting', 'out("marg_watch S396.1 starting')
s = s.replace("""S396 (25-Sep-2026, F-620): ANY .txt""", """S396 (25-Sep-2026, F-620): ANY .txt""")
rep("""    to Drive's Clinic Data Archive\\\\FromMedical beside the heartbeat.
""", """    to Drive's Clinic Data Archive\\\\FromMedical beside the heartbeat. S396.1: a report text the reader
    refused is copied there too (FromMedical\\\\refused_text), with its reason, so it can be read and the
    reader mended without going to the medical PC.
""")
open(p, "w", encoding="ascii", newline="\n").write(s)
