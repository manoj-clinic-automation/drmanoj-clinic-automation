#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_papers_index.py v1.0 (S269) -- one page that answers the only question
the owner has about 373 working papers: is there anything here I still need?

    python build_papers_index.py --root D:\\Downloads\\ClaudeCowork -o PAPERS.html

It walks 03_WORKING_PAPERS, classifies every file, and writes ONE html page.
Nothing is moved, renamed or deleted -- it only reads and describes.

THE FOUR SHELVES
    NEEDS YOU   a document naming an action only the owner can take, still open.
    CURRENT     the live reference set: this session, and the canon pointers.
    RECENT      the last three closed sessions -- still worth a look.
    ARCHIVE     everything older. Grouped by session, never browsed, searchable.

STALENESS, COMPUTED NOT GUESSED
    age        days since the file was last written.
    orphan     the file's name appears in NONE of 00_INDEX.md,
               CANONICAL_MANIFEST.md or the current KB Register. Written once,
               never referred to again -- the honest signal that a paper was
               not worth writing.
    superseded a per-kit evidence note, or a dated snapshot of a document that
               has a newer live version (OWNER_TODO_LIVE_*, START_HERE_*).

F-491 (S259).  v1.0 built its citation corpus from 00_INDEX.md PLUS
MANIFEST.md5.  Since S268 the manifest is rebuilt nightly over the whole tree,
so every paper's name was in the corpus by construction and "never cited" could
only ever read 0 -- a fault that reported itself as success.  MANIFEST.md5 is
gone from the corpus, and a share gate now REFUSES any source that names
INVENTORY_SHARE or more of the papers, naming it on the page.  A file whose name
says NEVER_CITED is refused outright: a list of the uncited is not a reading of
them.  The corpus, and anything refused, are printed on the page so the figure
can never again be meaningless in silence.
"""
import argparse, io, json, os, re, time, html

VERSION = "1.1"

KINDS = [
    (re.compile(r'_BUILD_BRIEF\.md$'),              "brief",    "the session's one handover"),
    (re.compile(r'_CLOSE_REPORT\.md$'),             "close",    "what the session did, and what it did not"),
    (re.compile(r'_CLOSE_FACTS\.md$'),              "close",    "the close's checked facts"),
    (re.compile(r'^OWNER_TODO_LIVE'),               "snapshot", "a dated copy of the owner's to-do list"),
    (re.compile(r'^START_HERE_SESSION'),            "snapshot", "a dated session entry point"),
    (re.compile(r'^HANDOFF_RUNBOOK'),               "snapshot", "a dated runbook"),
    (re.compile(r'live_pins.*READBACK|_LIVE_PIN|_Live_Pin', re.I), "pins", "pins read back from a machine"),
    (re.compile(r'^_.*(APPEND|append|FOLD|fold)'),  "machinery","text spliced into a canon document"),
    (re.compile(r'^_index_row|^_register_append|^_archive_append|^_fault_append'), "machinery", "text spliced into a canon document"),
    (re.compile(r'(_BUILT|_LIVE|_INSTALLED|_DONE)\.md$'), "evidence", "a note that one kit went live"),
    (re.compile(r'(FINDING|FINDINGS|_F\d+_)', re.I), "finding",  "something that was wrong, and why"),
    (re.compile(r'(DESIGN|SPEC|PLAN|CONTRACT|DRAFT|ROADMAP|ATLAS)', re.I), "design", "a design or plan"),
    (re.compile(r'\.(xlsx|pdf|docx|html|zip|png)$', re.I), "artefact", "something to open, print or send"),
    (re.compile(r'\.(py|bat|ps1|ahk|sql|txt|md5)$', re.I), "tooling", "a script or its output"),
]
KEEP = ("brief", "close")          # the two kinds worth reading later
SUPERSEDED_KINDS = ("snapshot", "machinery", "pins", "evidence")


def classify(name):
    for rx, kind, blurb in KINDS:
        if rx.search(name):
            return kind, blurb
    return "paper", "a working paper"


def session_of(relpath):
    m = re.match(r'03_WORKING_PAPERS/(S\d+)', relpath.replace("\\", "/"))
    if m:
        return int(m.group(1)[1:])
    m = re.match(r'03_WORKING_PAPERS/S(\d+)_S\d+_moved', relpath.replace("\\", "/"))
    if m:
        return int(m.group(1))
    return None


def _read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


# F-491: a source that names EVERY paper is an inventory, not a citation, and it
# drives "never cited" silently to zero.  Refuse it and say so.
INVENTORY_SHARE = 0.90
NOT_A_CITATION = re.compile(r'NEVER_CITED', re.I)


def gather_corpus(root, extra_paths, names):
    """The places a paper could be REFERRED TO: 00_INDEX.md, plus whatever
    --also-scan / --canon supplied (the canonical manifest, the newest KB
    Register).  Missing files are reported, never silently treated as empty
    (F-443).  MANIFEST.md5 is deliberately not here -- see F-491 above."""
    used, rejected, missing, parts = [], [], [], []
    stems = [(n, os.path.splitext(n)[0]) for n in names]
    total = float(len(stems) or 1)
    for p in [os.path.join(root, "00_INDEX.md")] + list(extra_paths):
        base = os.path.basename(p)
        if not os.path.exists(p):
            missing.append(p)
            continue
        if NOT_A_CITATION.search(base):
            rejected.append("%s -- a list of the uncited is not a reading of them" % base)
            continue
        txt = _read(p)
        hit = sum(1 for n, st in stems if n in txt or st in txt)
        share = hit / total
        if share >= INVENTORY_SHARE:
            rejected.append("%s -- names %.0f%% of the papers: an inventory, not a citation"
                            % (base, 100.0 * share))
            continue
        used.append("%s (%.0f%%)" % (base, 100.0 * share))
        parts.append(txt)
    return "\n".join(parts), used, rejected, missing


def walk(root, extra_haystack_paths):
    """The papers first, then the corpus -- the share gate needs the names."""
    base = os.path.join(root, "03_WORKING_PAPERS")
    rows = []
    now = time.time()
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            try:
                st = os.stat(full)
            except Exception:
                continue
            kind, blurb = classify(name)
            rows.append({
                "path": rel,
                "name": name,
                "dir": os.path.relpath(dirpath, base).replace(os.sep, "/"),
                "session": session_of(rel),
                "kind": kind,
                "blurb": blurb,
                "bytes": st.st_size,
                "age_days": int((now - st.st_mtime) // 86400),
                "mtime": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
            })
    hay, used, rejected, missing = gather_corpus(
        root, extra_haystack_paths, [r["name"] for r in rows])
    for r in rows:
        stem = os.path.splitext(r["name"])[0]
        r["orphan"] = (r["name"] not in hay and stem not in hay)
    return rows, missing, used, rejected


def shelve(rows, current_session):
    for r in rows:
        s = r["session"]
        r["superseded"] = r["kind"] in SUPERSEDED_KINDS and (s is None or s < current_session)
        if s == current_session:
            r["shelf"] = "CURRENT"
        elif s is not None and s >= current_session - 3:
            r["shelf"] = "RECENT"
        else:
            r["shelf"] = "ARCHIVE"
    return rows


CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root{
 --paper:#f4f5f7; --card:#ffffff; --ink:#191b20; --dim:#61656e; --faint:#8b8f98;
 --line:#dfe2e7; --rule:#c9cdd5; --accent:#3f5d8f; --warn:#9a4a2f; --ok:#3a6b4a;
 --chip:#eceef2; --bar:#c6ccd6; --barwarn:#c99a86;
 --disp:"IBM Plex Sans Condensed",ui-sans-serif,-apple-system,"Segoe UI",sans-serif;
 --body:"IBM Plex Sans",ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
 --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --paper:#121417; --card:#191c21; --ink:#e6e8ec; --dim:#8d929c; --faint:#6e737c;
 --line:#272b32; --rule:#343941; --accent:#8fa9d8; --warn:#d68d6f; --ok:#8cc39f;
 --chip:#222630; --bar:#3a3f49; --barwarn:#7d5241;
}}
:root[data-theme="dark"]{
 --paper:#121417; --card:#191c21; --ink:#e6e8ec; --dim:#8d929c; --faint:#6e737c;
 --line:#272b32; --rule:#343941; --accent:#8fa9d8; --warn:#d68d6f; --ok:#8cc39f;
 --chip:#222630; --bar:#3a3f49; --barwarn:#7d5241;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);margin:0;
 padding-block:34px;padding-left:20px;padding-right:20px;
 font:400 15px/1.6 var(--body);-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;display:flex;flex-direction:column;gap:34px}
.eyebrow{font:500 11px/1 var(--mono);letter-spacing:.11em;text-transform:uppercase;
 color:var(--accent)}
h1{font:700 30px/1.15 var(--disp);margin:9px 0 0;letter-spacing:-.015em;text-wrap:balance}
.answer{font:400 17px/1.5 var(--body);color:var(--ink);margin:12px 0 0;max-width:62ch}
.answer b{font-weight:600}
.meta-line{font:400 12.5px/1.5 var(--mono);color:var(--faint);margin:14px 0 0}

.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
 border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.fig{padding:15px 18px 16px;border-left:1px solid var(--line)}
.fig:first-child{border-left:none;padding-left:0}
.fig b{display:block;font:500 27px/1.1 var(--mono);letter-spacing:-.02em;
 font-variant-numeric:tabular-nums}
.fig span{display:block;margin-top:5px;font:400 12px/1.35 var(--body);color:var(--dim)}
.fig.is-warn b{color:var(--warn)}

section{display:flex;flex-direction:column;gap:11px}
h2{font:600 13px/1 var(--mono);letter-spacing:.09em;text-transform:uppercase;
 color:var(--dim);margin:0;padding-bottom:9px;border-bottom:1px solid var(--rule);
 display:flex;justify-content:space-between;gap:12px;align-items:baseline}
h2 em{font-style:normal;color:var(--faint);letter-spacing:.04em}
.lead{margin:0;color:var(--dim);font-size:13.5px;max-width:64ch}

ol.todo{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}
ol.todo li{background:var(--card);border-left:2px solid var(--accent);
 padding:12px 16px;display:flex;gap:13px;align-items:baseline}
ol.todo .n{font:500 12px/1.5 var(--mono);color:var(--accent);min-width:1.4em}
ol.todo .t{font:500 14.5px/1.45 var(--body)}

.files{display:flex;flex-direction:column;background:var(--card);
 border:1px solid var(--line)}
.f{display:grid;grid-template-columns:1fr auto;gap:4px 16px;padding:11px 16px;
 border-top:1px solid var(--line);align-items:baseline}
.f:first-child{border-top:none}
.f .nm{font:500 13.5px/1.4 var(--body);word-break:break-word}
.f .bl{grid-column:1;color:var(--dim);font-size:12.5px}
.f .tags{grid-column:2;grid-row:1/3;display:flex;flex-direction:column;
 align-items:flex-end;gap:4px;text-align:right}
.tag{font:500 10.5px/1.5 var(--mono);letter-spacing:.05em;text-transform:uppercase;
 color:var(--faint);white-space:nowrap}
.tag.keep{color:var(--ok)}
.tag.orphan{color:var(--warn)}
.tag.date{font-weight:400;font-variant-numeric:tabular-nums}
.empty{padding:14px 16px;color:var(--dim);font-size:13.5px}

.ledger{width:100%;border-collapse:collapse;font-size:13px}
.ledger th{font:500 10.5px/1 var(--mono);letter-spacing:.07em;text-transform:uppercase;
 color:var(--faint);text-align:left;padding:0 10px 8px 0;font-weight:500}
.ledger th.r,.ledger td.r{text-align:right;font-variant-numeric:tabular-nums}
.ledger td{padding:7px 10px 7px 0;border-top:1px solid var(--line);vertical-align:middle}
.ledger td.s{font:500 12.5px/1 var(--mono);color:var(--ink);white-space:nowrap}
.ledger td.d{font:400 12px/1 var(--mono);color:var(--faint);white-space:nowrap}
.bar{display:block;height:7px;background:var(--bar);position:relative;min-width:26px}
.bar i{position:absolute;inset:0 auto 0 0;background:var(--barwarn);display:block}
.scroller{overflow-x:auto}

details>summary{cursor:pointer;font:500 13px/1 var(--mono);letter-spacing:.06em;
 text-transform:uppercase;color:var(--accent);padding:11px 0;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"+ ";font-weight:600}
details[open]>summary::before{content:"2 "}
details>summary:focus-visible{outline:2px solid var(--accent);outline-offset:3px}

.legend{border-top:1px solid var(--rule);padding-top:16px;color:var(--dim);
 font-size:12.5px;line-height:1.65;max-width:70ch}
.legend b{color:var(--ink);font-weight:600}
.legend .k{font:500 11px/1 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.legend .k.keep{color:var(--ok)}
.legend .k.orphan{color:var(--warn)}
.sig{font:400 11.5px/1.5 var(--mono);color:var(--faint);margin-top:14px}
@media (max-width:520px){
 h1{font-size:25px}
 .fig{border-left:none;padding-left:0;border-top:1px solid var(--line)}
 .fig:first-child{border-top:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def row_html(r):
    tags = ['<span class="tag date">%s</span>' % r["mtime"]]
    if r["kind"] in KEEP:
        tags.append('<span class="tag keep">keep</span>')
    if r["orphan"]:
        tags.append('<span class="tag orphan">never cited</span>')
    elif r.get("superseded"):
        tags.append('<span class="tag">superseded</span>')
    return ('<div class="f"><span class="nm">%s</span>'
            '<span class="bl">%s</span>'
            '<span class="tags">%s</span></div>') % (
        html.escape(r["name"]), html.escape(r["blurb"]), "".join(tags))


def files_block(rows, empty="Nothing here."):
    if not rows:
        return '<div class="files"><div class="empty">%s</div></div>' % html.escape(empty)
    return '<div class="files">%s</div>' % "".join(row_html(r) for r in rows)


SKIP_TODO = re.compile(r'^(carried|what nothing touches|your rulings)', re.I)


def build(rows, current_session, owner_items, missing, corpus=None, rejected=None):
    rows = sorted(rows, key=lambda r: (-(r["session"] or 0), r["name"]))
    cur = [r for r in rows if r["shelf"] == "CURRENT"]
    rec = [r for r in rows if r["shelf"] == "RECENT"]
    arc = [r for r in rows if r["shelf"] == "ARCHIVE"]
    orph = [r for r in rows if r["orphan"]]
    keep = [r for r in rows if r["kind"] in KEEP]
    todo = [t for t in owner_items if not SKIP_TODO.match(t)]

    o = []
    o.append("<title>Clinic Paper Shelf</title>")
    o.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             'family=IBM+Plex+Mono:wght@400;500&'
             'family=IBM+Plex+Sans+Condensed:wght@500;600;700&'
             'family=IBM+Plex+Sans:wght@400;500;600&display=swap">')
    o.append("<style>%s</style>" % CSS)
    o.append('<div class="wrap">')

    # header
    o.append("<header>")
    o.append('<div class="eyebrow">Dr Manoj Agarwal Clinic &middot; working papers</div>')
    o.append("<h1>The paper shelf</h1>")
    o.append('<p class="answer">%d documents have been written to your PC across %d sessions. '
             '<b>%d of them want something from you.</b> The rest are the project&rsquo;s memory, '
             'kept so nothing is lost &mdash; not a list for you to work through.</p>'
             % (len(rows), len(set(r["session"] for r in rows if r["session"])), len(todo)))
    o.append('<p class="meta-line">Rebuilt %s &middot; session S%d</p>'
             % (time.strftime("%d %b %Y, %H:%M"), current_session))
    o.append("</header>")

    # figures
    o.append('<div class="figs">')
    figs = [(len(rows), "papers on the shelf", False),
            (len(keep), "briefs and close reports — the two kinds written to be read later", False),
            (len(orph), "never cited anywhere since the day they were written", True),
            (len(todo), "open items that need you", False)]
    for val, label, warn in figs:
        o.append('<div class="fig%s"><b>%d</b><span>%s</span></div>'
                 % (" is-warn" if warn else "", val, label))
    o.append("</div>")

    # needs you
    o.append("<section>")
    o.append('<h2>Needs you <em>%d</em></h2>' % len(todo))
    o.append('<p class="lead">Not documents &mdash; the open items from your own to-do list, '
             'in your order. Nothing else on this page is waiting on you.</p>')
    if todo:
        o.append('<ol class="todo">')
        for i, t in enumerate(todo, 1):
            o.append('<li><span class="n">%d</span><span class="t">%s</span></li>'
                     % (i, html.escape(t)))
        o.append("</ol>")
    else:
        o.append('<div class="files"><div class="empty">Nothing open.</div></div>')
    o.append("</section>")

    # current
    o.append("<section>")
    o.append('<h2>This session <em>S%d &middot; %d</em></h2>' % (current_session, len(cur)))
    o.append('<p class="lead">Written today. The build brief is the one to read; '
             'everything beside it is the evidence behind it.</p>')
    o.append(files_block(cur, "Nothing written yet this session."))
    o.append("</section>")

    # recent
    o.append("<section>")
    o.append('<h2>The last three sessions <em>%d</em></h2>' % len(rec))
    o.append('<p class="lead">Closed, but recent enough that you might still want them.</p>')
    o.append(files_block(rec))
    o.append("</section>")

    # archive ledger
    bysess = {}
    for r in arc:
        bysess.setdefault(r["session"], []).append(r)
    o.append("<section>")
    o.append('<h2>Archive <em>%d files &middot; %d sessions</em></h2>' % (len(arc), len(bysess)))
    o.append('<p class="lead">Folded into the record and closed. The bar shows how much of each '
             'session&rsquo;s paperwork has never been cited since &mdash; the shaded part.</p>')
    o.append("<details><summary>Session ledger</summary>")
    o.append('<div class="scroller"><table class="ledger">')
    o.append("<thead><tr><th>Session</th><th>Closed</th><th class='r'>Files</th>"
             "<th class='r'>Never cited</th><th>&nbsp;</th></tr></thead><tbody>")
    for sn in sorted(bysess, key=lambda x: -(x or 0)):
        g = bysess[sn]
        no = sum(1 for r in g if r["orphan"])
        pct = (100.0 * no / len(g)) if g else 0
        o.append('<tr><td class="s">%s</td><td class="d">%s</td>'
                 '<td class="r">%d</td><td class="r">%d</td>'
                 '<td><span class="bar" style="width:%dpx"><i style="width:%.0f%%"></i></span></td></tr>'
                 % (("S%d" % sn) if sn else "unfiled", g[0]["mtime"], len(g), no,
                    min(180, 26 + len(g) * 6), pct))
    o.append("</tbody></table></div></details>")
    o.append("</section>")

    # legend
    o.append('<div class="legend">')
    o.append("<b>How a document is judged.</b> "
             '<span class="k keep">keep</span> &mdash; a build brief or a close report: the two kinds '
             "written to be read again. "
             '<span class="k orphan">never cited</span> &mdash; the file&rsquo;s name appears in no index, '
             "no canonical manifest and no register. Written once, never referred to again. "
             '<span class="k">superseded</span> &mdash; a dated snapshot, or a note that one kit went live, '
             "whose living version has moved on.")
    if corpus:
        o.append("<br><br><b>Looked for a mention in:</b> %s"
                 % html.escape(", ".join(corpus)))
    if rejected:
        o.append("<br><b>Refused as a corpus (F-491):</b> %s"
                 % html.escape("; ".join(rejected)))
    if missing:
        o.append("<br><br><b>Could not be read, so not counted:</b> %s"
                 % html.escape(", ".join(missing)))
    o.append("</div>")
    o.append('<div class="sig">build_papers_index.py v%s &middot; reads only, moves nothing</div>'
             % VERSION)
    o.append("</div>")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="the ClaudeCowork folder")
    ap.add_argument("--inventory", help="a prebuilt json inventory instead of a walk")
    ap.add_argument("--also-scan", nargs="*", default=[],
                    help="extra files a paper may be referred to in (manifest, register)")
    ap.add_argument("--canon", default=None,
                    help="the KB_canon_all folder; the manifest, the newest KB Register and "
                         "OWNER_TODO_LIVE.md are taken from it automatically")
    ap.add_argument("--session", default="auto",
                    help="session number, or 'auto' to take the highest S### folder present")
    ap.add_argument("--owner-items", default=None, help="OWNER_TODO_LIVE.md to read open items from")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--fragment", action="store_true",
                    help="omit the html/head/body wrapper (for publishing as an artifact)")
    a = ap.parse_args()

    missing, corpus, rejected = [], [], []
    if a.canon:
        cand = os.path.join(a.canon, "CANONICAL_MANIFEST.md")
        if os.path.exists(cand):
            a.also_scan.append(cand)
        else:
            missing.append(cand)
        regs = sorted(f for f in os.listdir(a.canon)
                      if re.match(r'KB_Register_v5_\d+.*\.md$', f)) if os.path.isdir(a.canon) else []
        if regs:
            a.also_scan.append(os.path.join(a.canon, regs[-1]))
        else:
            missing.append(os.path.join(a.canon, "KB_Register_v5_*.md"))
        if not a.owner_items:
            a.owner_items = os.path.join(a.canon, "OWNER_TODO_LIVE.md")

    if a.inventory:
        rows = json.load(io.open(a.inventory, encoding="utf-8"))
    else:
        rows, missing, corpus, rejected = walk(a.root, a.also_scan)

    if str(a.session).lower() == "auto":
        nums = [r["session"] for r in rows if r["session"]]
        session = max(nums) if nums else 0
    else:
        session = int(a.session)

    rows = shelve(rows, session)

    owner_items = []
    if a.owner_items and os.path.exists(a.owner_items):
        txt = io.open(a.owner_items, encoding="utf-8", errors="replace").read()
        sec = txt.split("## \u2b500")[-1].split("## \u2b501")[0] if "\u2b500" in txt else ""
        for m in re.finditer(r'^\*\*(\d+)\s*[·.]\s*(.+?)\*\*', sec, re.M):
            owner_items.append(m.group(2).strip().rstrip(".").replace("**", ""))
    elif a.owner_items:
        missing.append(a.owner_items)

    page = build(rows, session, owner_items, missing, corpus, rejected)
    if not a.fragment:
        page = ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                + page.split("</style>")[0] + "</style></head><body>"
                + page.split("</style>", 1)[1] + "</body></html>")
    io.open(a.out, "w", encoding="utf-8").write(page)
    print("wrote %s  (%d papers, %d never referred to)" % (
        a.out, len(rows), sum(1 for r in rows if r["orphan"])))
    if corpus:
        print("corpus   : %s" % ", ".join(corpus))
    for x in rejected:
        print("REFUSED  : %s" % x)


if __name__ == "__main__":
    main()
