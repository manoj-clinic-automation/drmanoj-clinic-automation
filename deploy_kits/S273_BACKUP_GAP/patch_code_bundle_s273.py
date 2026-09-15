# -*- coding: utf-8 -*-
r"""patch_code_bundle_s273.py -- S273, the six live files that had no off-box copy.

Runs ON THE BOX. It refuses to touch /root/state_backup/code_bundle.py unless that
file is EXACTLY the one this kit was built from, writes a backup beside it, and
re-reads what it wrote.

WHAT IT CHANGES, and nothing else:

  1. THREE new source directories, appended after the existing ones:
       root/assetapp   root/shared   root/deploy
     plus the one folder under /root/deploy the item spine actually runs from.

  2. ONE new source entry for root/finance, carrying "*.json" only, with its own
     secret-shaped-name guard. The EXISTING root/finance entry is not edited --
     a second entry is added beside it, so no file carried today can stop being
     carried. This is what brings freshness_legs.json in.

  3. DEPLOY_ALLOW -- a named list of the ONLY paths permitted to survive the
     existing "deploy" wall. The wall itself is untouched. A path not on the
     list is still dropped, so the git checkout under /root/deploy/repo stays
     excluded apart from the two spine files.

WHAT IT DOES NOT CHANGE: every HARD_EXCLUDE, every BASENAME_EXCLUDE, EXCLUDE_DIRS
itself, the credential content scan, the Drive half, the manifest, the tar, the
crontab capture, the FATAL guards. No secret wall is loosened. Every new file is
still read and scanned by the repository's own publish gate before it is carried,
exactly as every existing file is.

    python3 patch_code_bundle_s273.py --file /root/state_backup/code_bundle.py
    python3 patch_code_bundle_s273.py --file X --check     say what it would do
"""
import argparse
import hashlib
import os
import shutil
import sys

FROM_MD5 = "27e42d0d970a3e475aae7b2fdcebb780"
TO_MD5 = "ed5b483f6eb09f0e3663091a01aaa251"

# ---------------------------------------------------------------- anchor 1
A1 = '    ("root",                         ("*.py",),                                      False, ()),'
A1_NEW = A1 + '''
    # --- v1.3 (S273, 15-Sep-2026) --------------------------------------------
    # S258 held every live pin against this bundle, then against GitHub, then
    # against the encrypted state bundle's own SRC_FILES and SRC_DIRS. SIX files
    # pinned as LIVE had no byte-exact copy in ANY store. Five of them are here;
    # the sixth, freshness_legs.json, comes in through the root/finance "*.json"
    # entry added below. Nothing above this comment changed.
    #
    #   root/assetapp  -- assets.dr-manoj.in. Its DATA (assets.db) has been in
    #                     the encrypted state bundle since S230; its CODE was in
    #                     no store at all. uploads/ and static/ are not matched.
    #   root/shared    -- sarvam_ocr.py, shared by the scanner surfaces.
    #   root/deploy    -- walled off by EXCLUDE_DIRS and still is: only the
    #                     paths named in DEPLOY_ALLOW survive that wall.
    ("root/assetapp",                ("*.py", "*.js", "*.html", "*.sql"),            False, ("users", "secret")),
    ("root/shared",                  ("*.py",),                                      False, ()),
    ("root/deploy",                  ("*.py", "*.txt"),                              False, ()),
    ("root/deploy/repo/deploy_kits/S229_ITEM_SPINE",
                                     ("*.py", "*.sql"),                              False, ()),
    # freshness_legs.json is CONFIGURATION, not code: a leg is widened or retired
    # there and never in freshness.py, so the file IS the setting. A SECOND entry
    # for root/finance rather than an edit to the first, so that no file carried
    # today can stop being carried by this change.
    ("root/finance",                 ("*.json",),                                    False, ("secret", "token", "cred", "key")),'''

