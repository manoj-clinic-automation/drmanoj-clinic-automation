#!/usr/bin/env python3
"""pc_kits_current.py -- kit S723_PC_KITS_CURRENT (session 390, the parent, 06-Nov-2026). D803, F-1048.
S794 (S431, 11-Nov-2026): a member left as packed is BEHIND, never CURRENT; the word 'superseded', not a file name.
S822 (S456, 14-Nov-2026, D972, F-1385): a NEW program file on the medical PC joins the kit by itself.

THE OWNER, 29-Oct-2026 (D803): "find a way how to keep them current automatically" -- and on the board, 06-Nov 08:48 IST:
"Clinic pc tiles - the pc etc setup files stay uptodate - build was planned but it's pending".
THE OWNER, 14-Nov-2026 (D972): the Clinic PCs page says how each PC is set up now and its set-ups stay current.

WHAT IT DOES, nightly on Dr Manoj's PC, BEFORE the kit rehearsal (NIGHTLY.bat):
  For each setup kit the Clinic PCs page serves (the repository's deploy_kits/PC_KITS/<pc>/kit.zip), every member that
  has a live source is compared with it:
    medical    payload/<f>  <->  the PC's mirror of D:\\SendToClinic (D:\\Downloads\\margsync\\medical_SendToClinic\\<f>),
               cross-checked with the newest live pin of D:\\SendToClinic\\<f> and, when Drive is mounted, with
               ToMedical\\_kit\\KIT_MANIFEST.txt. A member behind its source is REPACKED: only that member's bytes change,
               every other member is copied byte for byte in the same order, MD5SUMS.txt is rewritten in its own shape,
               the zip is proved (every member against MD5SUMS) and KIT_INFO.txt's kit_md5 / packed / version follow.
               S822 -- NEW PROGRAM FILES: a program file (.py .bat .cmd .ps1 .ahk) at the top of the mirror that the kit
               does not carry is looked at too. The mirror is robocopy without /PURGE, so it keeps every file ever
               deleted on that PC: a file is taken as ON THE PC only when the PC's own share lists it tonight
               (\\\\<medical>\\DDrive\\SendToClinic, read-only). A new file that is on the PC and whose bytes are its newest
               live pin is ADDED to the kit (payload/<f>, a row in MD5SUMS.txt); one on the PC with no live pin, or whose
               bytes are not its pin, is REPORTED and not packed; one the PC no longer has is said to be mirror-only;
               with the PC unreachable, every new file is reported as 'on the PC unknown tonight' and none is packed.
               Backups and leftovers (*.bak*, *.before_*, *RETIRED*, *.superseded*) are never looked at.
    reception  <f>  <->  the newest live pin of C:\\ClinicAgent\\<f>. Its bytes are not on this PC, so a member behind is
               REPORTED (BEHIND), never repacked.
    manojz     restores from the nightly state zip by design: listed CURRENT, nothing to compare.
  Refused (nothing written for that kit, said in the report): the mirror older than 26 hours; a member whose mirror copy
  is not its newest live pin, or that has no pin at all; the Drive manifest naming another md5; a zip or KIT_INFO that is
  not whole to begin with. A repack moves the rehearsal's report aside, so the same night's rehearsal re-proves the new
  kit on Windows. The owner's next PUBLISH_ALL carries it to the server (the server pulls the repository by itself, S822).
  Report: <tools>\\PC_KITS_CURRENT_LATEST.txt. No secret, no patient, no number is read or written; members are only
  ever those the kit already has or program files proved on the PC and pinned (token.txt and the like are never packed).

  python pc_kits_current.py [--tools D:\\Downloads\\_kbtools] [--repo D:\\dr-manoj-git\\drmanoj-clinic-automation]
         [--mirror D:\\Downloads\\margsync\\medical_SendToClinic] [--share \\\\100.119.151.40\\DDrive\\SendToClinic | --no-share]
         [--dry] [--now YYYY-MM-DDTHH:MM]
Exit 0 always unless the script itself breaks (2)."""
import argparse, datetime as dt, glob, hashlib, io, os, re, shutil, string, sys, tempfile, threading, zipfile

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
FRESH_H = 26
KIT = "S723+S794+S822"
PROGRAM_EXT = (".py", ".bat", ".cmd", ".ps1", ".ahk")                        # S822: what counts as a program file
_LEFTOVER = re.compile(r"(\.bak|\.before_|retired|\.superseded|\.s723new|\.tmp)", re.I)   # never looked at
_INSTALLER = re.compile(r"^(install_|setup_check|_kit_)", re.I)              # one-off installers / checkers: reported, never packed
DEF_HOST, DEF_SHARE_NAME = "100.119.151.40", "DDrive"                         # the medical PC over Tailscale (PULL_FROM_MEDICAL.bat)
MACHINE_CONF = r"D:\Downloads\margsync\_config\machine.conf"                 # MEDICAL_HOST / MEDICAL_SHARE win when present (S260)
SHARE_WAIT_S = 40


