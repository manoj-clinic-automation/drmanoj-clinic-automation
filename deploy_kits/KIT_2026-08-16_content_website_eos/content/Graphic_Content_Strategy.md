# Graphic Content Strategy — Dr. Manoj Agarwal Clinic
**Scope:** every visual the content system produces — blog figures, animations, Shorts frames, social kits, print/QR. **Method:** researched (2026 tool landscape), then a Knee-OA pilot to learn from before scaling. **Owner:** Dr. Agarwal (accuracy gate) + Claude (briefs, refinement guidance) + Canva Pro (production home).

---

## 1. Principles (from research + our rules)

1. **AI drafts, humans correct.** Research is unambiguous: the winning workflow is a strong AI first draft inside an *editable correction layer* — the correction loop matters more than the generator. Our correction layer is **Canva Pro** (already owned).
2. **The anatomy gate is non-negotiable.** Plausible-but-wrong anatomy is the specific known failure mode of AI medical images. Every anatomical visual passes the doctor's checklist (§6) before publish. Non-anatomical visuals (icons, metaphors, comparisons) skip the gate — which is why we deliberately design many visuals as metaphors (the sciatica "switchboard") or tables.
3. **Never generate text inside AI images.** AI renders garbled labels. Rule: generate clean *unlabelled* art → add ALL labels, captions and Hindi text in Canva. This one rule eliminates 80% of AI-image embarrassments.
4. **Consistency beats beauty.** A recognisable house style across 14 blogs builds brand memory. Locked tokens below.
5. **No new subscriptions to start.** Canva Pro covers refinement, tables, icon strips, animation and resizing. AI drafting uses free/cheap generator tiers. Specialist tools (BioRender ~$35/mo) only if the pilot proves AI+Canva can't deliver anatomy quality.
6. **Every asset earns its production cost** — mapped to a placement, a channel and a UTM before it's made.

## 2. Locked visual system (house style)

- **Colours:** Primary blue **#1565C0** · accent green **#43A047** · alert red **#D32F2F** (red-flag assets only) · warm neutral background **#F7F9FC** · text **#1A2B3C**.
- **Typography (Canva):** Headings **Poppins SemiBold** · body **Open Sans** · Hindi **Noto Sans Devanagari** (renders cleanly at small sizes).
- **Brand frame:** logo top-left · "Dr. Manoj Agarwal — 30 Years of Excellence" footer strip · short-link chip bottom-right on social exports.
- **Illustration style token (paste in every AI prompt):** *"flat modern medical-education illustration, clean vector look, soft blue and green palette, white background, no text, no labels, no photorealism, calm and reassuring, Indian adult figures where people appear"*.
- **People:** middle-aged Indian adults, everyday clothing, respectful and dignified — never distressed faces, never graphic pathology.
- **Red-flag assets:** the ONLY place alert red is used — instant visual grammar: red = act now.

## 3. Asset taxonomy → tool routing

| Type | Examples | Draft tool | Finish | Anatomy gate |
|---|---|---|---|---|
| A. Anatomy explainers | knee cross-section, spine segment | AI generator (no-text rule) | Canva labels/frame | **YES** |
| B. Comparison tables | OA vs gout vs RA | — (skip AI) | Canva direct | No |
| C. Icon strips | red flags, start-today | — | Canva icon library | No |
| D. Exercise panels | quads set, isometrics, nerve glides | AI (figure poses) or Canva people-illustration assets | Canva captions | Poses: doctor sanity-check |
| E. Metaphor visuals | switchboard, 1kg=4kg | AI or Canva | Canva | No (by design) |
| F. Animations (≤15s loops) | joint-space narrowing, bed-rest vs movement | Canva Animate on the static layers (preferred) or AI-video tool | Canva end-frame | If anatomical: YES |
| G. Long video | YouTube explainers | HeyGen avatar + Sarvam Bulbul V3 VO | VN edit + Canva intro/outro | Script already doctor-approved |
| H. Shorts/Reels | 3 per blog | Cut from G + Canva frames | VN captions | Inherited |
| I. Social carousels | 5–7 slides per blog | — | Canva direct from blog figures | Inherited |
| J. Print/QR | posters, advice sheets | — | Canva direct | Inherited |

**Reading of the table:** only rows A, D, F ever touch an AI generator; nearly half the library is Canva-direct — faster, zero hallucination risk, and consistent by construction.

