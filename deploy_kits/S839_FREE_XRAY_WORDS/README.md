# S839_FREE_XRAY_WORDS — "Free X-ray" on every screen

The parent, session S465, 14-Nov-2026, on his word at 20:41 IST: **"MUFT = FREE"**.

S836 (live 20:39) said "Muft X-ray" on the staff screens and "Complimentary (Muft X-ray)" on his. Now every screen says
**Free X-ray**: Shavez's and reception's Check karein (the button, the card's line "Docterz mein entry nahi — free X-ray?"),
his X-ray page (the tile, the heading, the button), the Aaj ka kaam line ("Free X-ray? N"). A tap already made reads
"explained: free X-ray" from now on (the stored word is the same key). Nothing else changes.

- `/root/finance/check_screens.py` f3c16787 (S836) → ac0e890a, built by `apply_s839.py` (15 anchors, each exactly once).

**Proof.** `walk_s839.py` (S836's walk with the new words) 40/40 on a copy of the 13-Nov database with made-up patients; on S836's file
it goes red on the three wording checks (the control). Both pages' scripts pass `node --check`.

**Install:** the publish, then one server line (the installer's header). `--undo` puts S836's file back.
