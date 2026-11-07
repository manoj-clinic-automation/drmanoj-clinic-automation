# -*- coding: utf-8 -*-
"""edits_s743.py -- S743_STATIONERY_PICK_ALL: the counted edits on /root/assetapp/stationery.py (S741's TO).

S741's live read (07-Nov 07:0x IST): a product box that already holds a name not on the list (the reader's name, e.g. 'A4 Ream')
listed no product to pick -- only 'not on the list'. Now the note comes first, and when the text matches no product the list shows
every product under it (the nearest by shared words first, 15 at a time), so one tap still picks the right one.
"""

EDITS = []


def E(name, old, new):
    EDITS.append((name, (old, new)))


E("1 the kit marker",
  'PICK_S741 = "S741"                     # S741_STATIONERY_PRODUCT_PICK (F-1160): the product and unit boxes a searchable list\n',
  'PICK_S741 = "S741"                     # S741_STATIONERY_PRODUCT_PICK (F-1160): the product and unit boxes a searchable list\n'
  'PICK_S743 = "S743"                     # S743_STATIONERY_PICK_ALL: a name not on the list still lists every product to pick\n')

E("2 the list when the text matches no product", '   var M=opts.filter(function(o){var l=o.toLowerCase();if(l==q){exact=true;}return !q||l.indexOf(q)>=0;});\n   M.sort(function(a,b){return (a.toLowerCase().indexOf(q)==0?0:1)-(b.toLowerCase().indexOf(q)==0?0:1)||a.localeCompare(b);});\n   M.slice(0,15).forEach(function(o){h+="<button type=button class=o741 data-v=\'"+esc(o)+"\'>"+esc(o)+"</button>";n++;});\n   if(prod&&q&&!exact){h+="<div class=\'o741 nw\'>"+(STAFF?"Naya saamaan \\u201c"+esc(v)+"\\u201d \\u2014 Save par list mein judega":"\\u201c"+esc(v)+"\\u201d is not on the list \\u2014 it is added on Save")+"</div>";n++;}', '   var M=opts.filter(function(o){var l=o.toLowerCase();if(l==q){exact=true;}return !q||l.indexOf(q)>=0;});\n   M.sort(function(a,b){return (a.toLowerCase().indexOf(q)==0?0:1)-(b.toLowerCase().indexOf(q)==0?0:1)||a.localeCompare(b);});\n   var near=!M.length&&!!q;if(near){var W=q.split(/[^a-z0-9]+/).filter(function(x){return x.length>1;}),sc=function(o){var l=o.toLowerCase(),k=0;W.forEach(function(w){if(l.indexOf(w)>=0){k++;}});return k;};M=opts.slice().sort(function(a,b){return sc(b)-sc(a)||a.localeCompare(b);});}\n   if(prod&&q&&!exact){h+="<div class=\'o741 nw\'>"+(STAFF?"Naya saamaan \\u201c"+esc(v)+"\\u201d \\u2014 Save par list mein judega":"\\u201c"+esc(v)+"\\u201d is not on the list \\u2014 it is added on Save")+(near?(STAFF?" \\u2014 ya neeche se chunein":" \\u2014 or pick one below"):"")+"</div>";n++;}\n   M.slice(0,15).forEach(function(o){h+="<button type=button class=o741 data-v=\'"+esc(o)+"\'>"+esc(o)+"</button>";n++;});')
