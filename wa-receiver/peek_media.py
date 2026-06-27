#!/usr/bin/env python3
# Read-only diagnostic. Prints the STRUCTURE of one media message with all
# sensitive values masked. Never prints phone numbers, captions, names, or raw URLs.
import sys, json, glob, os
from urllib.parse import urlparse

LOGDIR = "/root/wa/wa_logs"
MEDIA_HINTS = ("image","document","video","audio","sticker","voice","media","mime")

# keys whose VALUES are safe structural enums -> show as-is
SHOW = {"type","mime_type","mimetype","content_type","contenttype","event_type",
        "eventtype","direction","status","language","ext","extension","animated",
        "voice","object","category"}
# keys that are phone-ish -> fully masked regardless of type
PHONEISH = {"phone","number","customer_number","from","to","msisdn","wa_id",
            "waid","mobile","contact","sender","recipient","customer"}
# keys that are free text / personal -> length only
TEXTISH = {"caption","text","body","name","message","title","filename","file_name","first_name","last_name"}
# numeric keys that are safe/useful to show
NUMOK = {"timestamp","time","width","height","duration","filesize","file_size","size","seq","page"}

def looks_media(line):
    low = line.lower()
    return any(h in low for h in MEDIA_HINTS)

def redact(obj, key=None):
    k = (key or "").lower()
    if isinstance(obj, dict):
        return {kk: redact(vv, kk) for kk, vv in obj.items()}
    if isinstance(obj, list):
        return [redact(v, key) for v in obj][:3] + (["…(+%d more)"%(len(obj)-3)] if len(obj)>3 else [])
    if isinstance(obj, str):
        if k in PHONEISH: return "<phone masked>"
        if k in SHOW:     return obj            # safe enum value
        if obj.startswith("http://") or obj.startswith("https://"):
            u = urlparse(obj)
            return "<url scheme=%s host=%s path_len=%d has_query=%s total_len=%d>" % (
                u.scheme, u.netloc, len(u.path), bool(u.query), len(obj))
        if k in TEXTISH:  return "<text len=%d>" % len(obj)
        return "<str len=%d>" % len(obj)
    if isinstance(obj, (int, float)):
        if k in PHONEISH: return "<phone masked>"
        if k in NUMOK:    return obj
        if len(str(abs(int(obj)))) >= 10: return "<num masked len=%d>" % len(str(abs(int(obj))))
        return obj
    return obj

def main():
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    files = [os.path.join(LOGDIR, fname)] if fname else sorted(glob.glob(os.path.join(LOGDIR,"*.jsonl")))
    for fp in files:
        if not os.path.exists(fp): continue
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or not looks_media(line): continue
                try: obj = json.loads(line)
                except Exception: continue
                print("=== one media message from %s (all sensitive values masked) ===" % os.path.basename(fp))
                print(json.dumps(redact(obj), indent=2, ensure_ascii=False))
                # quick hint
                blob = json.dumps(obj).lower()
                has_url = "http://" in blob or "https://" in blob
                has_mid = '"id"' in blob or "media_id" in blob or '"media"' in blob
                print("--- HINT: direct_url_present=%s  media_id_like_present=%s ---" % (has_url, has_mid))
                return
    print("No media message could be parsed.")

if __name__ == "__main__":
    main()
