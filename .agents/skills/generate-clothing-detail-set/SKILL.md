---
name: generate-clothing-detail-set
description: Plan, generate, assemble, review, and package a complete mobile clothing product-detail long page from real garment references. GPT Image 2 creates every final module in one pass, including approved Chinese copy, labels, callouts, zoom explanations, and tables; the local compositor only stacks finished modules. Use for tops, trousers, coordinated sets, and outerwear when the user asks for 淘宝商品详情页、商品详情长图、详情页套图、商品主图、模特上身图、卖点图、细节图、尺码或版型说明、营销文案、店主朋友圈内容, or any stage of that paid-call-gated workflow.
---

# 终极服装商品详情套图

Create one evidence-backed commercial image system for one sellable clothing
SKU. A folder containing a top and bottom may expand to two sequential SKU
scopes only after the user confirms the sale mode. Orchestrate the project's
existing garment, model, photography, QA, and provider skills; do not replace
them or route work through a researched vendor API.

## Read the relevant resources

Read these files before planning a full set:

- `references/product-truth.md` for evidence status, garment facts, sizing, and claims.
- `references/detail-blueprint.md` for visual directions, the adaptive 6-10 slice story, and two approval gates.
- `references/page-planning-method.md` for sale-mode confirmation, screen-card fields, optional product presentation, and the page module vocabulary.
- `references/taobao-page-system.md` for the gallery/long-page distinction, AI-rendered module contract, assembly-only composition, and the completion test.
- `references/prompt-patterns.md` before writing any image prompt.
- `references/copy-and-moments.md` when the request includes detail-page copy or shop-owner Moments content.
- `references/qa-and-delivery.md` before accepting or packaging outputs.
- `references/source-provenance.md` only when auditing why a rule or prompt pattern exists.

For a single requested stage, read only the resources that govern that stage, but retain the same truth and paid-call gates.

## Reuse the project capabilities

Resolve and read the active project copies of these skills when available:

- garment capture sufficiency: standalone `garment-reference-capture` when installed, otherwise Stage 2 of `model-catalog`;
- garment facts and styling: `product-analysis-styling`;
- model selection and master creation: `model-catalog` and `product-tryon-visualization`;
- garment and human acceptance: standalone `garment-fidelity-qa` when installed, otherwise Stage 7 of `model-catalog`;
- studio/editorial and lifestyle variants: `fashion-model-photography` and `garment-lifestyle-photography`;
- detail evidence: `macro-product-photography`;
- brand direction (optional, not shipped here): `brand-consistent-visuals` when installed;
- transport: `openai-compatible-image-provider`, which is pinned to the verified Right.codes asynchronous client.

Resolve the two documented fallbacks above before declaring a capture or QA capability missing. If another required capability is missing, stop and identify it. Never silently install or invoke Higgsfield, Linkfox, MuAPI, fal.ai, EachLabs, or another researched provider.

## Core invariants

1. Treat the sellable SKU and supplied garment references as visual truth.
2. Keep confirmed facts, creative recommendations, and unknowns separate.
3. Do not invent material composition, measurements, performance, origin, certification, price, discount, stock, sales, reviews, or scarcity.
4. Do not expose real inventory counts or customer-facing `缺货` language.
5. Use exact reference roles. A model reference supplies identity only; a garment reference supplies only its visible view and details; a scene reference supplies environment only; a layout reference supplies composition only.
6. Create an approved neutral worn master before creative model variants. Use that master for later pose, scene, and lighting edits.
7. Change one major creative variable per paid edit when practical.
8. Default to `text_rendering=ai_embedded_one_pass`. GPT Image 2 renders each final module's approved Chinese copy, labels, callouts, zoom explanations, and supplied numeric table in the same image call. Keep the user as final copy reviewer and do not add a dedicated OCR gate.
9. Preserve high-resolution, platform-independent masters. Export WeChat Mini Program and shop-owner Moments derivatives without regenerating the garment.
10. Do not run third-party source scripts from the research workspace.
11. Never infer whether a top and bottom are sold separately or as one set. A paired folder requires an explicit `sale_mode=separate_pairing` or `sale_mode=true_set` answer before the plan advances.
12. `ghost_mannequin` is an optional product-presentation mode, not a mandatory detail screen. Generate or retain it only when the user selects it.
13. A clean white product image is a reusable truth master, not a complete ecommerce detail set. A complete 6-10 screen set must combine one product-truth screen with designed information/selling-point treatment and an editorial, lifestyle, or brand-close screen.
14. Presentation is selected per screen. A job-level `presentation.mode` is only a legacy fallback and must never flatten every screen into the same white-background treatment.
15. Each generated PNG is a finished detail module, not the whole page. A complete delivery requires an approved 750px logical-width blueprint, AI-embedded module text/annotations, local vertical assembly with no added text, a full-page render, module slices when needed, and mobile visual QA.

