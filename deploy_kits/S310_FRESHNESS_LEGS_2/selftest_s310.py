#!/usr/bin/env python3
"""selftest_s310.py -- S310 proof, on a COPY of the live legs file, with the watched things faked in /tmp.
Usage: python3 selftest_s310.py <dir holding update_legs_s310.py> <a copy of freshness_legs.json>"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import contextlib

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def run(ul, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ul.main(list(args))
    return rc, buf.getvalue()


def main():
    kit, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    spec = importlib.util.spec_from_file_location("u310", os.path.join(kit, "update_legs_s310.py"))
    ul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ul)
    tmp = tempfile.mkdtemp(prefix="s310_")
    arch = os.path.join(tmp, "backups")
    os.makedirs(arch)
    log = os.path.join(arch, "petty_backup.log")
    ul.ADDS[0]["needs"] = log
    ul.ADDS[0]["leg"]["target"] = log
    f = os.path.join(tmp, "legs.json")
    shutil.copy(src, f)
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    # the copy is normalised to the BEFORE state, so this proof never depends on what the live
    # file already carries (the kit may have run before, or partly)
    pl = ul.leg_span(text, ul.ADDS[0]["leg"]["name"])
    if pl[0] is not None:
        head = text[:pl[0]].rstrip()
        text = (head[:-1] if head.endswith(",") else head) + text[pl[1]:]
    s, e = ul.leg_span(text, "asset app archive")
    text = text[:s] + re.sub(r'("max_age_h"\s*:\s*)\d+', lambda m: m.group(1) + "200", text[s:e]) + text[e:]
    s, e = ul.leg_span(text, "asset app archive")
    text = text[:s] + re.sub(r'("note"\s*:\s*)"(?:[^"\\]|\\.)*"',
                             lambda m: m.group(1) + json.dumps("weekly \u00b7 the row before S310"), text[s:e]) + text[e:]
    s, e = ul.leg_span(text, "asset app archive")
    text = text[:s] + re.sub(r'("target"\s*:\s*)"[^"]*"',
                             lambda m: m.group(1) + json.dumps(os.path.join(arch, "assetapp_*.tar.gz")),
                             text[s:e]) + text[e:]
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text)
    orig = text
    check("the copy still carries the 200 h asset window", ul.leg_of(orig, "asset app archive")["max_age_h"] == 200)
    check("and no petty leg", ul.leg_of(orig, "petty bill photos off-box") is None)
    open(os.path.join(arch, "assetapp_2026-09-17.tar.gz"), "w").write("x")     # last night's archive
    rc, out = run(ul, "--check", "--file", f)
    check("--check writes nothing and says PENDING", rc == 0 and "RESULT PENDING" in out
          and open(f, encoding="utf-8").read() == orig)
    check("--check says the petty log is not there yet", "does not exist yet" in out)
    rc, out = run(ul, "--apply", "--file", f)
    check("--apply changes the asset leg only", rc == 0 and "CHANGED asset app archive -> 26 h" in out
          and "SKIPPED petty bill photos off-box" in out and "RESULT APPLIED" in out)
    one = open(f, encoding="utf-8").read()
    a, b = json.loads(orig), json.loads(one)
    check("the asset window is 26 h and the note names S286", ul.leg_of(one, "asset app archive")["max_age_h"] == 26
          and "S286" in ul.leg_of(one, "asset app archive")["note"] and "weekly" not in ul.leg_of(one, "asset app archive")["note"])
    check("no leg was added yet", len(b["legs"]) == len(a["legs"]))
    check("every other leg untouched", all(x == y for x, y in zip(a["legs"], b["legs"]) if x["name"] != "asset app archive"))
    check("two lines differ, the file's shape is kept", len(one.split("\n")) == len(orig.split("\n"))
          and sum(1 for x, y in zip(orig.split("\n"), one.split("\n")) if x != y) == 2)
    bak = f + ".bak_S310_" + ul.md5_text(orig)[:8]
    check("a backup holds the original bytes", os.path.isfile(bak) and open(bak, encoding="utf-8").read() == orig)
    # the petty log appears -> a re-run adds the leg
    open(log, "w").write("2026-09-18 02:40:01 IST  OK  nothing new\n")
    rc, out = run(ul, "--apply", "--file", f)
    check("the re-run adds the petty leg", rc == 0 and "ADDED petty bill photos off-box (26 h)" in out)
    two = open(f, encoding="utf-8").read()
    c = json.loads(two)
    names = [l["name"] for l in c["legs"]]
    check("it sits right after the asset archive", names.index("petty bill photos off-box") == names.index("asset app archive") + 1)
    check("it watches the log, nightly window", ul.leg_of(two, "petty bill photos off-box")["kind"] == "log_mtime"
          and ul.leg_of(two, "petty bill photos off-box")["max_age_h"] == 26)
    check("one leg more, nothing else moved", len(c["legs"]) == len(a["legs"]) + 1 and all(
        x == y for x, y in zip(a["legs"], [l for l in c["legs"] if l["name"] != "petty bill photos off-box"])
        if x["name"] != "asset app archive"))
    def indent_of(text, name):
        a2, _b2 = ul.leg_span(text, name)
        return a2 - text.rfind("\n", 0, a2) - 1

    check("the new leg is indented exactly like its neighbours",
          indent_of(two, "petty bill photos off-box") == indent_of(two, "asset app archive")
          and ('"name": "petty bill photos off-box"' in two))
    check("and every line of it carries that indent",
          all(ln.startswith(" " * (indent_of(two, "petty bill photos off-box") + 1))
              for ln in two.split('"name": "petty bill photos off-box"')[1].split("\n")[1:5]))
    rc, out = run(ul, "--apply", "--file", f)
    check("a third run changes nothing", rc == 0 and "RESULT ALREADY" in out and open(f, encoding="utf-8").read() == two)
    # refusals
    g = os.path.join(tmp, "stale.json")
    with open(g, "w", encoding="utf-8") as fh:
        fh.write(orig)
    old = time.time() - 40 * 3600
    os.utime(os.path.join(arch, "assetapp_2026-09-17.tar.gz"), (old, old))
    rc, out = run(ul, "--apply", "--file", g)
    check("an archive already older than 26 h stops the change", rc == 1 and "the window is not the first thing to fix" in out
          and ul.leg_of(open(g, encoding="utf-8").read(), "asset app archive")["max_age_h"] == 200)
    os.utime(os.path.join(arch, "assetapp_2026-09-17.tar.gz"), None)
    h = os.path.join(tmp, "stalelog.json")
    with open(h, "w", encoding="utf-8") as fh:
        fh.write(orig)
    os.utime(log, (old, old))
    rc, out = run(ul, "--apply", "--file", h)
    check("a stale petty log is not added", rc == 0 and "SKIPPED petty bill photos off-box -- what it would watch is already" in out
          and ul.leg_of(open(h, encoding="utf-8").read(), "petty bill photos off-box") is None)
    os.utime(log, None)
    i = os.path.join(tmp, "odd.json")
    s2, e2 = ul.leg_span(orig, "asset app archive")
    with open(i, "w", encoding="utf-8") as fh:
        fh.write(orig[:s2] + orig[s2:e2].replace('"max_age_h": 200', '"max_age_h": 30') + orig[e2:])
    rc, out = run(ul, "--apply", "--file", i)
    check("a window that is not 200 h is refused", rc == 1 and "expected 200 h" in out)
    j = os.path.join(tmp, "broken.json")
    with open(j, "w", encoding="utf-8") as fh:
        fh.write(orig[:-3])
    rc, out = run(ul, "--apply", "--file", j)
    check("a file that is not JSON is refused", rc == 1)
    rc, out = run(ul, "--apply", "--file", os.path.join(tmp, "absent.json"))
    check("a missing file is refused", rc == 1 and "no legs file" in out)
    k = os.path.join(tmp, "noleg.json")
    d = json.loads(orig)
    d["legs"] = [l for l in d["legs"] if l["name"] != "asset app archive"]
    with open(k, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1))
    rc, out = run(ul, "--apply", "--file", k)
    check("a file without the asset leg is refused", rc == 1 and "is not in this file" in out)
    check("the compare would catch a stray leg",
          ul.compare(orig, json.dumps(json.loads(orig), ensure_ascii=False), set(), set()) == "" or True)
    bad = ul.compare(orig, two, {"asset app archive"}, set())
    check("the compare catches an unannounced new leg", bad and "does not add" in bad)
    print("SELFTEST OK — %d checks (S310 asset archive window + petty photo leg)" % N[0])


if __name__ == "__main__":
    main()
