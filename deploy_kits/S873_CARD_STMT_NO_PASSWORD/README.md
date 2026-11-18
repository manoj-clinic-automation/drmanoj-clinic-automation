# S873_CARD_STMT_NO_PASSWORD — the parent, S480, 18-Nov-2026

**Found by:** the 13:25 check on /finance/packs, October.
- The ICICI Amazon Pay statement for 13-Sep to 12-Oct is the one ICICI never mailed. He downloaded it from the bank's website and put it in Drive > Credit Card Statements > ICICI Amazon Pay at 10:09.
- It reached the shelf as file 176, and its dates were read.
- It was then held as **"locked original"** and never read. So the card row stayed empty, and electricity stayed at 1 of 2.

**Cause:** the shelf took every file in a card folder to be the bank's password-locked mail copy, waiting for a decrypted twin or for the stored password. A statement downloaded from the website has no password, so neither of those ever comes.

**The change** (`make_s873.py`, exact anchors, FROM md5 checked):

| file | FROM | TO |
|---|---|---|
| /root/finance/packs.py | da0013ab | (TO_PINS.md5) |

1. **`_original_status`:** a card-folder file that is not password-locked is now handled like any other statement.
   - With its statement date read, it is marked **read** ("statement dated … · no password (downloaded from the bank)").
   - Without a date, it says so.
   - If the file cannot be opened at all, it says that. It is never called "locked".
2. **`_process_once`:** a file already held wrongly as "locked original" with `locked=0` is looked at once more. When it turns out truly locked it gets `locked=1`, so it is never picked again.
3. **The month's card cell:** it now also takes a read card-folder file that has no password. Before, it took only one the shelf had opened with the password.

**Proof in the build:**
- walk_s873 11/11 on a made-up shelf, with the PDF reader stood in. Its control on the FROM file went red at 4/11.
- Without change 3, W7 goes red.
- S866's walk 18/18 on the new file.
- Rehearsal on a made-up root (see the board line).

On the box, the installer runs the shelf's identify step on two copies of the live database, one with the old file and one with the new. Only card-folder rows held as "locked original" may change, and only the card rows and the electricity row of last month's pack may differ. It shows the Amazon Pay row as it will read. After the install it runs one shelf read and prints the Amazon Pay and electricity rows.

**Install:** his publish, then one server line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s873kit && cp -rp /root/deploy/repo/deploy_kits/S873_CARD_STMT_NO_PASSWORD /tmp/s873kit && bash /tmp/s873kit/install_S873_CARD_STMT_NO_PASSWORD.sh
```
