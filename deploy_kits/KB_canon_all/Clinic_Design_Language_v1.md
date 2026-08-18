# Clinic Design Language v1 (S187 · owner directive: "make design element default throughout our works")

**Adopted with kit `S187_H1b` (the Sanjeevni Hub redesign). Every NEW clinic page adopts this;
existing pages (entry, review, workbench, clinic screens) migrate opportunistically — whenever a
kit already touches them, never as gratuitous rebuilds. Grounded in the dataviz skill's method:
color by ROLE, status never color-alone, text wears text tokens, numbers are tabular and
right-aligned.**

## 1. Tokens (CSS custom properties — copy the `:root` block verbatim)

```css
:root{
  --surface-page:#f3f2ee;   /* warm paper — the eyestrain fix; never blue-grey */
  --surface-1:#fbfaf8;      /* cards */
  --surface-2:#f5f4f0;      /* insets, zebra rows, sticky table heads */
  --line:#e6e3dc;
  --text-1:#23272f;         /* primary ink — softened, never #000 */
  --text-2:#5d6470;         /* secondary */
  --text-3:#8a8f99;         /* muted / kickers */
  --accent:#2a78d6;         /* the ONE accent (series-1 blue): links, primary buttons */
  --accent-ink:#1c5cab;     /* link text / hover — passes contrast on surface-1 */
  --good:#0ca30c; --good-bg:#e9f6e9;
  --warn:#8a6100; --warn-bg:#fdf3d7;
  --bad:#b02a2a;  --bad-bg:#fbeaea;
  --shadow:0 1px 3px rgba(35,39,47,.06);
}
```

Status text colors are darkened for text-on-tint (the palette's raw status steps are for marks).
**A status is never color alone** — every badge pairs an icon (✓ ⚠ ⚑ ✗ ⏳) with its label.
Charts, when they come, take the dataviz reference palette (slot order fixed, validator-run).

## 2. Type

System stack; **base 15px / 1.6** (never 13px body again); h2 16px with an 11px UPPERCASE
`kicker` above it naming the section's job ("The drawer", "Your queue"); notes 12.5px.
**All numerals `font-variant-numeric: tabular-nums`; every numeric table column right-aligned
(`th.num, td.num`).** Money strings display through `fmt()` — trailing `.00` stripped.

## 3. Structure

- **Sticky branded header**: logo mark (40px) + product name + clinic line
  ("Advanced Orthopaedic Surgery Centre · Dr Manoj Agarwal, Bareilly") + a tab row of
  in-page section links; `scroll-padding-top` matched to the header height. The header is
  the answer to "where am I / where next" at every scroll position.
- **Floating back-to-top**: fixed bottom-right, **46px**, appears after 500px of scroll —
  the Console spec §4.8 pattern promoted to a default. Never a small link at the page foot.
- **Cards**: 12px radius, 18px padding, `--shadow`, one `<h2>` with kicker; explanatory prose
  lives in `<details class="help"><summary>How this works</summary>…` — visible when wanted,
  silent otherwise. This is the density valve: the working surface shows data, not essays.
- **Tables**: wrapped in `.tblwrap` (max-height ~430px, inner scroll, rounded border) so no
  table can swallow the page; sticky `<thead>`; zebra rows via `--surface-2`; hover row tint;
  key figure per row in `<b>`.
- **Stat tiles** for hero numbers (cash in hand, custody balances): 11px uppercase label over
  a 22–26px tabular value. A number that matters gets a tile, not a sentence.
- **Chips** (the "Today" strip): count-above-label tiles, min-width 120px; zero-state faded
  and inert. Every count is a link to its rows.
- **Buttons ≥ 38px tall** (fingers, not cursors); primary = accent, secondary = ghost.
- **Hindi**: small muted companions (`.hindi`) — kept per the owner ("don't need, don't mind").

## 4. The logo slot

The header's mark is one swappable element. Current: an inline SVG lockup (blue tile, bone +
cross). **The real logo lives in Canva** (`dr manoj logo.pdf`, design `DAHKiFFICC0`; also
`LOGO.psd`, `DAGcSJmvuus`) — the sandbox cannot reach Canva's export CDN, so the swap path is:
export PNG (transparent, ~480px) from Canva on any owner device → drop into the repo →
embedded as a data-URI in the header slot at the next page kit. One-element change.

## 5. Rollout

| Page | Status |
|---|---|
| Sanjeevni Hub (`/finance/approvals`) | **v1 applied (S187_H1b)** |
| Workbench · review · entry (medical) | migrate when next touched |
| Clinic entry/review · portal | migrate when next touched (portal keeps its dark tile grid — a launcher, not a worksheet; adopt tokens/type only) |
| Darpan's D2 mirror, reception returns (D-R), 360 strips | born in v1 |

*v1 · S187 · companion to the dataviz skill's reference palette · change via a versioned bump
of this doc, never silent divergence.*
