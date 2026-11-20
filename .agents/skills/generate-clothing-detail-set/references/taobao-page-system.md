# 淘宝式服装详情长页系统

## Contents

- [Two delivery layers](#two-delivery-layers)
- [Default mobile story](#default-mobile-story)
- [Module contract](#module-contract)
- [Generation versus composition](#generation-versus-composition)
- [Typography and annotation rules](#typography-and-annotation-rules)
- [No-model adaptation](#no-model-adaptation)
- [Completion test](#completion-test)

## Two delivery layers

Keep the product gallery and the long detail page separate.

- **Gallery:** clean hero, on-body/in-scale view, front/back, close detail,
  colour/SKU and optional video. It supports quick recognition and zoom.
- **Long detail page:** a 750px logical-width mobile story that explains the
  garment through ordered modules. It is not a vertical concatenation of
  unrelated posters.

Each generated product, model, macro or scene PNG is a finished detail module:
its approved Chinese, labels, arrows, zoom explanation and table are already
inside the image. A complete detail page exists after these modules pass QA and
are assembled according to the approved long-page blueprint.

## Default mobile story

Adapt six to ten modules while preserving the decision sequence:

1. **Identity/KV:** one truthful hero and one short positioning line.
2. **Fit or scale:** worn view, approved model, or a clearly labelled no-model
   alternative; explain what cannot be proven without a body.
3. **Front/back evidence:** two-up comparison or another supported angle.
4. **Construction feature:** one buyer-relevant feature with a detail inset,
   short label and callout line rendered by GPT Image 2 in the same module.
5. **Material proof:** macro plus surrounding context; do not infer fibre or
   performance.
6. **Colour/SKU or styling context:** include only confirmed variants and make
   companion garments contextual when sold separately.
7. **Size/fit guide:** supplied numeric table or qualitative fit/measuring
   guidance. Never generate numeric sizes from an image.
8. **Care/trust/brand close:** confirmed care/service facts or a restrained
   close. Do not fabricate reviews, guarantees or inventory.

The page may use one or two brand-colour families, but information density must
change by module. White or neutral evidence modules are useful; repeating the
same complete product on different decorative backgrounds is not.

## Module contract

Every module must declare:

- `id`, `template`, `buyer_question`, `height` and order;
- 750px-grid `regions` with `x/y/width/height`, fit mode and optional radius;
- source asset ids and the exact garment-reference lineage;
- AI `text_layers` specifications with exact copy, bounds, hierarchy and colour intent;
- `annotations` with label, target coordinates and label anchor when needed;
- fact ids, copy ids, unknowns, risk notes and QA status;
- `text_rendering=ai_embedded_one_pass` and the required visual text-review state.

Use `scripts/build_page_blueprint.py` to create the initial geometry. Edit the
JSON when the product needs a different module, not by asking the image model to
invent a new whole-page layout.

## Generation versus composition

### The image model must create

- faithful product masters and alternate views;
- approved-model worn masters and controlled scene variants;
- macro/detail photographs;
- backgrounds and editorial scenes;
- final Chinese title/body hierarchy, labels, leader lines, zoom circles and
  approved numeric tables in the same call;
- one complete module image ready to stack into the long page.

Use exact copy-ledger strings and only approved numeric JSON. A module with no
approved copy stays intentionally text-free; the model must not invent wording.

### The local compositor may create

- vertical module order and spacing;
- the 750px-wide long-page render;
- individual module slices and a render manifest.

It must not add, replace or cover Chinese copy, arrows, callouts, zoom circles,
tables or other information. Those belong to the paid one-pass module image.

Use `scripts/compose_detail_page.py`. Its input is the page blueprint plus an
asset-map JSON. It renders a 750px-wide full page and optional module slices.

The blueprint retains the exact copy and geometry as an audit specification,
not as a second overlay layer. Size tables may be rendered by AI only after the
exact approved rows, columns, units and numbers are injected into the prompt.

## Typography and annotation rules

- Body text is at least 22px on the 750px logical canvas; use 36px or larger for
  normal module headings.
- Maintain visible contrast and at least 32px mobile-safe separation between
  text and garment edges on the 750px canvas.
- Use one display and one body family at most. Keep hierarchy consistent across
  the page.
- Each information module answers one buyer question. Limit a callout module to
  three or four short labels; every line endpoint must land on the named detail.
- Use a detail inset when the full garment cannot prove the feature at mobile
  size. Do not label a feature that has no matching source evidence.
- Keep price, promotion and volatile inventory outside permanent masters unless
  the user approves a temporary channel-specific asset.

## No-model adaptation

A no-model page still needs fit/scale honesty. Use flat lay, ghost mannequin,
editorial still life or product scene for mood, but state that these do not prove
body fit. Add supported measurements, qualitative fit language, or a later
approved worn view instead of implying body proportions from a floating item.

Do not spend several modules on the same floating full garment. Reuse the passed
master as a source asset and allocate the page to front/back, construction,
macro, size/fit, colour, styling and care/trust questions.

## Completion test

Classify delivery as `complete_mobile_detail_page` only when all are true:

1. an approved page blueprint exists;
2. six to ten modules have assets and passed product-truth QA;
3. every text-bearing module contains AI-rendered approved copy/annotations and passed visual review;
4. an assembly-only 750px-wide full-page render exists;
5. individual module slices exist when the channel needs them;
6. the full page was inspected at 100% and at target mobile width;
7. the manifest records module geometry, source assets, copy/facts and verdicts.

Otherwise use `asset_pack_only`, `truth_master_pack`, or
`page_blueprint_needs_assets`. Attractive standalone posters do not satisfy this
completion test.
