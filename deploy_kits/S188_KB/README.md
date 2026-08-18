# S188_KB — the S188 record fold-in (docs only · no code · nothing to install)

Two canonical documents, bumped mid-session so the live pins are recorded **as they moved**,
not saved up for the close (the S186/S187 practice; Runbook §1 *"record live pins as they move"*).

| Doc | version | md5 |
|---|---|---|
| `Fault_Action_Register_v2_23.md` | **v2.23** | `8630142ffa5198058cd7ea2fb398c1f5` |
| `KB_Register_v5_23_S188.md` | **v5.23** | `64814f4fdcf6570d2cd195ad07e20f14` |

## What changed

**Fault Register v2.22 → v2.23** — **F-127 · F-128 · F-129** appended the session they were raised
(third consecutive close with no owed append). §7 index extended F-126 → F-129, full text in a new
§7.1 S188 section, changelog row added, next-free advanced **F-127 → F-130**.

**KB Register v5.22 → v5.23** — the four live pins from `S188_D2a` and `S188_D2b`
(`finance_app.py` and `finance_ui/finance_entry.html`, each with its predecessor kept as a
`*(superseded)*` row), the three findings into the findings index, the how-to-use pointer advanced
to Fault Register v2.23, a v5.23 lineage row, and the end marker corrected.

## Zero loss, proven mechanically — not asserted

Both were verified by **reverse application**: strip from the new file exactly the blocks S188
inserted, undo exactly the line edits S188 made, and require the result to be the old file
byte-for-byte. Both reconstructions land on the **manifest's own pins**:

```
Fault Register  v2.23 with S188 undone -> cfd8f958cd37fbee502dd46726e8256d   (= the v2.22 pin)
KB Register     v5.23 with S188 undone -> 116a0bdba426f33c0fda69652bba46fc   (= the v5.22 pin)
```

If anything else had moved, the hashes could not match. §0–§6 of the Fault Register and every prior
finding are untouched.

## Placement

These are **not** promoted into `KB_canon_all/` or into `CANONICAL_MANIFEST.md` here — that happens
at the close, when the manifest is rebuilt and `MD5SUMS_ALL.txt` regenerated. The bytes are
preserved in this kit meanwhile, exactly as the v5.13–v5.20 intermediates were at S187. The same
bytes are also in project knowledge as `claude/Fault_Action_Register_v2_23.md` and
`claude/KB_Register_v5_23_S188.md`.

**Owed at the close:** promote both into `KB_canon_all/`, rebuild `MD5SUMS_ALL.txt`, rebuild
`CANONICAL_MANIFEST.md`, append Archive §S188, bump the Runbook, regenerate START_HERE 189.
