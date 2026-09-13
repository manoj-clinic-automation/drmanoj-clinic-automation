#!/usr/bin/env python3
"""S245_AMIR_BILLTAP -- step 5: one tap per bill, the reasons hidden until they are needed.

Every replacement is an exact, unique, asserted string swap against the S244 live file.
If the source is not that file, or any anchor has moved, this refuses and writes nothing.
"""
import hashlib
import io
import os
import sys

SRC_MD5 = "aad400fa9c4b7804229c9f175c86533b"          # live /root/finance/amir_day.py, S244

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


# ---------------------------------------------------------------- 1. docstring
edit(
    "docstring",
    '''  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.
"""''',
    '''  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.

S245_AMIR_BILLTAP (owner ruling 13-Sep-2026):
  * Step 5 was five radio buttons on every bill, all open at once -- forty choices on
    one phone screen for a normal day.  It is now ONE tap per bill: "Theek hai", or
    "Theek nahi", and the four reasons appear only when he says it is not right.
  * The reasons live in a <details>, so this is still a page with no JavaScript, and
    the answer is still one radio group per bill -- the form the server reads is
    unchanged, byte for byte.
  * `required` is gone from the radios ON PURPOSE: a required control inside a closed
    <details> cannot be focused, and the browser then refuses the whole submit without
    saying why.  The forcing was never the browser's job -- an unanswered bill is
    simply not written and comes straight back on the list, which is stronger.
"""''',
)

# ---------------------------------------------------------------- 2. CSS
edit(
    "css",
    '''.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}''',
    '''.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}
/* S245: one tap per bill; the reasons stay shut until he says it is not right */
.bill .tap{display:block;padding:15px 13px;border:1px solid #bfe0c6;border-radius:10px;
           background:#f2f9f4;color:var(--ok);font-size:17px;font-weight:600;margin:0 0 8px}
.bill .tap input{margin-right:11px;transform:scale(1.35);vertical-align:-2px}
.bill details.notok{border:1px solid var(--line);border-radius:10px;background:#fff}
.bill details.notok summary{padding:15px 13px;font-size:17px;font-weight:600;
            color:var(--bad);cursor:pointer;list-style:none}
.bill details.notok summary::-webkit-details-marker{display:none}
.bill details.notok summary::after{content:" \\25BE";color:var(--soft);float:right}
.bill details.notok[open] summary{border-bottom:1px solid var(--line)}
.bill details.notok[open] summary::after{content:" \\25B4"}
.why{padding:4px 13px 13px}
.why label{display:block;padding:13px 11px;border:1px solid var(--line);border-radius:8px;
           margin:9px 0 0;font-size:16px}
.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
.bill:has(input:checked){border-color:var(--ok);box-shadow:0 0 0 1px var(--ok) inset}
.bill:has(details input:checked){border-color:var(--bad);box-shadow:0 0 0 1px var(--bad) inset}
.savebar{position:sticky;bottom:0;background:var(--bg);padding:10px 0 4px;
         border-top:1px solid var(--line);margin:14px 0 0}
.savebar .btn{margin:0}''',
)

# ---------------------------------------------------------------- 3. _bill_block
edit(
    "bill_block",
    '''def _bill_block(i, b):
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    opts = "".join(
        "<label><input type=radio name='r_%s' value='%s' required>%s</label>"
        % (_esc(str(i)), _esc(code), _esc(label))
        for code, label in REASONS
    )
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>"
            "<input type=hidden name='k_%d' value='%s'>"
            "<div class=opts>%s</div></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               i, _esc(key), opts))''',
    '''def _bill_block(i, b):
    """One bill, one tap.  (S245)

    What he sees is two lines: *Theek hai* and *Theek nahi*.  The four reasons sit
    inside the second one and open only when he taps it -- a <details>, so the page
    still carries no JavaScript.  All five are the same radio group, so picking a
    reason un-picks *theek hai* by itself and the form the server reads is exactly
    the one it read before.
    """
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    ok_label = REASON_MAP.get("ok", "Theek hai")
    why = "".join(
        "<label><input type=radio name='r_%d' value='%s'>%s</label>"
        % (i, _esc(code), _esc(label))
        for code, label in REASONS if code != "ok"
    )
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>"
            "<input type=hidden name='k_%d' value='%s'>"
            "<label class=tap><input type=radio name='r_%d' value='ok'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               i, _esc(key), i, _esc(ok_label), why))''',
)

# ---------------------------------------------------------------- 4. _step5
edit(
    "step5",
    '''    body = [_export_band(w)]
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill." % len(carry))
        body.append("</div>")
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<button class=btn name=go value=5>Save kijiye</button></form>")
    return _page(5, w, "Aaj ke bill", "".join(body),
                 "Har bill par ek jawab zaroori hai.")''',
    '''    body = [_export_band(w)]
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill." % len(carry))
        body.append("</div>")
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>"
                "</div></form>")
    n = len(carry) + len(bills)
    return _page(5, w, "Aaj ke bill", "".join(body),
                 "%d bill. Har bill par ek tap. Kuch gadbad ho to hi "
                 "\\"Theek nahi\\" kholiye." % n)''',
)


# ---------------------------------------------------------------- apply


def _read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def build(src):
    """The S244 live file in, the S245 file out.  Refuses rather than guesses."""
    if "\r\n" in src:
        raise SystemExit("REFUSED: source has CRLF (F-294)")
    if hashlib.md5(src.encode("utf-8")).hexdigest() != SRC_MD5:
        raise SystemExit("REFUSED: source is not the S244 live amir_day.py (%s expected)" % SRC_MD5)
    text = src
    for name, old, new in EDITS:
        c = text.count(old)
        if c != 1:
            raise SystemExit("REFUSED: anchor %r matched %d times (need exactly 1)" % (name, c))
        text = text.replace(old, new, 1)
    if "\r\n" in text:
        raise SystemExit("REFUSED: result has CRLF")
    return text


def main(argv):
    if len(argv) == 4 and argv[1] == "--selftest":
        out = build(_read(argv[2]))
        kit = _read(argv[3])
        if out != kit:
            raise SystemExit("REFUSED: patch(live) is NOT the kit file, byte for byte")
        print("OK  patch(%s) == %s  (%d edits, md5 %s)"
              % (argv[2], argv[3], len(EDITS), hashlib.md5(kit.encode("utf-8")).hexdigest()))
        return 0
    if len(argv) == 4 and argv[1] == "--build":
        text = build(_read(argv[2]))
        d = os.path.dirname(os.path.abspath(argv[3]))
        if d:
            os.makedirs(d, exist_ok=True)
        with io.open(argv[3], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("OK  %d edits applied -> %s  (md5 %s)"
              % (len(EDITS), argv[3], hashlib.md5(text.encode("utf-8")).hexdigest()))
        return 0
    raise SystemExit("usage: %s --selftest <live amir_day.py> <kit amir_day.py>\n"
                     "       %s --build    <live amir_day.py> <out amir_day.py>"
                     % (argv[0], argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
