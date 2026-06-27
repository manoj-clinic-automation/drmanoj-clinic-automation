#!/usr/bin/env python3
# Read-only. Finds the MyOperator S3 'link' for one media message and reports
# ONLY the HTTP status / content-type / size. Never prints the URL itself.
import sys, json, os, urllib.request
from urllib.parse import urlparse
LOGDIR = "/root/wa/wa_logs"
def find_link(fp):
    with open(fp, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: o = json.loads(line)
            except Exception: continue
            ctx = (o.get("body",{}).get("payload",{}).get("data",{}).get("context",{}))
            if isinstance(ctx, dict) and ctx.get("link"):
                return ctx.get("link"), ctx.get("url"), ctx.get("mime_type")
    return None, None, None
def probe(label, url):
    if not url:
        print("%-9s: (none in this message)" % label); return
    host = urlparse(url).netloc
    req = urllib.request.Request(url, method="GET")  # GET; we read nothing
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            ct = r.headers.get("Content-Type","?")
            cl = r.headers.get("Content-Length","?")
            print("%-9s: status=%s  type=%s  size=%s  host=%s" % (label, r.status, ct, cl, host))
    except urllib.error.HTTPError as e:
        print("%-9s: status=%s (BLOCKED/needs-auth)  host=%s" % (label, e.code, host))
    except Exception as e:
        print("%-9s: error=%s  host=%s" % (label, type(e).__name__, host))
def main():
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    fp = os.path.join(LOGDIR, fname) if fname else None
    if not fp or not os.path.exists(fp):
        print("file not found"); return
    link, url, mime = find_link(fp)
    print("mime_type:", mime)
    probe("S3_link", link)        # the one we hope is public
    probe("meta_url", url)        # the lookaside one, for contrast
if __name__ == "__main__":
    main()