def default_share():
    r"""\\<host>\<share>\SendToClinic from machine.conf's MEDICAL_HOST / MEDICAL_SHARE, else the constants -- the same two keys
    PULL_FROM_MEDICAL.bat reads, so there is one authority for which PC is 'medical'."""
    host, share = DEF_HOST, DEF_SHARE_NAME
    try:
        with open(MACHINE_CONF, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = (x.strip() for x in ln.split("=", 1))
                if k.upper() == "MEDICAL_HOST" and v:
                    host = v
                elif k.upper() == "MEDICAL_SHARE" and v:
                    share = v
    except OSError:
        pass
    return "\\\\%s\\%s\\SendToClinic" % (host, share)


def md5b(b):
    return hashlib.md5(b).hexdigest()


def md5f(p):
    with open(p, "rb") as fh:
        return md5b(fh.read())


def newest_pins(canon):
    c = [p for p in glob.glob(os.path.join(canon, "live_pins_S*close.txt"))
         if re.fullmatch(r"live_pins_S\d+close\.txt", os.path.basename(p))]
    c.sort(key=lambda p: int(re.search(r"live_pins_S(\d+)close", os.path.basename(p)).group(1)))
    return c[-1] if c else None


_SUP = re.compile(r"(?<![.\w])superseded\b", re.I)   # S794: the word, not a file name such as x.py.superseded


def pin_map(pins_path):
    """{lower(path tail): md5} from the TOPMOST row naming it that is not marked superseded (the newest)."""
    out = {}
    if not pins_path:
        return out
    with open(pins_path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            f = ln.rstrip("\n").split("\t")
            if len(f) < 3 or not re.fullmatch(r"[0-9a-f]{32}", f[1] or ""):
                continue
            if _SUP.search(f[2]) or (len(f) > 3 and _SUP.search(f[3])):
                continue
            m = re.search(r"([A-Za-z]:\\[^\s·]+)", f[2])
            if not m:
                continue
            key = m.group(1).lower()
            out.setdefault(key, f[1])
    return out


def read_manifest(p):
    out = {}
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            f = [x.strip() for x in ln.split("|")]
            if len(f) >= 3 and re.fullmatch(r"[0-9a-f]{32}", f[2]):
                out[f[0].lower()] = f[2]
    return out


def drive_manifest(path=""):
    """{lower file name: md5} from ToMedical\\_kit\\KIT_MANIFEST.txt on whichever drive letter has it; None if not mounted.
    S822: the folder lives under 'Clinic Data Archive' on the clinic Drive (the medical PC's heartbeat names it so); the
    older bare path is still looked at. `path` (--manifest) names the file directly -- the walk's hook, never the nightly's."""
    if path:
        return read_manifest(path) if os.path.isfile(path) else None
    if os.name != "nt":
        return None
    for L in string.ascii_uppercase:
        for p in (r"%s:\My Drive\Clinic Data Archive\ToMedical\_kit\KIT_MANIFEST.txt" % L,
                  r"%s:\My Drive\ToMedical\_kit\KIT_MANIFEST.txt" % L):
            if os.path.isfile(p):
                return read_manifest(p)
    return None


def share_listing(share):
    """S822: {lower name} of the files at the top of the medical PC's own SendToClinic share, read-only; None when the PC
    cannot be reached within SHARE_WAIT_S seconds (off, or the share blocked). Nothing is opened, nothing is written."""
    if not share:
        return None, "not asked"
    box = {}

    def work():
        try:
            with os.scandir(share) as it:                    # one round trip on Windows; names only, nothing opened
                box["names"] = {e.name.lower() for e in it if e.is_file()}
        except Exception as e:                              # noqa: BLE001
            box["err"] = str(e)[:120]
    th = threading.Thread(target=work, daemon=True)
    th.start()
    th.join(SHARE_WAIT_S)
    if "names" not in box:
        box.setdefault("err", "no answer within %d s" % SHARE_WAIT_S)
    return box.get("names"), box.get("err")


def read_info(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    info = {}
    for ln in text.splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            info[k.strip()] = v.strip()
    return raw, text, info


def sums_rows(text):
    return [(l[:32], l[34:]) for l in text.splitlines() if re.match(r"^[0-9a-f]{32}  ", l)]


def check_zip(zpath):
    """(ok, why, {member: bytes}, infolist, md5sums text) -- whole means every MD5SUMS row matches its member."""
    try:
        z = zipfile.ZipFile(zpath)
    except Exception as e:                                  # noqa: BLE001
        return False, "not a readable zip (%s)" % e, None, None, None
    with z:
        if z.testzip() is not None:
            return False, "a member fails its CRC", None, None, None
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        infos = z.infolist()
    if "MD5SUMS.txt" not in data:
        return True, "", data, infos, None
    st = data["MD5SUMS.txt"].decode("ascii")
    bad = [n for m, n in sums_rows(st) if not (n not in data and n.lower().endswith(".zip"))     # the bundled Python
           and md5b(data.get(n, b"\0missing")) != m]                                           # travels beside the zip
    if bad:
        return False, "MD5SUMS.txt disagrees with %s" % ", ".join(bad[:3]), None, None, None
    return True, "", data, infos, st


def repack(zpath, infos, data, sums_text, changes, stamp, adds=None):
    """Write the new zip beside the old one; return (bytes, new sums text). Only `changes` {member: bytes} differ;
    `adds` {member: bytes} (S822) are NEW members, written after every existing one in name order, each with a row
    appended to MD5SUMS.txt in its own shape (md5, two spaces, the member)."""
    adds = adds or {}
    nl = "\r\n" if "\r\n" in (sums_text or "") else "\n"
    new_data = dict(data)
    new_data.update(changes)
    new_data.update(adds)
    if sums_text is not None:
        lines = sums_text.split(nl)
        out = []
        for ln in lines:
            m = re.match(r"^([0-9a-f]{32})  (.+)$", ln)
            if m and m.group(2) in changes:
                ln = "%s  %s" % (md5b(changes[m.group(2)]), m.group(2))
            out.append(ln)
        if adds:
            trailing = out and out[-1] == ""                 # the file ended with a line ending: keep it so
            if trailing:
                out.pop()
            for n in sorted(adds):
                out.append("%s  %s" % (md5b(adds[n]), n))
            if trailing:
                out.append("")
        new_data["MD5SUMS.txt"] = nl.join(out).encode("ascii")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zo:
        for i in infos:
            touched = i.filename in changes or (i.filename == "MD5SUMS.txt" and sums_text is not None)
            zi = zipfile.ZipInfo(i.filename, date_time=stamp if touched else i.date_time)
            zi.compress_type = i.compress_type
            zi.external_attr = i.external_attr
            zi.create_system = i.create_system
            zo.writestr(zi, new_data[i.filename])
        like = next((i for i in infos if i.filename.startswith("payload/") and not i.filename.endswith("/")), infos[0] if infos else None)
        for n in sorted(adds):
            zi = zipfile.ZipInfo(n, date_time=stamp)
            zi.compress_type = like.compress_type if like else zipfile.ZIP_DEFLATED
            zi.external_attr = like.external_attr if like else 0
            zi.create_system = like.create_system if like else 0
            zo.writestr(zi, adds[n])
    return buf.getvalue(), (new_data.get("MD5SUMS.txt") or b"").decode("ascii") if sums_text is not None else None


def write_atomic(path, b):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".s723_", dir=d)
    with os.fdopen(fd, "wb") as fh:
        fh.write(b)
    os.replace(tmp, path)
    if md5f(path) != md5b(b):
        raise IOError("read-back of %s did not match" % path)


def new_program_files(a, data, pins, manifest, on_pc, notes):
    """S822: {payload/<f>: bytes} of the mirror's top-level program files the kit does not carry and that may be ADDED
    (on the PC tonight, bytes = the newest live pin, the Drive manifest not disagreeing). Everything else is a note."""
    adds = {}
    try:
        names = sorted(os.listdir(a.mirror))
    except OSError as e:
        notes.append("the mirror could not be listed for new files (%s)" % e)
        return adds
    for n in names:
        p = os.path.join(a.mirror, n)
        if not os.path.isfile(p) or not n.lower().endswith(PROGRAM_EXT) or _LEFTOVER.search(n):
            continue
        member = "payload/" + n
        if member in data or any(k.lower() == member.lower() for k in data):
            continue
        if on_pc is None:
            notes.append("NEW %s: in the mirror, on the PC unknown tonight (the PC could not be reached) -- not packed" % n)
            continue
        if n.lower() not in on_pc:
            notes.append("NEW %s: mirror-only (that PC no longer has it) -- not packed" % n)
            continue
        if _INSTALLER.match(n):
            notes.append("NEW %s: on the PC, an installer or checker by its name -- never packed (a set-up kit carries programs, not installers)" % n)
            continue
        sb = open(p, "rb").read()
        pin = pins.get(("d:\\sendtoclinic\\" + n).lower())
        if not pin:
            notes.append("NEW %s: on the PC, no live pin -- not packed (record it as a pin, or retire it)" % n)
            continue
        if pin != md5b(sb):
            notes.append("NEW %s: on the PC, the mirror %s is not its newest pin %s -- not packed" % (n, md5b(sb)[:8], pin[:8]))
            continue
        if manifest is not None and n.lower() in manifest and manifest[n.lower()] != md5b(sb):
            notes.append("NEW %s: Drive's KIT_MANIFEST names %s, the mirror has %s -- not packed" % (n, manifest[n.lower()][:8], md5b(sb)[:8]))
            continue
        adds[member] = sb
    return adds


def do_medical(a, kits, pins, manifest, now, say):
    kd = os.path.join(kits, "medical")
    zpath, ipath = os.path.join(kd, "kit.zip"), os.path.join(kd, "KIT_INFO.txt")
    if not (os.path.isfile(zpath) and os.path.isfile(ipath)):
        return say("medical", "NOT CHECKED", "no kit.zip / KIT_INFO.txt in the repository")
    iraw, itext, info = read_info(ipath)
    if md5f(zpath) != info.get("kit_md5"):
        return say("medical", "REFUSED", "kit.zip is not the one KIT_INFO names -- not whole to begin with; nothing touched")
    ok, why, data, infos, sums = check_zip(zpath)
    if not ok:
        return say("medical", "REFUSED", "kit.zip " + why)
    stp = os.path.join(a.mirror, "push_state.json")
    if not os.path.isfile(stp):
        return say("medical", "REFUSED", "the mirror of D:\\SendToClinic is not at %s" % a.mirror)
    age_h = (now.timestamp() - os.path.getmtime(stp)) / 3600.0
    if age_h > FRESH_H:
        return say("medical", "REFUSED", "the mirror is %.0f hours old (over %d) -- it may not be what that PC runs" % (age_h, FRESH_H))
    behind, notes, changes = [], [], {}
    for n in sorted(data):
        if not n.startswith("payload/"):
            continue
        rel = n[len("payload/"):]
        src = os.path.join(a.mirror, *rel.split("/"))
        if not os.path.isfile(src):
            notes.append("%s not in the mirror" % rel)
            continue
        sb = open(src, "rb").read()
        if md5b(sb) == md5b(data[n]):
            continue
        pin = pins.get(("d:\\sendtoclinic\\" + rel.replace("/", "\\")).lower())
        if not pin:
            notes.append("%s differs but has no live pin -- left as packed" % rel)
            continue
        if pin != md5b(sb):
            notes.append("%s: the mirror %s is not its newest pin %s -- left as packed" % (rel, md5b(sb)[:8], pin[:8]))
            continue
        if manifest is not None and rel.split("/")[-1].lower() in manifest and manifest[rel.split("/")[-1].lower()] != md5b(sb):
            return say("medical", "REFUSED", "Drive's KIT_MANIFEST names %s as %s, the mirror has %s" % (
                rel, manifest[rel.split("/")[-1].lower()][:8], md5b(sb)[:8]))
        changes[n] = sb
        behind.append("%s %s -> %s" % (rel, md5b(data[n])[:8], md5b(sb)[:8]))
    on_pc, share_err = share_listing(a.share)                # S822: what that PC has tonight (None = unreachable)
    a.pc_state = "not asked (--no-share)" if not a.share else (
        "its SendToClinic folder listed read-only (new program files judged against it)" if on_pc is not None else
        "could NOT be listed tonight (%s) -- a new program file, if any, waits; nothing new packed" % share_err)
    if a.share and on_pc is None:
        notes.append("the PC's own folder could not be listed tonight (%s) -- a new program file, if any, waits" % share_err)
    adds = new_program_files(a, data, pins, manifest, on_pc, notes)
    added = ["%s NEW %s" % (n[len("payload/"):], md5b(b)[:8]) for n, b in sorted(adds.items())]
    if sums is None and adds:                                # a kit with no MD5SUMS cannot prove a new member: report only
        notes.append("the kit has no MD5SUMS.txt -- a new member cannot be proved; " + "; ".join(added) + " not packed")
        adds, added = {}, []
    if not changes and not adds:
        held = [x for x in notes if "left as packed" in x]             # S794: a member behind and not repacked is never CURRENT
        if held:
            return say("medical", "BEHIND -- NOT REPACKED", "; ".join(notes))
        return say("medical", "CURRENT", "every payload file equals the PC's own copy" + ("; " + "; ".join(notes) if notes else ""))
    if a.dry:
        return say("medical", "BEHIND (dry run)", "; ".join(behind + added + notes))
    stamp = (now.year, now.month, now.day, 12, 0, 0)
    zb, _ = repack(zpath, infos, data, sums, changes, stamp, adds)
    tmpz = zpath + ".s723new"
    open(tmpz, "wb").write(zb)
    ok2, why2, d2, _, _ = check_zip(tmpz)
    if not ok2 or any(md5b(d2[n]) != md5b(b) for n, b in changes.items()) or any(md5b(d2.get(n, b"")) != md5b(b) for n, b in adds.items()) \
            or sorted(d2) != sorted(list(data) + list(adds)) or \
            any(md5b(d2[n]) != md5b(data[n]) for n in data if n not in changes and n != "MD5SUMS.txt"):
        os.remove(tmpz)
        return say("medical", "REFUSED", "the repacked zip did not prove itself (%s) -- the old kit stands" % (why2 or "members"))
    new_md5 = md5b(zb)
    nl = "\r\n" if "\r\n" in itext else "\n"
    lines = itext.split(nl)
    names = ", ".join(n.split("/")[-1] for n in sorted(changes)) if changes else ""
    if adds:
        names = (names + "; " if names else "") + "added " + ", ".join(n.split("/")[-1] for n in sorted(adds))
    for k, ln in enumerate(lines):
        if ln.startswith("kit_md5="):
            lines[k] = "kit_md5=" + new_md5
        elif ln.startswith("packed="):
            lines[k] = "packed=" + now.strftime("%d-%b-%Y")
        elif ln.startswith("version="):
            lines[k] = re.sub(r"; repacked by S723 .*$", "", ln) + "; repacked by S723 %s (%s)" % (now.strftime("%d-%b-%Y"), names)
    bdir = os.path.join(a.tools, "_pc_kits_before")        # the last kit before a repack -- never inside the repository
    os.makedirs(bdir, exist_ok=True)
    bz, bi = os.path.join(bdir, "medical_kit.zip"), os.path.join(bdir, "medical_KIT_INFO.txt")
    shutil.copy2(zpath, bz)
    shutil.copy2(ipath, bi)
    try:
        os.replace(tmpz, zpath)
        write_atomic(ipath, nl.join(lines).encode("utf-8"))
        if md5f(zpath) != new_md5:
            raise IOError("kit.zip read-back")
    except Exception as e:                                  # noqa: BLE001
        shutil.copy2(bz, zpath)
        shutil.copy2(bi, ipath)
        return say("medical", "REFUSED", "could not place the repacked kit (%s) -- the old kit put back" % e)
    return say("medical", "REPACKED", "kit.zip -> %s: %s%s" % (new_md5[:8], "; ".join(behind + added), ("; " + "; ".join(notes)) if notes else ""), repacked=True)


def do_reception(kits, pins, say):
    kd = os.path.join(kits, "reception")
    zpath, ipath = os.path.join(kd, "kit.zip"), os.path.join(kd, "KIT_INFO.txt")
    if not (os.path.isfile(zpath) and os.path.isfile(ipath)):
        return say("reception", "NOT CHECKED", "no kit.zip / KIT_INFO.txt in the repository")
    _, _, info = read_info(ipath)
    if md5f(zpath) != info.get("kit_md5"):
        return say("reception", "NOT WHOLE", "kit.zip is not the one KIT_INFO names")
    ok, why, data, _, _ = check_zip(zpath)
    if not ok:
        return say("reception", "NOT WHOLE", "kit.zip " + why)
    behind, seen = [], 0
    for n in sorted(data):
        pin = pins.get(("c:\\clinicagent\\" + n.replace("/", "\\")).lower())
        if not pin:
            continue
        seen += 1
        if pin != md5b(data[n]):
            behind.append("%s kit %s, the PC %s" % (n, md5b(data[n])[:8], pin[:8]))
    if behind:
        return say("reception", "BEHIND (report only -- that PC's files are not on this PC; a kit is built for it)", "; ".join(behind))
    return say("reception", "CURRENT", "%d pinned files equal the reception PC's own" % seen)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default=r"D:\Downloads\_kbtools")
    ap.add_argument("--repo", default=r"D:\dr-manoj-git\drmanoj-clinic-automation")
    ap.add_argument("--mirror", default=r"D:\Downloads\margsync\medical_SendToClinic")
    ap.add_argument("--share", default=default_share(), help="the medical PC's own SendToClinic folder, read-only (S822)")
    ap.add_argument("--no-share", action="store_true", help="do not look at the PC (S822): new files are reported, never packed")
    ap.add_argument("--manifest", default="", help="a KIT_MANIFEST.txt to read instead of looking for the Drive (the walk's hook)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--now", default="")
    a = ap.parse_args(argv)
    if a.no_share:
        a.share = ""
    a.pc_state = "not asked (--no-share)" if not a.share else "not reached (the medical kit was not checked)"
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=IST) if a.now else dt.datetime.now(IST)
    kits = os.path.join(a.repo, "deploy_kits", "PC_KITS")
    pins_path = newest_pins(os.path.join(a.repo, "deploy_kits", "KB_canon_all"))
    pins = pin_map(pins_path)
    manifest = drive_manifest(a.manifest)
    lines, state = [], {"repacked": False}

    def say(kit, verdict, why, repacked=False):
        lines.append("  %-10s %s -- %s" % (kit, verdict, why))
        if repacked:
            state["repacked"] = True

    do_medical(a, kits, pins, manifest, now, say)
    do_reception(kits, pins, say)
    say("manojz", "CURRENT", "restores from the nightly state zip on the SSD by design; nothing to compare")
    moved = ""
    if state["repacked"]:
        rep = os.path.join(a.tools, "PC_KITS_REHEARSAL_LATEST.txt")
        if os.path.isfile(rep):
            dst = os.path.join(a.tools, "PC_KITS_REHEARSAL_before_S723_%s.txt" % now.strftime("%Y%m%d_%H%M"))
            os.replace(rep, dst)
            moved = "the rehearsal's report moved aside (%s): tonight's rehearsal re-proves the repacked kit" % os.path.basename(dst)
    out = ["PC SETUP KITS -- are they what the PCs run? (%s, pc_kits_current.py %s)" % (now.strftime("%Y-%m-%d %H:%M IST"), KIT),
           "pins   : %s" % (os.path.basename(pins_path) if pins_path else "none found"),
           "drive  : %s" % ("ToMedical KIT_MANIFEST read" if manifest is not None else "not mounted -- the mirror and the pins decide"),
           "the PC : %s" % a.pc_state,
           ""] + lines + ([""] + ["  " + moved] if moved else []) + \
          ["", "A repacked kit reaches the Clinic PCs page with the owner's next PUBLISH_ALL (the server pulls the repository by itself)." if state["repacked"] else
           "Nothing to publish from this check."]
    text = "\n".join(out) + "\n"
    if not a.dry:
        write_atomic(os.path.join(a.tools, "PC_KITS_CURRENT_LATEST.txt"), text.encode("utf-8"))
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                                  # noqa: BLE001
        print("pc_kits_current: broke -- %s" % e)
        sys.exit(2)
