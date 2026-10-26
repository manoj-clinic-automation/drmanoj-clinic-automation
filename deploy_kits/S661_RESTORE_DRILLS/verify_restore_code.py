#!/root/wa/venv/bin/python3
# =============================================================================
#  verify_restore_code.py  ·  kit S661, session S357  ·  the RESTORE side of the code
#  bundle.  Sibling of verify_restore.py (S230, the finance.db drill) and
#  companion to /root/state_backup/code_bundle.py (S243, cron 01:35).
#
#  WHAT THE EXISTING CHAIN PROVES, AND WHAT IT DOES NOT.
#
#  Every night code_bundle.py gathers the live code of the box into
#  code_nightly.tar.gz with its own MANIFEST.md5, re-reads the tarball it just
#  wrote against that manifest, overwrites an owner-owned Drive slot file and
#  reads Drive's md5Checksum back. The nightly on the owner's PC then copies the
#  slot down and checks the same manifest.
#
#  That proves TRANSPORT and SELF-CONSISTENCY AT BUILD TIME. It does NOT prove
#  RECOVERABILITY from Drive: nobody has pulled the slot back down ON THE BOX,
#  untarred it, hashed every member against the manifest, and held the result
#  against the files the box is actually running. A bundle whose gzip is torn,
#  or whose content silently stopped matching the box, would ship and verify
#  and stamp its description exactly like a good one.
#
#  This script closes that hole, and only that hole. It downloads the slot,
#  checks the md5, UNTARS IT (the step nobody has run), verifies every member
#  against the bundle's own MANIFEST.md5, and then compares each member with
#  the LIVE file at its path on the box (/root/..., /etc/...).
#
#  WHAT A DIFFERENCE MEANS. The bundle is taken at 01:35 and the box changes
#  through the day; a member that differs from, or is absent on, the live box
#  is REPORTED, never a failure by itself. FAIL means the restore chain is
#  broken: download, md5, untar or MANIFEST. Unit files are compared the way
#  code_bundle.py masks them (F-518): the manifest row is the md5 of the MASKED
#  bytes, and BUNDLE_INFO.txt records the ORIGINAL md5 per masked file, so a
#  masked unit is held against the live one by that original md5.
#
#  IT IS STRICTLY READ-ONLY, ON BOTH SIDES.
#  Nothing is uploaded. No description is patched, no revision is pinned, no
#  metadata is touched -- there is no patch_meta and no update_content in this
#  file at all (the Drive class below has list, get and download, and nothing
#  else). On the box it writes exactly three things: temp files in the work
#  dir (deleted unless --keep), its own state file and one summary line.
#
#  A VERIFICATION THAT CANNOT STATE ITS OWN AGE HAS NOT BEEN DONE -- which is
#  why EVERY run, PASS or FAIL, leaves the state file behind with an ISO
#  timestamp on it.
#
#  Modes:
#    (default)   download, untar, verify, compare with the live box
#    --dry       preflight: conf, key json present, folder listed, slot present.
#                No download, no untar. Writes last_preflight_iso only.
#    --keep      leave the download and the untarred tree in the work dir
#    --root P    root every path at P instead of "/" (the test harness; on the
#                box it is unset). Same idea as code_bundle.py's ROOT.
#
#  Config: the SAME conf code_bundle.py reads (KEY=VALUE, chmod 600), never in
#  git:   /root/finance/drive_backup.conf
#      SA_JSON=                 service-account json  (required here)
#      FOLDER_ID=               the Drive folder      (required here)
#      WORK_DIR=                optional, default /tmp
#      VERIFY_CODE_STATE_FILE=  optional, default
#                               /root/state_backup/verify_restore_code.state.json
#
#  Exit codes:
#    0 pass · 2 usage · 10 conf/SA · 11 no FOLDER_ID · 13 slot missing
#    20 Drive unreachable · 30 download bad · 31 untar failed
#    32 MANIFEST bad or missing
#
#  No patient data, no ids, no key paths, no secrets in this file (F-185).
# =============================================================================
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth py3.9 EOL noise

# --- the same names code_bundle.py uses, so a rename there is a rename here --
CONF_REL   = "root/finance/drive_backup.conf"        # code_bundle.py CONF_PATH
SLOT       = "code_nightly.tar.gz"                    # code_bundle.py SLOT
MANIFEST   = "MANIFEST.md5"                           # code_bundle.py MANIFEST
CRONFILE   = "crontab.txt"                            # code_bundle.py CRONFILE
UNITSTATE  = "unit_state.txt"                         # code_bundle.py UNITSTATE
INFOFILE   = "BUNDLE_INFO.txt"                        # code_bundle.py INFOFILE
GENERATED  = (CRONFILE, UNITSTATE, INFOFILE, MANIFEST)  # no live file to compare
STATE_REL  = "root/state_backup/verify_restore_code.state.json"
SUMMARY_REL = "root/state_backup/verify_restore_code.summary.txt"
CHUNK      = 1 << 20
LIST_N     = 12                       # differing / absent paths named, at most
STALE_H    = 30                       # a bundle older than this gets a warning