## Workflow

### 1. Resolve the SKU and evidence

Resolve the exact garment directory, SKU/variant, requested channels, and
existing approved assets. Inspect only that scope. If the folder contains both
a top and a bottom, ask and wait for the exact commercial-scope answer from
`references/page-planning-method.md` before treating the images as a set or
writing a paid-ready plan.

The required question is:

> 上衣和裤子是分开卖，还是作为一个整套 SKU 卖？请回复
> `sale_mode=separate_pairing` 或 `sale_mode=true_set`。

Do not infer sale mode from filenames, SKU numbering, matching visuals, or a
model wearing both pieces. If the answer is missing or ambiguous, stop with
`NEEDS_CONFIRMATION`; do not request a paid-call approval.

Require at minimum:

- a front and back reference for each top, trouser, or outerwear piece;
- four references for a coordinated top-and-bottom set: top front/back and bottom front/back;
- the smallest additional detail references needed for identity-defining pockets, zippers, hardware, waistband, drawstring, logo, pattern, cuffs, seams, hems, lining, or fabric texture;
- one or more approved model identity packs when model images are requested.

Allow a front-only deliverable when front facts are sufficient, but block any back deliverable without back evidence. Do not pay for a view whose identity-defining facts remain missing or ambiguous.

### 2. Build the product truth package

Create a garment truth record with source and status for category, color, material observation, silhouette, fit, length, construction, distinctive details, layer order, variant, sizing, confirmed claims, unknowns, and prohibited inventions. Present the free plan in three readable layers—`visible_facts`, `user_provided_facts`, and `unconfirmed_facts`—then map each line to the full evidence/status ledger. An unconfirmed observation remains a blocked/open question.

Use `scripts/build_plan.py` when available to validate the job and persist the initial state. A missing real size chart must replace the numeric size module with fit, ease, measuring-position, or styling guidance. Never infer S/M/L/XL values or weight-based fit advice from an image.

### 3. Offer visual directions

Offer up to five materially different directions. Prefer roles such as:

- product-truth studio;
- brand lookbook;
- natural lifestyle;
- conversion-focused detail and selling points;
- seasonal campaign.

For each direction, state applicable modules, product/brand fit, scene and lighting, palette, obstruction or distortion risk, estimated paid image count, Moments suitability, and compatible combinations. Merge near-duplicates rather than filling a quota.

### 4. Plan the complete long page

Keep gallery assets separate from the long detail page. Default to an adaptive
eight-module mobile story; use six to ten modules according to product
complexity and evidence. Each module must answer a different buyer question.
Include, adapt, or omit:

1. product identity and independent product hero;
2. approved-model hero and overall silhouette;
3. front/back or useful multi-angle fit evidence;
4. fabric and surface detail;
5. construction such as pockets, zippers, hardware, seams, waistband, or hems;
6. styling or plausible lifestyle use;
7. verified sizing, fit guidance, target wearer, or scenario guidance;
8. brand close and next action.

Plan the product presentation and model roles separately. The user selects the
Mini Program cover/main visual before paid generation; keep any other approved
hero in the detail set. `product_only`, `ghost_mannequin`, `flat_lay`, and
`model` are presentation choices, not automatic extra screens. A ghost
mannequin image is optional product baseline material and must not be inserted
as a mandatory detail slot merely because the product is clothing.

