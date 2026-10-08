#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""make_s499.py -- kit S499_MEDICAL_AGENT_BACKUP -- builds medical_agent.py S499.1 from S205.1's own bytes.

Rule 2: built from the live bytes (medical_agent.py 70d5c4e3, deploy_kits\S212_LIVE_TOOLS\medical\medical_agent.py, the file
the medical PC's heartbeat reports as running). Every anchor must occur exactly once, or nothing is built. The new text is
built AND COMPILED in memory before a byte is written.

  1  the stick leg     Marg's own automatic backup (D:\MARGERP\serverbackup: the newest database file and the files written
                       beside it) is copied each pass to the agent's OWN folder on the stick, E:\MargAuto_by_agent\<date_time>\,
                       via a temp name, size + md5 checked against the source, the source's time kept. A source Marg may still
                       be writing is left for the next pass. The newest 30 sets are kept THERE; nothing else on the stick is
                       touched; nothing is ever deleted on Drive.
  2  truthful words    heartbeat.json keeps every key and gains: the hand-made backup's name and age, the automatic copy's
                       name and age, the newest database file on D: and the newest one in the offsite folder. Loud ONLY when
                       the newest backup of ANY kind on the stick is over 3 days old, or the stick has been out -- or in but
                       holding no Marg backup -- for over a day. A gap in Marg's own backup alone is one calm line.
  3  for the record    once a day, the file LIST (never a member) of the newest hand-made .mbk and of the automatic database
                       file nearest to it in time: is it a zip, how many members, how many bytes, a hash of the names.
  4  the prune alarm   judged by the prune's own rule (3 old copies per kit file, every file the kit channel manages, the
                       manifest's included) or by a prune that could not remove a file -- no longer "more than 5".
  5  the hourly loop   three backups with ONE name in three folders of the stick shared one offsite name and were copied over
                       each other every pass (7,429,171 bytes an hour). Sources that share a name now get distinct offsite names.

    make_s499.py --agent <medical_agent.py S205.1> --out DIR
"""
import argparse
import hashlib
import os

FROM = "70d5c4e3c439eaa049acb27f9851688c"

# (old, new): old occurs exactly once.   (start, end, new): both occur exactly once, start before end; the span start..end is replaced.
EDITS = [
    # ---- A. the version
    (r'''AGENT_VERSION = "S205.1"''',
     r'''AGENT_VERSION = "S499.1"'''),

    # ---- B. the head: where this file writes, said truthfully
    (r'''Reads Marg's folders; writes only inside D:\\SendToClinic and the Drive
FromMedical folder. Never writes inside D:\\MARGERP.
"""''',
     r'''Reads Marg's folders; writes only inside D:\\SendToClinic and the Drive
FromMedical folder. Never writes inside D:\\MARGERP.

