"""make_s663.py -- kit S663_PORTAL_CONSOLIDATE (the parent, session 358, 26-Oct-2026).. START_HERE_SESSION_358 §0 B: portal.py had
been patched five times since it was last read whole (drift 5, Fault §7.110). S358 read fe9cc368 WHOLE and checked every finding
against its consumers. What is dead or crossed, and safe to settle, is settled here; nobody's tiles change.
  /root/portal/portal.py   fe9cc368 (S660's TO) -> TO   4 counted edits:
    E1 CROSSED (S657): the Expiry watch box sets `hidden` when the expiry page refuses the login (Dr Bhawna), but `.chipbox{display:block}`
       outranks the hidden flag, so the box stayed, showing a dash, and the strip -- squeezed to three columns by the same code -- wrapped.
       One rule: .chipbox[hidden]{display:none}.
    E2 CROSSED (S383): the Clinic Gist page's "Reports pending" card is `hidden` with an inline display:block that defeats it; it showed
       a dash when its numbers could not be read. One rule: #gReports[hidden]{display:none!important}.
    E3 the folded-folder faces say what is inside now: Patients (the parchi desk and procedures, S641/S646) and System (WhatsApp
       Approvals moved in, S660). Display only, his login only (only a folded login sees a face).
    E4 DEAD: the Call Console's Staff tab ran _query_staff (eight database queries) on every load and the page never used the result
       (the tab draws from _staff_week since S171). The call and the function go; nothing else in the estate calls it (the 26-Oct bundle searched: /root/portal and every other module).
  tile_grants.json NOT touched. Every login's tiles, folders and order are unchanged (walked).
Usage: python make_s663.py <root holding portal/portal.py at fe9cc368> <out dir>   (writes <out>/portal/portal.py)"""
import hashlib, os, sys

FROM = {"portal/portal.py": "fe9cc3680b078e1fc6806c28a5f136a2"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s (S660 must be installed, and nothing after it)" % (r, h[:8])
    T[r] = b.decode("utf-8")
P = "portal/portal.py"
N = [0]


def rep(old, new):
    assert T[P].count(old) == 1, "anchor not found exactly once: %r" % old[:80]
    T[P] = T[P].replace(old, new, 1)
    N[0] += 1


# E1 -- the Expiry watch box hides when it is told to
rep(".chipbox:hover{border-color:var(--blue)}\n",
    ".chipbox:hover{border-color:var(--blue)}\n"
    ".chipbox[hidden]{display:none}   /* S663: a box told to hide hides -- S657's Expiry watch on a login the expiry page refuses */\n")
# E2 -- the Clinic Gist page's Reports pending card hides when it is told to
rep(".gnote{font-size:11px;color:var(--muted)}\n</style>",
    ".gnote{font-size:11px;color:var(--muted)}\n"
    "#gReports[hidden]{display:none!important}   /* S663: the inline display:block no longer defeats hidden */\n</style>")
# E3 -- two folded-folder faces say what the folder holds now
rep('"Patients":             ("\\U0001FA7B", "Records \\u00b7 checks \\u00b7 slips \\u00b7 pending reports"),',
    '"Patients":             ("\\U0001FA7B", "Records \\u00b7 parchi desk \\u00b7 procedures \\u00b7 reports"),   # S663')
rep('"System":               ("\\u2699\\uFE0F", "Board \\u00b7 users \\u00b7 clinic PCs"),',
    '"System":               ("\\u2699\\uFE0F", "Board \\u00b7 users \\u00b7 clinic PCs \\u00b7 WhatsApp approvals"),   # S663')
# E4 -- the Staff tab's unused queries, and the function nothing else calls
rep('                    ctx["staff"] = _query_staff(conn, f)\n', '')
t = T[P]
i = t.index("\n\n\ndef _query_staff(conn, f):\n")
j = t.index("\n\n\ndef ", i + 5)
assert t.count("_query_staff") == 1, "_query_staff is called from somewhere else"
T[P] = t[:i] + t[j:]
assert "_query_staff" not in T[P]
assert N[0] == 5   # E1, E2, E3 (two faces), E4's call; E4's function is the sixth hunk, removed above
for r, s in T.items():
    os.makedirs(os.path.dirname(os.path.join(out, r)), exist_ok=True)
    open(os.path.join(out, r), "wb").write(s.encode("utf-8"))
    print(r, hashlib.md5(s.encode("utf-8")).hexdigest())
