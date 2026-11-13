# S816_TILES_CALLS_WHATSAPP — the home-screen tiles: WhatsApp messages moves to Calls & WhatsApp, two old tiles retired

**The owner, 13-Nov-2026:** approved the mock-up "the tiles" (artifact 8J3R3QtW9awbajmLN4rmic; his finding F-1324).
Built in S447 (the parent) on the live bytes of `/root/portal/portal.py` from the 13-Nov bundle (md5 `3a0f7cd1…`, S798's).

**ONE live file changes — `/root/portal/portal.py` `3a0f7cd1` → `8f60b310` — and in it only the tile list, the group table and one group face:**

1. **WhatsApp messages** (`/portal/messages`, the doctors' by role) **moves from Patients to Calls & WhatsApp**, standing between
   WhatsApp Inbox and Send WhatsApp as on the mock-up. Its small line becomes `Daily patient messages · switches · what went`
   (it was `Show only · who would get which message`). Name, icon, address and roles are untouched.
2. **Follow-up WhatsApps** (only a link into `/portal/console#followups`) is **retired** from the home screen.
3. **WhatsApp Approvals** (`/wa-approve`, in System) is **retired** from the home screen.
4. The folded **System** group's own small line drops ` · WhatsApp approvals` and nothing else: it reads `Board · users · clinic PCs`
   (decided in S447 after the first build: a group's face must not name a tile that is gone).

Calls & WhatsApp after this, in order: Clinic Gist · Call Console · Call Tracker · Call ke baad · GMB Review Assist ·
WhatsApp Inbox · **WhatsApp messages** · Send WhatsApp (+ Follow-up Tracker on the clinic PC only, as before).

**Nothing else changes.** No route, no page code, no grant, no other tile, no other group face; both retired addresses still answer when
typed. "Retired" is done the way S586 retired its eight tiles — the dict is taken out of `TILES` (portal.py has no other switch
for it) — and a note stands where each was. Tiles are keyed by their NAME (grants, masks, the live numbers on tiles): no name
changes, so every grant and every badge keeps working.

**Who sees a difference:** only a login that is drawn these tiles — the doctor role. All three carry `roles ["doctor"]` and
nobody is granted any of them by name (the 13-Nov `tile_grants.json` was read: the only mention is Dr Bhawna's *mask* of
Follow-up WhatsApps, which now matches nothing — harmless, left alone). Dr Bhawna's "only" list keeps all three off her home
already, so her screen is the same. **No staff or manager login loses or gains anything** (the walk proves it tile for tile).

| role (by role alone) | before | after |
|---|---|---|
| doctor | 59 tiles | 57: Patients loses WhatsApp messages · Calls & WhatsApp gains it and loses Follow-up WhatsApps · System loses WhatsApp Approvals |
| manager | 7 tiles | the same screen |
| staff | 5 tiles | the same screen |

## The wa-approve service — NOT touched by this kit

The plan said "its service stopped, kept to put back". It was checked first, and **something expects it to be running**, so this
kit retires the tile only and leaves `wa-approve.service` (gunicorn on 127.0.0.1:8101, `/root/wa/wa_approve.py`) exactly as it is:

- `/root/deploy/clinic_doctor.py:70` — the clinic-doctor's `SERVICES` list names `wa-approve` ("WhatsApp approvals", port 8101,
  probed at `/`). A manual `clinic-doctor` run restarts it when it does not answer; `clinic-doctor --check` calls it DOWN and
  ends NOT FIXED; only `--auto` leaves a unit alone when it is stopped AND disabled.
- `/root/wa/swap_key_s701.py:51` — the key-swap tool restarts `wa-approve` as one of the three services that read the key at start.
- `unit_state.txt:120` of the bundle: enabled, active.

To stop it later (a separate, small kit): take the `wa-approve` row out of clinic-doctor's `SERVICES` and out of
`swap_key_s701.py`'s readers in the same install, then `systemctl disable --now wa-approve` (unit file and code stay; putting it
back is `systemctl enable --now wa-approve`).

## Left as it is, on purpose (said so the next reader does not think it was missed)

- The mock-up draws shortened small lines for the group's other tiles (for example Send WhatsApp: "One approved message, by
  hand"). Only the WhatsApp messages tile is marked as changed there, so the other tiles keep their live wording.
- `calls_console.py` still carries its own in-page link to the batch page `/portal/wa/followups`; page code is out of scope.

## Putting a retired tile back

Undo puts everything back (below). To put back ONE tile by hand in a later kit: its dict goes back into `TILES` and its line into
`_TILE_GROUP` (`"Follow-up WhatsApps": "Calls & WhatsApp"` / `"WhatsApp Approvals": "System"`). The two dicts, as they stood:

```
    {"icon": "\U0001F4E3", "name": "Follow-up WhatsApps",
     "desc": "The follow-up list, cleaned \u00b7 on the Call Console", "live": True,
     "url": "/portal/console#followups",
     "roles": ["doctor"]},

    {"icon": "\U0001F4F1", "name": "WhatsApp Approvals",
     "desc": "Vendor panel \u2014 active again", "live": True,
     "url": "https://followup.dr-manoj.in/wa-approve",
     "roles": ["doctor"]},
```

## How it was built and proven

`make_s816.py` remakes portal.py **on the box, from the file that is live there** (the kit carries no copy of portal.py): six
exact anchors, each required to occur exactly once; the FROM pin is checked before and the TO pin after.
`walk_s816.py <before> <after>` runs the portal's OWN tile code from both files (the tile list, the groups, `_grants_for`,
`_visible_sections`, `_home_blocks`) with made-up logins and a made-up grants file: **34/34** on the remade file; the **CONTROL**
(the unpatched live bytes as "after") **red, 18 of 34**. It checks: only six places of the file differ and everything outside
the tile list and the grouping tables is byte-for-byte the same; no route changed; the moved tile's group and small line to the letter;
the two retired tiles gone; every other tile identical in every field and in the same order; the ten groups untouched and nine faces
untouched, the System face to the letter; per role and per login, phone and clinic PC, the only differences are the three; every non-doctor screen EXACTLY the same.
The installer was rehearsed on a stand-in root (16 runs): DRY · install · already · undo byte-identical · a kit file altered → stops ·
live file not the pinned one → stops (and undo refuses) · the install lock held → stops · the portal unhealthy before → stops ·
outside the install window → stops · red after placing (health / a door / the journal / the run interrupted) → the old file back
byte-identically each time.

**The installer** checks the kit's SUMS, that the live file is the pinned FROM, remakes it and checks the TO pin, compiles it,
runs the walk and the control on the box, checks the portal's health and six doors, takes the install lock, keeps the backup
`/root/portal/portal.py.bak_S816_3a0f7cd1`, places the file, restarts `clinic-portal`, checks health and that every door
answers exactly as before, reads the journal; anything red after placing puts the old file back byte-identically.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s816kit && cp -rp /root/deploy/repo/deploy_kits/S816_TILES_CALLS_WHATSAPP /tmp/s816kit && bash /tmp/s816kit/install_S816_TILES_CALLS_WHATSAPP.sh
```
A rehearsal that writes nothing: the same line with `DRY=1 ` in front of `bash`.
Undo: `bash /tmp/s816kit/install_S816_TILES_CALLS_WHATSAPP.sh --undo`