S203 added the Drive MargBackups folder (the offsite copy of the backups).
S499 adds ONE folder on the backup stick, E:\\MargAuto_by_agent -- the agent's
own; it writes and deletes there and nowhere else on the stick.
"""'''),

    # ---- C. the constants of the stick leg
    (r'''BACKUP_EXTS = (".mbk", ".jmbkh", ".zip", ".bak", ".rar", ".7z")
''',
     r'''BACKUP_EXTS = (".mbk", ".jmbkh", ".zip", ".bak", ".rar", ".7z")
# S499: the stick leg. The .mbk on the stick is made only when a person accepts
# Marg's prompt; Marg's OWN automatic backup was copied offsite every hour and
# never to the stick. Now it goes to the agent's own folder there.
STICK_AUTO_DIRNAME = "MargAuto_by_agent"
STICK_AUTO_KEEP = 30          # newest sets kept in that folder -- and only there
STICK_SET_WINDOW = 300        # s: written this close to the database file = its set
STICK_QUIET_SECS = 120        # s: a folder written this recently is left alone
STICK_MTIME_SLACK = 3.0       # s: a FAT stick keeps times to two seconds
STICK_ABSENT_LOUD_DAYS = 1    # the stick unplugged longer than this is called out
STICK_FREE_FACTOR = 10        # copy only with ten times the set's size free
FUTURE_SLACK = 86400          # s: a file dated further ahead is ignored for ages
HANDMADE_CALM_DAYS = 7        # an older hand-made backup is mentioned, calmly
ZIP_COMPARE_EVERY = 86400     # s: the file-list comparison, at most once a day
KIT_BACKUP_KEEP = 3           # .before_ copies the prune keeps per kit file
'''),

    # ---- D. the prune and its count: every file the kit channel manages, judged by the prune's own rule
    (r'''def prune_kit_backups(keep=3):''',
     r'''            n += sum(1 for f in os.listdir(d) if f.startswith(base))
        except OSError:
            pass
    return n
''',
     r'''# S499: what the last prune did, so the heartbeat can judge the prune by the
# prune's own rule instead of by a number picked in S201 (see kit_backup_state).
_PRUNE_LAST = {"ran": False, "removed": 0, "failed": 0, "failed_names": [],
               "covered": []}


def _kit_dests():
    """Every file the kit channel manages on this PC: the built-in list plus
    whatever the manifest legally adds.

    S499. The prune and its count walked KIT_FILES only, so a file delivered by
    KIT_MANIFEST.txt had its .before_ copies neither pruned nor counted.
    """
    try:
        files, _want, _notes = manifest_files(find_drive_kit())
    except Exception:                                          # noqa: BLE001
        files = dict(KIT_FILES)
    seen, out = set(), []
    for dest in files.values():
        k = _win_norm(dest)
        if k not in seen:
            seen.add(k)
            out.append(dest)
    return out


def _kit_baks(dest):
    """(folder, [names]) of the .before_ copies lying beside one kit file."""
    d = os.path.dirname(dest) or "."
    base = os.path.basename(dest) + ".before_"
    return d, [f for f in os.listdir(d) if f.startswith(base)]


def prune_kit_backups(keep=KIT_BACKUP_KEEP):
    """Keep the newest few .before_ backups beside each kit file; bin the rest.

    S201.6: clear the read-only flag before removing, and report FAILURES as
    well as successes. S201.5 removed nothing and said nothing, because every
    os.remove hit the same read-only attribute that had blocked the install,
    and the log line only fired when something was actually deleted. A tidy-up
    that cannot tidy, silently, is the fault it was written to clean up after.

    S499: every file the kit channel manages, the manifest's included, and the
    result is kept for the heartbeat.
    """
    import stat as _st
    removed = failed = 0
    failed_names, covered = [], []
    for dest in _kit_dests():
        try:
            d, names = _kit_baks(dest)
            baks = sorted(names,
                          key=lambda f: os.path.getmtime(os.path.join(d, f)),
                          reverse=True)
        except OSError:
            continue
        covered.append(_win_norm(dest))
        for f in baks[keep:]:
            fp = os.path.join(d, f)
            try:
                try:
                    os.chmod(fp, _st.S_IWRITE)
                except OSError:
                    pass
                os.remove(fp)
                removed += 1
            except OSError:
                failed += 1
                failed_names.append(fp)
    _PRUNE_LAST.update({"ran": True, "removed": removed, "failed": failed,
                        "failed_names": failed_names[:5], "covered": covered})
    if removed or failed:
        log("pruned %d stale kit backup(s)%s"
            % (removed, ("; %d could NOT be removed" % failed) if failed else ""))
    return removed, failed


def backup_count():
    """How many .before_ files are lying beside the kit files right now."""
    n = 0
    for dest in _kit_dests():
        try:
            n += len(_kit_baks(dest)[1])
        except OSError:
            pass
    return n


def kit_backup_state(keep=KIT_BACKUP_KEEP):
    """The .before_ copies, judged by what the prune actually allows.

    S499. The heartbeat said "the prune is not working" above FIVE files, while
    the prune keeps THREE per kit file -- twelve are legal for the four
    built-in files alone -- so the line was a false alarm for weeks. Now it
    fires only when a prune could not remove a file, or when a file the prune
    has been over still has more than it keeps.
    """
    dests = _kit_dests()
    covered = set(_PRUNE_LAST.get("covered") or [])
    n, over = 0, []
    for dest in dests:
        try:
            c = len(_kit_baks(dest)[1])
        except OSError:
            continue
        n += c
        if c > keep and _win_norm(dest) in covered:
            over.append("%s: %d" % (os.path.basename(dest), c))
    return {"count": n, "files": len(dests), "keep": keep,
            "allowed": keep * len(dests), "over": over[:5],
            "prune_ran": bool(_PRUNE_LAST.get("ran")),
            "prune_failed": int(_PRUNE_LAST.get("failed") or 0),
            "prune_failed_names": list(_PRUNE_LAST.get("failed_names") or [])[:3]}
'''),

    # ---- E. the walk of the stick: the agent's own folder is not a hand-made backup and is not sent offsite a second time
    (r'''            dirs[:] = [d for d in dirs if d.lower() not in
                       ("system volume information", "$recycle.bin")]
''',
     r'''            dirs[:] = [d for d in dirs if d.lower() not in
                       ("system volume information", "$recycle.bin")]
            # S499: the agent's own folder at the top of the stick holds copies
            # of serverbackup, which goes offsite from D: itself (below).
            if _same_dir(base, BACKUP_STICK):
                dirs[:] = [d for d in dirs
                           if d.lower() != STICK_AUTO_DIRNAME.lower()]
'''),

    # ---- F. the backup pass: the stick leg, the ages, the offsite names, the comparison
    (r'''def backup_pass():''',
     r'''            return json.load(fh) or {}
    except (OSError, ValueError):
        return {}
''',
     r'''# --------------------------------------------------------------------------
# S499: the stick leg, the ages said truthfully, the file-list comparison
# --------------------------------------------------------------------------
_SET_NAME = re.compile(r"^\d{4}-\d\d-\d\d_\d{6}$")
_NOT_WHOLE = (".part", ".copying")


def _when(ts, fmt="%d-%b-%Y %H:%M"):
    """A file's time in words -- or '?' for a time Windows cannot express (a
    year before 1970 or after 9999 raises OverflowError / OSError /
    ValueError there). One bad file must never stop a pass or a heartbeat."""
    try:
        return dt.datetime.fromtimestamp(float(ts)).strftime(fmt)
    except (OverflowError, OSError, ValueError, TypeError):
        return "?"


def _same_dir(a, b):
    return (os.path.normcase(os.path.abspath(a))
            == os.path.normcase(os.path.abspath(b)))


def _is_marg_blob(name):
    """Marg's own automatic database backup, <n>_c18_d_<x>.<y>_<n>.

    The financial year sits in the name (c18 = 2026-27, c17 the year before),
    so the digits are not spelt out: next April's files will say c19."""
    return re.search(r"_c\d\d_", name.lower()) is not None


def _stick_auto_dir():
    return os.path.join(BACKUP_STICK, STICK_AUTO_DIRNAME)


def _serverbackup_files():
    """(path, size, mtime) for every file in Marg's own backup folder, newest
    first. Empty if the folder is away or cannot be read."""
    sb = []
    try:
        if os.path.isdir(SERVERBACKUP):
            for f in os.listdir(SERVERBACKUP):
                p = os.path.join(SERVERBACKUP, f)
                if not os.path.isfile(p):
                    continue
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                sb.append((p, st.st_size, st.st_mtime))
    except OSError:
        pass
    sb.sort(key=lambda r: r[2], reverse=True)
    return sb


def _newest_auto_set(sb):
    """Marg's newest automatic backup as a SET: the newest database file first,
    then every file written in that folder within STICK_SET_WINDOW of it.

    Measured on this PC (census, 26-Aug-2026): <weekday>.mst is written first,
    the database file under a minute later, <n>_d01_retail_<x> seconds after
    that. A day on which Marg writes only the .mst has no database file and is
    not a backup. Returns ([rows], why_not)."""
    blobs = [r for r in sb if _is_marg_blob(os.path.basename(r[0]))]
    if not blobs:
        return [], "there is no database file in %s" % SERVERBACKUP
    blob = blobs[0]
    rows = [blob] + [r for r in sb if r is not blob
                     and abs(r[2] - blob[2]) <= STICK_SET_WINDOW]
    return rows[:12], ""


