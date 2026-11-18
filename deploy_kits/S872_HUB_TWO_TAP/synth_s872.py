"""synth_s872.py <finance_approvals.html> -- kit S872's marker proof for the box (no node there): the S869/S872 block holds no confirm dialog,
the two-tap is defined once and called by the three buttons, each button passes itself. The behaviour (arm, send, reset) is proven by
synth_s872.js in the chat (node). Last line: 'SYNTH S872: n PASS, m FAIL'."""
import re, sys
h = open(sys.argv[1], encoding="utf-8").read()
P = F = 0
def ok(c, w):
    global P, F
    P, F = (P + 1, F) if c else (P, F + 1)
    print(("PASS " if c else "FAIL ") + w)
i, j = h.find("KIT_S869_HUB_DAYS_CASH"), h.find("end KIT_S869")
blk = h[i:j] if i > 0 and j > i else ""
ok(len(blk) > 1000, "T1 the S869 block is on the page")
ok("window.confirm" not in blk, "T2 no confirm dialog in the block")
ok(blk.count("function s872TwoTap(") == 1 and blk.count("s872TwoTap(") == 4, "T3 the two-tap defined once, used by the three buttons")
ok("s869ReceivedAll('+U.length+',this)" in h and "s869Accept(\\''+r.date+'\\',this)" in h and re.search(r"s869Remove\('\+e\.id\+'[^)]*,this\)", h) is not None,
   "T4 Mark all, Accept and remove pass their own button")
ok("Tap again to mark all" in blk and "Tap again to write off" in blk and "tap again to remove" in blk, "T5 the arming words")
ok(h.count("<script>") == 1 and h.count("</script>") == 1 and h.rstrip().endswith("</html>"), "T6 the page whole: one script, closed html")
print("SYNTH S872: %d PASS, %d FAIL" % (P, F))
sys.exit(0 if F == 0 else 1)
