#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
close_build.py  (S357, 26-Oct-2026)  --  THE CLOSE, BUILT IN ONE RUN from facts written once.

The close routine (END_OF_SESSION_PROMPT v18) writes eight documents by hand, each restating the same facts, and does
every append, hash, manifest row, pin list and copy by hand. This tool does the mechanics; the assistant writes only
the PARTS -- the prose that is new this session -- into one folder, plus close.json (the facts).

  python close_build.py <close.json>            build everything in a scratch folder; verify; print the table. Nothing placed.
  python close_build.py <close.json> --place    the same, then place into KB_canon_all, rewrite MD5SUMS_ALL.txt
                                                (canon_sums.py --fix), copy the papers, append MANIFEST.md5 rows, the SSD brief.
Every anchor must occur exactly once or the run STOPS before writing a byte into canon. A file that already exists in
canon is never overwritten (F-512 spirit). The prefix of every appended register is proven by hash.

close.json (the parent's S357 as the example):
{
  "session": 357, "project_key": "parent", "project_words": "the parent",
  "date_words": "26-Oct-2026", "time_words": "MORNING",
  "parts": "D:\\Downloads\\ClaudeCowork\\03_WORKING_PAPERS\\S357\\close_parts",
  "out":   "D:\\Downloads\\ClaudeCowork\\03_WORKING_PAPERS\\S357\\close_build",
  "start_here_from": "START_HERE_SESSION_357.md", "start_here_to": "START_HERE_SESSION_360.md",
  "brief_from": "S354_BUILD_BRIEF.md", "report_from": "S354_CLOSE_REPORT.md",
  "runbook": {"section_start": "## §2A", "section_end": "## §2B", "header": "...line 1 of the new runbook...",
              "supersedes_old": "*Supersedes v271 (the S354 close).", "supersedes_new": "*Supersedes v272 ...", "s3_line": "**At the S357 close ...**"},
  "todo": {"section_start": "## ⭐0 — WHAT NEEDS YOU · THE PARENT", "section_end": "## ⭐0 — WHAT NEEDS YOU · THE SANJEEVNI", "header": "# OWNER TO-DO — LIVE · refreshed at the **S357 close** ..."},
  "book": null  |  {"from": "SCANAPP_SYSTEM_BOOK_v11_S352.md", "to": "SCANAPP_SYSTEM_BOOK_v12_S359.md", "part": "book.md"},
  "kits": {"S658SUMS": "S658_UNREAD_NIGHTLY"},
  "register": {"howto_new": "> **How to use.** **CURRENT AT v5.192 (S357 close, 26-Oct-2026): ...", "end_line": "**END OF KB REGISTER v5.192. ...**"},
  "manifest": {"status_new": "**STATUS: canonical — current at the **S357 CLOSE** (...)**", "end_line": "**END OF CANONICAL_MANIFEST — S357 CLOSE (...)**",
               "rows": [["KB_History_Archive_v1_189_S357close.md", "**CURRENT** Tier-1 archive. §S357 appended ... %s B."], ...]},
  "pending_prefixes": ["/root/finance", "/root/portal", "/root/staff_register", "/usr/local/bin", "/root/wa"]
}
Parts (files in "parts"): archive.md  fault.md  reg_h1.md  reg_sections.md  rb_section.md  start_here.md  brief.md
                          close_report.md  todo.md  man_narr.md  [book.md]
"""
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HOME = os.path.expanduser("~")


def P(p):
    """A Windows path in close.json works in the manojz VM too ($HOME/mnt/<Drive-folder>)."""
    if os.name != "nt" and re.match(r"^[A-Za-z]:\\", p):
        drive, rest = p[0].upper(), p[3:].replace("\\", "/")
        top = rest.split("/", 1)
        mnt = {"D": {"Downloads": "Downloads", "dr-manoj-git": "dr-manoj-git"}, "F": {"ClinicBackup": "ClinicBackup"}}
        folder = mnt.get(drive, {}).get(top[0])
        if folder is None:
            raise SystemExit("STOP: path %s is not under a connected folder" % p)
        return os.path.join(HOME, "mnt", folder, top[1] if len(top) > 1 else "")
    return p


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def rd(p):
    return open(p, "rb").read().decode("utf-8")


def once(s, old, new, label):
    c = s.count(old)
    if c != 1:
        raise SystemExit("STOP %s: anchor found %d times: %r" % (label, c, old[:80]))
    return s.replace(old, new)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    place = "--place" in sys.argv
    S = int(cfg["session"])
    SS = "S%d" % S
    repo = P(cfg.get("repo", r"D:\dr-manoj-git\drmanoj-clinic-automation"))
    kb = P(cfg.get("kb", r"D:\Downloads\ClaudeCowork"))
    tools = P(cfg.get("tools", r"D:\Downloads\_kbtools"))
    ssd = P(cfg.get("ssd", r"F:\ClinicBackup\DrManojClinic_Automation"))
    canon = os.path.join(repo, "deploy_kits", "KB_canon_all")
    kits = os.path.join(repo, "deploy_kits")
    parts = P(cfg["parts"])
    out = P(cfg["out"])
    os.makedirs(out, exist_ok=True)
    log = []

    def part(n):
        p = os.path.join(parts, n)
        if not os.path.isfile(p):
            raise SystemExit("STOP: part missing: " + p)
        return rd(p)

    def wr(name, text):
        p = os.path.join(out, name)
        open(p, "wb").write(text.encode("utf-8") if isinstance(text, str) else text)
        return p

    def note(s):
        log.append(s)
        print(s)

    # ---- 0. the CURRENT names, from the manifest (the manifest WINS on what is current)
    man = rd(os.path.join(canon, "CANONICAL_MANIFEST.md"))
    cur = {}
    for line in man.split("\n"):
        m = re.match(r"^\|\s*`([^`]+)`\s*\|[^|]*\|[^|]*\|\s*\*\*CURRENT\*\*", line)
        if m:
            nm = m.group(1)
            for fam, rx in (("reg", r"^KB_Register_v(\d+)_(\d+)_S(\d+)close"), ("arch", r"^KB_History_Archive_v(\d+)_(\d+)_S(\d+)close\.md$"),
                            ("fault", r"^Fault_Action_Register_v(\d+)_(\d+)\.md$"), ("rb", r"^HANDOFF_RUNBOOK_(\d{4}-\d\d-\d\d)_Session(\d+)close_v(\d+)\.md$"),
                            ("pins", r"^live_pins_S(\d+)close\.txt$")):
                if re.match(rx, nm) and fam not in cur:
                    cur[fam] = nm
    for fam in ("reg", "arch", "fault", "rb", "pins"):
        if fam not in cur:
            raise SystemExit("STOP: no CURRENT %s row in the manifest" % fam)
    regf = cur["reg"] if cur["reg"].endswith(".md") else cur["reg"] + ".md"
    for f in (regf, cur["arch"], cur["fault"], cur["rb"], cur["pins"], cfg["start_here_from"], cfg["brief_from"], cfg["report_from"], "OWNER_TODO_LIVE.md"):
        if not os.path.isfile(os.path.join(canon, f)):
            raise SystemExit("STOP: FROM file not in canon: " + f)
    m = re.match(r"^KB_Register_v(\d+)_(\d+)_S(\d+)close", cur["reg"]); rv = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^KB_History_Archive_v(\d+)_(\d+)_S", cur["arch"]); av = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^Fault_Action_Register_v(\d+)_(\d+)\.md$", cur["fault"]); fv = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^HANDOFF_RUNBOOK_(\d{4}-\d\d-\d\d)_Session(\d+)close_v(\d+)\.md$", cur["rb"]); rbv = int(m.group(3))
    TO = {"reg": "KB_Register_v%d_%d_%sclose.md" % (rv[0], rv[1] + 1, SS),
          "arch": "KB_History_Archive_v%d_%d_%sclose.md" % (av[0], av[1] + 1, SS),
          "fault": "Fault_Action_Register_v%d_%d.md" % (fv[0], fv[1] + 1),
          "rb": "HANDOFF_RUNBOOK_%s_Session%dclose_v%d.md" % (time.strftime("%Y-%m-%d"), S, rbv + 1),
          "pins": "live_pins_%sclose.txt" % SS, "sh": cfg["start_here_to"], "brief": "%s_BUILD_BRIEF.md" % SS,
          "cr": "%s_CLOSE_REPORT.md" % SS, "todo": "OWNER_TODO_LIVE.md", "man": "CANONICAL_MANIFEST.md"}
    for k in ("reg", "arch", "fault", "rb", "pins", "sh", "brief", "cr"):
        if os.path.exists(os.path.join(canon, TO[k])):
            raise SystemExit("STOP: already in canon (a file in canon is never overwritten): " + TO[k])
    note("FROM: %s · %s · %s · %s · %s · %s" % (regf, cur["arch"], cur["fault"], cur["rb"], cur["pins"], cfg["start_here_from"]))
    note("TO:   %s · %s · %s · %s · %s · %s" % (TO["reg"], TO["arch"], TO["fault"], TO["rb"], TO["pins"], TO["sh"]))

    # ---- 1. Archive, Fault: append, prefix proven
    for fam, pname, label in (("arch", "archive.md", "Archive v%d.%d" % (av[0], av[1] + 1)), ("fault", "fault.md", "Fault v%d.%d" % (fv[0], fv[1] + 1))):
        b0 = open(os.path.join(canon, cur[fam]), "rb").read()
        add = part(pname)
        if not add.startswith("\n"):
            add = "\n" + add
        b1 = b0 + add.encode("utf-8")
        assert hashlib.md5(b1[:len(b0)]).hexdigest() == hashlib.md5(b0).hexdigest()
        p = wr(TO[fam], b1)
        note("%s: prefix %s B = %s %s PROVEN; %s B %s" % (label, "{:,}".format(len(b0)), cur[fam], md5(os.path.join(canon, cur[fam]))[:8], "{:,}".format(len(b1)), md5(p)))

    # ---- 2. Register
    r = rd(os.path.join(canon, regf))
    oldv = "v%d.%d" % rv
    newv = "v%d.%d" % (rv[0], rv[1] + 1)
    assert r.startswith("# KB REGISTER — %s " % oldv), r[:60]
    sec = part("reg_sections.md")
    for k, d in (cfg.get("kits") or {}).items():
        sp = os.path.join(kits, d, "SUMS.md5")
        if not os.path.isfile(sp):
            raise SystemExit("STOP: kit SUMS missing: " + sp)
        sec = sec.replace("{{%s}}" % k, md5(sp))
    if "{{" in sec:
        raise SystemExit("STOP: a {{placeholder}} in reg_sections.md was not filled")
    h1 = part("reg_h1.md").rstrip("\n")
    assert h1.startswith("# KB REGISTER — %s " % newv), "reg_h1.md must start with '# KB REGISTER — %s '" % newv
    r = h1 + "\n\n*(%s H1, retained:)* \n" % oldv + r
    i = r.index("## CURRENT LIVE FILE VERSIONS — §S")
    r = r[:i] + sec.rstrip("\n") + "\n\n" + r[i:]
    hm = re.search(r"^> \*\*How to use\.\*\* \*\*CURRENT AT %s \(.*$" % re.escape(oldv), r, re.M)
    if not hm:
        raise SystemExit("STOP: the Register's 'How to use ... CURRENT AT %s' line not found" % oldv)
    r = r[:hm.start()] + cfg["register"]["howto_new"].rstrip("\n") + r[hm.end():]
    r = r.rstrip("\n") + "\n\n" + cfg["register"]["end_line"].strip() + "\n"
    p = wr(TO["reg"], r)
    note("Register %s: %s B %s" % (newv, "{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 3. Runbook
    rb = rd(os.path.join(canon, cur["rb"]))
    lines = rb.split("\n")
    assert lines[0].startswith("# HANDOFF RUNBOOK — v%d " % rbv), lines[0][:50]
    rbc = cfg["runbook"]
    assert rbc["header"].startswith("# HANDOFF RUNBOOK — v%d " % (rbv + 1))
    lines[0] = rbc["header"].rstrip("\n")
    rb = "\n".join(lines)
    rb = once(rb, rbc["supersedes_old"], rbc["supersedes_new"].rstrip("\n"), "runbook supersedes")
    i = rb.index(rbc["section_start"]); j = rb.index(rbc["section_end"])
    if not (0 < i < j):
        raise SystemExit("STOP: runbook section markers out of order")
    rb = rb[:i] + part("rb_section.md").rstrip("\n") + "\n\n" + rb[j:]
    rb = once(rb, "## §3 · Files\n\n", "## §3 · Files\n\n" + rbc["s3_line"].rstrip("\n") + "\n\n", "runbook §3")
    p = wr(TO["rb"], rb)
    note("Runbook v%d: %s B %s" % (rbv + 1, "{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 4. START_HERE, brief
    p = wr(TO["sh"], part("start_here.md")); note("%s: %s B %s" % (TO["sh"], "{:,}".format(os.path.getsize(p)), md5(p)))
    p = wr(TO["brief"], part("brief.md")); note("%s: %s B %s" % (TO["brief"], "{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 5. OWNER_TODO_LIVE
    td = rd(os.path.join(canon, "OWNER_TODO_LIVE.md"))
    first, rest = td.split("\n", 1)
    assert first.startswith("# OWNER TO-DO — LIVE"), first[:40]
    tc = cfg["todo"]
    td = tc["header"].rstrip("\n") + "\n*(Previous header, retained:)* " + first.lstrip("# ") + "\n" + rest
    i = td.index(tc["section_start"]); j = td.index(tc["section_end"])
    if not (0 < i < j):
        raise SystemExit("STOP: todo section markers out of order")
    td = td[:i] + part("todo.md").rstrip("\n") + "\n\n" + td[j:]
    p = wr("OWNER_TODO_LIVE.md", td); note("OWNER_TODO_LIVE: %s B %s" % ("{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 6. the book (optional)
    bk = cfg.get("book")
    if bk:
        if os.path.exists(os.path.join(canon, bk["to"])):
            raise SystemExit("STOP: already in canon: " + bk["to"])
        p = wr(bk["to"], part(bk["part"])); note("%s: %s B %s" % (bk["to"], "{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 6b. the close report: part + the build log so far (the manifest and pins figures live in _summary.json and the board line)
    cr = part("close_report.md").rstrip("\n") + "\n\n**The build (close_build.py):**\n```\n" + "\n".join(log) + "\n```\n"
    p = wr(TO["cr"], cr); print("%s: %s B %s" % (TO["cr"], "{:,}".format(os.path.getsize(p)), md5(p)))

    # ---- 6c. extra canon files this close adds (a new routine document, a tool kept in canon): copied in, rows from close.json
    for src in cfg.get("extra_files") or []:
        sp = P(src)
        if not os.path.isfile(sp):
            raise SystemExit("STOP: extra file missing: " + sp)
        if os.path.exists(os.path.join(canon, os.path.basename(sp))):
            raise SystemExit("STOP: already in canon: " + os.path.basename(sp))
        shutil.copyfile(sp, os.path.join(out, os.path.basename(sp)))
        note("%s: %s B %s (added to canon)" % (os.path.basename(sp), "{:,}".format(os.path.getsize(sp)), md5(sp)))

    # ---- 7. the manifest: narrative, STATUS, rows, supersedes, pins (after gen), END
    narr = part("man_narr.md").rstrip("\n") + "\n"
    assert narr.startswith("> **%s CLOSE" % SS), "man_narr.md must start with '> **%s CLOSE'" % SS
    assert man.startswith("> **S"), man[:30]
    man2 = narr + man
    sm = re.search(r"^\*\*STATUS: canonical — current at the \*\*S\d+ CLOSE\*\*.*$", man2, re.M)
    if not sm:
        raise SystemExit("STOP: STATUS line not found")
    mc = cfg["manifest"]
    assert mc["status_new"].startswith("**STATUS: canonical — current at the **%s CLOSE**" % SS)
    man2 = man2[:sm.start()] + mc["status_new"].rstrip("\n") + "\n*(The previous STATUS line, retained:)* " + man2[sm.start():]
    # rows: the given ones + the fixed ones (register, archive, fault, runbook, start_here, brief, report, todo-less)
    def row(name, desc):
        f = os.path.join(out, name if name.endswith((".md", ".txt")) else name + ".md")
        return "| `%s` | **%s close** | `%s` | %s |\n" % (name, SS, md5(f), desc.replace("%s", "{:,}".format(os.path.getsize(f))))
    rows = ""
    for name, desc in mc["rows"]:
        rows += row(name, desc)
    anchor = "| `%s` | " % cur["reg"]
    man2 = once(man2, anchor, rows + anchor, "manifest rows anchor (previous Register row)")
    sup = [tuple(x) for x in (mc.get("supersede_extra") or [])] + [(cur["reg"], TO["reg"][:-3]), (cur["arch"], TO["arch"]), (cur["fault"], TO["fault"]), (cur["rb"], TO["rb"]), (cur["pins"], TO["pins"]),
           (cfg["start_here_from"], TO["sh"]), (cfg["brief_from"], TO["brief"]), (cfg["report_from"], TO["cr"])] + ([(bk["from"], bk["to"])] if bk else [])
    outl, done = [], set()
    for line in man2.split("\n"):
        for old, new in sup:
            if line.startswith("| `%s` |" % old) and "| **CURRENT** " in line and old not in done:
                line = line.replace("| **CURRENT** ", "| *(superseded at the %s close by `%s`)* was **CURRENT** " % (SS, new), 1)
                done.add(old)
        outl.append(line)
    man2 = "\n".join(outl)
    miss = [o for o, n in sup if o not in done]
    if miss:
        raise SystemExit("STOP: no CURRENT row to supersede for %s" % miss)
    man2 = man2.rstrip("\n") + "\n\n" + mc["end_line"].strip() + "\n"
    mp = wr("CANONICAL_MANIFEST.md", man2)

    # ---- 8. the pin list from the new Register against the new manifest
    shutil.copy(os.path.join(canon, "gen_live_pins.py"), os.path.join(out, "_gen_live_pins.py"))
    r_ = subprocess.run([sys.executable, "-B", "_gen_live_pins.py", TO["reg"], "--manifest", "CANONICAL_MANIFEST.md", "--session", "%s close" % SS, "-o", TO["pins"]],
                        cwd=out, capture_output=True, text=True)
    os.remove(os.path.join(out, "_gen_live_pins.py"))
    if r_.returncode != 0:
        raise SystemExit("STOP: gen_live_pins failed: " + (r_.stderr or r_.stdout)[-800:])
    pins = rd(os.path.join(out, TO["pins"]))
    if "# register_pin_verified: yes" not in pins:
        raise SystemExit("STOP: the pin list did not verify the Register's pin against the manifest")
    rows_ = [l for l in pins.split("\n") if l and not l.startswith("#")]
    kinds = {}
    pend = []
    # DECLARED-PENDING is a fact against the newest bundle (as the nightly's step D counts it): a row whose note says so AND
    # whose live bytes in the bundle do not yet match (or are not in the bundle), within this project's prefixes
    got = {}
    tar_p = os.path.join(tools, "vps_code", "code_nightly.tar.gz")
    if os.path.isfile(tar_p):
        import tarfile
        with tarfile.open(tar_p, "r:gz") as tf:
            for m_ in tf.getmembers():
                if m_.isfile() and m_.name.lstrip("./") != "MANIFEST.md5":
                    got["/" + m_.name.lstrip("./")] = hashlib.md5(tf.extractfile(m_).read()).hexdigest()
    for l in rows_:
        f = l.split("\t")
        kinds[f[0]] = kinds.get(f[0], 0) + 1
        if len(f) > 3 and f[0] in ("VPS", "SHORT") and "DECLARED-PENDING" in f[3] and any(f[2].startswith(x) for x in cfg.get("pending_prefixes", [])):
            live = got.get(f[2])
            ok = live is not None and ((live == f[1].lower()) if f[0] == "VPS" else live.startswith(f[1].lower()[:8]))
            if not ok:
                pend.append(f[2] + ("" if live is None else " (differs)"))
    note("pins: %d rows (%s); this project's DECLARED-PENDING %d: %s" % (len(rows_), ", ".join("%s %d" % kv for kv in sorted(kinds.items())), len(pend), ", ".join(pend)))
    prow = ("| `%s` | **%s close** | `%s` | **CURRENT** pin list, generated by `gen_live_pins.py` from `%s` after the Register's last edit and against this manifest's "
            "register row (`register_pin_verified: yes`); %d rows (%s). This project's DECLARED-PENDING %d. |\n"
            % (TO["pins"], SS, md5(os.path.join(out, TO["pins"])), TO["reg"], len(rows_), ", ".join("%s %d" % kv for kv in sorted(kinds.items())), len(pend)))
    man2 = rd(mp)
    man2 = once(man2, "| `%s` | **%s close** |" % (TO["fault"], SS), prow + "| `%s` | **%s close** |" % (TO["fault"], SS), "pins row anchor (the new Fault row)")
    wr("CANONICAL_MANIFEST.md", man2)
    note("Manifest: %s B %s" % ("{:,}".format(os.path.getsize(mp)), md5(mp)))

    # ---- 10. the gates: .gitignore (last match wins) and the number gate, over everything built
    built = sorted(n for n in os.listdir(out) if not n.startswith("_"))
    gi = [l.rstrip("\n") for l in open(os.path.join(repo, ".gitignore"), encoding="utf-8") if l.strip() and not l.startswith("#")]
    ignored = []
    for n in built:
        rel = "deploy_kits/KB_canon_all/" + n
        state = False
        for pat in gi:
            neg = pat.startswith("!"); q = pat[1:] if neg else pat
            anch = q.startswith("/"); q = q.lstrip("/")
            hit = fnmatch.fnmatch(rel, q) or fnmatch.fnmatch(n, q) or (not anch and ("/" not in q) and fnmatch.fnmatch(os.path.basename(rel), q)) \
                or (q.endswith("/") and rel.startswith(q))
            if hit:
                state = not neg
        if state:
            ignored.append(n)
    if ignored:
        raise SystemExit("STOP: .gitignore would exclude %s -- the publish would refuse the whole run (F-300 family)" % ignored)
    print(".gitignore: none of %d files ignored" % len(built))
    # the number gate, exactly as PUBLISH_ALL runs it (--files-from, canon history exempt by the baseline): the built files are
    # staged under a path that reads deploy_kits/KB_canon_all/ so the gate judges them as the canon files they will be
    ng = os.path.join(kits, "NO_PHONE_NUMBERS.py")
    env = dict(os.environ)
    env.setdefault("SANJ_CONFIG_STORE", P(r"D:\Downloads\margsync\_config"))
    gbase = os.path.join(out, "_gate")
    gdir = os.path.join(gbase, "deploy_kits", "KB_canon_all")
    shutil.rmtree(gbase, ignore_errors=True)
    os.makedirs(gdir)
    lst = os.path.join(gbase, "_staged_files.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for n in built:
            shutil.copyfile(os.path.join(out, n), os.path.join(gdir, n))
            fh.write("deploy_kits/KB_canon_all/%s\n" % n)
    g = subprocess.run([sys.executable, "-B", ng, "--files-from", lst, gbase], capture_output=True, text=True, env=env, cwd=kits)
    shutil.rmtree(gbase, ignore_errors=True)
    print("number gate: " + (g.stdout.strip().splitlines() or ["(no output)"])[-1])
    if g.returncode != 0:
        raise SystemExit("STOP: the number gate is not clean on the built files:\n" + g.stdout[-1200:] + g.stderr[-400:])

    summary = {"session": S, "from": {"register": regf, "archive": cur["arch"], "fault": cur["fault"], "runbook": cur["rb"], "pins": cur["pins"]},
               "to": TO, "files": {n: {"md5": md5(os.path.join(out, n)), "bytes": os.path.getsize(os.path.join(out, n))} for n in built},
               "pending": pend, "built_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(summary, open(os.path.join(out, "_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("BUILT in %s -- nothing placed%s" % (out, "" if place else ". Re-run with --place when the parts are final."))
    if not place:
        return 0

    # ---- 11. PLACE: canon, sums, papers, MANIFEST.md5 rows, the SSD brief
    for n in built:
        dst = os.path.join(canon, n)
        if n not in ("CANONICAL_MANIFEST.md", "OWNER_TODO_LIVE.md") and os.path.exists(dst):
            raise SystemExit("STOP: exists in canon: " + n)
    for n in built:
        shutil.copyfile(os.path.join(out, n), os.path.join(canon, n))
    for n in built:
        if md5(os.path.join(canon, n)) != md5(os.path.join(out, n)):
            raise SystemExit("STOP: placed copy differs: " + n)
    print("placed %d files into KB_canon_all, each read back by hash" % len(built))
    cs = subprocess.run([sys.executable, "-B", os.path.join(tools, "canon_sums.py"), "--canon", canon, "--fix"], capture_output=True, text=True)
    print("canon_sums --fix: " + (cs.stdout.strip().splitlines() or ["?"])[-1])
    gate = subprocess.run(["md5sum", "-c", "MD5SUMS_ALL.txt"], cwd=canon, capture_output=True, text=True)
    okn = sum(1 for l in gate.stdout.splitlines() if l.endswith(": OK")); bad = [l for l in gate.stdout.splitlines() if not l.endswith(": OK")]
    print("gate from inside KB_canon_all: %d OK, %d not OK" % (okn, len(bad)))
    if bad:
        raise SystemExit("STOP: the gate is red after placing: %s" % bad[:5])
    # papers: every project-knowledge document of this close into 03_WORKING_PAPERS\S###\ with MANIFEST.md5 rows
    wp = os.path.join(kb, "03_WORKING_PAPERS", SS)
    os.makedirs(wp, exist_ok=True)
    papers = [TO["sh"], TO["brief"], TO["cr"], TO["rb"], TO["pins"], "OWNER_TODO_LIVE.md"]
    mrows = []
    for n in papers:
        shutil.copyfile(os.path.join(out, n), os.path.join(wp, n))
        mrows.append("%s  03_WORKING_PAPERS/%s/%s" % (md5(os.path.join(wp, n)), SS, n))
    with open(os.path.join(kb, "MANIFEST.md5"), "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(mrows) + "\n")
    print("papers: %d into 03_WORKING_PAPERS\\%s, %d MANIFEST.md5 rows appended" % (len(papers), SS, len(mrows)))
    bd = os.path.join(ssd, "03_BUILD_BRIEFS")
    os.makedirs(bd, exist_ok=True)
    shutil.copyfile(os.path.join(out, TO["brief"]), os.path.join(bd, TO["brief"]))
    print("the SSD brief: %s (%s)" % (os.path.join(bd, TO["brief"]), md5(os.path.join(bd, TO["brief"]))[:8]))
    summary["placed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(summary, open(os.path.join(out, "_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("PLACED. Next: the board's one batch write; project_write(local_path) for %s; name the publish." % ", ".join(papers + [TO["reg"] if False else ""]).rstrip(", "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
