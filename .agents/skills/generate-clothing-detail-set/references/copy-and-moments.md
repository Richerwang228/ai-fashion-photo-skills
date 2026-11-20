# Copy, image text, and WeChat moments

## Contents

- [Copy truth contract](#copy-truth-contract)
- [Copy ledger](#copy-ledger)
- [Image text contract](#image-text-contract)
- [Six natural moments per SKU](#six-natural-moments-per-sku)
- [Moment card template](#moment-card-template)
- [Forbidden shortcuts](#forbidden-shortcuts)
- [Adopted source structures](#adopted-source-structures)

## Copy truth contract

Copy makes product statements more prominent; it does not make them true. Keep
three layers separate:

- `FACT`: directly supported by the approved garment truth sheet or supplied
  source (for example, “front patch pocket” when its shape is visible).
- `CREATIVE`: a subjective mood, styling suggestion, or scene (“适合通勤层搭”)
  that does not claim a measured property.
- `PENDING`: a plausible statement that needs user confirmation.

Never write as fact that a garment is a particular fiber, waterproof, breathable,
slimming, sustainable, certified, made in a named country, endorsed, reviewed,
popular, discounted, available, or nearly sold out unless the user supplies and
approves the evidence. Do not invent a customer story, testimonial, rating,
press mention, award, or “best” claim.

The long-lived detail master may include a confirmed SKU/name, color name, size
range, and confirmed material. Price, discount, delivery, urgency, inventory,
“缺货”, and limited-time wording belong to a separate temporary asset and must
not enter the master or default image text.

## Copy ledger

Keep one row for every title, subtitle, callout, label, caption, and CTA:

| Field | Required value |
|---|---|
| `copy_id` | stable id tied to screen and locale |
| `text` | exact approved string; no model paraphrase |
| `status` | `FACT`, `CREATIVE`, or `PENDING` |
| `evidence` | source image/document or “creative wording” |
| `allowed_surface` | image text, detail body, WeChat moment, or temporary asset |
| `numeric` | yes/no; if yes, source and unit required |
| `reviewer` | user or named approver |
| `reviewed_at` | timestamp/version |
| `notes` | qualifiers, forbidden implication, or unresolved risk |

Only `FACT` rows with a numeric source may appear as numerical size or
measurement callouts. A `CREATIVE` row may describe a look or moment but must
not smuggle in an objective performance claim.

## Page text contract

Use `ai_embedded_one_pass` for approved Chinese text by default. Preserve the
ledger text, typography intent, safe bounds and annotation targets in the page
blueprint, then ask GPT Image 2 to render them together with the product visual
in the same module image. Prompt constraints should say:

- preserve characters, punctuation, line breaks, and units exactly;
- do not rewrite, translate, add, remove, or invent labels;
- do not show font names, color codes, placeholders, fake reviews, ratings,
  badges, certification, price, discount, inventory, or “缺货”;
- use enough contrast and safe spacing for mobile reading;
- finish labels, leader lines, zoom explanations and tables inside the image.

There is no dedicated OCR tool or per-character acceptance gate. Perform an
ordinary visual check and let the user make the final decision; one explicit
paid text correction is permitted. Do not silently cover AI text with a local
overlay. Do not treat a garment-structure or
numeric-size error as a text exception.

## Six natural moments per SKU

The default WeChat Moments package has six distinct, owner-voice posts per SKU.
They are organic posts for the shop owner's own circle, not paid advertising,
ad trafficking, audience targeting, or performance claims. Each post should feel
like a real note about choosing or wearing a garment; use one or two images from
the approved detail set and avoid a hard-sell cadence.

| # | Moment | Natural purpose | Recommended visual |
|---:|---|---|---|
| 1 | New arrival / first look | Share why the piece caught the owner's eye | Product hero or model hero with a short “刚到店” observation |
| 2 | Styling note | Show one believable outfit or layering idea | Model hero or lifestyle screen with unobstructed silhouette |
| 3 | Material/detail touch | Point to a visible weave, seam, pocket, or closure | Evidence macro or construction module |
| 4 | Try-on diary | Describe how the cut reads while moving or sitting | Fit/silhouette proof; no invented size or universal-fit claim |
| 5 | Shop-floor moment | Bring the item into a quiet store routine | Lifestyle/brand close with props that are clearly not included |
| 6 | Gentle invitation | Invite a question or a visit without pressure | Chosen hero/detail crop; no false scarcity, stock count, or discount |

Vary the opening, sentence rhythm, image role, and question. Do not publish all
six in one burst or turn them into a six-frame ad carousel. “自然” is a
production goal, not a claim about customer response.

## Moment card template

Create one card per post:

```text
SKU / moment id: [sku]-M[1..6]
Voice: first-person shop owner; conversational, specific, unforced
Approved fact(s): [copy_id and source]
Creative observation: [optional subjective styling note]
Natural owner version: [2–5 short sentences, no hard-sell language]
Short image caption: [one concise line, only approved facts]
Recommended image: [screen id / crop / why it fits]
Question or invitation: [optional soft question, no urgency]
Do not say: [unsupported material, performance, price, stock, review, claim]
```

Example (illustrative wording, not a product fact):

```text
M3 · material/detail
Natural owner version: “今天整理这件时又停在袖口看了好一会儿。近看能看到
细密的纹理，搭在薄针织外面不会抢戏。你们平时更喜欢看这种细节近照，还是上身
走动的效果？”
Short image caption: “袖口和纹理的近看。”
Recommended image: screen 5 macro, with no added fiber claim.
Do not say: “纯羊毛”“不起球”“耐穿” unless those facts are supplied.
```

For the six cards, include the natural owner version, a shorter image-caption
line, one recommended screen, and the forbidden implication list. A user may
replace any card before Gate 1; copy approval is not inferred from an earlier
SKU or a previous outfit.

## Forbidden shortcuts

- Do not label organic Moments as “广告投放”, “投流”, “转化素材”, or a paid
  campaign without a separate request and review.
- Do not show actual stock counts, “缺货”, restock promises, shipping urgency,
  discount, or price in the default six posts.
- Do not create fake comments, customer reviews, influencer quotes, stylist
  endorsements, or before/after body outcomes.
- Do not use a model's body to imply a numerical size or universal fit.
- Do not use generated Chinese text as evidence that a material or construction
  exists; the image must still trace to a reference role.
- Do not translate or strengthen a supplied claim. If a claim is qualified,
  keep the qualifier.

## Adopted source structures

- **Generative Media Skills** (`MIT`, commit `8c85352d5d75d4dcbe58480bd138e37b9742bab1`),
  `fashion-campaign-production/SKILL.md`: claim ledger, viewer promise,
  shopper-facing alt/copy purpose, and “creative choice cannot override fact.”
- **LinkFox** (`MIT`, commit `87750632f9bd538ac6a9989e3c9f6b00fc3c6949`),
  `.../references/maintainer/collection/S1-content-reasoning.md` and
  `.../references/types/selling-point.md`: distinct selling-point fields,
  non-repeating concepts, layout roles (概览/功能/品质/场景), and exact
  language handling, independently rewritten without its text-generation
  service or template prose.
- **Nexscope Amazon Skills** (`MIT`, commit `bdc556233805bbc3b5d8d865f3f3bd153864970f`),
  `amazon-a-plus-content/SKILL.md`: one message per module, feature-to-benefit
  organization, mobile-readable hierarchy, and approval of social proof; all
  unverified persuasion and performance claims are intentionally excluded here.
- **Project `CONTEXT.md`** (`深入调研skills/CONTEXT.md`): six owner-written
  WeChat moments per SKU, organic-only boundary, and separation from ad buying.

This document preserves template structure and safeguards, not supplier copy or
API behavior.
