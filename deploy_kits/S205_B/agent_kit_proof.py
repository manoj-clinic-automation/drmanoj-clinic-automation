#!/usr/bin/env python3
"""
agent_kit_proof.py  --  S205 · the medical agent's NEW kit gate, exercised

WHAT IS BEING PROVEN
--------------------
`medical_agent.py` S205.1 replaces a hardcoded three-name allowlist with a
manifest, so a new file never again needs a trip to the medical PC. The
allowlist's guarantee -- *"a stray file appearing in the kit folder can never
become code that runs here"* -- has to survive that, and it is now carried by
three rules instead of by the list:

  1. the destination must lie under D:\\SendToClinic
  2. a non-python file must arrive with its md5 DECLARED, and it must match
  3. a .py is still compile-checked, on top of the hash

This imports the real module and exercises the real functions. It does not
re-implement them: a proof that tests a copy of the logic proves nothing about
the logic that ships (F-208).

    python3 agent_kit_proof.py
"""
import hashlib
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "agent_s205", os.path.join(HERE, "medical_agent.S205.py"))
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)

OK = [0]
BAD = []


def ck(cond, msg):
    OK[0] += 1
    if cond:
        print("  ok   %s" % msg)
    else:
        print("  FAIL %s" % msg)
        BAD.append(msg)