Give every screen its own `presentation_mode`, `visual_family`,
`background_treatment`, and `palette_id`. Keep one coherent two-to-three-color
brand palette across the set, while varying the visual function: clean product
truth, evidence layout, material macro, designed selling point/information,
editorial or lifestyle scene, and brand close. Do not create random background
changes, but do not repeat the same white seamless frame across the story.

For `sale_mode=true_set`, plan one set SKU and one complete set detail package,
with top/bottom references kept as separate evidence roles. For
`sale_mode=separate_pairing`, plan two independent packages and generate the
complete top package first, then the complete trouser package. A coordinated
outfit page may follow both packages as contextual styling; it is not a
replacement for either SKU's product evidence.

If the user explicitly opts out of model imagery, replace the model hero with a
billable non-model editorial product scene and replace model-dependent lifestyle
roles with flat-lay, styled still life, spatial product scene, or restrained
floating product poster roles. These replacements must use a non-white brand
background and preserve the original shopper question. Do not merely defer or
delete the missing model pages. If model imagery was requested but no identity
was approved, keep those model slots blocked instead of silently converting
the request.

Default to one approved model. Allow two when selected before the first paid gate; create a separate worn master and image group for each. Treat a two-person image as a separate, explicitly approved high-risk deliverable.

Write exact Chinese copy, the page narrative, the image slots, reference roles,
aspect ratios, master/derivative relationships, output filenames, and risk
notes. Every screen card must also state `headline`, `subcopy` (or no-text),
`visual_direction`, `presentation_mode`, `visual_family`,
`background_treatment`, `palette_id`, `facts_used`, and `risk_notes`; see
`references/page-planning-method.md`. Do not put volatile price, discount, or
inventory in permanent detail masters. Treat campaign price art as a separate
temporary asset.

Run `scripts/build_page_blueprint.py` after the plan passes. For
`separate_pairing`, build one page blueprint with `--work-unit top`, finish or
stop it, then build the bottom page. Review the ordered 750px wireframe before
paid generation. Every module must contain regions, AI text-layout bounds,
annotation targets when applicable, source roles and a buyer question. Do not
approve a list of independent 4:5 posters as the page blueprint.

### 5. Prepare marketing and Moments copy

Create detail-page marketing copy from approved facts and clearly labeled creative recommendations. For each SKU, prepare six natural shop-owner Moments entries:

1. new arrival or selection reason;
2. styling idea;
3. fabric, silhouette, or construction observation;
4. wearer or scenario guidance;
5. genuine store or product-preparation daily context;
6. one light-sales entry using only a gentle question, visit invitation, or purchase invitation—without price, discount, inventory, or urgency.

For each entry provide a natural shop-owner version, a short image-caption version, recommended images, and hard-sell phrases to avoid. Do not create paid-ad targeting, budgets, posting automation, fake customer stories, or fabricated personal life.

If the user supplies a current price or campaign term, put it in a separately approved temporary sales post or temporary image asset with an expiry/review note. Never merge it into the default six Moments entries or the permanent detail masters.

### 6. First approval gate: approve the free plan

Before any paid image request, show:

- the reference-role map and unresolved evidence;
- the confirmed sale mode and per-SKU scope (top-first/bottom-second when the mode is `separate_pairing`);
- the product truth package and copy fact status;
- up to five visual directions and the selected combination;
- the 6-10 slice blueprint, selected product presentation (including optional ghost mannequin), and any model hero;
- the 750px mobile long-page wireframe, module order, grids, exact in-image text, callouts, and which final modules still require paid generation;
- selected model count and requested views;
- exact marketing and Moments copy direction;
- planned outputs, estimated paid image calls, and possible one-call Chinese-text correction allowance.

Stop and obtain approval. Do not treat prior approval of another SKU or stage as approval.

### 7. Generate and review the sample package

Read the active provider skill immediately before generation. Use the project's configured OpenAI-compatible provider and explicit reference-role labels.

Render each approved sample slot with `scripts/build_prompt.py` when available and review the resulting plain text before any provider call. The script must remain a prompt builder only; it does not authorize payment, upload references, or call the provider.

Generate only three representative **finished detail modules**:

