# S875_PACKS_REVIEW — the parent, S480, 18-Nov-2026

**His word:** 14:10, "do all" on the packs review. His rule: the scanned bills of section 8 are **not** in the accountants' mail by default. He gets an option, month by month, to send them or not.

**The change** (`make_s875.py`: build_bundle replaced as one checked block, plus exact anchors; FROM md5 checked):

| file | FROM | TO |
|---|---|---|
| /root/finance/packs.py | 0a50fd59 | (TO_PINS.md5) |
| /root/finance/packs.html | 666fea71 | (TO_PINS.md5) |

- **8.x bundles** (`bundle_rows` + `build_bundle`)
  - The index lists the month's bills first, with their count and total. Then come the papers scanned this month for earlier months, grouped by month, each with its own count and total. The scans follow in the same order.
  - A paper scanned after its month is **late**, marked or not. Before, an unmarked one (B.L. Computers, a July bill scanned on 1-Oct) fell out of every pack.
  - **Kept out and named on his page** ("fix it on the sorting desk"): a paper with no total, a total of Rs 1 or less, no vendor, or no bill date. Also a paper with the same vendor, date and total as an earlier paper in any lane.
- **Opt-in**
  - Each bundle shows "Kept back — send with the pack". The door `POST /finance/packs/api/send8 {month, lane, on}` records his tick as pack_tick `send8:<lane>`.
  - A kept-back bundle is neither attached to the mail nor named in it. A ticked one is attached and named "[enclosed]".
- **7 Payment papers**
  - A renewal or confirmation notice with no receipt **and** no card line is dropped as "not a charge". A notice that matches a card line stays.
  - "Payment successful for X" shows X as the vendor.
  - NK Pathology's papers go on their own sheet.
  - A new column names the card line each paper matches (amount within Rs 1, date within 7 days), or says "not on a card statement".
- **4.4 Card sheet:** the top of the sheet says which dates each statement covers. The page's statement table has a Covers column.

**Proof in the build:**
- walk_s875 28/28 on a made-up root (made-up finance db, made-up asset app, invented vendors). Its control on the FROM files went red at 2/28.
- S866's walk 18/18 and S873's walk 11/11 on the new files.
- Rehearsal: see the board line.
- On the box, the installer reads last month's pack on a copy of the live database, old against new. Only the payment papers, the card sheet and section 8 may differ, and the attachments may only lose the section-8 bundles.

**For the Scan App chat** (on the board): the Envirad bill sits in two lanes (B-0137 read as Rs 1); Shivam Communication is filed as a lab purchase; B-0220 and B-0222 were read with no bill number or items; the scans are cropped; B-0104 was never marked late.

**Install:** his publish, then one server line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s875kit && cp -rp /root/deploy/repo/deploy_kits/S875_PACKS_REVIEW /tmp/s875kit && bash /tmp/s875kit/install_S875_PACKS_REVIEW.sh
```
