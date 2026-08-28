# WHERE THIS KIT'S DATA LIVES — and why it is not here

**The repository is CODE ONLY** — its `.gitignore` says so on line 3, and line 17 blocks **all
`*.json`** so that a key file can never slip in. That rule is older than this kit and it is a good
one; it is not weakened for our convenience.

So this kit's generated `.json` files live in:

```
D:\Downloads\ClaudeCowork\04_SOURCE_DATA\S207\
```

**Every one of them is rebuilt by the code in this folder** — they are outputs, not inputs, and the
kit is not less complete without them. The commands are in `README.md`.

**One exception worth knowing:** `salt_expected_state.json` is *not* rebuildable from Marg alone —
it encodes the owner's rulings of 28-Aug-2026 on 77 item changes, 38 salt creations and 2 renames,
and it is the set Amir's work is checked against later. **It is data, and its home is the KB folder
and the SSD, not the repo.**