1. one selected product-truth or worn main-visual master;
2. one construction/macro module with its approved Chinese callout rendered in the same call;
3. one editorial/lifestyle asset, using a non-model scene when `model_count=0`;
4. a free sample-page assembly using `scripts/compose_detail_page.py`, stacking the three already finished modules without adding text or callouts.

The other hero, any second model master, optional product presentation, and all
remaining variants stay planned but unpaid until the second gate unless the
approved sample explicitly selected them. The ordinary sample therefore
estimates three paid image calls before any explicitly approved text correction.

Run garment-fidelity QA after every paid image. Reject wrong category, silhouette, color, layer order, length, pocket, zipper, waistband, hardware, seam, hem, pattern, fabric behavior, model identity, anatomy, or unsupported claim even when the image looks attractive.

For the default AI-embedded route, perform a normal visual copy check but no
dedicated OCR or character-by-character gate. If the user finds a text-only error, allow one
paid regeneration and record it. Never use this exception for garment, model,
size, annotation-target or claim failures.

### 8. Second approval gate: approve the sample package

Present the approved selected master, representative detail asset,
representative editorial/lifestyle or no-model module, assembly-only sample-page preview, QA
verdicts, actual call count, the still-unpaid second hero or second-model plan,
and unresolved risks together. Stop and obtain approval before generating the
rest.

### 9. Generate remaining assets and compose the page

Generate remaining final modules only from approved masters, facts, and copy.
Default every generated slot to `text_rendering=ai_embedded_one_pass`: the same
image call must complete the product visual, approved Chinese hierarchy, labels,
arrows, zoom explanation, and any supplied table. Before
calling the provider, reject a plan whose set has fewer than four visual
families, exactly one product-truth screen per unit, a construction/information
role and an editorial/lifestyle/brand role. Every paid request must use
`.agents/scripts/right_codes_image_generator.py` with `RIGHT_CODES_API_KEY`;
persist each task id and never silently retry a billed or indeterminate call.

After module QA, map passed files to blueprint module ids and run
`scripts/compose_detail_page.py`. Render the full 750px-wide page, individual
module slices and a page-render manifest. The compositor may only resize each
finished module and stack modules vertically; it must not add or redraw Chinese,
arrows, callouts, zoom circles, or tables. Inspect the full page at 100% and at
target mobile width. A module-level text or layout problem is corrected by one
explicit regeneration, not by a hidden local overlay.

For transient transport failures, follow the active provider's policy. For a detected Chinese text error, use the single approved exception above. After two consecutive failures of the same structural garment fact, stop paid sampling until the evidence, role map, prompt, or route changes.

### 10. Package and report

Create or validate a manifest containing SKU/variant, source references and hashes when available, fact statuses, selected directions, selected models, slots, prompts or prompt hashes, provider/model, call counts, outputs, dimensions, master/derivative relationships, QA verdicts, approval state, residual risks, and temporary versus permanent assets.

Set `delivery_classification=complete_mobile_detail_page` only when the manifest
also contains `page_blueprint`, `composed_page`, and `page_render_manifest`.
Otherwise classify the result as `asset_pack_only` or
`page_blueprint_needs_assets`. `scripts/validate_manifest.py` enforces this
boundary when a complete-page claim is made.

Preserve:

- platform-independent masters;
- individual Mini Program detail slices;
- the full vertical detail preview;
- the page blueprint, final-module asset map, assembly-only full-page render, module slices and page-render manifest;
- product-only and model heroes;
- model, studio, lifestyle, macro, and selling-point assets;
- exact detail-page copy and the six-entry Moments package;
- approved, rejected, and unresolved output lists;
- actual paid-call count, including any text regeneration.

Use `scripts/validate_manifest.py` before reporting completion. A saved file or valid checksum is not proof that garment truth, copy, rights, or commercial suitability passed.

## Completion boundary

Report local/package verification separately from real API generation and real business use. Do not claim production readiness until the user has reviewed the actual images, copy, mobile long-page render, Mini Program presentation, and commercial facts for the target SKU.
An all-white collection, a group of styled posters, or a valid set of generated
slots may be delivered as an `asset_pack_only` or `truth-master pack`; none is a
complete product-detail page until the page-system completion test passes.
