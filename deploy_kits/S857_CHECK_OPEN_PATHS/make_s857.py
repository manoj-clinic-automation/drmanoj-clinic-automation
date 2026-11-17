"""make_s857.py <code dir holding the FROM files> <out dir> -- kit S857_CHECK_OPEN_PATHS: scan_register.py gets ONE tail block (no anchor inside the
old text); month_asks.py is replaced whole (this script's folder holds it). Every FROM file is checked against its pin first."""
import hashlib, os, shutil, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"scan_register.py": "95c5ad0e42b957de37a60f16eb335d73", "month_asks.py": "d0592c402c4838d8fe2fa311220de4e1"}
TAIL = '''


# ---- S857_CHECK_OPEN_PATHS (17-Nov-2026, Sanjeevni session 476; the owner 20:54): the purchase check names what is open --------------------------
#  The strip 'NEFT on hold · N open' names the open items and expands inline: each with its row, whose it is and its full path to resolution
#  (month_asks.open_items, one source); every row holding something open is highlighted; 'Open row N' opens that row in place. Row 7's
#  'your confirm' says which it is: 'settled by your confirmation' (row 3 has nothing waiting) or 'waiting for your confirmation (row 3)'.
#  Fail-soft: without month_asks, the page as before.
import re as _re857
S857_CSS = ("<style>#s726chk details.s857{cursor:pointer}#s726chk details.s857>summary{list-style:none;font-weight:600}"
            "#s726chk details.s857>summary::-webkit-details-marker{display:none}#s726chk .s857tap{font-weight:400;font-size:13px;opacity:.85;white-space:nowrap}"
            "#s726chk .s857i{background:#fff;color:#1d2939;border:1px solid #fedf89;border-radius:8px;padding:8px 10px;margin:8px 0;font-weight:400}"
            "#s726chk .s857i ol{margin:6px 0 4px 18px;padding:0}#s726chk .s857w{font-size:13px;color:#667085}"
            "#s726chk details.row.s857open{border-left:5px solid #dc6803;background:#fffaeb}</style>")
S857_JS = ("<script>function s857row(n){var e=document.getElementById('s857r'+n);if(e){e.open=true;e.scrollIntoView({behavior:'smooth',block:'start'});}"
           "return false;}</script>")


def _s857_words(h, pending):
    if pending:
        h = _re857.sub(r"(\\d+) your confirm\\b", r"\\1 waiting for your confirmation (row 3)", h)
        h = h.replace("Your confirm counts as the summary", "Waiting for your confirmation on row 3 — it will stand as the summary")
        h = h.replace("your Confirm on row 3 counts as the summary", "your confirmation on row 3 is awaited — it will stand as the summary")
    else:
        h = _re857.sub(r"(\\d+) your confirm\\b", r"\\1 settled by your confirmation", h)
        h = h.replace("Your confirm counts as the summary", "Settled by your confirmation — it stands as the summary")
        h = h.replace("your Confirm on row 3 counts as the summary", "settled by your confirmation on row 3 — it stands as the summary")
    return h


def _s857_item(it):
    steps = "".join("<li>%s</li>" % esc(s) for s in it.get("steps") or [])
    return ('<div class="s857i"><b>Row %d · %s</b><div class="s857w">Whose: %s</div><ol>%s</ol>'
            '<a href="#s857r%d" onclick="return s857row(%d)">Open row %d ▸</a></div>'
            % (int(it["row"]), esc(it["what"]), esc(it.get("whose") or ""), steps, int(it["row"]), int(it["row"]), int(it["row"])))


_check_body_before_s857 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S857: what is open, named, with its path
    h = _check_body_before_s857(con, month, prefix, months, r)
    try:
        if month_class(con, month) != "counted":
            return h
        import month_asks as _ma857                            # noqa: PLC0415
        if _ma857.is_off():                                    # its switches (and an older kit's frozen walk) -- the page as before S857
            return h
        items = _ma857.open_items(con, month)
        unread = any(str(it.get("what") or "").startswith("The purchase check could not be read") for it in items)
        if not unread:                                         # review: row 3's state from the same reading; nothing reassuring when unread
            h = _s857_words(h, any(int(it["row"]) == 3 for it in items))
        rows_open = {int(it["row"]) for it in items}
        k = [0]

        def _rid(m):
            k[0] += 1
            n = k[0]
            if n > 8:
                return m.group(0)
            return '<details id="s857r%d" class="row%s' % (n, " s857open" if n in rows_open else "")
        h = _re857.sub(r'<details class="row', _rid, h)
        m = _re857.search(r'<div class="strip hold" id="s726strip">([^<]*)</div>', h)
        if m and items:
            names = "; ".join(it["what"] for it in items[:3]) + (" and %d more" % (len(items) - 3) if len(items) > 3 else "")
            new = ('<details class="strip hold s857" id="s726strip"><summary>%s — %s <span class="s857tap">· tap to see what each needs ▾</span></summary>%s</details>'
                   % (m.group(1), esc(names), "".join(_s857_item(it) for it in items)))
            h = h[:m.start()] + new + h[m.end():]
        h = h + S857_CSS + S857_JS
    except Exception as e:                                    # noqa: BLE001 -- the page as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S857: %r" % (e,), file=_sys.stderr)
    return h
# ---- S857 end ---------------------------------------------------------------------------------------------------------------------------
'''
os.makedirs(OUT, exist_ok=True)
b = open(os.path.join(SRC, "scan_register.py"), "rb").read()
assert hashlib.md5(b).hexdigest() == FROM["scan_register.py"], "scan_register.py is not at its FROM pin"
assert hashlib.md5(open(os.path.join(SRC, "month_asks.py"), "rb").read()).hexdigest() == FROM["month_asks.py"], "month_asks.py is not at its FROM pin"
t = b.decode("utf-8").rstrip("\n") + TAIL
open(os.path.join(OUT, "scan_register.py"), "wb").write(t.encode("utf-8"))
print("scan_register.py", hashlib.md5(t.encode("utf-8")).hexdigest())
here = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(OUT) != here:
    shutil.copy(os.path.join(here, "month_asks.py"), os.path.join(OUT, "month_asks.py"))
print("month_asks.py", hashlib.md5(open(os.path.join(OUT, "month_asks.py"), "rb").read()).hexdigest())