## 4. AI generator choice (researched, pragmatic)

- **Default drafting:** any current strong general model via its free/cheap tier — FLUX-family models currently lead for medical-style illustration quality; Canva's built-in Magic Media is acceptable for simple scenes and keeps everything in one tool.
- **The no-text rule applies everywhere** (§1.3).
- **Anatomy fallback ladder** if a draft fails the gate twice: (1) regenerate with corrective prompt → (2) build from **Canva's labelled medical illustration assets** (searchable library — knee joint, spine, nerve figures exist) → (3) free community scientific libraries (SciDraw-type) → (4) only then consider a BioRender month. The pilot (§8) tells us how far down this ladder real work lands.

## 5. Production pipeline (every asset, 7 steps)

1. **Brief** — from the blog's Media Index (already written, paste-ready).
2. **Draft** — AI generation (rows A/D/F) or straight to Canva (B/C/E/I/J). 2–4 candidates, pick one.
3. **Correct & compose in Canva** — brand frame, colours, crop; fix drafting flaws.
4. **Label** — all text added in Canva: English labels, Hindi captions, leader lines.
5. **Gate** — doctor checklist (§6) for anatomical assets; WhatsApp preview → "ok" reply is sufficient record.
6. **Export** — Magic Resize: 1200×675 (blog) · 1080×1080 (WABA/social) · 1080×1920 (story/Shorts frame). WebP for web where possible.
7. **File & register** — Drive: `Blog Drafts/<Blog>/media/` · name `IMG-B2-1_v2.png` · one line in the Asset Register sheet (asset ID, status checkbox from the Media Index, file link).

## 6. Doctor's anatomy checklist (the gate)

☐ Correct bones/structures present — nothing extra, nothing missing ☐ Joint space / disc space plausible for the stage shown ☐ Nerve/vessel paths anatomically sensible ☐ Left/right and view (front/side/rear) correct and consistent with the caption ☐ Pathology shown matches the text (e.g., narrowing not erosion) ☐ Labels point to the right structures ☐ Nothing frightening or graphic. **Fail any → fallback ladder §4.**

## 7. Prompt playbook (for the AI-agent briefs)

- **Skeleton:** [style token §2] + [subject & view] + [pathology/feature to show] + [composition: side-by-side / single / 3-panel] + ["no text, no labels"].
- **Corrective iteration:** name the error explicitly ("the femur and tibia must be separated by a visible gap; do not fuse the bones").
- **Consistency:** reuse the exact style token every time; where the tool supports reference images, seed with an approved prior asset.
- **Negative habits:** never ask for text, numbers, arrows (added in Canva); never "realistic surgery/blood"; never real-patient likeness. Never present generated art as a real X-ray or patient image — schematic only, always.

## 8. Pilot: Knee OA — the learning build (do this before scaling)

Produce Blog 01's set in this exact order, logging time and gate-failures per asset:
1. **IMG-03 comparison table** (Canva-direct — warm-up, zero risk)
2. **IMG-04 red-flags strip** (Canva-direct, icon grammar established)
3. **IMG-02 exercise panel** (first AI draft — poses easy, low gate risk)
4. **IMG-01 healthy-vs-OA knee** (the real test: anatomy + gate + label pass)
5. **ANI-02 1kg=4kg** (Canva Animate on simple shapes — metaphor, no gate)
6. **ANI-01 joint-space narrowing** (anatomical animation — hardest; attempt Canva Animate layering of IMG-01 art before any AI-video tool)
**Pilot outputs:** time-per-asset-type · where on the fallback ladder anatomy landed · one refined prompt token set → written back into this strategy → THEN batch-produce Batch 1's nine statics + four animations in one Canva session.

## 9. Cadence & learning loop

- **Batch production:** one Canva session per blog-batch (research shows tool-switching is the hidden cost).
- **Measure:** GA4 scroll-depth on figure-heavy sections; social insights per Shorts topic; WABA link-tap by condition. Quarterly: double down on the visual types that earn attention, drop what doesn't.
- **Register as single source of truth:** the Media Index checkboxes + Drive register — no asset exists unless registered.

## 10. What is explicitly out of scope (for now)

Custom 3D/animation studios · BioRender subscription (until pilot says otherwise) · stock-photo realism (off-brand and legally fussy) · AI-generated "X-ray-look" images (never — schematic only, per research and ethics).