def _copy_verified(src, dst, size, mtime):
    """Copy src to dst so that dst only ever appears WHOLE, CHECKED and DATED.

    Through a temp name (_copy_one), then: the size, the md5 against the
    source, the source not changed meanwhile, the source's own time put on the
    copy (so its age stays the backup's age, not the copy's) -- and only then
    the real name."""
    tmp = dst + ".copying"
    ok, err = _copy_one(src, tmp)
    if not ok:
        return False, err
    try:
        with open(tmp, "rb+") as fh:           # to the stick itself, not a cache,
            os.fsync(fh.fileno())               # before the md5 is believed
        if os.path.getsize(tmp) != size:
            raise OSError("the copy's size differs from the source's")
        _a, _b = _md5(src), _md5(tmp)
        if not _a or _a != _b:
            raise OSError("the copy's md5 differs from the source's")
        _s = os.stat(src)
        if _s.st_size != size or _s.st_mtime != mtime:
            raise OSError("the source changed while it was being copied")
        os.utime(tmp, (mtime, mtime))
        os.replace(tmp, dst)
        return True, ""
    except OSError as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False, "%s: %s" % (e.__class__.__name__, e)


def _stick_auto_blobs():
    """(path, size, mtime) of every database file in the agent's own folder on
    the stick, newest first. The time is the SOURCE's, kept by _copy_verified."""
    rows = []
    auto = _stick_auto_dir()
    try:
        sets = [d for d in os.listdir(auto) if _SET_NAME.match(d)]
    except OSError:
        return rows
    for d in sets:
        p = os.path.join(auto, d)
        if not _really_inside(p, auto):
            continue
        try:
            for f in os.listdir(p):
                if f.endswith(_NOT_WHOLE) or not _is_marg_blob(f):
                    continue
                fp = os.path.join(p, f)
                if not os.path.isfile(fp):
                    continue
                st = os.stat(fp)
                rows.append((fp, st.st_size, st.st_mtime))
        except OSError:
            continue
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def _really_inside(path, top):
    """True only when `path` itself -- links and junctions resolved -- lies
    inside `top`, and is not a link. A link with a set's name must never lead
    the pruner out of the agent's own folder."""
    try:
        if os.path.islink(path):
            return False
        rp = os.path.normcase(os.path.realpath(path))
        rt = os.path.normcase(os.path.realpath(top))
        return rp.startswith(rt.rstrip("\\/") + os.sep)
    except (OSError, ValueError):
        return False


def _prune_stick_sets(auto, keep=STICK_AUTO_KEEP):
    """Keep the newest `keep` sets in the agent's own folder; remove the older.

    ONLY inside that folder, ONLY folders this agent named itself
    (YYYY-MM-DD_HHMMSS), ONLY the files directly inside them. Nothing else on
    the stick is listed for removal, let alone removed -- not a hand-made
    backup, not a folder anyone else made. Returns (kept, removed, errors)."""
    import stat as _st
    kept = removed = 0
    errors = []
    if not _same_dir(os.path.dirname(os.path.abspath(auto)), BACKUP_STICK) \
            or os.path.basename(auto) != STICK_AUTO_DIRNAME:
        return kept, removed, ["refused: %s is not the agent's own folder" % auto]
    try:
        names = sorted((d for d in os.listdir(auto) if _SET_NAME.match(d)
                        and os.path.isdir(os.path.join(auto, d))), reverse=True)
    except OSError:
        return kept, removed, errors
    with_blob = 0
    for d in names:
        p = os.path.join(auto, d)
        if not _really_inside(p, auto):
            errors.append("refused: %s is a link or leads outside %s -- left alone"
                          % (d, auto))
            continue
        if with_blob < keep:
            try:
                has = any(_is_marg_blob(f) and not f.endswith(_NOT_WHOLE)
                          for f in os.listdir(p))
            except OSError:
                has = False
            if has:
                with_blob += 1
                kept += 1
            else:
                try:
                    os.rmdir(p)            # only ever succeeds on an EMPTY one
                except OSError:
                    pass
            continue
        try:
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isdir(fp) or not _really_inside(fp, auto):
                    raise OSError("it holds a folder or a link this agent did not make")
                try:
                    os.chmod(fp, _st.S_IWRITE)
                except OSError:
                    pass
                os.remove(fp)
            os.rmdir(p)
            removed += 1
        except OSError as e:
            errors.append("could not remove the old set %s: %s: %s"
                          % (d, e.__class__.__name__, e))
    return kept, removed, errors


