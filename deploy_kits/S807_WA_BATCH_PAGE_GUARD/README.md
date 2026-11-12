# S807_WA_BATCH_PAGE_GUARD — the old follow-up batch page works on today's list only, and says LIVE or TEST (F-1301)

**Before:** `https://followup.dr-manoj.in/portal/wa/followups` (the batch page of S172) is LIVE — its "Send selected" really
sends — and it stood on a list of 13-Aug with 120 sendable rows. Nothing on the page said LIVE, and nothing said the list
was three months old.

**Now** (one file, `/root/portal/portal_followups.py` 98547bc4 → the kit's; the page file is untouched):
- **Today's list only.** A list is today's when its file is named exactly `Staff_Action_Today_YYYY-MM-DD.xlsx` and that
  date is today in IST. A list of any other day, a file named any other way (a copy, `_old`, two dates), or no list: the
  page shows the reason in plain words ("The follow-up list on the server is dated 13 Aug 2026 -- it is not today's …")
  and **not one row of it**. The folder's name and the file's write time are not used.
- **The send door checks again at the moment of sending.**
  - Not today's list → HTTP 409, the sender is never called. Today's list unreadable → nothing is sent.
  - The page must have been opened on this same list: the strip gives the page the list's date and the page's send
    request carries it back (header `X-List-Date`). A page left open from an earlier day is told "Reload the page …" and
    nothing goes.
  - A row goes only when its S.N, name and number are **all** a sendable row of today's list, each exactly as the list
    has it. The number and the words handed to the sender are then the **list's** — what the request says about them is
    not used. The template is the one picked on the page, and must be one of the five follow-up messages.
  - **A sender failure stops the batch there**: that row is not tried again, the rows after it are not sent, and the
    page is told row by row (before, a failure gave an error page with every row still ticked — a second press sent the
    first rows twice).
- **LIVE or TEST on its face.** The server puts a strip straight after the page's `<body>` tag on every load: **LIVE** (a
  message sent from this page goes to the patient's WhatsApp) or **TEST** (logged only), with the list's date or the
  reason nothing can be sent, and a link to the WhatsApp messages page. The page is served `no-store`.
- **Unchanged:** the list's parser, the template ladder, the values' shape, the one sender (`portal_wa.send`) and its log,
  the test switch (`PORTAL_WA_DRYRUN`), the login guard on all three doors, "no rows selected" (400), the 500-row cap, two
  patients on one mobile each getting their own message.

**What it does not do:** it does not look at the stop list or at what another page already sent — this page is the old
road; the daily messages are being built on `/portal/messages` with those rules. With the feed of this page's list stopped
since 13-Aug, the page will simply refuse until a list named for today arrives.

**Walk** 47/47 on made-up lists (made-up names, mobiles from a counter; the sender is a recorder that can be told to
fail); the CONTROL red on the live file (40 of 47). Nine mutations each turn it red (the list-date check, the words from
the request, the stop after a failure, the name rule, the server's zone, the template check, a match on the number
only, a list date given on a stale list, the freshness check at sending). The repository's page file run in Chromium at
400 and 1100 px against the kit's file: the refused list, today's list sent through the page's own button (the strip's
script carries the list date), the list turning old under an open page, TEST. The installer rehearsed on a stand-in root.

**Cold review (a second reader, S440): SAFE TO INSTALL on the first build, with one claim that was not true as written**
("a page left open from an earlier day cannot send its old rows" — only the number was checked). Closed in code, not in
words: the list date carried by the page, the S.N + name + number match, the number and words taken from the list.
Its should-fixes built: the sender handed the list's own number; the batch stopped at a sender failure; the strip's
wording when the list is refused; the exact file name; the walk's gaps (the zone at +14 and −11, name not folder, the
overclaiming names); the installer (`-I` on its python line, a killed run's lock and switch cleared on the next run, a
note when the portal answers the same to every path, the journal read checked, the copy tested before the move, exactly
one `<body>`). Left as they are: a request whose `items` is not a list still answers an error page, nothing sent (as
before); `--undo` takes no lock.

**The installer (S805's pattern):** the kit's file is remade on the box from the live bytes and must equal the kit's;
compile; walk and control; before placing — the portal healthy, the three doors closed without a login, the page file
there with a `<body>` tag, and what the new file says about the list on the server (its date only, never a row); place;
restart; health; the three doors as before (a 404 on the data door = the page did not load → the old file back); journal
read and clean; the list's state read with the placed file. Red after placing → the old file back and the portal restarted.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s807kit && cp -rp /root/deploy/repo/deploy_kits/S807_WA_BATCH_PAGE_GUARD /tmp/s807kit && bash /tmp/s807kit/install_S807_WA_BATCH_PAGE_GUARD.sh
```
Undo: `bash /tmp/s807kit/install_S807_WA_BATCH_PAGE_GUARD.sh --undo`.
