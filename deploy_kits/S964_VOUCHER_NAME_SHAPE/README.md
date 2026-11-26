# S964_VOUCHER_NAME_SHAPE — the voucher reader takes item names with an inch mark (Sanjeevni session 530, 26-Nov-2026)

**Why:** S963 went live at 17:03 (server) and 17:11 (medical PC). His server read at 18:02 IST: the Stock Issue report of 01-10..26-11
stored whole (37 vouchers, 181 lines, Marg's totals to the paisa), the 11-14 Nov issue export too (5 / 23 — the same vouchers; the
newest export wins those days), but the **Stock Receive report was NOT READ**: the server's own cell check (S963's cold review S2)
allowed only some marks in an item name, and four real names carry an inch mark — `PRIME PAD 4"`, `PRIME PAD 6"`, `PRIME CAST 4"`,
`PRIME CAST 5"`. As designed, the door then kept no file of it. The medical PC had read it correctly.

**What it does:**
1. `/root/marg_ingest/marg_vouchers.py` 7bc3df84 -> see `TO_PINS.md5`: an item name is any printed mark, single spaces, at most 24
   letters, starting with a letter, a digit or "(". Both real reports now read whole on the server's own check (receive 16 / 73,
   issue 37 / 181). Selftest 21/21 (an inch-marked name read; a 25-letter name, a name starting "-" not read).
2. Clears the server's record of every voucher sheet refused for that shape (its `mi_voucher_file` and `mi_file` rows — nothing else;
   a sheet refused for a name in its party cell is never touched), under the collector's lock. The five-minute collection then takes
   the medical PC's own copy from Drive `MargArchive\_UNKNOWN` again — no step for anyone.

**Proof:** the S963 walk 11/11 on the new reader (made-up reports); the control — the live reader refuses an inch-marked name;
`rehearse_s964.sh` 6/6 on a made-up root (dry · red at [4/5] · install clearing exactly the shape-refused record and keeping a
name-refused and a sound one · again · undo · wrong FROM).

**Install:** his publish, then one server line (in the installer's head). **Undo:** `bash /root/deploy/repo/deploy_kits/S964_VOUCHER_NAME_SHAPE/undo_s964.sh`.

**Noted for the next kit (the judge and the two screens):** a held text retried by the medical PC is stamped with the retry time
(`20261126-171126`), not its export time — the "newest export wins" order should take the second stamp in the file name; and the medical
PC files voucher sheets under `_UNKNOWN` in MargArchive (its own report list does not know the kind yet).
