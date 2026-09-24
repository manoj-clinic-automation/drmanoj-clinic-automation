#!/usr/bin/env python3
"""apply_s393.py -- kit S393_PETTY_FOLD. Makes the S393 petty_book.py from the live bytes (88f28571) by anchored
edits; each anchor must occur exactly once. The two page builders are replaced whole from new_pages.py (the keeper's
Hindi page + the fold helper) and new_owner.py (the doctors' page).
Usage: python apply_s393.py <live petty_book.py> <kit folder> <out>"""
import hashlib, os, sys

src, kdir, dst = sys.argv[1], sys.argv[2], sys.argv[3]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == "88f2857193938a493f20c9c31f672d1e", "the source is not the live petty_book.py"
s = b.decode("utf-8")


def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:80])
    s = s.replace(old, new)


def between(start, end, new):
    global s
    i, j = s.index(start), s.index(end)
    assert s.count(start) == 1 and s.count(end) == 1 and i < j, "block %r" % start
    s = s[:i] + new + s[j:]


# 1 -- the two pages, replaced whole
between("def _keeper_html(con, u, msg):", "def _form_html(", open(os.path.join(kdir, "new_pages.py"), encoding="utf-8").read())
between("def _owner_html(con, u, msg):", "# ---------------------------------------------------------------- shells",
        open(os.path.join(kdir, "new_owner.py"), encoding="utf-8").read())

# 2 -- the same entry twice in a few minutes is refused (24-Sep: one 9,000 top-up saved three times)
rep('''    other = (request.form.get("other_name") or "").strip()[:60] if need_name else ""
    if need_name and not other:
        return redirect(back + "?msg=name")
    photo, perr = _save_photo(request.files.get("photo"))''', '''    other = (request.form.get("other_name") or "").strip()[:60] if need_name else ""
    if need_name and not other:
        return redirect(back + "?msg=name")
    # S393: the same entry by the same person within DUP_MINUTES is a repeated tap, not a second payment
    cut = (_now() - dt.timedelta(minutes=DUP_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    if con.execute("SELECT 1 FROM petty_entry WHERE void_at='' AND kind=? AND party=? AND other_name=? AND amount_p=? "
                   "AND by_whom=? AND at BETWEEN ? AND ? LIMIT 1", (kind, party, other, amt, _who(u), cut, _stamp())).fetchone():
        return redirect("/finance/petty?msg=dup")
    photo, perr = _save_photo(request.files.get("photo"))''')
rep('''UPLOAD_MAX = 12 * 1024 * 1024
''', '''UPLOAD_MAX = 12 * 1024 * 1024
DUP_MINUTES = 10          # S393
''')
rep('''          "amount": "Rakam sahi likhiye", "name": "Naam likhiye",''',
    '''          "dup": "Yeh entry abhi-abhi save ho chuki hai — dobara nahi likhi. Sach mein doosri baar diya ho to 10 minute baad likhiye.",
          "amount": "Rakam sahi likhiye", "name": "Naam likhiye",''')

# 3 -- the look of the folds and the strip
rep('''.pill{font-size:14px;padding:2px 9px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line)}
</style>''', '''.pill{font-size:14px;padding:2px 9px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line)}
.strip{display:flex;flex-wrap:wrap;gap:4px 16px;background:var(--paper);border:2px solid var(--accent);border-radius:10px;padding:8px 12px;margin:0 0 8px;font-size:17px;line-height:1.35}
.strip .hot{color:#8c2f2f;font-weight:700}
details.fold{padding:0;margin:0 0 6px}
details.fold>summary{list-style:none;display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 12px;min-height:46px;font-weight:600;font-size:17px;line-height:1.3}
details.fold>summary::-webkit-details-marker{display:none}
details.fold>summary .ft{flex:1 0 38%%;min-width:0}
details.fold>summary .ft::before{content:"▸ "}
details.fold[open]>summary .ft::before{content:"▾ "}
details.fold>summary .fs{flex:0 1 auto;font-weight:700;color:var(--ink);text-align:right;font-size:16px}
td.acts{border-top:0;padding-top:0}
.three td:first-child{width:40%%}
details.fold[open]{border-color:var(--accent)}
details.fold .fb{padding:0 12px 12px}
@media (max-width:600px){body{padding:10px}h1{font-size:18px;margin:0 0 8px}}
</style>''')
rep('''APP_VERSION = "S300-PETTY-BOOK-1.1"''', '''APP_VERSION = "S393-PETTY-BOOK-1.2"''')
rep('''NO JAVASCRIPT. Tables on first request''', '''S393 (24-Sep-2026) -- the owner: "maximum sections visible on a single screen without scrolling, as a collapsible
expandable system". Both pages are folds (details/summary, name='pb' = one open at a time, still no JavaScript): a
strip with the figures that matter is always on screen, each section shows its one-line figure, detail on a tap.
And the same entry by the same person within 10 minutes is refused (a 9,000 top-up had been saved three times).

NO JAVASCRIPT. Tables on first request''')

open(dst, "wb").write(s.encode("utf-8"))
print("S393 petty_book.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
