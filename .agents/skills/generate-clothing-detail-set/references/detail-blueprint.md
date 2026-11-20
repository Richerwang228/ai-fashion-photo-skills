# Detail-set blueprint

## Contents

- [Delivery contract](#delivery-contract)
- [Sale scope and product presentation](#sale-scope-and-product-presentation)
- [Default eight-screen architecture](#default-eight-screen-architecture)
- [Six-to-ten screen adjustment](#six-to-ten-screen-adjustment)
- [Visual direction set](#visual-direction-set)
- [Model and continuity policy](#model-and-continuity-policy)
- [Platform-independent masters and exports](#platform-independent-masters-and-exports)
- [Two paid gates](#two-paid-gates)
- [Adopted source structures](#adopted-source-structures)

## Delivery contract

The unit of work is one sellable SKU, one verified garment truth packet, one
optional approved model identity, and a complete platform-independent image
asset set plus an editable mobile long-page composition. A folder containing both an upper garment and trousers is not a set until
the user explicitly confirms the sale mode. The default is eight visual
screens, adjustable to six through ten when evidence or the user's channel
requires it. Every default model-enabled set has two principal images:

1. **Product hero** — a clean, product-first image suitable for the mini-program
   cover after the first approval.
2. **Model hero** — an approved worn master that communicates silhouette and fit.

If the user chooses the product presentation as the mini-program cover, retain
any approved model hero in the detail set when model imagery is part of scope.
Never let a model image be the only proof of the garment. The selected main
visual is an explicit plan choice among `product_only`, optional
`ghost_mannequin`, `flat_lay`, and an approved model master; do not infer it or
insert a ghost image by default. A ghost presentation is a product baseline,
not a mandatory detail screen. If no model image is requested, replace the
model hero with a non-model editorial product scene and convert model-dependent
lifestyle roles to flat-lay, styled still life, spatial scene, or restrained
floating-product roles. Do not defer or delete the story function.

Generate masters with enough resolution and safe crop space for later exports;
do not generate a 750px platform crop as the source. A screen is a visual role,
not necessarily one file: one master can yield several channel derivatives
without re-generating the garment.

The eight roles below are coordinated long-page modules, not unrelated
posters. Build their layout specifications with `build_page_blueprint.py`,
generate each required final module with its approved Chinese content, then
assemble the page with `compose_detail_page.py`.

## Sale scope and product presentation

When a folder contains both a top and a bottom, ask and wait for exactly one of:

- `sale_mode=separate_pairing`: two independent sellable scopes. Complete the
  top detail set first, then the trouser detail set. A coordinated outfit page
  may follow as styling context, but it cannot replace either SKU's evidence.
- `sale_mode=true_set`: one set SKU containing the confirmed pieces and layer
  order. Keep the component reference roles separate inside the set plan.

Do not infer this choice from a filename, SKU numbering, matching colors, or a
photographed outfit. Missing or ambiguous sale mode is `NEEDS_CONFIRMATION` and
blocks paid planning. Every screen card and prompt carries the selected sale
unit so a companion garment cannot silently become part of a separate SKU.

Product presentation is a separate choice from screen architecture. The user
may select a clean product-only hero, a flat-lay, an optional ghost mannequin,
or a model hero. `ghost_mannequin` means a solid-background product presentation
with no human body, skin, hands, feet, hanger, rail, or unapproved text unless
the user requests another treatment; it is not assumed to be an alpha cutout.
It may be the selected main visual or a retained baseline/reference asset, but
it is not a required detail screen.

## Default eight-screen architecture

Use this sequence unless the user explicitly changes it. Each card must name the
source references, factual payload, intended crop, and risk before generation.

| # | Screen | Shopper question | Evidence and visual job |
|---:|---|---|---|
| 1 | Product presentation / clean main | What exactly am I buying? | Product-only, flat-lay, optional ghost mannequin, or another approved presentation; faithful color, construction, and natural shadow; no props or unapproved text. |
| 2 | Model hero / worn master | What does the complete look feel like? | One approved model, full body, neutral pose, unobstructed silhouette; this is the continuity anchor. |
| 3 | Fit and silhouette proof | Where does it sit and how does it fall? | Front, side, or controlled walk; show hem, rise, sleeve/shoulder, drape, and natural tension. Use numbers only when sourced. |
| 4 | Construction / back proof | What happens on the other side? | Back or detail-led view only when top/back or bottom/back references support it; show closures, pockets, collar, cuff, lining, or hem. |
| 5 | Material and macro | What can I see and feel? | One named fabric/finish/texture close-up from a supplied detail reference; do not infer fiber or handfeel. |
| 6 | Feature / function module | Which confirmed feature matters? | One approved selling point, such as pocket shape, drawstring, zipper, or seam; use a clear crop or callout space, not a new feature. |
| 7 | Fit guide or size module | How should I judge fit? | Real size table/measurements only if supplied; otherwise qualitative measuring/fit guidance with no fabricated values. |
| 8 | Lifestyle / brand close | How might I wear it? | Plausible context that keeps the garment readable; show a natural moment and restrained brand world, not a scarcity or endorsement claim. |

Across the set, use exactly one clean white or warm-white product-truth master,
then move into a coherent brand system: warm grey/deep brown/black-silver/paper
texture or another approved two-to-three-color palette. Use at least four
visual families, including a designed selling-point/information page and an
editorial/lifestyle/brand-close page. This is controlled variation, not random
background swapping.

Screens 1 and 2 are both mandatory by default when model imagery is in scope;
the presentation mode chosen for screen 1 is not automatically a separate
additional screen. If a set has a second model,
the model hero and downstream images remain separate identity groups; do not
place two models together unless that special image is explicitly approved.

## Six-to-ten screen adjustment

Reduce only by removing a redundant role, never by removing both heroes or
truth-critical evidence:

- **Six:** 1 product hero, 2 model hero/master, 3 fit proof, 4 construction/back,
  5 macro, 6 lifestyle. Fold the feature into construction and omit the size
  module when no source numbers exist.
- **Seven:** add either a feature module or a qualitative fit guide.
- **Eight:** use the default architecture above.
- **Nine:** split macro into fabric and hardware, or add a supported styling
  transition. Keep both distinct and evidence-backed.
- **Ten:** add one additional approved view (for example a rear trouser detail,
  layered look, or mobile-safe crop) only if it answers a different shopper
  question. Do not create a tenth screen merely to fill a quota.

The plan table should show screen id, role, source references, copy state,
aspect/crop, expected generation count, and a short failure risk. It must also
carry `headline`, `subcopy` (or no-text), `visual_direction`, `facts_used`,
sale scope, per-screen presentation mode, `visual_family`,
`background_treatment`, `palette_id`, and `risk_notes`; see
`references/page-planning-method.md`. Similar views must be merged before the
user approves a paid count.

## Visual direction set

Before the first paid call, offer at most five materially different directions.
Each direction is a reusable art hypothesis, not a background swap. A direction
card contains:

- name and role (product-real, quiet brand editorial, natural lifestyle,
  high-conversion feature, or seasonal story);
- the modules it can serve and the garment feature it reveals;
- model/pose, environment, light, camera language, palette, and negative space;
- expected number of images and crop families;
- fit, text, identity, rights, and obstruction risks;
- why this direction fits the confirmed garment and brand evidence;
- whether it is suitable for an organic WeChat post (never imply paid ads);
- its composability with other directions (which master/detail roles may be
  shared, which combinations would look repetitive, and which must stay
  separate to preserve garment or model continuity).

Merge concepts that differ only by wall color, lens adjective, or one prop. A
direction must remain clothing-first: styling, set, and copy support the product
instead of concealing it. Keep “high-conversion” as an internal module role,
not a promise of sales performance.

## Model and continuity policy

Default to one approved AI model identity pack. Use the project's four-view pack
for identity only and create one neutral full-body worn master before any
creative variants. Lock face, hair, body build, proportions, garment category,
layer order, color, fit, length, pockets, closures, hardware, seams, and hems in
every master-derived prompt.

The user may choose two models before the first paid gate. In that case, create
two independent image groups and masters, with an explicit count for each. A
two-model image is a separate, higher-risk deliverable and is never implied by
the choice of two groups. Do not invent a new identity for each screen.

## Platform-independent masters and exports

Keep a master directory containing:

- `00_服装真值清单.md`
- product hero master and approved model worn master;
- optional back master, macro source crops, copy ledger, blueprint, and QA report;
- reference-role map and generation/provenance records.

Derivatives are named by SKU, role, aspect, locale, and version. Export product
hero, model hero, detail modules, and WeChat crops from the approved master.
Each derivative inherits the master fact lock; a crop may not hide a failed
closure, change a color, or imply a different SKU. Platform rules are volatile,
so verify the target mini-program or channel at delivery time instead of
hard-coding marketplace rules into the master.

## Two paid gates

Paid calls are explicit, counted, and never silently retried.

### Gate 1 — specification and three-call sample authorization

Before any paid generation, show:

- the confirmed/ambiguous/missing garment truth sheet;
- the explicit `sale_mode` and, for `separate_pairing`, the top-first/bottom-second scope order;
- reference-role map and exact uploaded order;
- selected direction(s), default eight-screen blueprint, and copy ledger;
- model choice (one by default, or two independent groups);
- mini-program cover/presentation choice (product-only, optional ghost mannequin,
  flat-lay, or model); any other approved hero remains in the complete detail
  set and is not discarded;
- exact sample outputs, output path, and expected paid-call count;
- the project provider/model and any indeterminate-call warning.

After approval, spend exactly three basic calls: **one explicitly selected
main-visual module, one construction/macro final module, and one
editorial/lifestyle final module**. For `model_count=0`, the third call is a non-model
flat-lay, still-life, spatial, or floating-product scene. The sample may
use the approved model master, product-only hero, or optional ghost mannequin;
the choice must be named in the plan. Place the three assets into a free
assembly-only sample-page render; its modules already contain copy and callouts, so do not count that
render as a paid call. Any other hero, optional
presentation, and second-model master wait for Gate 2.

### Gate 2 — continuation authorization

Present the inspected three-call sample, the two local detail previews, and
product-truth/human-integrity verdicts. The user must explicitly approve the
remaining screen list, exact count, and any correction calls before the rest of
the set is generated. The continuation count must name model groups: one model
means the approved first master plus the remaining hero/details; two models
means the second independent neutral master and its approved image group are
added explicitly. The second hero and second-model master are paid only after
this gate. A failed request is not silently re-submitted: a connection drop is
indeterminate and must be checked against provider consumption first.

Use this call-accounting table when presenting Gate 2:

| Selected presentation/model use | Gate 1 main visual | Gate 2 master calls before remaining details |
|---|---|---|
| No model; product-only or ghost selected | selected product presentation | none; generate only any user-approved remaining detail roles |
| One model | model 1 neutral worn master | independent product hero (the second hero) |
| Two models | model 1 neutral worn master | independent product hero + model 2 neutral worn master; keep each model's group separate |

Then add the exact remaining detail screens and any explicitly approved text-only
correction calls. Local previews never enter the paid-call count.

If the same structural fact fails twice, stop that route even if the second paid
gate was granted. Offer a changed evidence subset, camera, or master strategy;
resume only after a new exact approval.

## Adopted source structures

- **Generative Media Skills** (`MIT`, commit `8c85352d5d75d4dcbe58480bd138e37b9742bab1`),
  `fashion-campaign-production/SKILL.md`: shot grammar (world, full look, fit,
  macro, fabric behavior, styling, social hook, product-safe frame) and a
  truth-first campaign packet.
- **LinkFox** (`MIT`, commit `87750632f9bd538ac6a9989e3c9f6b00fc3c6949`),
  `.../references/maintainer/collection/{S0-scene-routing,S1-content-reasoning,S2-plan-confirm}.md`:
  staged route → content reasoning → user plan confirmation. The original
  provider dispatch, backend templates, and default counts are not used.
- **Open Design** (`Apache-2.0`, commit `2523669517f1f508f630e918c86cd6ef4afdb725`),
  `skills/ecommerce-image-workflow/SKILL.md`: compact slot planning, identity
  lock, and platform-independent manifest idea, adapted from three slots to a
  clothing-first eight-screen architecture with dual heroes.
- **Nexscope Amazon Skills** (`MIT`, commit `bdc556233805bbc3b5d8d865f3f3bd153864970f`),
  `amazon-product-photography/SKILL.md`: separate main-image compliance from
  secondary persuasion and use one shopper question per image.

No candidate commercial API or CLI is part of the runtime. Only the existing
project image provider and approved specialist skills may execute generation.