def stick_leg(sb, hand_rows=()):
    """S499. Marg's newest automatic backup set, onto the stick.

    The .mbk on the stick exists only when a person accepts Marg's prompt --
    every two to four days, nobody's duty -- so the stick was stale and the
    alarm stood for days, while Marg's own daily backup sat on D:, the same
    disk as the data. This puts that backup where a dead disk cannot take it.

    Never raises for a stick that is absent, full or write-protected: the
    reason goes into the state and from there into the heartbeat.

    A drive at E: is written to ONLY when it is the backup stick: its own
    folder is already there, or a hand-made Marg backup (.mbk, or a _cNN_
    file) lies on it. Any other drive that happens to take the letter E: --
    a phone, a camera card, someone's pen drive -- is left untouched."""
    auto = _stick_auto_dir()
    out = {"dir": auto, "present": os.path.isdir(BACKUP_STICK), "set": None,
           "recognised": False, "free_mb": None,
           "set_files": 0, "copied": 0, "copied_bytes": 0, "already_there": 0,
           "waiting": "", "errors": [], "sets_kept": 0, "sets_removed": 0}
    if not out["present"]:
        return out
    out["recognised"] = os.path.isdir(auto) or any(
        r[0].lower().endswith(".mbk") or _is_marg_blob(os.path.basename(r[0]))
        for r in hand_rows)
    if not out["recognised"]:
        out["waiting"] = ("%s does not look like the backup stick (no Marg backup"
                          " on it, no %s folder) -- nothing is written to it"
                          % (BACKUP_STICK, STICK_AUTO_DIRNAME))
        return out
    members, why = _newest_auto_set(sb)
    if not members:
        out["waiting"] = why
    else:
        _gap = time.time() - sb[0][2]
        if -STICK_QUIET_SECS < _gap < STICK_QUIET_SECS:
            out["waiting"] = ("Marg wrote to its backup folder %d second(s) ago"
                              " -- it is copied once that folder has been quiet"
                              " for %d seconds"
                              % (max(0, int(_gap)), STICK_QUIET_SECS))
            members = []
    if members:
        setname = _when(members[0][2], "%Y-%m-%d_%H%M%S")
        if setname == "?":
            out["errors"].append("%s carries a time this PC cannot express -- "
                                 "not copied" % os.path.basename(members[0][0]))
            members = []
        setdir = os.path.join(auto, setname)
        out["set"] = setname
        out["set_files"] = len(members)

        def _there(src, size, mt):
            try:
                _d = os.stat(os.path.join(setdir, os.path.basename(src)))
                return (_d.st_size == size
                        and abs(_d.st_mtime - mt) <= STICK_MTIME_SLACK)
            except OSError:
                return False
        if not all(_there(*m) for m in members):
            import shutil as _sh
            need = STICK_FREE_FACTOR * sum(m[1] for m in members)
            try:
                free = _sh.disk_usage(BACKUP_STICK).free
                out["free_mb"] = round(free / 1048576.0, 1)
            except OSError:
                free = None
            if free is not None and free < need:
                out["errors"].append(
                    "the stick has only %.1f MB free; Marg's backup set needs"
                    " %.1f MB (ten times its size) -- nothing copied"
                    % (free / 1048576.0, need / 1048576.0))
                members = []
        for src, size, mt in members:
            name = os.path.basename(src)
            dst = os.path.join(setdir, name)
            try:
                _d = os.stat(dst)
                if (_d.st_size == size
                        and abs(_d.st_mtime - mt) <= STICK_MTIME_SLACK):
                    out["already_there"] += 1
                    continue
            except OSError:
                pass
            try:
                _s = os.stat(src)
            except OSError as e:
                out["errors"].append("%s: %s: %s" % (name, e.__class__.__name__, e))
                break
            if _s.st_size != size or _s.st_mtime != mt:
                out["waiting"] = ("%s changed while it was being read -- left"
                                  " for the next pass" % name)
                break
            try:
                if not os.path.isdir(setdir):
                    os.makedirs(setdir)        # only when there is a file for it
            except OSError as e:
                out["errors"].append("cannot make %s: %s: %s"
                                     % (setdir, e.__class__.__name__, e))
                break
            ok, err = _copy_verified(src, dst, size, mt)
            if not ok:
                # the database file is first: no companion goes without it
                out["errors"].append("%s: %s" % (name, err))
                break
            out["copied"] += 1
            out["copied_bytes"] += size
        try:
            if os.path.isdir(setdir) and not os.listdir(setdir):
                os.rmdir(setdir)
        except OSError:
            pass
    if os.path.isdir(auto):
        kept, removed, errs = _prune_stick_sets(auto)
        out["sets_kept"], out["sets_removed"] = kept, removed
        out["errors"].extend(errs)
    return out


def _offsite_names(rows, sb_rows):
    """The name each source file gets in the offsite folder.

    S499. The offsite folder is flat and the name was always the file's own --
    so three backups called d1-sanjeevni-20250401-20260331.mbk, in three
    folders of the stick and of three sizes, shared ONE offsite name: every
    pass copied all three over each other (7,429,171 bytes an hour, the
    heartbeat's "copied: 3"), and only the one copied last -- the oldest --
    was kept. A name is still the file's own unless two sources share it; then
    the one in Marg's own folder, else the one at the top of the stick, keeps
    the plain name and every other carries its folder in its name.
    Returns ({source path: offsite name}, [the names that were changed])."""
    import hashlib
    groups = {}
    for r in rows:
        groups.setdefault(os.path.basename(r[0]).lower(), []).append(r)
    names, renamed = {}, []
    for grp in groups.values():
        if len(grp) == 1:
            names[grp[0][0]] = os.path.basename(grp[0][0])
            continue
        plain = None
        for r in grp:
            if r in sb_rows:
                plain = r
                break
        if plain is None:
            for r in grp:
                if _same_dir(os.path.dirname(r[0]), BACKUP_STICK):
                    plain = r
                    break
        for r in grp:
            base = os.path.basename(r[0])
            if r is plain:
                names[r[0]] = base
                continue
            if r in sb_rows:
                rel = "serverbackup"
            else:
                try:
                    rel = os.path.relpath(os.path.dirname(r[0]), BACKUP_STICK)
                except ValueError:
                    rel = os.path.dirname(r[0])
            slug = re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_")[:40] or "top"
            h = hashlib.md5(rel.lower().encode("utf-8", "replace")).hexdigest()[:6]
            stem, ext = os.path.splitext(base)
            names[r[0]] = "%s__in_%s_%s%s" % (stem, slug, h, ext)
            renamed.append(names[r[0]])
    return names, renamed


def _zip_listing(path, mtime):
    """The FILE LIST of a zip -- its central directory -- and nothing else.

    Marg's backups are password-protected zips. Listing one needs no password;
    no member is opened, read or extracted here, ever. Returns (facts, names):
    the facts go into the heartbeat, the names stay in this process."""
    import hashlib
    import zipfile
    out = {"name": os.path.basename(path), "bytes": None,
           "written_at": _when(mtime, "%Y-%m-%dT%H:%M:%S"),
           "is_zip": False, "members": None, "uncompressed_bytes": None,
           "password_protected_members": None, "names_hash": None, "note": ""}
    names = None
    try:
        out["bytes"] = os.path.getsize(path)
        with zipfile.ZipFile(path, "r") as z:
            infos = z.infolist()
        names = sorted(i.filename for i in infos)
        out["is_zip"] = True
        out["members"] = len(infos)
        out["uncompressed_bytes"] = sum(i.file_size for i in infos)
        out["password_protected_members"] = sum(1 for i in infos
                                                if i.flag_bits & 0x1)
        out["names_hash"] = hashlib.sha1(
            "\n".join(names).encode("utf-8", "replace")).hexdigest()[:12]
    except Exception as e:                                     # noqa: BLE001
        out["note"] = ("its file list could not be read: %s: %s"
                       % (e.__class__.__name__, str(e)[:80]))
    return out, names


