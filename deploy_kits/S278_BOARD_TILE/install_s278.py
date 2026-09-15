#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s278.py -- S278_BOARD_TILE

Adds ONE tile to the owner's portal: "System Board", the first tile in the
Clinic group, opening the Sanjeevni System Board.

WHAT IT TOUCHES
    /root/portal/portal.py   -- two insertions, both additive:
                                one entry at the head of TILES,
                                one entry in the _TILE_GROUP map.
    nothing else. No tile_grants.json change, no gate change, no database.

WHO SEES IT
    roles ["doctor"] only -- the owner. Staff logins are untouched and cannot
    see it, which is correct: the board is not a page they can open.

SAFETY
    * refuses unless /root/portal/portal.py is exactly dc8f363e389259130764219e01a6b42d
      -- the live pin, byte-confirmed against the box's own nightly bundle (S259).
    * refuses unless each anchor occurs EXACTLY once.
    * backs up to portal.py.bak_S278_dc8f363e before writing.
    * compiles the patched file before it is put in place.
    * restarts clinic-portal, then checks the service is active.
    * ROLLS BACK byte-identically and restarts again if anything fails.
"""
import hashlib
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile

TARGET = "/root/portal/portal.py"
EXPECT = "dc8f363e389259130764219e01a6b42d"
BACKUP = TARGET + ".bak_S278_dc8f363e"
SERVICE = "clinic-portal"

ANCHOR_TILES = '''TILES = [
    # ============================ DOCTOR + shared ============================
'''

NEW_TILE = '''    {"icon": "\\U0001F9ED", "name": "System Board",
     "desc": "What is done \\u00b7 what is running \\u00b7 what needs you", "live": True,
     "url": "https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk",
     "roles": ["doctor"]},

'''

ANCHOR_GROUP = '''    "GMB Review Assist": "Clinic", "Forms & Downloads": "Clinic",
'''

NEW_GROUP = '''    "System Board": "Clinic",
'''


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fail(msg):
    print("REFUSED: %s" % msg)
    print("Nothing was changed.")
    sys.exit(1)


def main():
    if not os.path.isfile(TARGET):
        fail("%s is not there" % TARGET)

    with open(TARGET, "r", encoding="utf-8") as fh:
        src = fh.read()

    # Asked first on purpose: running this twice is harmless and must say so
    # plainly, not raise a fingerprint alarm about its own earlier run.
    if '"name": "System Board"' in src:
        print("Already installed -- the tile is there. Nothing changed.")
        return 0

    before = md5(TARGET)
    if before != EXPECT:
        fail("portal.py is %s, expected %s -- the file has moved on since this kit "
             "was built. Do not force it; the kit must be rebuilt against the file "
             "as it is now." % (before, EXPECT))

    for name, anchor in (("TILES head", ANCHOR_TILES), ("_TILE_GROUP", ANCHOR_GROUP)):
        n = src.count(anchor)
        if n != 1:
            fail("the %s anchor occurs %d times, expected exactly 1" % (name, n))

    out = src.replace(ANCHOR_TILES, ANCHOR_TILES + NEW_TILE)
    out = out.replace(ANCHOR_GROUP, ANCHOR_GROUP + NEW_GROUP)

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(TARGET), prefix=".s278_", suffix=".py")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(out)
        py_compile.compile(tmp, cfile=tmp + "c", doraise=True)
        os.remove(tmp + "c")
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        fail("the patched file does not compile: %s" % e)

    shutil.copy2(TARGET, BACKUP)
    print("backup   : %s  (%s)" % (BACKUP, md5(BACKUP)))

    shutil.copystat(TARGET, tmp)
    os.replace(tmp, TARGET)
    after = md5(TARGET)
    print("portal.py: %s -> %s" % (before, after))

    def restart():
        return subprocess.call(["systemctl", "restart", SERVICE])

    def active():
        return subprocess.call(["systemctl", "is-active", "--quiet", SERVICE]) == 0

    if restart() != 0 or not active():
        print("the portal did not come back -- rolling back")
        shutil.copy2(BACKUP, TARGET)
        restart()
        ok = active()
        print("rolled back to %s ; portal active: %s" % (md5(TARGET), ok))
        print("REFUSED: clinic-portal would not start with the new file.")
        print("portal.py is back to the bytes it had. The backup at %s was left "
              "in place deliberately." % BACKUP)
        sys.exit(1)

    print("clinic-portal restarted and active.")
    print("")
    print("DONE -- the System Board tile is the first tile on your portal.")
    print("To undo:  \\cp %s %s && systemctl restart %s" % (BACKUP, TARGET, SERVICE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
