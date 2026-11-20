#!/usr/bin/env python3
"""make_s895.py -- how the three server files of kit S895 were made from the 20-Nov-2026 bundle's bytes (exact anchors).
   python3 make_s895.py <bundle_root> <pc_tracker_dir> <out_dir>   -- refuses unless the inputs are at their FROM pins."""
import hashlib, os, sys
B, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]
def rd(p): return open(p, encoding="utf-8").read()
def wr(name, s): open(os.path.join(OUT, name), "w", encoding="utf-8", newline="").write(s); print(name, md5(os.path.join(OUT, name)))
def rep(s, old, new):
    assert s.count(old) == 1, old[:60]; return s.replace(old, new)
# 1. the receiver: the origin mark
src = os.path.join(B, "wa/followup_receiver.py"); assert md5(src) == "384e9ed8", md5(src)
s = rep(rd(src), '''    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    size  = final.stat().st_size
    return jsonify(ok=True, stored=name, bytes=size, at=stamp), 200
''', '''    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    size  = final.stat().st_size
    # S895: who sent it. The server's own runner marks its uploads X-FU-Origin: server; anything else is the
    # clinic PC (the spare after the switch). The mark file is the red line's evidence; the log holds no patient data.
    origin = (request.headers.get("X-FU-Origin", "") or "pc").strip()[:16]
    try:
        with open(str(INBOX_DIR / ".uploads.log"), "a", encoding="utf-8") as fh:
            fh.write("%s %s %s %d\\n" % (stamp, origin, name, size))
        if origin != "server":
            with open(str(INBOX_DIR / ".last_pc_upload"), "w", encoding="utf-8") as fh:
                fh.write("%s %s\\n" % (stamp, name))
    except OSError:
        pass
    return jsonify(ok=True, stored=name, bytes=size, at=stamp, origin=origin), 200
'''); wr("followup_receiver.py", s)
# 2. docterz_ingest: the box's outputs first (see the kit's docterz_ingest.py for the five blocks; anchors below)
src = os.path.join(B, "finance/docterz_ingest.py"); assert md5(src) == "d2102bb7", md5(src)
s = rd(src)
s = rep(s, 'TENDER_FILE = "Day_Tenders.csv"\n', 'TENDER_FILE = "Day_Tenders.csv"\n' + '''# S895: the tracker runs on this box from the switch evening; its outputs folder is read FIRST. A business date
# the box made is never overwritten from Drive (the PC spare's copy there is modified later and would win otherwise).
LOCAL_DIR = os.environ.get("DOCTERZ_LOCAL_OUTPUTS", "/root/followup_tracker/outputs")
LOCAL_TAG = "local:"
''')
s = rep(s, 'def list_day_files():\n', '''def list_local_files():
    """[(title, 'local:'+title, mtime iso)] for every Staff_Action_Today_*.xlsx the box's own tracker wrote."""
    out = []
    for p in sorted(glob.glob(os.path.join(LOCAL_DIR, PREFIX + "*.xlsx"))):
        try:
            mt = dt.datetime.utcfromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except OSError:
            continue
        out.append((os.path.basename(p), LOCAL_TAG + os.path.basename(p), mt))
    return out


def local_days(con):
    """the business dates the box's own tracker owns in the table"""
    return {r["business_date"] for r in con.execute("SELECT business_date FROM %s WHERE source_id LIKE ?" % TABLE, (LOCAL_TAG + "%",))}


def read_bytes(fid):
    """the file's bytes: the box's own outputs for a local: id, Drive otherwise"""
    if fid.startswith(LOCAL_TAG):
        with open(os.path.join(LOCAL_DIR, fid[len(LOCAL_TAG):]), "rb") as fh:
            return fh.read()
    return fetch_bytes(fid)


def list_day_files():
''')
s = rep(s, '''    f = find_tender_file()
    if not f:
        print("split legs: no %s in the folder -- skipped (this is normal until the PC-side pass "
              "has run)" % TENDER_FILE)
        return 0
    raw = fetch_bytes(f["id"]).decode("utf-8-sig", "replace")
''', '''    local_tf = os.path.join(LOCAL_DIR, TENDER_FILE)
    if os.path.exists(local_tf):                      # S895: the box's own legs first
        with open(local_tf, "rb") as fh:
            raw = fh.read().decode("utf-8-sig", "replace")
        f = {"id": LOCAL_TAG + TENDER_FILE, "modifiedTime": dt.datetime.utcfromtimestamp(os.path.getmtime(local_tf)).strftime("%Y-%m-%dT%H:%M:%S")}
    else:
        f = find_tender_file()
        if not f:
            print("split legs: no %s in the folder -- skipped (this is normal until the PC-side pass "
                  "has run)" % TENDER_FILE)
            return 0
        raw = fetch_bytes(f["id"]).decode("utf-8-sig", "replace")
''')
s = rep(s, '''    files = list_day_files()
    print("Drive: %d day files in the folder" % len(files))
    # of two files for one business date, the LATER-modified wins: process oldest first.
    files.sort(key=lambda t: t[2])
''', '''    local_files = list_local_files()
    drive_files = list_day_files()
    print("box: %d day files in %s; Drive: %d day files in the folder" % (len(local_files), LOCAL_DIR, len(drive_files)))
    # of two Drive files for one business date, the LATER-modified wins: process oldest first.
    drive_files.sort(key=lambda t: t[2])
    # S895: the box's own files FIRST; a Drive file is then skipped for any date the box owns.
    files = local_files + drive_files
    owned = local_days(con)
''')
s = rep(s, '''        try:
            d = parse_bytes(fetch_bytes(fid))
''', '''        try:
            d = parse_bytes(read_bytes(fid))
''')
s = rep(s, '''        if not a.dry_run:
            upsert(con, d, title, fid, mtime)
            upsert_lines(con, d)
        done += 1
''', '''        if fid.startswith(LOCAL_TAG):
            owned.add(d["business_date"])
        elif d["business_date"] in owned:
            print("  LOCAL WINS %-35s the box made %s itself -- Drive's copy not taken" % (title, d["business_date"]))
            skipped += 1
            continue
        if not a.dry_run:
            upsert(con, d, title, fid, mtime)
            upsert_lines(con, d)
        done += 1
'''); wr("docterz_ingest.py", s)
# 3. the Sheet writer = the PC's push_followups_today.py (the Do_Not_Call filter) with the box's two paths
src = os.path.join(PC, "push_followups_today.py"); assert md5(src) == "74122185", md5(src)
s = rd(src)
s = rep(s, 'OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")', 'OUTPUTS_DIR = os.environ.get("FU_INBOX_DIR", "/root/wa/followup-inbox")   # S895: the box\'s inbox (was the PC\'s outputs)')
s = rep(s, 'KEY_DIR = BASE_DIR', 'KEY_DIR = os.environ.get("FU_KEY_DIR", "/root/wa")   # S895')
wr("push_followups_vps.py", s)