def _zip_compare(prev, hand_rows, blob_rows):
    """For the record, at most once a day: is Marg's automatic backup the same
    KIND of file as the hand-made .mbk?

    The newest hand-made .mbk on the stick against the automatic database file
    nearest to it in time. File lists only -- see _zip_listing. It is evidence
    about what the two files ARE; it is not a restore, and no restore of either
    has ever been tested."""
    now_ts = time.time()
    prev = prev if isinstance(prev, dict) else {}
    try:
        if (prev.get("checked_ts") is not None
                and 0 <= now_ts - float(prev["checked_ts"]) < ZIP_COMPARE_EVERY):
            return prev
    except (TypeError, ValueError):
        pass
    mbk = [r for r in hand_rows if r[0].lower().endswith(".mbk")]
    if not mbk or not blob_rows:
        return {"checked_at": None, "checked_ts": None,
                "note": "nothing to compare yet: %s"
                        % ("no hand-made .mbk on the stick" if not mbk
                           else "no automatic database file")}
    hand = max(mbk, key=lambda r: r[2])
    auto = min(blob_rows, key=lambda r: abs(r[2] - hand[2]))
    a, na = _zip_listing(hand[0], hand[2])
    b, nb = _zip_listing(auto[0], auto[2])
    out = {"checked_at": now().isoformat(timespec="seconds"),
           "checked_ts": int(now_ts), "handmade": a, "automatic": b,
           "hours_apart": round(abs(auto[2] - hand[2]) / 3600.0, 1),
           "same_member_names": None, "same_base_names": None,
           "names_in_both": None, "only_in_handmade": None,
           "only_in_automatic": None,
           "note": "file lists only -- no member was opened; this says what "
                   "the two files are, not that either restores"}
    if na is not None and nb is not None:
        sa, sb_ = set(na), set(nb)
        out["same_member_names"] = (na == nb)
        out["names_in_both"] = len(sa & sb_)
        out["only_in_handmade"] = len(sa - sb_)
        out["only_in_automatic"] = len(sb_ - sa)
        _base = lambda ns: sorted(n.replace("\\", "/").rsplit("/", 1)[-1].lower()
                                  for n in ns)                # noqa: E731
        out["same_base_names"] = (_base(na) == _base(nb))
    return out


