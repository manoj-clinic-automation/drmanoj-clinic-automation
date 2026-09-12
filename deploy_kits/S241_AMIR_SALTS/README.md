# S241_AMIR_SALTS — the salt list as a sheet he can carry

**The owner's words:** *"make the salt correction file in such a way that he
downloads it and uploads it again so that he can copy the exact names from the
spreadsheet you make available for him."*

**Why the sheet, and not just the page.** A salt correction is worthless if the
name is retyped with a space in the wrong place — that is exactly what put
`METHYLPREDNISOLONE 8` and `METHYL PREDNISOLONE 16` into different groups. So
the sheet carries the exact string in its own column, and he copies **from** the
sheet **into** Marg. He never types a name into the sheet. What comes back is
one letter per row.

**The tabs.** `SALT KAAM` — the open work, one row each: `ID · KYA KARNA HAI ·
KIS PAR · ABHI KYA HAI · YEH EXACT NAAM COPY KIJIYE · HO GAYA (Y) · REMARK`,
the last two shaded as the only cells to type in. `DR SAHAB KE LIYE` — the
questions only the doctor answers, read-only, so he can see them without being
asked to do them. `NAYE ITEM` — what was bought for the first time this month.
`PADHIYE` — seven lines of how to use it.

**Matching back.** By `ID`, never by name — the name is the thing that was
wrong. A row whose ID has been deleted or edited is reported as unrecognised,
not guessed at. A blank is a blank, never a tick, and a blank row simply comes
back on the next sheet. Anything that is not a yes (`Y`, `haan`, `ok`, `done`,
`1`, a tick mark) is treated as not done.

**It cannot double-count.** The upload is de-duplicated by the file's own md5:
send the same file twice and the second one reports the first one's result and
writes nothing.

**Where the ticks go.** Into `purchase_salt_task` — the same rows his existing
page ticks — so the sheet and the page can never disagree, and the "Marg says"
column on that page still judges both.

**Nothing new on the server.** The workbook is written and read by
`padwriter.py` / `padreader.py`, the stock pad's own standard-library pair,
already beside the finance app. This kit does not ship or overwrite them; if
they are missing it goes RED and changes nothing.

**Install** — one line on the VPS:

```
bash /root/deploy/vps_deploy.sh S241_AMIR_SALTS
```

The installer runs both walks **on the box, against that box's own
padwriter/padreader**, before it copies anything.