def log(*a):
    print("[%s]" % time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)


def under_root(root, rel):
    return os.path.join(root, rel.lstrip("/"))


# ---------------------------------------------------------------- config ----
def load_conf(conf_path):
    conf = {}
    if os.path.exists(conf_path):
        for line in open(conf_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def find_sa_json(conf):
    """Conf only. The shipper also searches a few well-known paths; this file
    does not repeat them, because key paths do not belong in the repository
    (F-185). Whatever the shipper found, SA_JSON already records."""
    p = conf.get("SA_JSON")
    return p if p and os.path.exists(p) else None


def work_dir(conf):
    d = conf.get("WORK_DIR") or "/tmp"
    if not os.path.isdir(d):
        os.makedirs(d, 0o700)
    return d


def state_path(conf, root):
    return conf.get("VERIFY_CODE_STATE_FILE") or under_root(root, STATE_REL)


def summary_path(conf, root):
    return conf.get("VERIFY_CODE_SUMMARY_FILE") or under_root(root, SUMMARY_REL)


# ----------------------------------------------------------------- drive ----
def make_session(sa_json):
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"])
    return AuthorizedSession(creds)


class Drive:
    """The three READ-ONLY Drive calls this job needs, and nothing else.
    There is deliberately no update, no patch and no pin in this class."""
    API = "https://www.googleapis.com/drive/v3"

    def __init__(self, session):
        self.s = session

    def _ck(self, r, what):
        if r.status_code >= 300:
            raise RuntimeError("%s -> HTTP %s: %s" % (what, r.status_code, r.text[:300]))
        return r

    def list(self, folder_id):
        files, token = [], None
        while True:
            params = {"q": "'%s' in parents and trashed=false" % folder_id,
                      "fields": "nextPageToken,files(id,name,size,md5Checksum,description)",
                      "pageSize": "1000"}
            if token:
                params["pageToken"] = token
            r = self._ck(self.s.get(self.API + "/files", params=params), "list")
            j = r.json()
            files += j.get("files", [])
            token = j.get("nextPageToken")
            if not token:
                return files

    def get(self, file_id):
        r = self._ck(self.s.get(self.API + "/files/" + file_id,
                                params={"fields": "id,name,size,md5Checksum,description"}),
                     "file get")
        return r.json()

    def download(self, file_id, dest):
        """Stream the content to disk, never into memory."""
        r = self.s.get(self.API + "/files/%s" % file_id,
                       params={"alt": "media"}, stream=True)
        self._ck(r, "download")
        n = 0
        with open(dest, "wb") as fh:
            for b in r.iter_content(CHUNK):
                if b:
                    fh.write(b)
                    n += len(b)
        return n


def find_slot(listing, name):
    """The one owner-owned slot file, by exact name -- the same name the
    shipper writes, taken from the same constant. None when it is gone."""
    return {f["name"]: f for f in listing}.get(name)


# ---------------------------------------------------------------- verify ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def safe_members(tf):
    """Only directories and regular files with clean relative names. A member
    that could write outside the work dir, or is a link or device, is refused
    outright -- a restore drill must never be the thing that plants a file."""
    out = []
    for m in tf.getmembers():
        parts = m.name.replace("\\", "/").split("/")
        if m.name.startswith(("/", "\\")) or ".." in parts or parts[0] == "":
            raise RuntimeError("unsafe member path in the archive")
        if m.isdir():
            out.append(m)
        elif m.isfile():
            out.append(m)
        else:
            raise RuntimeError("archive carries a non-regular member")
    return out


def untar(src, dest):
    """Extract into dest and return the count of regular files written.
    filter="data" where this python has it (3.11.4+); the member walk above
    does the same refusals on an older one."""
    with tarfile.open(src, "r:gz") as tf:
        members = safe_members(tf)
        try:
            tf.extractall(dest, members=members, filter="data")
        except TypeError:
            tf.extractall(dest, members=members)
    return sum(1 for m in members if m.isfile())


def read_manifest(tree):
    """[(md5, rel)] from the bundle's own MANIFEST.md5 -- rows are
    '<md5>  <rel>' with two spaces, rel rooted at the box's root without a
    leading slash (code_bundle.py build())."""
    p = os.path.join(tree, MANIFEST)
    rows = []
    with open(p, "r", encoding="utf-8") as fh:
        for row in fh.read().splitlines():
            if not row.strip():
                continue
            m, rel = row.split("  ", 1)
            rows.append((m.strip(), rel.strip()))
    return rows


def read_info(tree):
    """BUNDLE_INFO.txt -> (built, {rel: original_md5}). code_bundle.py writes
    'built=<ts>' and, per masked unit, 'masked=<rel> original_md5=<md5>
    names=<...>' (never a value). Absent or odd lines simply yield less."""
    p = os.path.join(tree, INFOFILE)
    built, masked = None, {}
    if not os.path.exists(p):
        return built, masked
    with open(p, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh.read().splitlines():
            if line.startswith("built="):
                built = line[len("built="):].strip()
            elif line.startswith("masked="):
                fields = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
                if fields.get("masked") and fields.get("original_md5"):
                    masked[fields["masked"]] = fields["original_md5"]
    return built, masked


def verify_manifest(tree, rows):
    """Hash every extracted member against its row. (ok, bad, missing)."""
    ok = bad = missing = 0
    for m, rel in rows:
        p = os.path.join(tree, rel)
        if not os.path.isfile(p):
            missing += 1
        elif md5_file(p) != m:
            bad += 1
        else:
            ok += 1
    return ok, bad, missing


def compare_live(root, rows, masked):
    """Each manifest row against the live file at its path under root.
    (equal, differs, absent, [differing rels], [absent rels]). Generated
    members have no live counterpart and are skipped."""
    equal = differs = absent = 0
    diff_list, absent_list = [], []
    for m, rel in rows:
        if rel in GENERATED:
            continue
        live = under_root(root, rel)
        if not os.path.isfile(live):
            absent += 1
            absent_list.append(rel)
            continue
        want = masked.get(rel, m)
        if md5_file(live) == want:
            equal += 1
        else:
            differs += 1
            diff_list.append(rel)
    return equal, differs, absent, diff_list, absent_list


def age_hours(stamp):
    """Hours since a 'YYYY-MM-DD HH:MM:SS' stamp in local time, or None."""
    try:
        t = time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M:%S"))
        return (time.time() - t) / 3600.0
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ state ---
def load_state(p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except Exception:
        return {}


def write_state(p, new):
    """Merge over what is there (a preflight must not erase the last real
    verify and vice versa), then atomic replace, mode 600."""
    state = load_state(p)
    state.update(new)
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, 0o700)
        tmp = p + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, p)
        os.chmod(p, 0o600)
        log("state written:", p)
    except OSError as ex:
        log("WARNING: could not write the state file", p, ":", ex)


def append_summary(p, line):
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, 0o700)
        with open(p, "a") as fh:
            fh.write(line.rstrip("\n") + "\n")
    except OSError as ex:
        log("WARNING: could not write the summary line:", ex)


