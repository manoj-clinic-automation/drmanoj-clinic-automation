# KB_canon_S189 — the live-pin list regenerated at the S189 mid-session fold

`live_pins_S189.txt` is generated **from KB Register v5.27** against the S189 `CANONICAL_MANIFEST.md`
by `gen_live_pins.py` **v1.2** (`9c402c366e7c902f27047a2014062107`, selftest 22/22).

```
source                        : KB_Register_v5_27_S189.md
source_md5                    : 99b288309c2777b6c5d74c2662766c66
manifest_current_register_pin : 99b288309c2777b6c5d74c2662766c66
register_pin_verified         : yes        <- the generator PROVED it (F-110)
43 VPS rows · 11 BLIND rows
```

## Why this exists mid-session rather than at the close

Kit `S189_G1a` moved a live pin: `finance_app.py` `f06e139b…` → `16faf98caa720a662316fa235a4b35b9`.
The S186/S188 practice is to **record live pins as they move, not at the close**, because an
unrecorded live pin *is* the F-97 condition. So the Register went to **v5.27**, the manifest was
rebuilt to pin it, and — per **step A8**, the fix F-134 bought — the pin list was regenerated
**after** the manifest, since the generator refuses a Register the manifest does not pin as CURRENT.

Without this, `verify_live_pins.py` reports **RED on `finance_app.py`** — correctly, because the
record would be behind the box.

## Owner action — one copy, then one check

```
cd /root/deploy/repo && git pull
cp /root/deploy/repo/deploy_kits/KB_canon_S189/live_pins_S189.txt /root/deploy/live_pins.txt
python3 /root/deploy/verify_live_pins.py
```

Expect **GREEN**, with `source : VERIFIED ON THIS MACHINE`, and **43 match / 0 drift**.

The 76 untracked files and 11 unverifiable rows will still be listed. Neither is a failure — the
untracked list is F-97 part 2, and reading it is what produced **F-136** this session.


---

## S189 SECOND FOLD — `live_pins_S189b.txt` supersedes the file above

The pin moved twice after the first fold (`S189_W1a` → `S189_W1b`) and migration `S189_custody` was
applied. Regenerated from **KB Register v5.28** (`741ecde44e4263f36a88c0baf0e45907`),
`register_pin_verified: yes`, **43 VPS + 12 BLIND** (the applied custody migration is the new BLIND row
— state, not a file).

```
cp /root/deploy/repo/deploy_kits/KB_canon_S189/live_pins_S189b.txt /root/deploy/live_pins.txt
python3 /root/deploy/verify_live_pins.py
```

Expect **GREEN · match 43 · drift 0 · `source : VERIFIED ON THIS MACHINE`**.

---

## S189 THIRD FOLD — `live_pins_S189c.txt` supersedes both files above

Regenerated from **KB Register v5.29** (`ef40881f3b68a355db34632128a08b74`),
`register_pin_verified: yes`, 43 VPS + 12 BLIND. Carries the `S189_E1b` pins
(`finance_app.py 5cb73ff8…` · `finance_entry.html 1c7d2dc3…`).

```
cp /root/deploy/repo/deploy_kits/KB_canon_S189/live_pins_S189c.txt /root/deploy/live_pins.txt
python3 /root/deploy/verify_live_pins.py
```

Expect **GREEN · match 43 · drift 0 · `source : VERIFIED ON THIS MACHINE`**.

---

## S189 CLOSE — `live_pins_S189close.txt` is the FINAL S189 list

Regenerated from **KB Register v5.30** at the close (A8, after the manifest).
`register_pin_verified: yes` · 43 VPS + 12 BLIND.

```
cp /root/deploy/repo/deploy_kits/KB_canon_S189/live_pins_S189close.txt /root/deploy/live_pins.txt
python3 /root/deploy/verify_live_pins.py
```

Expect **GREEN · match 43 · drift 0 · `source : VERIFIED ON THIS MACHINE`** — the fifth of S189.
