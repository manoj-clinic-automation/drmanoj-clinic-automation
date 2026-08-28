# S207_SALT — same-salt alternatives, and why none of them is automatic

**Staged. Writes one page. Nothing reaches staff until the doctor approves it.**

When a stockist has none of a brand, another brand of the same molecule usually does. Marg's
**SALT WISE ITEM LIST** is the only place that mapping exists.

## The file has real errors, and they are not parsing artefacts

The owner said to expect some. There are more than some. The group headed
`ETORICOXIB 60 + THIO 4` contains **an arm sling, two knee caps, a rib belt and a pain patch** —
checked against the raw cells before saying so, because the first two versions of this parser were
themselves wrong and it would have been easy to blame the file for my own bug.

**The first bug was mine:** the report reprints its page header at every page break, so
`S.No. DESCRIPTION` read as a salt with 29 brands under it — the same fault the purchase parser met
with reprinted supplier headings. **43 such rows** in this export.

**After fixing that, the pollution was still there.** So it is the data.

## Three filters, each measured

| filter | why | effect |
|---|---|---|
| page furniture | the header reprints at every break | 43 rows skipped |
| **one pack form** | a group mixing `1*1` devices with `1*10` tablets is not a molecule | removes 16 groups, 113 brands |
| **2 to 4 brands** | a 376-item pharmacy does not stock six brands of one molecule; the 5s and 6s were the polluted ones | removes the rest |

**40 groups, 90 brands survive** — and roughly **one in ten of those is still wrong**.
`PELVIC TRACTION BELT XL` lists a wrist brace. `TELM 80 + HYDROCHL 12.5` lists what looks like a
pantoprazole. Those three are **marked in red on the page**, as my reading, not as a ruling.

## Why nothing is automatic

**These are medicines.** A ninety-per-cent list is an excellent thing for one person to review once,
and an unacceptable thing to put in front of a counter. The page asks the doctor one question per
group — *are these interchangeable?* — and only an approved pair can ever be offered when a stockist
says they have none.

Each brand shows **what is on the shelf today**, so an alternative that is itself out of stock is
visible as such. Decisions are remembered and shared, the same two-copy design as the other pages.

## It confirms something found independently

Marg files `DISPO SYRINGE NIPRO 3ML` and `NIPRO 3 ML DISPO SYRINGE` under **the same salt** — the
duplicate item code found earlier from stock (199 on one code, −83 on the other). Two different
routes, same answer.

## Proven

`salt_alternatives.py --selftest` — **11 checks**, no data needed: page furniture skipped, a group
after a page break attaching to its own salt, a mixed-form group rejected *with its reason*, an
oversized group rejected, pack forms read rather than guessed, and a float cell coerced (one reader
hands back `1.0` where another hands back `"1"`).

*S207_SALT · staged 28-Aug-2026 · nothing live touched.*