def main():
    print("=" * 78)
    print("  medical_agent %s -- the kit gate" % A.AGENT_VERSION)
    print("=" * 78)
    print()

    # ---------------------------------------------------------- destinations
    print("RULE 1 -- nothing may be written outside %s" % A.KIT_DEST_ROOT)
    ck(A._dest_ok(r"D:\SendToClinic\SEND_TO_CLINIC.bat"),
       "a file directly in the root is allowed")
    ck(A._dest_ok(r"D:\SendToClinic\xlrd\__init__.py"),
       "a subfolder under the root is allowed (a vendored package can be "
       "delivered without another visit)")
    ck(not A._dest_ok(r"D:\MARGERP\users\evil.py"),
       "MARGERP is REFUSED -- the agent never writes inside Marg")
    ck(not A._dest_ok(r"C:\Users\SET\AppData\Roaming\Microsoft\Windows"
                      r"\Start Menu\Programs\Startup\x.cmd"),
       "Startup is REFUSED -- delivery must not be able to arrange its own "
       "execution at logon")
    ck(not A._dest_ok(r"D:\SendToClinic\..\..\Windows\System32\x.dll"),
       "`..` cannot walk out of the root -- resolved before comparing")
    ck(not A._dest_ok(r"E:\SendToClinic\x.bat"),
       "a DIFFERENT DRIVE with the same folder name is refused")
    ck(not A._dest_ok(r"\\somehost\share\x.bat"),
       "a UNC path is refused")
    ck(A._dest_ok(r"D:/SendToClinic/x.bat"),
       "forward slashes normalise the same way")
    print()

    # ---- and the check must give the SAME answer on any machine (F-217) ----
    print("   and the same answer everywhere it might be tested:")
    ck(A._win_norm(r"D:\SendToClinic\a\..\b") == r"d:\sendtoclinic\b",
       "_win_norm resolves paths WITHOUT the filesystem, so this proof is "
       "valid on Linux and on the medical PC alike (F-217)")
    print()

    t = tempfile.mkdtemp()
    kit = os.path.join(t, "_kit")
    os.makedirs(kit)

    def put(name, data):
        p = os.path.join(kit, name)
        with open(p, "wb") as fh:
            fh.write(data if isinstance(data, bytes) else data.encode())
        return p, hashlib.md5(open(p, "rb").read()).hexdigest()

    # ------------------------------------------------------------- the gate
    print("RULE 2 -- a non-python file needs its md5 DECLARED, and matching")
    _p, md5_bat = put("SEND_TO_CLINIC.bat", "@echo off\r\nrem hello\r\n")
    ok, why = A._kit_gate_ok("SEND_TO_CLINIC.bat", _p, md5_bat)
    ck(ok, "a .bat whose declared md5 matches is allowed")
    ok, why = A._kit_gate_ok("SEND_TO_CLINIC.bat", _p, "0" * 32)
    ck(not ok and "md5 does not match" in why,
       "a .bat whose declared md5 does NOT match is refused, and says so")
    ok, why = A._kit_gate_ok("SEND_TO_CLINIC.bat", _p, None)
    ck(not ok and "no declared md5" in why,
       "a .bat with NO declared md5 at all is refused -- 'it was in the "
       "folder' is not a check")
    with open(_p + ".md5", "w") as fh:
        fh.write(md5_bat + "  SEND_TO_CLINIC.bat\n")
    ok, why = A._kit_gate_ok("SEND_TO_CLINIC.bat", _p, None)
    ck(ok, "a companion .md5 file beside it also satisfies the rule")
    print()

    print("RULE 3 -- a .py is still compile-checked")
    _g, _ = put("good.py", "x = 1\n")
    _b, _ = put("bad.py", "def (\n")
    ck(A._kit_gate_ok("good.py", _g, None)[0], "a .py that compiles is allowed")
    ck(not A._kit_gate_ok("bad.py", _b, None)[0],
       "a .py that does not compile is refused -- unchanged from S203")
    print()

    # --------------------------------------------------------- the manifest
    print("THE MANIFEST -- what it may and may not add")
    good_line = "SEND_TO_CLINIC.bat | D:\\SendToClinic\\SEND_TO_CLINIC.bat | %s" % md5_bat
    man = os.path.join(kit, A.KIT_MANIFEST)
    with open(man, "w") as fh:
        fh.write(
            "# comment\n"
            "\n"
            + good_line + "\n"
            + "medical_agent.py | D:\\SendToClinic\\medical_agent.py | %s\n" % ("a" * 32)
            + "evil.py | C:\\Windows\\System32\\evil.py | %s\n" % ("b" * 32)
            + "esc.py | D:\\SendToClinic\\..\\..\\Windows\\x.py | %s\n" % ("c" * 32)
            + "nohash.py | D:\\SendToClinic\\nohash.py | nope\n"
            + "garbage line with no pipes\n")
    files, want, notes = A.manifest_files(kit)
    ck(files.get("SEND_TO_CLINIC.bat") == r"D:\SendToClinic\SEND_TO_CLINIC.bat"
       and want.get("SEND_TO_CLINIC.bat") == md5_bat,
       "a well-formed line is accepted, with its md5")
    ck("medical_agent.py" not in want,
       "THE AGENT ITSELF can never be delivered this way -- a process that "
       "overwrites itself while running is how a machine bricks itself")
    ck("evil.py" not in want, "a destination outside the root is refused")
    ck("esc.py" not in want, "a `..` escape is refused")
    ck("nohash.py" not in want, "a line with no usable md5 is refused")
    ck(len(notes) == 5,
       "every refusal is REPORTED (%d notes), not silently dropped -- they "
       "reach the heartbeat" % len(notes))
    for n in notes:
        print("       note: %s" % n)
    print()

    print("THE FLOOR -- the built-in list still stands with no manifest at all")
    files2, want2, notes2 = A.manifest_files(t)   # a folder with no manifest
    ck(files2 == A.KIT_FILES and not want2 and not notes2,
       "no manifest => exactly the built-in allowlist, and no complaints")
    ck("SEND_TO_CLINIC.bat" in A.KIT_FILES,
       "and SEND_TO_CLINIC.bat is now in that built-in list, so AF-1's cure "
       "reaches the machine without a manifest at all")
    print()

    print("=" * 78)
    if BAD:
        print("  %d of %d checks FAILED" % (len(BAD), OK[0]))
        return 1
    print("  ALL %d CHECKS PASSED." % OK[0])
    print()
    print("  SCOPE: this exercises the real functions from the real file. What")
    print("  it does NOT prove is the copy itself -- install_kit's read-only")
    print("  clearing, the backup, and the verify-after-copy are unchanged")
    print("  from S203 and are proven by their own history on this machine.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
