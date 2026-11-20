# Product truth and reference contract

## Contents

- [Purpose and precedence](#purpose-and-precedence)
- [Evidence intake](#evidence-intake)
- [Truth table](#truth-table)
- [Reference roles](#reference-roles)
- [Silhouette and clothing-specific rules](#silhouette-and-clothing-specific-rules)
- [Facts, copy, and size gates](#facts-copy-and-size-gates)
- [Readiness decisions](#readiness-decisions)
- [Adopted source structures](#adopted-source-structures)

## Purpose and precedence

The garment is the source of truth. The customer must be able to recognize the
actual SKU, not an attractive redesign. Use this precedence order for every
screen and prompt:

1. User-supplied product photos, approved tech/spec sheets, and confirmed copy.
2. An approved neutral worn master for identity, fit, and continuity.
3. A project-approved silhouette reference when the garment category requires
   one. It controls only silhouette, volume, length, shoe coverage, and drape;
   it never supplies a person, color, fabric, top, shoes, accessories, or
   setting.
4. Creative direction: camera, light, setting, pose, palette, and mood.

If a lower-priority instruction conflicts with a higher-priority garment fact,
stop and ask for evidence. A model's plausible guess is not a product fact.

## Evidence intake

For an ordinary two-piece outfit, request four square, evenly lit, uncropped
images:

- `top_front`
- `top_back`
- `bottom_front`
- `bottom_back`

Separate trouser legs so the crotch and width curve are readable. Expose black
fabric enough to show seams and pocket edges without changing its color. Add
one contextual detail image only when a commercial feature is unclear: collar,
cuff, pocket, waistband, drawstring, closure, zipper, logo/mark, lining, hem,
or hardware. Use a macro only when the contextual image proves location but not
shape. Four to eight garment images is the normal range; a complex garment may
need up to ten.

Do not ask for a human try-on image. Do not infer a pattern, material, or
measurement from industry convention. A missing back image blocks a back-facing
deliverable but does not block a well-supported front master.

For every requested view, state one of:

- `GO`: the visible garment facts are sufficiently supported.
- `NEEDS_REFERENCE`: name the single minimum additional image or approved fact.
- `STOP`: the requested claim or view cannot be made truthful with the available
  evidence.

## Truth table

Keep one row per garment and one row for each commercially important detail.
Use only the following evidence states:

| Field | Values | Required discipline |
|---|---|---|
| Category/layer | top, bottom, outer, inner, set; confirmed/ambiguous/missing | Never swap a layer because it is stylistically convenient. |
| Color/finish | exact visible color family and surface finish | Do not turn a photo impression into a dye code or fiber claim. |
| Silhouette/fit | confirmed shape, looseness, rise, length, drape | Use the real photo; avoid guessed numerical ease. |
| Construction | collar, sleeve, cuff, waistband, hem, seams, lining | Count and locate only visible features. |
| Pockets/closures | count, side, opening, zipper/slider, hardware | Record deliberately absent details when useful. |
| Marks | logo, embroidery, label, print, or explicitly absent mark | Do not generate a readable mark from a vague hint. |
| Material | base, construction, surface finish | Mark `AMBIGUOUS` if the photo cannot distinguish cotton, wool, blend, etc. |
| Size data | user-provided table or measured data only | No number without a cited source and approval. |
| Availability | user-provided release status | Never turn a temporary status into an image claim. |

Use `CONFIRMED`, `AMBIGUOUS`, `MISSING`, and `NOT_APPLICABLE` in the saved
truth sheet. Preserve an uncertainty note beside every `AMBIGUOUS` or `MISSING`
field; do not silently promote it later.

## Reference roles

Before every paid edit, create a role map whose order exactly matches the
uploaded file order. A reference has one primary job:

| Order | Role | Inherit | Explicitly ignore |
|---:|---|---|---|
| 1 | `MODEL_IDENTITY` | approved face, hair, build, proportions | clothes, pose, background, accessories |
| 2 | `TOP_FRONT` / `BOTTOM_FRONT` | visible product construction for the target view | unrelated scene and styling |
| 3 | `INNER_LAYER` | only the confirmed layer shown under the product | invented layers |
| 4 | `DETAIL_<location>` | one named count/shape/position | all other regions |
| 5 | `SILHOUETTE_STANDARD` | approved width, length, and drape bounds | person, palette, material, shoes, scene |

For a back view, replace the garment role with `TOP_BACK` and/or `BOTTOM_BACK`
and retain the approved front master as the identity/continuity anchor. Do not
upload every available reference by default. Missing paths, mismatched order,
or unrelated details are a paid-call blocker.

## Silhouette and clothing-specific rules

When the product is labelled 阔腿裤、大阔版、超宽裤腿, use the project standard
and the approved A/B bounds. The target is a balanced extra-wide straight leg:

- width establishes immediately below the waistband;
- two legs remain visibly separate from the crotch;
- `上大腿宽度 ≥ 膝部宽度 ≥ 裤脚宽度`;
- outer seams are nearly parallel, with only a subtle recovery below the knee;
- full length covers about one-half to two-thirds of the shoe and makes a
  natural break.

Never let a silhouette reference override real waistband, drawstring, pockets,
seams, fabric, or color. Reject ordinary narrow straight legs, A-line or
flare, skirt-like mass, low/drop crotch, merged legs, or exposed ankles. The
retired hakama reference is not an allowed source or wording.

## Facts, copy, and size gates

Separate every statement into:

- `CONFIRMED_FACT`: supported by a source image or approved document.
- `CREATIVE_SUGGESTION`: pose, setting, mood, or subjective styling language.
- `NEEDS_CONFIRMATION`: plausible but unsupported wording.
- `PROHIBITED`: invented construction, material, certification, review, price,
  scarcity, availability, or customer outcome.

Numerical size or measurement graphics may ship only when the user supplied an
approved size table, measured sample, or other cited source. Otherwise replace
the number with a qualitative fit guide (where the hem falls, how to measure,
or a styling view) and label it as guidance. Never have the model infer a size
from a model's body or from “industry standard.”

Render approved Chinese headings, labels, tables and callouts in the same GPT
Image 2 module call by default. Pass one language and exact copy, forbid
rewriting or extra text, and inject every numeric table cell from its approved
source. There is no dedicated OCR gate or local text overlay. The user is the
final text reviewer. A text-only correction may be attempted once; it does not waive garment,
identity or numeric-fact QA.

Do not show real inventory, “缺货”, remaining units, urgency, ratings, reviews,
or endorsements in a long-lived detail set. A user-provided current price or
campaign note belongs in a separately approved temporary asset, never in the
platform-independent master.

## Readiness decisions

The truth gate is satisfied only when every planned screen has a source role,
an evidence state, and a clear allowed/blocked decision. A screen can be
planned while evidence is missing, but its paid generation must remain blocked.
When the same structural fact fails twice (for example, the left pocket shape
or trouser width curve), stop that prompt/edit route. Change the evidence set,
camera, or master strategy and request a new approval; do not spend on a third
near-identical attempt.

## Adopted source structures

These are independently re-authored from licensed research, not vendor API
instructions:

- **Generative Media Skills** (`MIT`, commit `8c85352d5d75d4dcbe58480bd138e37b9742bab1`),
  `.../ecommerce-product-imagery/SKILL.md` and
  `.../fashion-campaign-production/SKILL.md`: truth table, garment truth sheet,
  fixed-facts versus creative-direction split, and reference-role discipline.
- **Open Design** (`Apache-2.0`, commit `2523669517f1f508f630e918c86cd6ef4afdb725`),
  `skills/ecommerce-image-workflow/SKILL.md` and `references/checklist.md`:
  reference-required mode, identity anchors, and three evidence-backed slots,
  expanded here for clothing and the eight-screen contract.
- **Project `model-catalog`** (`AI 模特照/.agents/skills/model-catalog/SKILL.md`):
  four-view identity pack, neutral master, role map, and A/B wide-leg standard.

The commercial providers studied in the research workspace are not runtime
dependencies. This document keeps their useful evidence discipline while using
the existing project image provider only.