def cleanup(paths, keep):
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        if keep:
            log("kept:", p)
            continue
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.unlink(p)
            log("deleted:", p)
        except OSError as ex:
            log("WARNING: could not delete", p, ":", ex)


# ------------------------------------------------------------------- run ----
def _connect(root):
    conf_path = under_root(root, CONF_REL)
    conf = load_conf(conf_path)
    if not os.path.exists(conf_path):
        die(10, "no conf at", conf_path, "-- this verifier reads the SAME conf"
            " the shipper reads; install and preflight the shipper first.")
    sa = find_sa_json(conf)
    if not sa:
        die(10, "SA_JSON is not set in", conf_path, "or does not point at an"
            " existing file -- this verifier reads the key path from the conf"
            " and never carries one of its own.")
    fid = conf.get("FOLDER_ID")
    if not fid:
        die(11, "FOLDER_ID is not set in", conf_path)
    return conf, sa, fid


def preflight(root="/", drive_cls=Drive, session_maker=make_session):
    """--dry: prove conf, key json, folder and slot. No download."""
    conf, sa, fid = _connect(root)
    sp = state_path(conf, root)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    pre = {"last_preflight_iso": now, "preflight": "FAIL (did not start)"}
    try:
        log("conf ok · SA_JSON present · FOLDER_ID set · work dir", work_dir(conf))
        try:
            listing = drive_cls(session_maker(sa)).list(fid)
        except Exception as ex:
            pre["preflight"] = "FAIL (drive unreachable)"
            die(20, "cannot reach Google Drive:", ex)
        meta = find_slot(listing, SLOT)
        if meta is None:
            pre["preflight"] = "FAIL (slot missing)"
            die(13, "slot file", SLOT, "is not in the Drive folder")
        log("slot present:", SLOT, "·", meta.get("size", "?"), "bytes · drive md5",
            meta.get("md5Checksum") or "(none)")
        log("    description:", (meta.get("description") or "(empty)")[:300])
        pre["preflight"] = "OK"
        log("PREFLIGHT OK -- nothing downloaded; run without --dry for the drill")
        return 0
    finally:
        write_state(sp, pre)