def backup_pass():
    """Marg's own backup onto the stick, then what is missing offsite.

    Offsite: newest first, a few megabytes at a time; never deletes; never
    overwrites a file that is already there at the same size.
    Stick (S499): only inside the agent's own folder -- see stick_leg.
    Returns the state dict that the heartbeat prints. Every key S205 wrote is
    still written, with the same meaning; S499 only adds."""
    st = {"checked_at": now().isoformat(timespec="seconds"),
          "offsite": None, "copied": 0, "copied_bytes": 0,
          "already_there": 0, "pending": 0, "errors": [],
          "newest_stick": None, "newest_stick_age_days": None,
          "newest_serverbackup_age_days": None,
          "offsite_files": 0, "offsite_bytes": 0, "note": "",
          # ---- S499: added, nothing renamed ----
          "stick_present": False,
          "newest_handmade": None, "newest_handmade_age_days": None,
          "newest_auto_on_stick": None, "newest_auto_on_stick_age_days": None,
          "newest_serverbackup_blob": None,
          "newest_serverbackup_blob_age_days": None,
          "newest_serverbackup_offsite": None,
          "newest_serverbackup_offsite_age_days": None,
          "stick_copy": {}, "offsite_renamed": [], "zip_compare": {},
          "stick_absent_since": None, "stick_absent_since_ts": None,
          "stick_unrecognised_since": None, "stick_unrecognised_since_ts": None,
          "offsite_measured": False, "future_dated": []}
    prev = backup_state_read()
    if not isinstance(prev, dict):
        prev = {}

    def _days(ts):
        return round((time.time() - ts) / 86400.0, 1)

    rows = _backup_sources()
    sb_all = _serverbackup_files()
    # The two ages are NOT interchangeable and are never mixed: the stick is
    # the only copy that survives this disk dying. serverbackup is reported
    # beside it, never in place of it.
    _stick = [r for r in rows
              if os.path.abspath(r[0]).lower().startswith(
                  os.path.abspath(BACKUP_STICK).lower())]
    _sb = [r for r in rows if r not in _stick]
    _hand_all = list(_stick)
    # A file dated more than a day ahead (a PC clock that was wrong) would be
    # "the newest" for months: it is left out of every choice and every age,
    # and named in one calm line.
    _lim = time.time() + FUTURE_SLACK
    _fut = [r for r in sb_all + rows if r[2] > _lim]
    st["future_dated"] = sorted(set(
        "%s (dated %s)" % (os.path.basename(r[0]),
                           _when(r[2], "%d-%b-%Y"))
        for r in _fut))[:5]
    sb_all = [r for r in sb_all if r[2] <= _lim]
    _stick = [r for r in _stick if r[2] <= _lim]
    _sb = [r for r in _sb if r[2] <= _lim]
    _blobs = [r for r in sb_all if _is_marg_blob(os.path.basename(r[0]))]

    # ---- 1. the stick leg. It does not wait for Drive: the day Drive is away
    # ---- is the day the stick matters most.
    try:
        st["stick_copy"] = stick_leg(sb_all, _hand_all)
    except Exception as e:                                     # noqa: BLE001
        st["stick_copy"] = {"dir": _stick_auto_dir(),
                            "present": os.path.isdir(BACKUP_STICK),
                            "waiting": "", "copied": 0,
                            "errors": ["%s: %s" % (e.__class__.__name__, e)]}
    _sc = st["stick_copy"]
    st["stick_present"] = bool(_sc.get("present"))
    # Since when is there no backup stick at E:? Two cases, each its own
    # clock: nothing plugged in at all -- or a drive plugged in that holds no
    # Marg backup (a new, blank stick: a hand-made backup onto it starts the
    # copies). A stick that is in and recognised has neither.
    for _key, _now_true in (("stick_absent_since", not st["stick_present"]),
                            ("stick_unrecognised_since",
                             st["stick_present"] and not _sc.get("recognised"))):
        if not _now_true:
            continue
        try:
            _ts = float(prev.get(_key + "_ts"))
        except (TypeError, ValueError):
            _ts = time.time()
        st[_key + "_ts"] = round(_ts)
        st[_key] = _when(_ts, "%Y-%m-%dT%H:%M:%S")
    if _sc.get("copied"):
        log("stick copy: %d file(s), %.1f MB of Marg's own backup -> %s\\%s"
            % (_sc["copied"], _sc.get("copied_bytes", 0) / 1048576.0,
               _sc.get("dir"), _sc.get("set")))
    for _e in (_sc.get("errors") or [])[:2]:
        log("stick copy FAILED: %s" % _e)
    if _sc.get("sets_removed"):
        log("stick copy: %d old set(s) removed from %s (the newest %d are kept)"
            % (_sc["sets_removed"], _sc.get("dir"), STICK_AUTO_KEEP))

    # ---- 2. the ages. newest_stick keeps its meaning -- the newest backup
    # ---- file of ANY kind on the stick -- and now has two parts beside it:
    # ---- the hand-made one and the automatic copy.
    _auto = [r for r in _stick_auto_blobs() if r[2] <= _lim]
    if _stick:
        st["newest_handmade"] = os.path.basename(_stick[0][0])
        st["newest_handmade_age_days"] = _days(_stick[0][2])
    if _auto:
        st["newest_auto_on_stick"] = os.path.basename(_auto[0][0])
        st["newest_auto_on_stick_age_days"] = _days(_auto[0][2])
    _any = sorted(_stick[:1] + _auto[:1], key=lambda r: r[2], reverse=True)
    if _any:
        st["newest_stick"] = os.path.basename(_any[0][0])
        st["newest_stick_age_days"] = _days(_any[0][2])
    if _sb:
        st["newest_serverbackup_age_days"] = _days(_sb[0][2])
    if _blobs:
        st["newest_serverbackup_blob"] = os.path.basename(_blobs[0][0])
        st["newest_serverbackup_blob_age_days"] = _days(_blobs[0][2])

    # ---- 3. the offsite leg, as S203 made it
    dest = _offsite_dir()
    have = None
    if not dest:
        st["note"] = "clinic Drive not found -- nothing copied"
    else:
        st["offsite"] = dest
        have = {}
        try:
            for f in os.listdir(dest):
                p = os.path.join(dest, f)
                if os.path.isfile(p) and not f.endswith(".part"):
                    have[f] = os.path.getsize(p)
        except OSError as e:
            st["errors"].append("cannot read %s: %s" % (dest, e.__class__.__name__))
            have = None
    if have is not None:
        st["offsite_measured"] = True
        st["offsite_files"] = len(have)
        st["offsite_bytes"] = sum(have.values())
        names, renamed = _offsite_names(rows, _sb)
        st["offsite_renamed"] = renamed[:10]

        budget = BACKUP_BYTES_PER_PASS
        for src, size, _mt in rows:
            name = names.get(src) or os.path.basename(src)
            if have.get(name) == size:
                st["already_there"] += 1
                continue
            if budget <= 0:
                st["pending"] += 1
                continue
            ok, err = _copy_one(src, os.path.join(dest, name))
            if ok:
                st["copied"] += 1
                st["copied_bytes"] += size
                budget -= size
                have[name] = size
            else:
                st["errors"].append("%s: %s" % (name, err))
                budget -= size
        if st["copied"]:
            log("offsite backup: copied %d file(s), %.1f MB, %d still pending"
                % (st["copied"], st["copied_bytes"] / 1048576.0, st["pending"]))
        try:
            _f = [f for f in os.listdir(dest)
                  if os.path.isfile(os.path.join(dest, f)) and not f.endswith(".part")]
            st["offsite_files"] = len(_f)
            st["offsite_bytes"] = sum(os.path.getsize(os.path.join(dest, f)) for f in _f)
        except OSError:
            pass
        # the newest of Marg's own database files that is in the offsite
        # folder under its name and at its size (the offsite leg's own test)
        for r in _blobs:
            if have.get(names.get(r[0]) or os.path.basename(r[0])) == r[1]:
                st["newest_serverbackup_offsite"] = os.path.basename(r[0])
                st["newest_serverbackup_offsite_age_days"] = _days(r[2])
                break

    # ---- 4. for the record, once a day
    try:
        st["zip_compare"] = _zip_compare(prev.get("zip_compare"), _stick,
                                         _blobs + _auto)
    except Exception as e:                                     # noqa: BLE001
        st["zip_compare"] = {"checked_at": None, "checked_ts": None,
                             "note": "the comparison failed: %s: %s"
                                     % (e.__class__.__name__, str(e)[:80])}

    _tmp = BACKUP_STATE + ".tmp"              # whole or not at all
    try:
        _blob = json.dumps(st, indent=2)
        with open(_tmp, "w", encoding="utf-8") as fh:
            fh.write(_blob)
        os.replace(_tmp, BACKUP_STATE)
    except OSError:
        try:
            if os.path.exists(_tmp):
                os.remove(_tmp)
        except OSError:
            pass
    return st


def backup_state_read():
    try:
        with open(BACKUP_STATE, "r", encoding="utf-8") as fh:
            _s = json.load(fh)
        # S499: a spoiled file (a list, a string) must not stop the heartbeat
        return _s if isinstance(_s, dict) else {}
    except (OSError, ValueError):
        return {}
