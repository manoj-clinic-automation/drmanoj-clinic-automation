"""spine_evidence.py -- S272 / kit S331 (Sanjeevni). The evidence store: one PHI-free reading per Marg export.

    /root/wa/venv/bin/python3 -B /root/finance/spine/spine_evidence.py [--source drive|FOLDER] [--out DIR] [--limit N]

For every export in the Marg archive (Google Drive 'Clinic Data Archive/MargArchive', the same mirror the
collector reads, through the same read-only service account) that has no reading yet, by md5:
  fetch it to a private temporary folder -> read it with the certified readers (marg_read.py) ->
  write <md5>.json into the store -> delete the temporary copy. Nothing else is kept.

* A sale report's patient columns are never read into a reading (marg_read.read_sale_detail), so the store
  holds no name and no mobile. The raw file is never kept here, exactly as the collector keeps none.
* Readings in MargArchive/_SPINE_SEED/*.json (made on manojz with the same reader, for the April-August
  back-fill that exists nowhere else) are copied in as they are, after the same PHI check.
* A reading is written once and never changed. A new reader version does not rewrite old readings unless
  --reread is given; the spine records which reader produced each reading.
* Changes no table, no file of the collector, no archive. Its OFF switch is /root/finance/_off/ALL_OFF
  (S274) and its own /root/finance/spine/OFF.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import marg_read  # noqa: E402

OUT_DEFAULT = os.path.join(HERE, "readings")
INGEST_DIR = "/root/marg_ingest"
OFF_FLAGS = (os.path.join(HERE, "OFF"), "/root/finance/_off/ALL_OFF")
SKIP_FOLDERS = ("_spool", "_outbox", "_REFUSED", "_UNKNOWN", "_rescued")
SEED_FOLDER = "_SPINE_SEED"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
PHI_KEYS = re.compile(r'"(patient|mobile|phone|party|customer|doctor)"', re.I)


def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def phi_free(rec):
    """A reading may carry no key that names a person, and no 10-digit run anywhere (a mobile)."""
    s = json.dumps(rec)
    s = re.sub(r'[0-9a-f]{32}', '', s)                    # md5 hashes are not numbers
    return not PHI_KEYS.search(s) and not re.search(r'(?<![0-9a-zA-Z])[6-9]\d{9}(?![0-9a-zA-Z])', s)


class Folder:
    """A local folder laid out like the archive (tests, and manojz)."""

    def __init__(self, root):
        self.root = root

    def list(self):
        out = []
        for dp, dns, fns in os.walk(self.root):
            rel = os.path.relpath(dp, self.root)
            top = rel.split(os.sep)[0]
            if top in SKIP_FOLDERS:
                continue
            for fn in fns:
                p = os.path.join(dp, fn)
                if fn.lower().endswith((".xls", ".xlsx")) or (top == SEED_FOLDER and fn.endswith(".json")):
                    b = open(p, "rb").read()
                    out.append(dict(id=p, name=fn, folder="" if rel == "." else rel, md5=hashlib.md5(b).hexdigest()))
        return out

    def fetch(self, f):
        return open(f["id"], "rb").read()


class Drive:
    """The collector's own Drive reader (marg_ingest.DriveSource), imported read-only; lists .json in the seed folder too."""

    def __init__(self):
        sys.path.insert(0, INGEST_DIR)
        import marg_ingest  # noqa: E402  -- definitions only; nothing runs on import
        self.D = marg_ingest.DriveSource()

    def list(self):
        out, stack = [], [(self.D.root_id, "")]
        while stack:
            fid, rel = stack.pop()
            for f in self.D._children(fid):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    if f["name"] not in SKIP_FOLDERS:
                        stack.append((f["id"], os.path.join(rel, f["name"]) if rel else f["name"]))
                    continue
                top = rel.split(os.sep)[0] if rel else ""
                ok = f["name"].lower().endswith((".xls", ".xlsx")) or (top == SEED_FOLDER and f["name"].endswith(".json"))
                if ok and f.get("md5Checksum"):
                    out.append(dict(id=f["id"], name=f["name"], folder=rel, md5=f["md5Checksum"]))
        return out

    def fetch(self, f):
        return self.D._media(f["id"])


def run(src, out, limit=400, reread=False, log=print):
    os.makedirs(out, exist_ok=True)
    have = {fn[:-5] for fn in os.listdir(out) if fn.endswith(".json")}
    files = src.list()
    todo = []
    for f in files:
        if f["name"].endswith(".json"):
            m = re.match(r'^([0-9a-f]{32})\.json$', f["name"])
            if m and m.group(1) not in have:
                todo.append(f)
        elif reread or f["md5"] not in have:
            todo.append(f)
    done = failed = skipped = 0
    for f in todo[:limit]:
        tmp = tempfile.mkdtemp(prefix="spine_ev_")
        try:
            raw = src.fetch(f)
            if hashlib.md5(raw).hexdigest() != f["md5"]:
                raise RuntimeError("bytes do not match the source md5")
            if f["name"].endswith(".json"):
                rec = json.loads(raw.decode("utf-8"))
                if rec.get("md5") != f["name"][:-5] or not rec.get("family"):
                    raise RuntimeError("a seed reading must be named by the md5 it carries")
                rec["seeded_from"] = f["folder"]
            else:
                p = os.path.join(tmp, f["name"])
                with open(p, "wb") as fh:
                    fh.write(raw)
                rec = marg_read.reading_record(p, f["name"])
                rec["folder"] = f["folder"]
                if rec.get("family") is None:
                    skipped += 1
                    rec = dict(md5=rec["md5"], name=f["name"], family=None, folder=f["folder"], reader=marg_read.READER_VERSION)
            if not phi_free(rec):
                raise RuntimeError("the reading would carry a person's detail -- refused, nothing written")
            rec["read_at"] = now()
            with open(os.path.join(out, rec["md5"] + ".json.tmp"), "w") as fh:
                json.dump(rec, fh)
            os.replace(os.path.join(out, rec["md5"] + ".json.tmp"), os.path.join(out, rec["md5"] + ".json"))
            done += 1
            if rec.get("family"):
                log("  %-5s %-24s %s%s" % ("ok" if rec.get("ok") else "FAIL", rec["family"], f["name"][:70],
                                            "" if rec.get("ok") else "  -- " + "; ".join(rec.get("failed", [])[:2])))
        except Exception as e:  # noqa: BLE001
            failed += 1
            log("  ERROR %s -- %s" % (f["name"][:70], str(e)[:160]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    n = len([x for x in os.listdir(out) if x.endswith(".json")])
    log("spine_evidence %s: listed %d, read %d (%d not a report the spine uses), failed %d, store now %d readings%s" % (
        now(), len(files), done, skipped, failed, n, "; more next run" if len(todo) > limit else ""))
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="drive")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--reread", action="store_true")
    a = ap.parse_args(argv)
    for f in OFF_FLAGS:
        if os.path.exists(f):
            print("spine_evidence: switched off (%s)" % f)
            return 0
    src = Drive() if a.source == "drive" else Folder(a.source)
    return run(src, a.out, limit=a.limit, reread=a.reread)


if __name__ == "__main__":
    sys.exit(main())
