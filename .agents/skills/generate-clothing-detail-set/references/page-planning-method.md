# Page planning method

## Purpose

This method turns a garment folder into a sale-scope-aware page plan. It adds a
small planning vocabulary to the clothing truth contract; it does not replace
the project's reference-role map, paid gates, provider route, or garment QA.

The plan describes one sellable unit at a time. A folder may contain an upper
garment and trousers, but the visual pairing does not prove that the pieces are
sold as one set.

## Mandatory commercial-scope question

When a folder contains both a top and a bottom, ask before completing the truth
packet, writing final copy, or requesting any approval for paid generation:

> 上衣和裤子是分开卖，还是作为一个整套 SKU 卖？请明确回复：
> `sale_mode=separate_pairing`（分开卖）或 `sale_mode=true_set`（整套卖）。

Wait for the user's explicit choice. Never infer the answer from a directory
name, SKU numbering, a filename, a photographed outfit, matching colors, or a
model wearing both pieces. A response such as “都可以”“看着像套装” or “一起
拍” is not a sale-mode confirmation.

If the answer is absent or ambiguous, mark the plan `NEEDS_CONFIRMATION` and
stop before paid generation. Do not silently downgrade a paired folder to one
SKU or silently combine two SKUs into a set.

## Two sale modes

### `separate_pairing`

- Create two independent scopes: the complete top detail set first, then the
  complete trouser detail set.
- Each scope receives its own SKU/variant, truth rows, reference-role map,
  copy ledger, plan, paid-call estimate, QA verdicts, and manifest.
- A coordinated outfit page or image may be added after both individual sets,
  when the user requests it. Label it as styling/pairing context; it is not
  evidence that the two pieces are one purchase unit.
- A companion garment may appear in a styling image only when its role and
  availability are clearly stated. Never copy the companion's facts, size
  claims, price, or inventory into the other SKU's permanent assets.
- The top set must be completed or explicitly stopped before paid work starts
  on the trouser set. The pairing page is downstream and cannot reorder this
  sequence.

### `true_set`

- Plan one set SKU containing exactly the confirmed pieces and layer order.
- Use top and bottom front/back evidence as separate role inputs, while the
  buyer-facing page answers questions about the complete sellable set.
- Keep any inner layer, footwear, or props limited to what the evidence and
  sale scope confirm. A styling prop is not an included component.
- One set-level copy ledger, call count, QA report, and delivery manifest may
  cover the page, with component facts kept distinguishable inside it.

## Fact layers for planning

Keep three user-facing layers in the free plan, then map each line to the
project's evidence/status ledger:

1. `visible_facts`: directly inspectable in supplied product references.
2. `user_provided_facts`: explicit statements or approved documents supplied by
   the user.
3. `unconfirmed_facts`: plausible observations that cannot become a claim or
   prompt instruction until evidence is added.

The first two layers still require source paths and an approved status before
they enter paid prompts. `unconfirmed_facts` remain visible as open questions,
not as softened copy. A visible texture is not a confirmed fibre composition;
an outfit photograph is not a confirmed sale bundle.

## Screen-card contract

Every planned screen, including a deferred or blocked one, has these fields:

- `screen_id` and plain-language `type`;
- `headline` and `subcopy` (or an explicit “no text” state);
- `visual_direction` and target crop/aspect;
- `presentation_mode` for this screen, not merely a job-wide mode;
- `visual_family` (`product_truth_clean`, `evidence_layout`, `material_macro`,
  `designed_selling_point`, `information_graphic`, `worn_editorial`,
  `editorial_scene`, `lifestyle_scene`, or `brand_close`);
- `background_treatment` and shared `palette_id`;
- `facts_used` with the corresponding source/evidence ids;
- reference roles in upload order;
- `risk_notes`, including what would make the image `NEEDS_REFERENCE` or
  `REJECT`;
- sale scope (`separate_pairing` top/bottom or `true_set`);
- presentation mode (`product_only`, `ghost_mannequin`, `flat_lay`, `model`,
  or `none`) when relevant;
- generation status, expected call count, and master/derivative relation.
- long-page module template, order and 750px-grid regions (`x/y/width/height`);
- AI text-layout bounds, typography intent and rendering mode;
- annotation label, target and anchor coordinates when a callout is required.

