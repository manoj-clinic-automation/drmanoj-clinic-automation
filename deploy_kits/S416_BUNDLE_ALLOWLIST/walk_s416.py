#!/usr/bin/env python3
"""walk_s416.py -- kit S416_BUNDLE_ALLOWLIST (F-631). Points the kit's code_bundle.py at a MOCK ROOT built here from
the kit's own copies of the five files (the S366/S385/S376 kit bytes, byte-identical to the live pins), plus decoys
that must stay out (a .env, a token file, a ring_hook.env, a data file under casepack/), and runs its gather() twice:
with the live v1.7 file (the control: the five are ABSENT) and with the kit file (the five are PRESENT, the decoys
absent, and everything v1.7 carried is still carried). Nothing on the box is touched; no network.
Usage: python3 walk_s416.py <kit code_bundle.py> <live code_bundle.py> <dir with the five files>"""
import importlib.util, os, shutil, sys, tempfile
kit, live, five = [os.path.abspath(x) for x in sys.argv[1:4]]
N = [0]


def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)


root = tempfile.mkdtemp(prefix="s416_walk_")
def put(rel, src=None, text=None):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if src: shutil.copyfile(src, p)
    else: open(p, "w").write(text or "x\n")
# the five (from the kit folder) at their live paths
put("root/portal/portal_sw.js", os.path.join(five, "portal_sw.js"))
put("root/portal/http_ece.py", os.path.join(five, "http_ece.py"))
put("etc/systemd/system/ring-hook.service", os.path.join(five, "ring-hook.service"))
put("root/wa/casepack/casepack_page.html", os.path.join(five, "casepack_page.html"))
put("root/wa/fu_push_on_arrival.sh", os.path.join(five, "fu_push_on_arrival.sh"))
# what v1.7 already carried, one of each kind, must still be carried
put("root/finance/finance_app.py", text="# app\n")
put("root/portal/portal.py", text="# portal\n")
put("root/wa/wa_receiver.py", text="# rx\n")
put("etc/systemd/system/clinic-finance.service", text="[Unit]\nDescription=x\n")
# decoys that must never be carried
put("root/portal/ring_hook.env", text="RING_HOOK_PORT=8110\n")
put("root/portal/.env", text="X=1\n")
put("root/wa/token_ring.sh", text="echo hi\n")
put("root/wa/casepack/packs.db", text="data")
put("root/wa/casepack/secret_notes.html", text="<p>x</p>\n")
put("root/portal/users_sw.js", text="var a=1;\n")
put("root/finance/drive_backup.conf", text="[x]\n")


def gather_with(path):
    os.environ["ROOT"] = root
    sp = importlib.util.spec_from_file_location("cb_" + os.path.basename(os.path.dirname(path)), path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    files, _, hits = m.gather()
    return {rel for rel, _ in files}, hits


new, hits_new = gather_with(kit)
old, hits_old = gather_with(live)
FIVE = {"root/portal/portal_sw.js", "root/portal/http_ece.py", "etc/systemd/system/ring-hook.service",
        "root/wa/casepack/casepack_page.html", "root/wa/fu_push_on_arrival.sh"}
ok(not (FIVE - {"root/portal/http_ece.py"}) & old, "control: v1.7 leaves the four out", sorted(FIVE & old))
ok(FIVE <= new, "v1.8 carries all five", sorted(FIVE - new))
ok(old <= new, "everything v1.7 carried is still carried", sorted(old - new))
for d in ("root/portal/ring_hook.env", "root/portal/.env", "root/wa/token_ring.sh", "root/wa/casepack/packs.db",
          "root/wa/casepack/secret_notes.html", "root/portal/users_sw.js", "root/finance/drive_backup.conf"):
    ok(d not in new, "decoy stays out: " + d)
ok(not hits_new, "no content-scan hit on the five", hits_new)
ok("root/portal/http_ece.py" in old, "v1.7 already carries http_ece.py when it exists -- so its absence from the live bundle means the file is not on the box")
ok(len(new) == len(old) + 4, "exactly four more files (%d -> %d)" % (len(old), len(new)))
shutil.rmtree(root, ignore_errors=True)
print("WALK OK %d/%d checks" % (N[0], N[0]))
