#!/usr/bin/env python3
"""pc_kits_current.py -- kit S723_PC_KITS_CURRENT (session 390, the parent, 06-Nov-2026). D803, F-1048.

THE OWNER, 29-Oct-2026 (D803): "find a way how to keep them current automatically" -- and on the board, 06-Nov 08:48 IST:
"Clinic pc tiles - the pc etc setup files stay uptodate - build was planned but it's pending".

WHAT IT DOES, nightly on Dr Manoj's PC, BEFORE the kit rehearsal (NIGHTLY.bat):
  For each setup kit the Clinic PCs page serves (the repository's deploy_kits/PC_KITS/<pc>/kit.zip), every member that
  has a live source is compared with it:
    medical    payload/<f>  <->  the PC's mirror of D:\\SendToClinic (D:\\Downloads\\margsync\\medical_SendToClinic\\<f>),
               cross-checked with the newest live pin of D:\\SendToClinic\\<f> and, when Drive is mounted, with
               ToMedical\\_kit\\KIT_MANIFEST.txt. A member behind its source is REPACKED: only that member's bytes change,
               every other member is copied byte for byte in the same order, MD5SUMS.txt is rewritten in its own shape,
               the zip is proved (every member against MD5SUMS) and KIT_INFO.txt's kit_md5 / packed / version follow.
    reception  <f>  <->  the newest live pin of C:\\ClinicAgent\\<f>. Its bytes are not on this PC, so a member behind is
               REPORTED (BEHIND), never repacked.
    manojz     restores from the nightly state zip by design: listed CURRENT, nothing to compare.
  Refused (nothing written for that kit, said in the report): the mirror older than 26 hours; a member whose mirror copy
  is not its newest live pin, or that has no pin at all; the Drive manifest naming another md5; a zip or KIT_INFO that is
  not whole to begin with. A repack moves the rehearsal's report aside, so the same night's rehearsal re-proves the new
  kit on Windows. The owner's next PUBLISH_ALL carries it to the server.
  Report: <tools>\\PC_KITS_CURRENT_LATEST.txt. No secret, no patient, no number is read or written; members are only
  ever those the kit already has (token.txt and the like are never packed).

  python pc_kits_current.py [--tools D:\\Downloads\\_kbtools] [--repo D:\\dr-manoj-git\\drmanoj-clinic-automation]
         [--mirror D:\\Downloads\\margsync\\medical_SendToClinic] [--dry] [--now YYYY-MM-DDTHH:MM]
Exit 0 always unless the script itself breaks (2)."""
import argparse, datetime as dt, glob, hashlib, io, os, re, shutil, string, sys, tempfile, zipfile

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
FRESH_H = 26
KIT = "S723"


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
            if "superseded" in f[2].lower() or (len(f) > 3 and "superseded" in f[3].lower()):
                continue
            m = re.search(r"([A-Za-z]:\\[^\s·]+)", f[2])
            if not m:
                continue
            key = m.group(1).lower()
            out.setdefault(key, f[1])
    return out


def drive_manifest():
    """{lower file name: md5} from ToMedical\\_kit\\KIT_MANIFEST.txt on whichever drive letter has it; None if not mounted."""
    if os.name != "nt":
        return None
    for L in string.ascii_uppercase:
        p = "%s:\\My Drive\\ToMedical\\_kit\\KIT_MANIFEST.txt" % L
        if os.path.isfile(p):
            out = {}
            with open(p, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    f = [x.strip() for x in ln.split("|")]
                    if len(f) >= 3 and re.fullmatch(r"[0-9a-f]{32}", f[2]):
                        out[f[0].lower()] = f[2]
            return out
    return None


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


def repack(zpath, infos, data, sums_text, changes, stamp):
    """Write the new zip beside the old one; return (bytes, new sums text). Only `changes` {member: bytes} differ."""
    nl = "\r\n" if "\r\n" in (sums_text or "") else "\n"
    new_data = dict(data)
    new_data.update(changes)
    if sums_text is not None:
        lines = sums_text.split(nl)
        out = []
        for ln in lines:
            m = re.match(r"^([0-9a-f]{32})  (.+)$", ln)
            if m and m.group(2) in changes:
                ln = "%s  %s" % (md5b(changes[m.group(2)]), m.group(2))
            out.append(ln)
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
    return buf.getvalue(), (new_data.get("MD5SUMS.txt") or b"").decode("ascii") if sums_text is not None else None


def write_atomic(path, b):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".s723_", dir=d)
    with os.fdopen(fd, "wb") as fh:
        fh.write(b)
    os.replace(tmp, path)
    if md5f(path) != md5b(b):
        raise IOError("read-back of %s did not match" % path)


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
    if not changes:
        return say("medical", "CURRENT", "every payload file equals the PC's own copy" + ("; " + "; ".join(notes) if notes else ""))
    if a.dry:
        return say("medical", "BEHIND (dry run)", "; ".join(behind + notes))
    stamp = (now.year, now.month, now.day, 12, 0, 0)
    zb, _ = repack(zpath, infos, data, sums, changes, stamp)
    tmpz = zpath + ".s723new"
    open(tmpz, "wb").write(zb)
    ok2, why2, d2, _, _ = check_zip(tmpz)
    if not ok2 or any(md5b(d2[n]) != md5b(b) for n, b in changes.items()) or sorted(d2) != sorted(data) or \
            any(md5b(d2[n]) != md5b(data[n]) for n in data if n not in changes and n != "MD5SUMS.txt"):
        os.remove(tmpz)
        return say("medical", "REFUSED", "the repacked zip did not prove itself (%s) -- the old kit stands" % (why2 or "members"))
    new_md5 = md5b(zb)
    nl = "\r\n" if "\r\n" in itext else "\n"
    lines = itext.split(nl)
    names = ", ".join(n.split("/")[-1] for n in sorted(changes))
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
    return say("medical", "REPACKED", "kit.zip -> %s: %s%s" % (new_md5[:8], "; ".join(behind), ("; " + "; ".join(notes)) if notes else ""), repacked=True)


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
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--now", default="")
    a = ap.parse_args(argv)
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=IST) if a.now else dt.datetime.now(IST)
    kits = os.path.join(a.repo, "deploy_kits", "PC_KITS")
    pins_path = newest_pins(os.path.join(a.repo, "deploy_kits", "KB_canon_all"))
    pins = pin_map(pins_path)
    manifest = drive_manifest()
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
           ""] + lines + ([""] + ["  " + moved] if moved else []) + \
          ["", "A repacked kit reaches the Clinic PCs page with the owner's next PUBLISH_ALL." if state["repacked"] else
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
