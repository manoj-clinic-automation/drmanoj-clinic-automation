#!/usr/bin/env python3
"""apply_s424.py -- kit S424_PHI_STORES_BACKUP (session 284, 27-Sep-2026). Two anchored edits to
/root/state_backup/clinic_state_backup.py (v4, 05397337), idempotent. usage: apply_s424.py <clinic_state_backup.py>

FINDING (S284): /root/wa/casepack -- the Surgical Case Pack's case ledger, consent ledger, every saved bundle and
consent -- is in NO backup. SRC_DIRS walks one level deep and never named it; the code bundle takes only its
*.html / *.py. Vitals & Plan (S423) keeps its records beside it in /root/wa/vitals.

v5 adds SRC_TREES: each tree walked FULLY (every depth), every file taken except code, temp files and anything the
secret patterns match (matched FIRST, as in _walk_dir_data), into data/<tree name>/<relative path> through the same
take(). For the vanished-source guard (FATAL 41) a tree counts as ONE source -- its apps version and supersede
their own files, and one superseded file must never refuse the whole night."""
import sys

TAG = "# v5 (S424): SRC_TREES"
E1_OLD = '''    "/root/finance/spine/readings",
]
'''
E1_NEW = '''    "/root/finance/spine/readings",
]
# v5 (S424): SRC_TREES -- the PHI stores that lived in NO backup (found at S284): the Surgical Case Pack
# (case ledger, consent ledger, every bundle and consent, case_archive/<year>/<patient>/...) and Vitals & Plan
# (S423: its two ledgers and plan_archive/<year>/<UID>/*.pdf). Walked to every depth, every file except code and
# temp files, secret patterns matched first. For FATAL 41 a tree is ONE source (see gather).
SRC_TREES = [
    "/root/wa/casepack",
    "/root/wa/vitals",
]
TREE_SKIP_PARTS = (".tmp", ".bak", ".swp", ".lock")


def _walk_tree(d):
    """Every file under d at every depth -> [(fullpath, relpath)], plus the count of secrets skipped.
    Secret patterns FIRST (they win), then code (DIR_SKIP_EXT) and temp/backup names."""
    out, secrets = [], 0
    d = d.rstrip(os.sep)
    for base, dirs, files in os.walk(d):
        dirs[:] = sorted(x for x in dirs if x not in DIR_SKIP_NAMES)
        for name in sorted(files):
            full = os.path.join(base, name)
            low = name.lower()
            if is_secret(name):
                secrets += 1
                continue
            if low.endswith(DIR_SKIP_EXT) or any(p in low for p in TREE_SKIP_PARTS):
                continue
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            out.append((full, os.path.relpath(full, d)))
    return out, secrets
'''
E2_OLD = '''            take(src, os.path.join(label, rel))

    _gather_shape(conf, shape_dir, g)
'''
E2_NEW = '''            take(src, os.path.join(label, rel))

    # v5 (S424): the PHI trees. Taken file by file through take(); then, for the vanished-source guard, the
    # tree's files are replaced by the tree itself -- ONE source, so a case bundle its app supersedes never
    # refuses the night, while a whole store that vanishes still does.
    for d in SRC_TREES:
        if not os.path.isdir(d):
            g.sources_missing.append(d)
            continue
        label = os.path.basename(d.rstrip("/"))
        before = len(g.sources_present)
        found, sec = _walk_tree(d)
        g.secrets_skipped += sec
        for src, rel in found:
            take(src, os.path.join(label, rel))
        del g.sources_present[before:]
        g.sources_present.append(d)

    _gather_shape(conf, shape_dir, g)
'''


def apply(path):
    s = open(path, encoding="utf-8", newline="").read()
    if TAG in s:
        return "already"
    for old in (E1_OLD, E2_OLD):
        if s.count(old) != 1:
            raise SystemExit("REFUSED: an anchor is not in the file exactly once: %r" % old[:60])
    s = s.replace(E1_OLD, E1_NEW).replace(E2_OLD, E2_NEW)
    open(path, "w", encoding="utf-8", newline="").write(s)
    return "patched"


if __name__ == "__main__":
    print("clinic_state_backup.py :", apply(sys.argv[1]))
