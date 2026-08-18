# KB_canon_S188final — the regenerated live-pin list (F-134)

`live_pins_S188final.txt` is generated **from KB Register v5.26**, against the S188-final
`CANONICAL_MANIFEST.md`, by `gen_live_pins.py` **v1.2** (`9c402c366e7c902f27047a2014062107`,
selftest 22/22).

```
source                        : KB_Register_v5_26_S188.md
source_md5                    : 3aa89f5a0c9dd7c6121c0a657dd573cd
manifest_current_register_pin : 3aa89f5a0c9dd7c6121c0a657dd573cd
register_pin_verified         : yes        <- the generator PROVED it (F-110)
43 VPS rows · 11 BLIND rows
```

## Why this folder exists — F-134

`live_pins.txt` is derived **from the Register**, so every Register bump stales it by definition.
S187 regenerated it and recorded the fact in the manifest — **narrative, not procedure**.
`END_OF_SESSION_PROMPT_v4` §A ran A0 → A7 and stopped at *"the manifest, ALWAYS updated last."*
**It was not last.** So the S188 close rebuilt the manifest, `MD5SUMS_ALL.txt` and `KIT_ID.txt` and
left the pin list on **Register v5.22 — three versions stale**, and the owner's own close-out run of
`verify_live_pins.py` went **RED on `finance_app.py` and `finance_entry.html`: two files the box had
exactly right.**

**The tool was flawless.** It refused to print VERIFIED, raised `MANIFEST_MISMATCH`, and printed the
CURRENT pin it expected beside the one it held — F-122's v1.2 fix behaving exactly as designed.

**Fixed at the source:** `END_OF_SESSION_PROMPT` **v4 → v5** adds **step A8 — regenerate the live-pin
list, after the manifest**, because the generator refuses unless the Register hashes to the
manifest's CURRENT row (F-110). *A close that rebuilds the manifest and not the pin list is not
finished.*

## Owner action — one copy, then one check

```
cp /root/deploy/repo/deploy_kits/KB_canon_S188final/live_pins_S188final.txt \
   /root/deploy/live_pins.txt
python3 /root/deploy/verify_live_pins.py
```

Expect **GREEN**, with `source : VERIFIED` — proved on the box, not merely attested.

The **76 untracked** files and **11 unverifiable** rows will still be listed. Neither is a failure:
the untracked list is **F-97 part 2** (already on the S189 backlog), and the unverifiable rows are
database migrations, Apps Script projects and PC-side files that no check on this box can reach.
They are blind spots, and the checker says so rather than counting them as passes.