def verify(root="/", keep=False, drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect(root)
    sp = state_path(conf, root)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")
    state = {"last_verify_iso": now_iso, "slot": SLOT,
             "result": "FAIL (did not start)", "drive_md5": None,
             "members": None, "manifest_rows": None, "manifest_bad": None,
             "manifest_missing": None, "equal": None, "differs": None,
             "absent": None, "built": None}
    wd = work_dir(conf)
    tgz_path = tree = None
    warned = []

    def fail(code, label, *msg):
        state["result"] = "FAIL (%s)" % label
        die(code, *msg)

    try:
        # -- 1 · the slot ----------------------------------------------------
        try:
            d = drive_cls(session_maker(sa))
            listing = d.list(fid)
        except Exception as ex:
            fail(20, "drive unreachable", "cannot reach Google Drive:", ex)
        meta = find_slot(listing, SLOT)
        if meta is None:
            fail(13, "slot missing", "slot file", SLOT, "is not in the Drive"
                 " folder -- it is owner-owned and must exist; recreate it from"
                 " the owner's account (the service account cannot, it has"
                 " zero quota).")
        drive_md5 = meta.get("md5Checksum")
        log("1 · slot file:", meta.get("name"), "·", meta.get("size", "?"),
            "bytes · drive md5", drive_md5 or "(none)")
        log("    description:", (meta.get("description") or "(empty)")[:300])
        state["drive_md5"] = drive_md5

        # -- 2 · download ----------------------------------------------------
        fd, tgz_path = tempfile.mkstemp(suffix=".tar.gz", prefix="restore_code_", dir=wd)
        os.close(fd)
        os.chmod(tgz_path, 0o600)
        try:
            got = d.download(meta["id"], tgz_path)
        except SystemExit:
            raise
        except Exception as ex:
            fail(20, "download failed", "download of", SLOT, "failed:", ex)
        log("2 · downloaded %d bytes -> %s" % (got, tgz_path))

        # -- 3 · the bytes that arrived --------------------------------------
        size = os.path.getsize(tgz_path)
        if size == 0:
            fail(30, "empty download", "the download is ZERO BYTES --"
                 " nothing to restore from")
        if meta.get("size") is not None and str(meta["size"]).isdigit() \
                and int(meta["size"]) != size:
            fail(30, "truncated download", "TRUNCATED: Drive reports %s bytes,"
                 " %d arrived" % (meta["size"], size))
        local_md5 = md5_file(tgz_path)
        if drive_md5 and local_md5 != drive_md5:
            fail(30, "download md5", "download DID NOT VERIFY: drive md5 %s vs"
                 " downloaded %s" % (drive_md5, local_md5))
        state["drive_md5"] = local_md5
        log("3 · md5 of the downloaded bytes matches Drive:", local_md5)

        # -- 4 · the step nobody has run -------------------------------------
        tree = tempfile.mkdtemp(prefix="restore_code_tree_", dir=wd)
        os.chmod(tree, 0o700)
        try:
            members = untar(tgz_path, tree)
        except SystemExit:
            raise
        except Exception as ex:
            fail(31, "untar", "UNTAR FAILED (%s: %s) -- the archive is corrupt;"
                 " transport verified these bytes but they are not a usable"
                 " tar.gz. This is the check that had never been run."
                 % (type(ex).__name__, ex))
        state["members"] = members
        log("4 · untarred cleanly: %d members (gzip CRC ok) -> %s" % (members, tree))

        # -- 5 · against its own manifest ------------------------------------
        try:
            rows = read_manifest(tree)
        except SystemExit:
            raise
        except Exception as ex:
            fail(32, "manifest missing", "the bundle carries no readable %s"
                 " (%s: %s) -- not a code bundle" % (MANIFEST, type(ex).__name__, ex))
        if not rows:
            fail(32, "manifest empty", "%s is empty" % MANIFEST)
        m_ok, m_bad, m_missing = verify_manifest(tree, rows)
        state["manifest_rows"] = len(rows)
        state["manifest_bad"] = m_bad
        state["manifest_missing"] = m_missing
        unlisted = members - m_ok - m_bad - (1 if os.path.exists(
            os.path.join(tree, INFOFILE)) else 0) - 1   # INFOFILE and MANIFEST carry no row
        log("5 · manifest: %d rows · %d ok · %d bad · %d listed-but-absent"
            % (len(rows), m_ok, m_bad, m_missing))
        if m_bad or m_missing:
            fail(32, "manifest", "the restored tree does NOT match the bundle's"
                 " own manifest: %d bad, %d missing" % (m_bad, m_missing))
        if unlisted > 0:
            warned.append("%d member(s) without a manifest row" % unlisted)
            log("    *** WARNING *** %d member(s) carry no manifest row" % unlisted)

        built, masked = read_info(tree)
        state["built"] = built
        age = age_hours(built)
        if built:
            log("    built=%s (%s)" % (built, "%.1f h ago" % age if age is not None else "age unknown"))
            if age is not None and age > STALE_H:
                warned.append("bundle is %.0f h old" % age)
                log("    *** WARNING *** the bundle is older than %d h -- the"
                    " 01:35 job may not be running" % STALE_H)
        else:
            log("    %s carries no built= stamp" % INFOFILE)

        # -- 6 · against the live box ----------------------------------------
        equal, differs, absent, diff_list, absent_list = compare_live(root, rows, masked)
        state["equal"], state["differs"], state["absent"] = equal, differs, absent
        log("6 · against the live box (root %s): %d equal · %d differ · %d absent"
            " · %d masked unit(s) held by original md5"
            % (root, equal, differs, absent, len(masked)))
        for rel in diff_list[:LIST_N]:
            log("      differs   /" + rel)
        if len(diff_list) > LIST_N:
            log("      ... and %d more differ" % (len(diff_list) - LIST_N))
        for rel in absent_list[:LIST_N]:
            log("      absent    /" + rel)
        if len(absent_list) > LIST_N:
            log("      ... and %d more absent" % (len(absent_list) - LIST_N))
        if differs or absent:
            log("    This is a REPORT, not a failure. The bundle is taken at"
                " 01:35 and the box changes through the day; a member that"
                " differs or is absent says the box moved on since the"
                " bundle, or that a file was retired. The restore itself is"
                " sound -- the bytes untarred and matched the manifest.")

        # -- 7 · verdict -----------------------------------------------------
        state["result"] = "PASS" + (" (with warnings)" if warned else "")
        state["last_pass_iso"] = now_iso
        log("RESTORE VERIFY PASS -- %s · %d members · %d manifest rows · %d equal"
            " · %d differ · %d absent" % (SLOT, members, len(rows), equal, differs, absent))
        if warned:
            log("PASS carries %d warning(s): %s" % (len(warned), "; ".join(warned)))
        return 0
    finally:
        # deletion happens on every path, failures included
        cleanup([tgz_path, tree], keep)
        if not state["result"].startswith("PASS"):
            state["last_failure_iso"] = now_iso
            log("RESTORE VERIFY FAIL -- %s · %s" % (SLOT, state["result"]))
        write_state(sp, state)
        append_summary(summary_path(conf, root),
                       "%s %s slot=%s drive_md5=%s members=%s manifest_bad=%s"
                       " equal=%s differs=%s absent=%s built=%s"
                       % (now_iso, state["result"], SLOT, state["drive_md5"],
                          state["members"], state["manifest_bad"], state["equal"],
                          state["differs"], state["absent"], state["built"]))


USAGE = ("usage: verify_restore_code.py [--dry] [--keep] [--root PATH]\n"
         "  (default)   download the code bundle, untar, verify the manifest,\n"
         "              compare with the live box\n"
         "  --dry       preflight only: conf, folder, slot present; no download\n"
         "  --keep      leave the download and the untarred tree in the work dir\n"
         "  --root P    root every path at P (test harness)\n"
         "read-only: this never writes to Drive.")


def main(argv, drive_cls=Drive, session_maker=make_session):
    keep = dry = False
    root = os.environ.get("ROOT", "/") or "/"
    args = list(argv[1:])
    while args:
        a = args.pop(0)
        if a == "--keep":
            keep = True
        elif a == "--dry":
            dry = True
        elif a == "--root" and args:
            root = args.pop(0)
        else:
            print(USAGE)
            return 2
    if dry:
        return preflight(root=root, drive_cls=drive_cls, session_maker=session_maker)
    return verify(root=root, keep=keep, drive_cls=drive_cls, session_maker=session_maker)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
