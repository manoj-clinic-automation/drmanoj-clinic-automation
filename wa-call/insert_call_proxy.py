#!/usr/bin/env python3
"""insert_call_proxy.py — safely add the /call proxy blocks to the live
vhost.conf of followup.dr-manoj.in.

WHAT IT DOES
  - Reads the REAL vhost.conf (so existing lines are never retyped/altered).
  - Inserts an  extprocessor call_api { ... }  block right AFTER the existing
    extprocessor wa_send_api { ... } block.
  - Inserts a   context /call { ... }          block right BEFORE the existing
    catch-all  context / { ... }  block.
  - Writes the result to vhost.conf.NEW. It does NOT touch the live file.
  - Idempotent: if /call is already present, it does nothing.
  - Aborts (writing nothing) if it can't find the expected anchor blocks.

USAGE
  python3 insert_call_proxy.py
Then review with:
  diff <the .bak file>  /usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf.new
"""
import sys

LIVE = "/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf"
NEW = LIVE + ".new"

CALL_EXTPROC = """extprocessor call_api {
  type                    proxy
  address                 127.0.0.1:8097
  maxConns                100
  pcKeepAliveTimeout      60
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}
"""

CALL_CONTEXT = """context /call {
  type                    proxy
  handler                 call_api
  addDefaultCharset       off
}
"""


def main():
    with open(LIVE, "r", encoding="utf-8") as f:
        txt = f.read()

    if "extprocessor call_api" in txt or "context /call" in txt:
        print("ALREADY PRESENT: /call blocks are already in the file. Nothing written.")
        return 0

    # 1) Insert the call_api extprocessor right after the wa_send_api block.
    marker = "extprocessor wa_send_api {"
    i = txt.find(marker)
    if i == -1:
        print("ABORT: could not find 'extprocessor wa_send_api {'. No file written.")
        return 2
    # The block has no nested braces, so the first "\n}" after it is its closer.
    j = txt.find("\n}", i)
    if j == -1:
        print("ABORT: could not find the end of the wa_send_api block. No file written.")
        return 2
    after = j + len("\n}")
    txt = txt[:after] + "\n" + CALL_EXTPROC.rstrip("\n") + "\n" + txt[after:]

    # 2) Insert the context /call block right before the catch-all "context / {".
    marker2 = "context / {"
    k = txt.find(marker2)
    if k == -1:
        print("ABORT: could not find the catch-all 'context / {'. No file written.")
        return 2
    txt = txt[:k] + CALL_CONTEXT.rstrip("\n") + "\n" + txt[k:]

    with open(NEW, "w", encoding="utf-8") as f:
        f.write(txt)

    print("OK: wrote", NEW)
    print("Existing lines untouched; two new blocks added (call_api extprocessor + /call context).")
    print("Now review the difference, then we validate before going live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