'''),

    # ---- K. the FIX line names the NEW installer, found where the agent found Drive -- no drive letter of its own (B4)
    (r'''    (D188), and neither is a constant a file claims about itself.
    """
    out = {"running_version": AGENT_VERSION, "checked": False,''',
     r'''    (D188), and neither is a constant a file claims about itself.

    S499: the heartbeat's FIX line names ToMedical\\INSTALL_AGENT_S499.bat
    in the Drive folder found here, with no drive letter of its own. The old
    INSTALL_AGENT.bat (v3, 25-Aug) stops the S387 guard and must not be run.
    """
    out = {"running_version": AGENT_VERSION, "checked": False,'''),
    (r'''    there = os.path.join(inn, "medical_agent.py")
''',
     r'''    out["installer"] = os.path.join(inn, "INSTALL_AGENT_S499.bat")
    there = os.path.join(inn, "medical_agent.py")
'''),
    (r'''        a("    FIX: double-click  F:\\My Drive\\Clinic Data Archive\\"
          "ToMedical\\INSTALL_AGENT.bat  on this PC.")
''',
     r'''        a("    FIX: double-click  %s  on this PC."
          % (_as.get("installer")
             or "INSTALL_AGENT_S499.bat in ToMedical of the clinic Drive"))
'''),

    # ---- G. the beat carries the prune's own state
    (r'''        "kit_backups": backup_count(),
''',
     r'''        "kit_backups": backup_count(),
        "kit_backup_state": kit_backup_state(),
'''),

    # ---- H. the prune's line: what is wrong and where, by the prune's own rule
    (r'''    _kb = beat.get("kit_backups", 0)
    if _kb > 5:
        a("BACKUPS : %d kit backup files are lying about - the prune is "
          "not working" % _kb)
''',
     r'''    _ks = beat.get("kit_backup_state") or {}
    if _ks.get("prune_failed"):
        a("BACKUPS : the prune could NOT remove %d old kit copy file(s) "
          "(.before_) under %s" % (_ks["prune_failed"], KIT_DEST_ROOT))
        a("          it keeps %d per kit file; %d are there now%s"
          % (_ks.get("keep", KIT_BACKUP_KEEP), _ks.get("count", 0),
             ("; first: %s" % _ks["prune_failed_names"][0])
             if _ks.get("prune_failed_names") else ""))
    elif _ks.get("over"):
        a("BACKUPS : more than %d old copies (.before_) still sit beside a kit "
          "file under %s" % (_ks.get("keep", KIT_BACKUP_KEEP), KIT_DEST_ROOT))
        a("          after the prune ran -- %s" % "; ".join(_ks["over"]))
'''),

    # ---- I. the BACKUP block: the same first line, then each kind by name, then an alarm that says which
    (r'''        _age = _bk.get("newest_stick_age_days")
        if _age is None:''',
     r'''            a("    Take one in Marg. Everything the pharmacy has done since")
            a("    then exists in exactly one place.")
''',
     r'''        _age = _bk.get("newest_stick_age_days")
        _s499 = "stick_copy" in _bk          # a state this version wrote
        _sc = _bk.get("stick_copy")
        _sc = _sc if isinstance(_sc, dict) else {}
        _aa = _bk.get("newest_auto_on_stick_age_days")
        _ha = _bk.get("newest_handmade_age_days")
        _bba = _bk.get("newest_serverbackup_blob_age_days")
        _oa = _bk.get("newest_serverbackup_offsite_age_days")
        _since = None
        try:
            _since = float(_bk.get("stick_absent_since_ts"))
        except (TypeError, ValueError):
            pass
        _since_txt = _when(_since) if _since is not None else ""
        _blank = None
        try:
            _blank = float(_bk.get("stick_unrecognised_since_ts"))
        except (TypeError, ValueError):
            pass
        if _age is None:
            a("BACKUP  : NO BACKUP FILE ON %s -- the stick is empty or absent"
              % BACKUP_STICK)
        else:
            a("BACKUP  : newest backup on the stick is %.1f day(s) old  (%s)"
              % (_age, _bk.get("newest_stick") or "?"))
        if _s499 and not _bk.get("stick_present"):
            a("          STICK ABSENT: %s is not there%s -- Marg's automatic"
              % (BACKUP_STICK, (" since " + _since_txt) if _since_txt else ""))
            a("          backup cannot be copied to a stick until it is plugged in.")
        elif _s499 and not _sc.get("recognised", True):
            a("          STICK HOLDS NO MARG BACKUP: %s is plugged in%s but holds no"
              % (BACKUP_STICK, (" since " + _when(_blank)) if _blank is not None else ""))
            a("          Marg backup -- nothing is written to it. Take one in Marg by hand")
            a("          onto this stick; then the copies start by themselves.")
        elif _s499:
            if _aa is not None:
                a("          automatic copy on the stick: %.1f day(s) old  (%s)"
                  % (_aa, _bk.get("newest_auto_on_stick") or "?"))
            else:
                a("          automatic copy on the stick: none yet")
            if _sc.get("errors"):
                a("          STICK COPY FAILED: %s" % _sc["errors"][0])
                a("          Marg's newest automatic backup is NOT on the stick --")
                a("          is the stick full, write-protected or faulty?")
            elif _sc.get("waiting"):
                a("          stick copy waiting: %s" % _sc["waiting"])
            if _ha is None:
                a("          hand-made backup on the stick: none")
            elif (_ha > HANDMADE_CALM_DAYS and _aa is not None
                  and _aa <= BACKUP_WARN_DAYS):
                a("          hand-made backup on the stick: %.1f day(s) old  (%s)"
                  % (_ha, _bk.get("newest_handmade") or "?"))
                a("          -- optional; the automatic copy is on the stick")
            else:
                a("          hand-made backup on the stick: %.1f day(s) old  (%s)"
                  % (_ha, _bk.get("newest_handmade") or "?"))
        for _fd in (_bk.get("future_dated") or [])[:3]:
            a("          ignored, dated in the future: %s" % _fd)
        _sba = _bk.get("newest_serverbackup_age_days")
        if _sba is not None:
            a("          Marg's own serverbackup: %.1f day(s) old -- on D:, the same"
              % _sba)
            a("          disk as the data. Not a disaster copy by itself.")
        if _s499:
            if _bba is not None:
                a("          its newest database file: %.1f day(s) old  (%s)"
                  % (_bba, _bk.get("newest_serverbackup_blob") or "?"))
            else:
                a("          it holds no database file yet")
            if _oa is not None:
                a("          newest automatic backup in the offsite folder: "
                  "%.1f day(s) old" % _oa)
            elif _bk.get("offsite"):
                a("          no automatic backup is in the offsite folder yet")
        if _bk.get("offsite"):
            a("          offsite: %d file(s), %.2f GB in %s"
              % (_bk.get("offsite_files", 0),
                 _bk.get("offsite_bytes", 0) / (1024.0 ** 3),
                 _bk["offsite"]))
            if _bk.get("pending"):
                a("          %d file(s) still to copy -- it works through them"
                  % _bk["pending"])
            else:
                a("          offsite copy is COMPLETE")
        else:
            a("          offsite: %s" % (_bk.get("note") or "not available"))
        for _e in (_bk.get("errors") or [])[:3]:
            a("          ERROR: %s" % _e)
        _zc = _bk.get("zip_compare")
        _zc = _zc if isinstance(_zc, dict) else {}
        _zh, _za = _zc.get("handmade"), _zc.get("automatic")
        if isinstance(_zh, dict) and isinstance(_za, dict) and _zh and _za:
            if _zh.get("is_zip") and _za.get("is_zip"):
                a("          for the record (file lists only, nothing opened): the"
                  " hand-made")
                a("          .mbk lists %s member(s), Marg's automatic file %s;"
                  " same names: %s"
                  % (_zh.get("members"), _za.get("members"),
                     "yes" if _zc.get("same_member_names") else "no"))
            else:
                a("          for the record: a file list could not be read "
                  "(hand-made: %s, automatic: %s)"
                  % ("zip" if _zh.get("is_zip") else "not readable as a zip",
                     "zip" if _za.get("is_zip") else "not readable as a zip"))
        # The loud lines, and only these: the newest backup of ANY kind on the
        # stick is over 3 days old -- or the stick has been out for over a day.
        # A gap in Marg's own backup alone is ordinary on this PC: it is the
        # calm "its newest database file" line above, never a loud one.
        _stale = _age is not None and _age > BACKUP_WARN_DAYS
        if _stale:
            a("")
            a("*** NO MARG BACKUP ON THE STICK FOR %.1f DAYS ***" % _age)
            if (_s499 and _bba is not None and _bba < _age
                    and _bba <= BACKUP_WARN_DAYS):
                a("    Marg's own automatic backup is fresh on D: (%.1f day(s) old)"
                  % _bba)
                a("    but it is not reaching the stick. Check the stick in %s --"
                  % BACKUP_STICK)
                a("    plugged in, not full, not write-protected -- or take a")
                a("    backup in Marg by hand.")
            else:
                a("    Take one in Marg today (it goes to the stick).")
            # said only when this pass MEASURED it: the stick in and stale, the
            # offsite folder read, and nothing newer than the stick's in it
            if (_s499 and _bk.get("stick_present") and _bk.get("offsite")
                    and _bk.get("offsite_measured")
                    and (_oa is None or _oa >= _age)
                    and (_ha is None or _ha > BACKUP_WARN_DAYS)
                    and (_aa is None or _aa > BACKUP_WARN_DAYS)):
                a("    Nothing newer is in the offsite folder either: everything the")
                a("    pharmacy has done since then exists in exactly one place --")
                a("    this PC's D: disk.")
        if (_s499 and _since is not None
                and time.time() - _since > STICK_ABSENT_LOUD_DAYS * 86400.0):
            a("")
            a("*** NO MARG BACKUP ON THE STICK -- the backup stick is not plugged"
              " in since %s ***" % _since_txt)
            a("    Plug the Marg backup stick back into this PC (it shows as %s)."
              % BACKUP_STICK)
        if (_s499 and _blank is not None and _bk.get("stick_present")
                and time.time() - _blank > STICK_ABSENT_LOUD_DAYS * 86400.0):
            a("")
            a("*** NO MARG BACKUP ON THE STICK -- %s is plugged in but holds no Marg"
              " backup since %s ***" % (BACKUP_STICK, _when(_blank)))
            a("    Take one in Marg by hand onto this stick (then copies start by"
              " themselves).")
'''),

    # ---- J. the prune runs hourly too, so the manifest's files are pruned once Drive is up
    (r'''                try:
                    _bs = backup_pass()
''',
     r'''                try:
                    # S499: at the start Drive may not be up yet, and the
                    # manifest's files are known only when it is.
                    prune_kit_backups()
                except Exception as _pe:                       # noqa: BLE001
                    log("kit backup prune FAILED: %s: %s"
                        % (_pe.__class__.__name__, _pe))
                try:
                    _bs = backup_pass()
'''),
]


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(raw):
    """FROM bytes -> TO bytes, or SystemExit. Nothing is written here."""
    if md5b(raw) != FROM:
        raise SystemExit("STOP: the agent is %s, not its FROM pin %s -- nothing built" % (md5b(raw), FROM))
    txt = raw.decode("utf-8")
    for ed in EDITS:
        for anchor in ed[:-1]:
            c = txt.count(anchor)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times -- nothing built: %r" % (c, anchor[:90]))
        if len(ed) == 2:
            txt = txt.replace(ed[0], ed[1], 1)
        else:
            i, j = txt.index(ed[0]), txt.index(ed[1]) + len(ed[1])
            if i >= j:
                raise SystemExit("STOP: a span's end is before its start -- nothing built: %r" % ed[0][:90])
            txt = txt[:i] + ed[2] + txt[j:]
    if "\r" in txt:
        raise SystemExit("STOP: a carriage return in the built text -- nothing built")
    out = txt.encode("utf-8")
    try:
        compile(txt, "medical_agent.py", "exec")
    except SyntaxError as ex:
        raise SystemExit("STOP: the built text does not compile (%s, line %s) -- nothing built" % (ex.msg, ex.lineno))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="medical_agent.py S205.1 (70d5c4e3)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.agent, "rb") as fh:
        raw = fh.read()
    out = build(raw)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "medical_agent.py"), "wb") as fh:
        fh.write(out)
    print("built medical_agent.py %s -> %s  (%d edits, %d -> %d bytes)" % (FROM[:8], md5b(out), len(EDITS), len(raw), len(out)))


if __name__ == "__main__":
    main()