# ---------------------------------------------------------------- anchor 2
A2 = 'EXCLUDE_DIRS = ("_retired", "_retired_*", "__pycache__", "backups", "deploy")'
A2_NEW = A2 + '''

# --- v1.3 (S273): the ONLY paths allowed to survive the "deploy" wall above.
#     The wall stays exactly as it is. These are named one at a time because
#     each is a LIVE file that S258 proved exists byte-exact in no other store:
#     not this bundle, not GitHub, not the encrypted state bundle, not the SSD.
#     A path not on this list is still dropped, so /root/deploy/repo -- the
#     deploy clone -- remains excluded apart from the two files the item spine
#     is actually run from. Every one of these is still name-checked and
#     content-scanned afterwards, like every other file.
DEPLOY_ALLOW = (
    "root/deploy/email_agent.py",
    "root/deploy/gen_live_pins.py",
    "root/deploy/verify_live_pins.py",
    "root/deploy/sweep_baseline.txt",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine_schema.sql",
)'''

# ---------------------------------------------------------------- anchor 3
A3 = '''def _path_excluded(rel):
    for part in rel.split("/"):
        for pat in EXCLUDE_DIRS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False'''
A3_NEW = '''def _path_excluded(rel):
    if rel in DEPLOY_ALLOW:          # v1.3 (S273) -- the named exceptions only
        return False
    for part in rel.split("/"):
        for pat in EXCLUDE_DIRS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False'''

# ---------------------------------------------------------------- anchor 4
A4 = '#  code_bundle.py  .  Session 243  .  S243_CODE_BUNDLE  .  v1.2'
A4_NEW = '#  code_bundle.py  .  Session 243  .  S243_CODE_BUNDLE  .  v1.3 (S273)'

EDITS = [("the SOURCES list", A1, A1_NEW),
         ("EXCLUDE_DIRS / DEPLOY_ALLOW", A2, A2_NEW),
         ("_path_excluded", A3, A3_NEW),
         ("the version banner", A4, A4_NEW)]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply_to_text(t):
    for what, old, new in EDITS:
        if t.count(old) != 1:
            raise ValueError("anchor for %s appears %d times, not once" % (what, t.count(old)))
        t = t.replace(old, new)
    return t


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    raw = open(a.file, "rb").read()
    got = md5(raw)
    if TO_MD5 != "REPLACED_AT_BUILD" and got == TO_MD5:
        print("ALREADY INSTALLED -- %s is already the S273 file (%s)" % (a.file, TO_MD5))
        return 0
    if got != FROM_MD5:
        print("REFUSING -- %s is not the file this kit was built from." % a.file)
        print("           it reads   %s" % got)
        print("           expected   %s" % FROM_MD5)
        return 2

    try:
        new_text = apply_to_text(raw.decode("utf-8"))
    except ValueError as exc:
        print("REFUSING -- %s" % exc)
        return 3

    new = new_text.encode("utf-8")
    if TO_MD5 != "REPLACED_AT_BUILD" and md5(new) != TO_MD5:
        print("REFUSING -- the patched file would be %s, not the predicted %s."
              % (md5(new), TO_MD5))
        return 4

    if a.check:
        print("would write %s -> %s" % (got, md5(new)))
        return 0

    bak = "%s.bak_S273_%s" % (a.file, got[:8])
    if not os.path.exists(bak):
        shutil.copyfile(a.file, bak)
    tmp = a.file + ".new"
    with open(tmp, "wb") as fh:
        fh.write(new)
    back = md5(open(tmp, "rb").read())
    if back != md5(new):
        os.remove(tmp)
        print("REFUSING -- the temporary file did not read back identical.")
        return 5
    os.replace(tmp, a.file)
    final = md5(open(a.file, "rb").read())
    if final != md5(new):
        shutil.copyfile(bak, a.file)
        print("ROLLED BACK -- the installed file read back as %s." % final)
        return 6
    print("backup %s" % bak)
    print("INSTALLED -- %s is now %s" % (a.file, final))
    return 0


if __name__ == "__main__":
    sys.exit(main())
