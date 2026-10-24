# S638 anchored edits for /root/portal/tile_grants.json (FROM 6498a916) -- THE PARENT'S FILE (named in the README and the PLANNED line)
# D778: Shivani is the fallback for the morning reports when Shavez is away -- her home shows 'Aaj ki reports' (display only: the page's
# own gate, the medical viewer role she already holds, is unchanged).
EDITS = []
EDITS.append((''' "version": 37,''', ''' "version": 38,'''))
EDITS.append(('''every page's own gate unchanged.",''', '''every page's own gate unchanged. | v38 (S638, 24-Oct-2026, D778, the SANJEEVNI chat -- a PLANNED line on the board first): 'Aaj ki reports' (/finance/reports/aaj) to shivani -- the morning reports' fallback when Shavez is away; the page counts the day, not the person. Display only: her medical viewer row (the page's own gate) is unchanged. Nothing else in this file moves.",'''))
EDITS.append(('''  "shivani": {
   "extra": [
    "Call Tracker",
    "Call ke baad",
    "Vaapsi Desk",
    "Docterz Revenue",
    "Docterz daily collection",
    "Morning match",''', '''  "shivani": {
   "extra": [
    "Call Tracker",
    "Call ke baad",
    "Vaapsi Desk",
    "Docterz Revenue",
    "Docterz daily collection",
    "Aaj ki reports",
    "Morning match",'''))
