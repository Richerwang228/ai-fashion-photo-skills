# Garment-first prompt patterns

## Contents

- [Prompt contract](#prompt-contract)
- [Sale-unit lock](#sale-unit-lock)
- [Reference-role header](#reference-role-header)
- [Pattern A: product hero](#pattern-a-product-hero)
- [Pattern B: neutral worn master](#pattern-b-neutral-worn-master)
- [Pattern C: master-derived lifestyle](#pattern-c-master-derived-lifestyle)
- [Pattern D: evidence macro](#pattern-d-evidence-macro)
- [Pattern E: Chinese information module](#pattern-e-chinese-information-module)
- [Pattern F: no-model editorial replacement](#pattern-f-no-model-editorial-replacement)
- [Pattern G: optional ghost mannequin presentation](#pattern-g-optional-ghost-mannequin-presentation)
- [Repair and stop language](#repair-and-stop-language)
- [Adopted licensed structures](#adopted-licensed-structures)

## Prompt contract

Write production direction plus constraints, not a pile of aesthetic
adjectives. Put the fixed garment truth near the top and keep creative variables
after it. A prompt must state:

1. asset purpose and target crop;
2. sale unit and confirmed sale mode;
3. presentation mode and reference roles in upload order;
4. visual family, background treatment, and shared palette id for this screen;
5. fixed product facts and details that must remain unchanged;
6. model/pose/fit representation, if a model is present;
7. setting, light, camera, composition, and integrated information layout;
8. negative constraints and what the model must ignore;
9. text and delivery requirements.

Default every paid prompt to `TEXT RENDERING: ai_embedded_one_pass`. Ask GPT
Image 2 to complete the product image, exact approved Chinese, labels, arrows,
zoom explanation, and supplied table inside one final module image. Do not ask
for blank layout space. If no copy row is approved, explicitly require a
text-free module and forbid invented wording.

The active project provider uses GPT Image 2 through the existing
OpenAI-compatible image-provider skill. Do not paste candidate vendor commands,
provider names, API routes, or backend template IDs into a production prompt.

## Sale-unit lock

Place this short block near the top of every prompt and fill it from the
approved plan, never from a filename:

```text
SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: [product_only / ghost_mannequin / flat_lay / model]
VISUAL FAMILY: [one approved screen family]
BACKGROUND: [screen-specific treatment inside the shared palette]
PALETTE ID: [approved shared palette]
```

For `separate_pairing`, name either the top SKU or the trouser SKU and forbid
the other piece from becoming an included product. If the other piece appears
as styling context, label it as contextual and do not borrow its facts. For
`true_set`, list every confirmed included piece and layer order, then forbid
silent additions. A missing or ambiguous sale mode blocks the prompt.

## Reference-role header

Prepend this compact role declaration to every edit prompt, replacing paths and
roles with the actual files:

```text
Reference image 1 — MODEL_IDENTITY: inherit only the approved face, hair, body
build and proportions. Ignore its clothing, pose, background, accessories and
lighting.
Reference image 2 — TOP_FRONT or BOTTOM_FRONT: inherit the visible garment
color, silhouette, construction, layer order and details for this view.
Reference image 3 — INNER_LAYER or named detail: inherit only the stated layer
or feature and its location.
Reference image 4 — SILHOUETTE_STANDARD (only when the project standard
applies): inherit only the approved width, length and drape bounds. Do not
inherit its person, palette, material, shoes, accessories or scene.
The written order above is the upload order. If a role is absent, do not guess.
```

Keep the approved worn master as reference image 1 for every creative variant;
attach only the additional detail image required by the target frame. This
master-first rule prevents a new outfit reconstruction on every edit.

## Pattern A: product hero

Use for the clean product-first hero and mini-program cover candidate. The
presentation can be product-only, flat-lay, or the optional ghost mannequin
mode; name the choice explicitly.

```text
Create a product-first clothing hero for SKU [name/variant]. Purpose: clean
cover and long-detail master, not an advertisement.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: [product_only / ghost_mannequin / flat_lay]

FIXED PRODUCT FACTS (from approved references):
- [category/layer, exact visible color family and finish]
- [silhouette, length, fit, rise, drape]
- [collar/sleeve/cuff/waistband/hem]
- [pocket, zipper, button, drawstring, logo/mark counts and locations]
- included pieces: [only confirmed pieces]

Show the complete product, centered with breathing room and a natural contact
shadow. Use restrained studio light that preserves fabric texture and color.
Keep the camera at [eye-level/garment-level] with no wide-angle distortion.

DO NOT redesign, recolor, resize, add, remove or relocate any garment feature.
No invented logo, label, certification, review, price, discount, stock or
“缺货” wording. No unapproved accessories or background props. Keep the exact
SKU variant visible and do not turn a creative suggestion into a fact.
```

## Pattern B: neutral worn master

Use once per selected model group before any pose, scene, or editorial variant.

```text
Generate one neutral, full-body worn master of the approved model wearing the
exact [garment/set] in the supplied front references. Purpose: fit and garment
truth master for later edits.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: model

MODEL LOCK: one person; preserve identity-pack face, hair, body build and
proportions. Front-facing or a slight natural offset, relaxed stance, hands away
from pockets, waistband, zipper and hardware. Head through shoe soles in frame.

GARMENT LOCK: preserve category, layer order, color, material appearance,
silhouette, fit, length, pockets, closures, hardware, seams, hems and natural
garment-body tension. No invented features or marks.

SET AND CAMERA: warm white or light-grey studio, even product-readable light,
realistic floor contact shadow, eye-level full-body framing, no bag, scarf, coat,
furniture or large accessory.

If this product is the project's approved balanced extra-wide straight trouser,
keep width established below the waistband, two legs visibly separate, nearly
parallel upper-thigh-to-knee lines, subtle recovery below the knee,
upper-thigh width >= knee width >= hem width, and the hem breaking naturally
over half to two-thirds of the shoe. Do not create an A-line, flare, skirt-like
mass, low/drop crotch or merged legs.
```

## Pattern C: master-derived lifestyle

Use only after the neutral master passes QA and the chosen direction is
approved. Change one major variable at a time.

```text
Create a [lifestyle/editorial] variation from the approved worn master.
Purpose: [shopper question / organic WeChat moment / brand story].

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: model

AUTHORITATIVE MASTER: reference image 1 supplies the complete model identity
and worn outfit. Preserve face, hair, build, proportions, garment category,
layer order, color, fit, length, pockets, closures, seams, hems and drape. Use
reference image 2 only for [named feature] visible in this frame.

POSE AND VISIBILITY: [natural action], with hands and props away from [critical
garment areas]. Keep the hero garment readable and show [feature]. Do not use a
pose to hide fit tension or missing construction.

SETTING/LIGHT/CAMERA: [specific location and materials], [light direction and
quality], [lens feel and angle], [crop/aspect], clean copy-safe area at [place].
Props are contextual and not included with the purchase.

NEGATIVE CONSTRAINTS: no changed garment, new colorway, extra layer, fake logo,
third-party mark, body morphing, impossible drape, floating prop, unsupported
claim, price, discount, availability or inventory message. No text unless the
approved Chinese copy block below is present.
```

For a two-model request, replace “one person” with an explicitly separate image
group. A shared frame is a different confirmed deliverable, not a default.

## Pattern D: evidence macro

Use only for a named, source-supported detail. Macro is dimensional photography,
not a flat crop or an opportunity to invent quality.

```text
Create an evidence-led garment macro for [location and feature]. Purpose:
answer one material/construction question in the detail set.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: product_only or flat_lay

SOURCE LOCK: reference image [N] proves the exact location and shape of
[feature]. Inherit only what is visible: [base material if confirmed],
[construction], [surface finish], [thread/hardware/closure count], and what is
explicitly absent. Do not infer fiber, durability, comfort, certification or
performance.

PHOTOGRAPHY: dimensional 20–45 degree angle, shallow depth of field with the
named feature occupying about 60–80% of the frame, controlled side light,
natural shadow and accurate color. Keep enough surrounding context to prove
where the detail sits on the garment.

NEGATIVE CONSTRAINTS: no added stitch lines, buttons, engravings, product labels,
patterns, logos, unapproved text, extra hardware, mirrored geometry or unrelated detail.
```

## Pattern E: Chinese information module

Use for every text-bearing selling-point or information module. The default
workflow renders Chinese in the same GPT Image 2 call and does not add a
separate OCR service or local text overlay.

```text
Create one clothing information module for SKU [name], role [feature/fit/guide].
Preserve the exact garment from reference image [N]. Use the approved visual
direction [name] and integrate the text block into the final composition.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: [product_only / ghost_mannequin / flat_lay / model]

APPROVED CHINESE COPY (render exactly; do not rewrite, translate, add or remove):
标题：[exact title]
要点：[exact factual or clearly labelled creative lines]
标注：[only confirmed labels and units]

Use one language only. Keep Chinese characters, punctuation, line breaks and
units exactly as supplied. Do not display a color code, font name, placeholder,
“headline” label, fake rating, certification, price, discount, stock, “缺货” or
review. Do not turn a qualitative styling suggestion into a measurement.

The user is the final text reviewer. This image receives a normal visual check,
not a dedicated OCR gate. If the user identifies a text-only error, permit one
explicit paid correction; stop this text route if the same error remains twice.
```

If the module includes a size table, each numeric cell must trace to a supplied
approved table or measured record. If no such record exists, replace the table
with “测量位置 / 版型说明 / 穿搭建议” style qualitative guidance.

## Pattern F: no-model editorial replacement

Use when `model_count=0` for the screen that would otherwise communicate worn
mood or lifestyle. It is a final detail-page role, not a deferred placeholder.

```text
Create one non-model editorial product scene for the exact sellable garment.
Purpose: communicate brand mood and plausible styling context while preserving
the garment as the only sellable subject.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: flat_lay or floating_product_poster
VISUAL FAMILY: editorial_scene
BACKGROUND: [approved non-white brand-color flat lay / still-life spatial scene
/ restrained floating-product composition]
PALETTE ID: [same approved two-to-three-color palette as the detail set]

PRODUCT LOCK: preserve category, color, silhouette, length, construction,
pockets, closures, hardware, seams, hems and visible surface from the assigned
product references. Maintain natural gravity and credible contact shadows.

COMPOSITION: use negative space, controlled depth and no more than a few
contextual props. Props are not included in the purchase and must not cover an
identity-defining garment area.

EXCLUDE: no person, face, skin, hands, feet, body outline, invisible mannequin,
hanger, rail, second sellable garment, fake mark, unsupported claim, price,
discount, stock or urgency. Do not fall back to a plain white seamless catalog
frame; that role is already served by the single product-truth screen.
```

## Pattern G: optional ghost mannequin presentation

Use only when the user explicitly selects `PRESENTATION: ghost_mannequin`.
This is a product presentation or baseline reference, not a mandatory detail
screen and not a replacement for a model-fit proof.

```text
Create one product presentation of the exact sellable garment unit in a hidden
form / ghost-mannequin treatment. Purpose: [cover candidate or optional product
baseline], not a model image and not a technical cutaway.

SALE UNIT: [SKU / variant / included pieces]
SALE MODE: [separate_pairing or true_set]
PRESENTATION: ghost_mannequin

PRODUCT LOCK: preserve the supplied garment's category, layer order, color,
silhouette, length, waistband, pockets, closures, hardware, seams, hems and
visible surface. For a set, show only confirmed included pieces; for a separate
SKU, do not turn the companion garment into part of the product.

FORM AND SCENE: retain a natural three-dimensional worn shape on an invisible
form. Use [warm solid background / user-approved treatment], restrained light,
accurate scale, and a natural contact shadow. This is not an alpha-transparent
cutout unless the user separately requests and approves that output.

EXCLUDE: no human face, skin, hands, feet, body outline, hanger, rail,
watermark, fake label, unapproved text, hidden lining, invented internal
structure, extra accessory or unsupported claim. Do not use a pose or crop to
hide a missing product feature.
```

## Repair and stop language

Name the defect, source, and exact correction rather than saying “make it more
premium.” Examples:

- `Restore the left chest pocket to the two-panel shape shown in TOP_FRONT;
  previous output invented a single welt pocket.`
- `Keep the approved master as reference image 1; the last edit changed the
  trouser hem width and exposed the ankle.`
- `The requested size value has no source. Replace the number with a measuring
  guide and keep the route blocked for numerical claims.`

After two failures with the same structural fact, issue `STOP_CURRENT_ROUTE`.
Change the reference subset, camera, prompt role, or master strategy and request
authorization again; do not add a third near-identical paid call.

## Adopted licensed structures

- **Generative Media Skills** (`MIT`, commit `8c85352d5d75d4dcbe58480bd138e37b9742bab1`),
  `fashion-campaign-production/SKILL.md`: fixed-facts / creative-direction /
  negative-constraints scaffold and garment-specific prompt example, rewritten
  here in original wording.
- **ShopOS project skills** (`Apache-2.0` in the skill frontmatter),
  `AI 模特照/.agents/skills/{model-catalog,fashion-model-photography,
  garment-lifestyle-photography,macro-product-photography,
  product-tryon-visualization}/SKILL.md`: identity/master-first ordering,
  pose/lighting/macro fields, and no-guess close-up rules.
- **LinkFox** (`MIT`, commit `87750632f9bd538ac6a9989e3c9f6b00fc3c6949`),
  `.../references/types/{model-image,scene,selling-point,size}.md`: role-based
  image descriptions, layout labels, and a staged size-analysis idea. Its
  model/API calls and textgen templates are not copied or executed.
- **Claude Ads** (`MIT`, commit `669c7608ecb50dd95c941a71fa3ca0a1c0e40512`),
  `skills/ads-photoshoot/SKILL.md`: rights-cleared source confirmation,
  distinct production hypotheses, and human review before release.

All examples above are independently rebuilt patterns. No proprietary supplier
prompt, API request, or backend template is a runtime dependency.
