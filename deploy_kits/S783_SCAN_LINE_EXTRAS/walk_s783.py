#!/usr/bin/env python3
"""walk_s783.py FILES_DIR SHARED_DIR FINANCE_DIR ASSETAPP_DIR SCHEMA [--control]
Kit S783_SCAN_LINE_EXTRAS. FILES_DIR holds the files under test (claude_reader.py, provisional_s781.py -- the kit's, or the live ones for
the control); the rest is read from FINANCE_DIR / ASSETAPP_DIR. Part A: the reader on made-up answers (no call to any reader, no key read).
Part B: the Purchase bills page on made-up rows -- walk_s781.py beside this file, run on FILES_DIR's provisional_s781.py.
Last line: 'WALK S783 GREEN' or, with --control on the live files, 'CONTROL S783 RED as it must be'."""
import importlib.util
import os
import subprocess
import sys

FILES, SHARED, FIN, APP, SCHEMA = sys.argv[1:6]
CONTROL = "--control" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


src = os.path.join(FILES, "claude_reader.py") if os.path.exists(os.path.join(FILES, "claude_reader.py")) else os.path.join(APP, "claude_reader.py")
spec = importlib.util.spec_from_file_location("claude_reader_s783walk", src)
CR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CR)                                     # module level only: no key is read, no call is made
ans = {"vendor": "WALK PHARMA", "bill_no": "W1", "bill_date": "2026-11-05", "total_amount": 1120,
       "items": [{"name": "PANTAVIN 40", "qty": 10, "free": "2", "mrp": 142.5, "discount": "5%", "gst": "5 %", "amount": 1000},
                 {"name": ""}, {"name": "SHELCAL 500", "qty": 1, "mrp": "n/a", "gst": 12, "amount": 120}]}
c1 = CR.clean_pharmacy(dict(ans, is_summary=False)) or {}
it = c1.get("items") or []
check("A1 the pharmacy prompt asks each item line for free, MRP, discount and GST", all(k in getattr(CR, "PHARMACY_PROMPT", "") for k in
                                                                                       ('"free"', '"mrp"', '"discount"', '"gst"')))
check("A2 the bill prompt of the other lanes is unchanged (no new keys)", '"mrp"' not in CR.PROMPT)
check("A3 a pharmacy bill's reading keeps the four figures as numbers ('5%' read as 5), null when unreadable, the lines in their order",
      len(it) == 2 and it[0].get("free") == 2.0 and it[0].get("mrp") == 142.5 and it[0].get("discount") == 5.0 and it[0].get("gst") == 5.0
      and it[1].get("mrp") is None and it[1].get("gst") == 12.0 and it[1]["name"] == "SHELCAL 500")
h, items = CR.to_bill(ans)
check("A4 to_bill (what reaches bill_items) is exactly as before", items and set(items[0]) == {"name", "qty", "pack", "rate", "amount", "make", "model",
                                                                                            "serial", "batch", "expiry", "hsn"})
sm = CR.clean_pharmacy({"is_summary": True, "dealer": "WALK", "lines": [{"kind": "bill", "no": "1", "date": "2026-10-03", "amount": 10}]}) or {}
check("A5 a dealer statement is cleaned as before (no item keys added)", sm.get("doc_kind") == "summary" and "items" not in sm)
check("A6 the other lanes' clean() is exactly as before (no new keys)", set(CR.clean(ans)["items"][0]) == {
    "name", "qty", "unit", "rate", "amount", "make", "model", "serial", "batch", "expiry", "hsn"})
sent = []
if hasattr(CR, "_post_before_s783"):
    def _fake(body, key):
        sent.append(body)
        return (200, {"stop_reason": "max_tokens", "content": []}, "") if len(sent) == 1 else (200, {"stop_reason": "end_turn", "content": []}, "")
    CR._post_before_s783 = _fake
    blk = {"type": "image", "source": {}}
    CR._post({"model": "m", "max_tokens": 8000, "messages": [{"role": "user", "content": [blk, {"type": "text", "text": CR.PHARMACY_PROMPT}]}]}, "k")
    CR._post({"model": "m", "max_tokens": 8000, "messages": [{"role": "user", "content": [blk, {"type": "text", "text": CR.PROMPT}]}]}, "k")
check("A7 a pharmacy reading may answer longer (16000); a bill still too long is asked once more with the prompt as before S783; another "
      "lane's call passes untouched", len(sent) == 3 and sent[0]["max_tokens"] == 16000 and sent[0]["messages"][0]["content"][1]["text"] == CR.PHARMACY_PROMPT
      and sent[1]["messages"][0]["content"][1]["text"] == getattr(CR, "_S783_PROMPT_BEFORE", None) and '"mrp"' not in sent[1]["messages"][0]["content"][1]["text"]
      and sent[2]["max_tokens"] == 8000 and sent[2]["messages"][0]["content"][1]["text"] == CR.PROMPT)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
out = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.join(HERE, "walk_s781.py")] + [os.path.abspath(x) for x in (FILES, SHARED, FIN, SCHEMA)],
                     capture_output=True, text=True, timeout=600, env=env, cwd="/tmp")
last = (out.stdout.strip().splitlines() or [""])[-1]
check("B the Purchase bills page walk (S781's 49 checks + S783's three): %s" % last[:160], last == "WALK S781 GREEN (+S783)")
red = [n for n, ok in RES if not ok]
if CONTROL:
    print("CONTROL S783 RED as it must be" if red else "CONTROL S783 NOT RED")
    sys.exit(0)
print("WALK S783 GREEN" if not red else "WALK S783 RED (%d of %d): %s" % (len(red), len(RES), "; ".join(red)))
