# S225_NEW_ITEMS — new medicines, recorded and highlighted (rev 10)

**The owner (spec §6):** *"new medicines added should be recorded and highlighted to me."*

An item the server has never seen — first bought this month (a Marg purchase line), or first appearing in the newest stock
snapshot without having been in any earlier one — is **logged once**: the item, when it was first seen, whether it was first
*bought* or first *on the shelf*, the stockist, the packing. The hub's last card reads **N new medicines this month** with the
list. The earliest stock snapshot on the server is the baseline: nothing in it is ever "new". A logged row is never rewritten.
The salt of a new item is not yet on the server — that is §8 item 6 (Amir's salt list); the card says so.

**Proof:** `selftest_new_items.py` **316/316** — baseline items are not logged; a new shelf item and a first-bought item are; a second
run logs nothing; the log records where each was seen and the stockist; the hub shows the card with both names. Install per F-321.
