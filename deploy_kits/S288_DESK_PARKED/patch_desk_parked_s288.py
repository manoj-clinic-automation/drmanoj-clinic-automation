#!/usr/bin/env python3
"""S288_DESK_PARKED -- the decision desk gets the word it was missing.

The owner, 17-Sep-2026, at the desk on count #1: "I find no way of saying that it
is with me and it is not lost." The server has always accepted PARKED ("kept
elsewhere") for any line (LANE_ACTIONS in stock_app.py), but the desk offered
that button only on the "adjustment stock" cards. Three anchored edits, all in
the page's own script; nothing on the server changes and the service is not
restarted (the page is read from disk on every request):

  1. every "Real shelf loss" card gets a fourth button:
         Kept elsewhere -- with me, not lost   (PARKED)
  2. every per-item row inside a lane list gets the same word;
  3. the find box: an item that already carries a word shows it and offers
         Change this word  -- which reopens the line (OPEN) and jumps to its card,
     so a tap given in the wrong place is corrected in two taps, not never.

Usage (the installer does this):
    python3 -B patch_desk_parked_s288.py --file /root/finance/stock_desk.html --from <md5>
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

EDITS = [
    # 1 -- the fourth button on a real-loss item card
    ('btns:[["RECOVER","Pursue","to be recovered from the person responsible","red"],'
     '["WRITE_OFF","Write off","accept the loss","grey"],'
     '["RECOUNT","Darpan counts again","before deciding","grey"]]}));',
     'btns:[["RECOVER","Pursue","to be recovered from the person responsible","red"],'
     '["WRITE_OFF","Write off","accept the loss","grey"],'
     '["RECOUNT","Darpan counts again","before deciding","grey"],'
     '["PARKED","Kept elsewhere — with me, not lost","parked: out of every list until a spot count finds it","amber"]]}));'),
    # 2 -- the same word on every per-item row of a lane list
    ('+\'<button data-act="RECOUNT" data-item="\'+esc(x.item)+\'">Darpan recounts</button></div></div>\';',
     '+\'<button data-act="RECOUNT" data-item="\'+esc(x.item)+\'">Darpan recounts</button>\''
     '+\'<button data-act="PARKED" data-item="\'+esc(x.item)+\'">Kept elsewhere</button></div></div>\';'),
    # 3 -- the find box: show the word already given and let it be changed
    ('if(k<0){ h.insertAdjacentHTML("beforeend",\'<div class="sub">already decided or not on a card — see the full report</div>\'); return; }',
     'if(k<0){ const hx=(D.differences||[]).find(x=>x.item===item); '
     'if(hx&&hx.word){ if(!h.querySelector("[data-reopen]")) h.insertAdjacentHTML("beforeend",\'<div class="sub">your word: \'+esc(LABEL[hx.word.action]||hx.word.action)+\'</div>'
     '<button class="b grey" data-reopen="\'+esc(item)+\'">Change this word</button>\'); return; } '
     'h.insertAdjacentHTML("beforeend",\'<div class="sub">not on a card — see the full report</div>\'); return; }'),
]

# the handler for "Change this word": reopen, reload, then jump to the item's card
HANDLER_ANCHOR = 'document.getElementById("q").addEventListener("input",e=>find(e.target.value));'
HANDLER = ('document.addEventListener("click", async e=>{ const r=e.target.closest("button[data-reopen]"); if(!r) return; '
           'const item=r.dataset.reopen; r.disabled=true; r.textContent="Reopening…"; '
           'if(!(await decide([item],"OPEN",item+" — reopened"))){ r.disabled=false; r.textContent="Change this word"; return; } '
           'LAST=null; const j=await fetch(BASE+"/api/pad/report/"+B.count_id).then(x=>x.json()).catch(()=>null); '
           'if(j&&j.ok){ D=j; build(); } '
           'let k=CARDS.findIndex(c=>c.t==="item"&&c.x.item===item); if(k<0) k=CARDS.findIndex(c=>c.t==="lane"&&c.xs.some(x=>x.item===item)); '
           'document.getElementById("q").value=""; document.getElementById("qr").hidden=true; '
           'if(k>=0){ SKIPPED.delete(cardId(CARDS[k])); I=k; render(); const l=document.getElementById("list"); if(l&&CARDS[k].t==="lane"){ l.hidden=false; } } else { render(); } });\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text):
    for old, new in EDITS:
        if text.count(old) != 1:
            raise SystemExit("REFUSING: anchor not found exactly once: %r" % old[:70])
        text = text.replace(old, new)
    if text.count(HANDLER_ANCHOR) != 1:
        raise SystemExit("REFUSING: handler anchor not found exactly once")
    text = text.replace(HANDLER_ANCHOR, HANDLER_ANCHOR + "\n" + HANDLER)
    return text


def already(text):
    return 'data-reopen' in text and '"PARKED","Kept elsewhere' in text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if already(text):
        print("ALREADY PATCHED: %s is %s" % (a.file, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    new = apply(text).encode("utf-8")
    if a.dry_run:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S288_%s" % (a.file, cur[:8])
    shutil.copy2(a.file, bak)
    with io.open(a.file, "wb") as fh:
        fh.write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s : %s -> %s  (backup %s)" % (a.file, cur, back, bak))
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