`headline` and `subcopy` are planning fields, not permission to put arbitrary
text in an image. Paid prompts may use only rows from the approved copy ledger.
Default `text_rendering=ai_embedded_one_pass`; each generated image is a final
module containing its approved copy and annotations. The page compositor only
stacks modules and never adds copy.

## Small module library

Use these as planning roles, not a mandatory six-screen quota:

- **Hero / product presentation** — identify the sellable unit in a clean frame.
- **Use scene** — show a believable styling or daily context after the product
  truth is established.
- **Structure** — show visible construction, back evidence, closures, pockets,
  cuffs, hems, waistband, or layer order; never expose invented internals.
- **Detail close-up** — prove one named surface or construction feature with
  enough surrounding context to locate it.
- **Multi-scene** — optional later variation from an approved master; do not use
  it to replace required product evidence.
- **Detail grid / contact sheet** — optional derivative assembled from passed
  outputs; it is not automatically a new paid generation.

For complex clothing sets, retain the adaptive six-to-ten screen blueprint.
The module names only help the user read the plan; they do not override the
truth, evidence, sale-mode, or gate rules.

A complete set uses exactly one clean product-truth screen per sellable unit,
at least four visual families, at least one designed selling-point/information
screen, and at least one editorial/lifestyle/brand-close screen. Repeating
white seamless product-only frames creates a product evidence pack, not a
complete detail page. Keep the selected palette coherent across screens rather
than changing colors randomly.

## Optional product presentation

`ghost_mannequin` is a selectable product presentation, not a compulsory detail
screen and not a substitute for a model-fit proof. If selected, name it on the
plan as the main visual or as an optional baseline/reference asset. If it is not
selected, do not add a ghost image merely to fill the page.

For a ghost presentation, state whether the intended output is a warm solid
background, flat-lay, or another user-approved treatment. Do not assume an
alpha-transparent cutout. The image must preserve the garment's 3-D form and
sellable pieces while excluding human skin, face, hands, feet, body contours,
hangers, rails, watermarks, and unapproved text. It must not invent hidden
lining or internal structure.

If the user chooses ghost-first sampling, the selected main visual can be the
ghost presentation. The other two sample calls must still represent the set:
one designed selling-point/information screen and one editorial/lifestyle or
non-model scene. The remaining model work still waits for the existing
continuation gate. This is a choice of sample order, not a new exception to
paid-call accounting.

## Prompt assembly fields

Before a prompt is sent to the provider, assemble the following in order:

1. sale unit and sale mode;
2. per-screen presentation mode, visual family, background treatment, and screen purpose;
3. source-role header and exact upload order;
4. approved fixed facts with evidence ids;
5. visual direction, crop, light, camera, and integrated information layout;
6. approved Chinese copy or an explicit no-text instruction, rendered in the same call;
7. negative constraints, unknowns, and stop conditions;
8. output/master relationship and delivery requirements.

After the plan passes, run `build_page_blueprint.py`. A screen-card list is not
yet a finished page: the blueprint must establish module order, image regions,
AI text layout and annotation geometry before paid image generation.

For `separate_pairing`, repeat the sale-unit lock in every prompt. For
`true_set`, list every included component and forbid silent additions. For a
ghost prompt, explicitly state that it is a product presentation with no human
body; for a model prompt, keep model identity and garment references in their
separate roles.

## Human-readable handoff checks

Before handoff, review these groups in addition to the full QA contract:

- **Scope:** explicit sale mode, correct SKU/unit, and correct top-before-bottom
  sequence for `separate_pairing`.
- **Plan:** every screen has the card fields above, and no optional ghost
  presentation was mistaken for a required detail screen.
- **Prompt:** identity lock, sale-unit lock, allowed text, visible facts, and
  negative constraints are present and understandable.
- **Image:** product identity, key construction, silhouette, layer order, and
  copy remain truthful at full size and mobile size.
- **Delivery:** each unit has its own masters/derivatives, manifest, QA,
  provenance, rejected list, and paid-call record; a pairing asset is clearly
  contextual when it is not itself the sold unit.
