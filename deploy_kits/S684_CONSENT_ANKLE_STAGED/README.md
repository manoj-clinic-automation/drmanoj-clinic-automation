# S684_CONSENT_ANKLE_STAGED — the parent, session S371, 31-Oct-2026

**What the owner asked (31-Oct 08:20–08:47 IST).** A patient with a proximal humerus fracture, a medial and a posterior malleolus fracture and ankle subluxation: an external fixator on the ankle now, definitive fixation later. The consent generator could not write it: the ankle opening promised plate-screws, the external fixator printed only as an open-fracture pathway, there was no posterior malleolus, no subluxation, and no "decided later" for the shoulder. His words: *"for ankle fractures how about a selector for the malleoli and subluxation, so can tick the ones patients has"* · *"definitive fixation can be screws and wires also, plates are not used always"* · *"proceed with this feature build now"*.

**One file.** `/root/wa/casepack/casepack_page.html` 26cba6b1 → the kit's page (SUMS.md5). Read by the portal on every request: no restart.

| | what changes on the Consent tab |
|---|---|
| Ankle | choosing *Ankle fracture* shows a box: bones broken (inner / outer / back malleolus), the joint (in place / subluxation / dislocation), fixed with (plate-screws / screws / wires — none ticked = "screws, wires or plate, as suitable"). The opening is built from the ticks; a line under the box reads it back in English (e.g. *Bimalleolar (medial + posterior), subluxation — external fixator now*). |
| Plan now | in the fracture panel (inside the ankle box for the ankle): fix now / external fixator now, fix later. The fixator plan prints *इलाज की योजना* (two stages), its risks, and the scope *"this consent is for the first stage"*; it ticks *operated now* by itself. An open fracture keeps its own pathway (the box greys out, and the ankle never promises fixation now under plaster-first or fixator-first); planned operations (replacements, ACL, implant removal…) show no plan-now. *Plaster/slab now* was left out at the cold review: the rest of the consent speaks of an operation. |
| Extra fractures | a *plan later* tick: "with or without an operation, decided later; a separate consent if operated". *op now* and *plan later* exclude each other. |
| Bones | the ankle list gains the posterior, medial and lateral malleolus and "all three". |
| Fixed | an opening already plural no longer prints "टूट गई हैंं" (seen live on the control run: distal tibia with "पैर की दोनों हड्डियाँ"). |

Every other procedure prints exactly as before (the walk compares five of them, word for word, with the old page). Saved cases are untouched; an old case reloads as before.

**Proof.** `walk_s684.py` in Chromium with a made-up patient: **45 of 45 green**; control on 26cba6b1: **30 S684 red · 0 older red**; ten mutants each caught. Independent cold review: round 1 NOT SAFE (the slab option; six corrections), round 2 NOT SAFE (overlapping Generate runs could print the plain ankle opening — the opening is now read live from the ticks, nothing swapped), each built and walked. Installer rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · a red after placing puts the old page back · a changed live page refused. On the box the gate is that `make_s684.py` rebuilds the kit's page byte for byte from the box's own live file.

**Install.** After the publish, one line on the VPS:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s684kit && cp -rp /root/deploy/repo/deploy_kits/S684_CONSENT_ANKLE_STAGED /tmp/s684kit && bash /tmp/s684kit/install_S684_CONSENT_ANKLE_STAGED.sh
```

Undo: the installer prints its one line (the backup is `casepack_page.html.bak_S684_26cba6b1`).
