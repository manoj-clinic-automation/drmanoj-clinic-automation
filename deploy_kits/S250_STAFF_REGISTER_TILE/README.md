# S250_STAFF_REGISTER_TILE

**The owner's ask, 13-Sep-2026:** *"staff register - receptionists are maker, shavez is checker,
need to add these to pwa of these 3 people, as since pwa its not accesible to them."*

Receptionists read as **Shivani and Alisha**. The three are the register's own working roles:
Shivani and Alisha are **makers**, Shavez is the **checker** (D272 -- and he still may not approve
a date he entered himself).

**What changes:** `/root/portal/tile_grants.json` only.
v14 `0efad736e71de7199e7c596a5b3d0c2e` -> v15 `932f7bd05f4bf19b1f53deb9a2f35d22`.

`"Staff Register"` is removed from the `mask` of `shavez`, `shivani` and `alisha`. That is the
entire diff, plus the version number and the note.

**Why there is no name-grant.** The tile carries `roles: ["doctor", "manager", "staff"]` in
`portal.py`, so it was always on the staff role -- it was **held back by a mask** at S239 v9
("Attendance and Staff Register are HELD from every staff login for the time being"). Lifting the
mask line is the whole change: no `extra` entry, no code file edited, no service restart. This also
means the tile cannot be lost if the grants file ever goes missing.

**The tile**

| | |
|---|---|
| name | `Staff Register` (icon 📅) |
| section | *Staff* (lowest -- the owner's ruling that attendance sits lowest because it is personal) |
| url | `/register/review` |
| page's own gate | `staff_register.py` resolves maker / checker from `SR_MAKER_USERS` (`alisha,shivani`) and `SR_CHECKER_USERS` (`shavez`) -- **unchanged** |

`tile_grants.json` decides what a person is SHOWN. It grants no access; every server-side gate
still decides what they may reach.

**What does NOT change**

- `Attendance` stays masked for all three -- he asked for the register, not the biometric app.
- `darpan`, `amir`, `awdhesh`, `sukhveer`, `surendra`, `parvesh`, `sandeep`, `vikky` keep the
  S239 v9 hold, tile for tile.
- `manoj` and `bhawna` unchanged; the section-order block untouched; `portal.py` untouched.

**Proof, in the order it was taken**

1. The live `portal.py` (`06f1b378`) reproduced offline from the S204 base plus fifteen anchored
   patchers, every declared pin reproduced exactly in order -- `EVIDENCE_portal_reconstruction_S250.txt`.
2. A **live-shape walk**, not a reading of the JSON: portal.py imported (its own "every tile is
   grouped" assert first) and its own `_visible_sections` asked what each of the fourteen logins is
   shown -- with v14 beside v15 as the baseline. **67 checks, 67 green** --
   `EVIDENCE_walk_S250.txt`. The three gain exactly `['Staff Register']` and lose nothing; every
   other login is identical section for section; the doctor keeps everything; fail-closed checked.
3. The installer rehearsed end to end against a fake box: it refuses unless the live file is still
   v14, takes the backup, prints the predicted md5 **byte for byte**, and a second run refuses and
   changes nothing.

**Install:** one line, `INSTALL_ONE_LINE.txt`, run on the VPS. It must print
`932f7bd05f4bf19b1f53deb9a2f35d22`. Backup left on the box: `tile_grants.json.bak_S250_v14`.
The line then prints the register's configured maker / checker lists, read-only, so a mismatch with
"makers alisha,shivani / checker shavez" is seen at once. (An environment override in the unit file
would not show there; the screen itself is the final word.)

**Verify after:** Shavez, Shivani or Alisha open the app -- 📅 **Staff Register** is at the bottom,
under *Staff*. If a maker lands on a "not activated" screen, that is the register's own role list,
not this kit: one line in the register config fixes it.
