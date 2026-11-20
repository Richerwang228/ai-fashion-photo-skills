---
name: model-catalog
description: Orchestrate this project's complete AI fashion-model catalog workflow from a reusable AI-model identity pack and fast garment capture through garment analysis, a neutral full-body master, user approval, 20 or more selectable pose/prop concepts, studio and lifestyle generation, per-image garment QA, paid-call control, and organized delivery. Use when the user invokes $model-catalog or asks to create model photos for a garment folder without hiring a human model.
---

# Model Catalog

Execute the complete model-photo workflow from this file. Treat this skill as the only orchestration source; do not look for or create a separate model-catalog workflow document.

## Operating goal

Produce convincing, commercially useful AI model photos while keeping the actual garment identity more important than an attractive but incorrect image.

Optimize for store throughput:

- never require a real person to wear the garment;
- never require 20-30 source photos for an ordinary outfit;
- reuse one approved AI-model identity pack across outfits;
- create and approve a neutral worn master before creative variants;
- allow the user to select many concepts and authorize roughly 10-20 paid variants per outfit;
- inspect every generated result before accepting it.

## Existing specialist skills

Read the relevant existing skill completely immediately before using that stage. Do not rewrite those specialist skills as part of ordinary catalog work.

- `../product-analysis-styling/SKILL.md`: garment facts and styling analysis.
- `../product-tryon-visualization/SKILL.md`: initial worn visualization.
- `../fashion-model-photography/SKILL.md`: studio, catalog, lookbook, and editorial direction.
- `../garment-lifestyle-photography/SKILL.md`: environmental and social imagery.
- `../macro-product-photography/SKILL.md`: evidence-based close details.
- `../product-background-generation/SKILL.md`: new settings and backgrounds.
- `../brand-consistent-visuals/SKILL.md` (optional, not shipped here): supplied brand direction.
- `../openai-compatible-image-provider/SKILL.md`: API transport, streaming, billing safety, and local delivery.

This skill decides the sequence, reference selection, approval gates, master-first behavior, and acceptance rules. A specialist skill supplies domain guidance but cannot bypass these orchestration rules.

## Persistent model identity pack

Maintain one reusable four-view AI-model pack:

1. front full body;
2. left-front 45-degree full body;
3. right-front 45-degree full body;
4. side or back full body.

Prefer four independent images. A four-panel contact sheet can remain as an identity overview, but use only the one or two views relevant to the requested camera angle when the provider supports the separate images.

Project fallback reference:

`<project>/output/model-pack/four_view_composite.png` (your own approved four-view identity sheet)

The model pack supplies identity, face, hair, body build, and proportions only. Explicitly tell the image model to ignore clothing, background, pose, accessories, and scene from identity references.

Do not recreate the model pack for every outfit.

## Stage 1: Resolve the garment scope

1. Resolve the exact garment directory from the user request.
2. Inspect only that directory unless the user explicitly requests a batch.
3. Identify existing front, back, detail, inner-layer, set, and previous generated images.
4. Show a file-to-role mapping before renaming anything.
5. Rename only after user confirmation; never overwrite a collision.

Use these canonical names when renaming is approved:

- `top_front.*`
- `top_back.*`
- `bottom_front.*`
- `bottom_back.*`
- `inner_front.*`
- `set_front.*`
- `detail_<location>_<feature>.*`

## Stage 2: Fast store capture gate

For an ordinary two-piece outfit, the required baseline is exactly four garment photos:

1. top front;
2. top back;
3. bottom front;
4. bottom back.

The garment must be fully visible, laid flat or hung square to the camera, evenly lit, and not cropped. Separate trouser legs so the crotch and width curve can be read. Use a white or light-gray background. Expose black garments enough to show seams and pocket edges without turning black fabric gray.

Request an additional photo only when a commercially important fact remains unclear, such as:

- unusual pocket construction or pocket hardware;
- zipper head, double-slider zipper, or special puller;
- waistband, drawstring, closure, or belt structure;
- logo, embroidery, badge, or back mark;
- unusual collar, cuff, panel, hem, lining, or seam;
- black-on-black construction invisible in the baseline image.

Prefer one contextual detail image. Add a macro only when the contextual image proves location but not shape. Ordinary outfits should normally use 4-8 garment images; genuinely complex products can approach 10.

Do not request a human try-on image. Do not request measurements: centimeter values do not make an image model reconstruct a true garment pattern and must not be presented as false precision.

For each requested output view, return:

- `GO`: the visible garment facts are sufficiently supported;
- `NEEDS_REFERENCE`: name the single minimum additional photo required.

A missing back image does not block a front master, but it blocks a back-view deliverable.

## Stage 3: Garment truth analysis

Read `../product-analysis-styling/SKILL.md`. Analyze top and bottom separately and show the user:

- category and layer order;
- exact visible color and surface finish;
- silhouette, looseness, length, and drape;
- collar, sleeves, cuffs, waistband, drawstring, seams, and hems;
- pocket count, side, opening direction, shape, and position;
- zipper count, slider count, puller shape, and endpoints;
- hardware count, geometry, finish, and position;
- logos, marks, and deliberately absent features;
- facts that cannot be confirmed from the supplied images.

Use evidence states:

- `CONFIRMED`: clearly visible;
- `AMBIGUOUS`: partly visible but unsafe to specify exactly;
- `MISSING`: required for the requested view but absent;
- `NOT_APPLICABLE`: the feature does not exist.

Never convert `AMBIGUOUS` into a confident material or construction claim. Explicitly state important absences when useful, for example: “the pocket hardware is not a round button.”

Present the analysis in chat and wait for user confirmation. After approval, save it as `00_服装真值清单.md` in the garment directory.

## Project wide-leg standard

When the user or product identifies the trousers as “阔腿裤”, “大阔版”, “超宽裤腿”, or a synonym, read this file completely:

`.agents/references/wide-leg-standard/STANDARD.md` (optional; create your own approved silhouette references — none are shipped in this repository)

Use the product images for color, fabric, waistband, drawstring, pockets, seams, and all garment-specific design. Use the approved wide-leg references only for silhouette and drape.

The result must remain between:

- `approved_output_A_balanced_wide_straight.png`;
- `approved_output_B_full_wide_straight.png`.

Require:

`上大腿宽度 ≥ 膝部宽度 ≥ 裤脚宽度`

The width must be established high on the leg and remain broadly straight with only slight inward recovery below the knee. Reject ordinary loose straight trousers, lower-leg flare, A-line expansion, skirt-pants, hakama, samurai-trouser, deep-drop-crotch, or fused-leg shapes.

`reference_02_front_hakama.jpg` is retired and must never be uploaded, described, or used for acceptance.

## Stage 4: Build a reference-role map

Keep all source images in the outfit archive, but upload only the subset relevant to the requested view.

Before each provider request, write the exact reference order into the prompt. Use wording such as:

```text
Reference image 1: model identity only; inherit face, hair, body build and proportions; ignore its clothing and background.
Reference image 2: top-front garment truth; inherit the visible top color, fit, pockets, zipper and hardware.
Reference image 3: bottom-front garment truth; inherit the visible waistband, trouser silhouette, pockets and hems.
Reference image 4: named pocket detail only; inherit only its count, geometry and position.
Reference image 5: approved wide-leg silhouette only; do not inherit its person, garment design, material, color, footwear or scene.
```

Rules:

- assign one primary responsibility to every reference;
- match the written order to the actual upload order;
- do not upload back references for a front master merely because they exist;
- do not upload unrelated details;
- do not let a silhouette reference override garment construction;
- stop before a paid request if any referenced path is missing.

## Stage 5: Paid-call gate

Read `../openai-compatible-image-provider/SKILL.md` before the first provider request.

Show the user:

- intended output;
- exact reference list and roles;
- exact paid-call count;
- output path;
- whether this is a master, correction, back view, or creative variant.

Wait for confirmation unless the user has already explicitly authorized that exact call or batch.

Use the provider’s validated completed-event route. Default to one image per request and zero automatic retries. A late disconnect is an indeterminate paid request; check provider consumption before submitting again. Never degrade a missing-reference edit into text-only generation.

## Stage 6: Neutral front full-body master

Read `../product-tryon-visualization/SKILL.md`. Generate one neutral master before any elaborate art direction.

Use:

- the most relevant model identity view, optionally one supporting angle;
- top front;
- bottom front;
- required inner layer;
- only indispensable visible detail references;
- the approved silhouette reference only when the project wide-leg standard applies.

Master requirements:

- one person;
- same face, hair, build, and proportions as the identity pack;
- full body from head through shoe soles;
- front-facing or a very slight natural offset;
- relaxed stance with hands away from pockets, zipper, waistband, and hardware;
- clean warm-white or light-gray studio background;
- even product-readable light and realistic contact shadow;
- no bag, furniture, scarf, coat, or large accessory;
- exact garment category, layer order, color, fit, length, pockets, zipper, waistband, hardware, and hems;
- natural skin, anatomy, fabric weight, wrinkles, and garment-body interaction;
- no invented logo, pocket, seam, button, decoration, or hardware.

Output:

`01_正面全身母版.png`

Do not continue to creative variants until the master passes inspection and the user explicitly approves it.

## Stage 7: Master inspection

Inspect the actual generated image after every paid call. Never equate API success or a saved file with acceptance.

### Gate A: Garment Truth

Compare against the relevant source images:

- category, color, and layer order;
- looseness, length, silhouette, and drape;
- pockets, zipper, waistband, drawstring, hardware, logos, seams, and hems;
- count, geometry, left/right side, and position of distinctive details;
- wide-leg A/B bounds and thigh-knee-hem curve when applicable.

Any identity-defining garment error fails the image even if it looks fashionable.

### Gate B: Human Integrity

Check identity, face, hair, body proportions, hands, feet, limbs, pose plausibility, grounding, contact shadows, and garment-body physics.

### Gate C: Art Direction

Only after Gates A and B pass, evaluate pose, expression, crop, lighting, background, old-money tone, props, and sales usefulness.

Report one verdict:

- `PASS`;
- `RETRY_WITH_CORRECTION`;
- `NEEDS_REFERENCE`;
- `STOP_CURRENT_ROUTE`.

Track repeated failures by structural fact, not merely by image number. If the same structural fact fails twice, stop that prompt/edit route before spending again. This does not cancel the whole outfit: change the evidence subset, prompt, camera angle, or master strategy, then request approval to resume.

Small isolated hardware, zipper-head, or logo errors on an otherwise correct image may be offered as an optional local repair, but never introduce complex compositing without explicit user approval.

## Stage 8: Present at least 20 selectable concepts

After the front master passes, create at least 20 complete shot cards tailored to the outfit. Providing text choices is free and must not be artificially restricted to 3-6 options.

Each card must include:

- number and short title;
- body pose and direction;
- hand action;
- expression and gaze;
- accessory choices;
- physical prop choices;
- background or environment;
- lighting and framing;
- garment feature displayed best;
- obstruction or distortion risk;
- image class: `严格商品图` or `氛围创意图`.

Cover a useful range of standing, measured walking, leaning, seated, prop-interaction, studio, lifestyle, and editorial directions. Favor full-body concepts when trouser silhouette is important. Offer more than 20 when the user asks.

For old-money direction, use quiet quality rather than costume wealth: dark brown leather, restrained eyewear or watch, books, wood, stone, wool or linen texture, mature warm neutrals, controlled directional light, and composed behavior. Avoid fake luxury logos, theatrical mansions, crests, loud gold jewelry, cigars, and props that cover the product.

The user may select a small set or authorize roughly 10-20 paid variants for one outfit. State the exact selected count before generation.

## Stage 9: Generate variants from the approved master

For studio, catalog, lookbook, or editorial images, read `../fashion-model-photography/SKILL.md`. For environmental images, read `../garment-lifestyle-photography/SKILL.md`. Use other specialist skills only when their stage is requested.

The first reference for every creative variant must be the approved worn master. It supplies the complete model identity and worn outfit. Attach only the additional source detail images needed for features visible in that target frame.

In the prompt, state that the approved master is authoritative and lock:

- identity, face, hair, body build, and proportions;
- garment color, category, layer order, looseness, length, and silhouette;
- pockets, zipper, waistband, drawstring, hardware, logos, seams, and hems;
- wide-leg curve and drape when applicable.

Do not reconstruct the complete outfit from the original model pack and flat-lays for every scene.

Prefer changing one major variable per edit: pose, environment, lighting, or one restrained prop/accessory set. When a chosen card changes several elements, repeat all locked facts and keep critical garment areas unobstructed.

Generate only the user-approved concepts. For a large selection, work in small waves by default so repeated structural failure can stop the faulty route before the remaining budget is spent. If the user explicitly requests the entire approved batch immediately, state the reduced opportunity for mid-batch correction before submitting it.

Inspect every result with Stage 7 before accepting it or using it as a later reference.

## Stage 10: Optional back master

A back master is not mandatory for every outfit. Generate it only when:

- the user requests a back product view;
- a selected concept uses a side-back or back-facing pose;
- the top has an important back design;
- rear trouser pockets or construction are commercially important.

Require top-back and bottom-back references for a two-piece back view. Use the approved front master to preserve identity and outfit continuity, then use the back garment references only for back construction.

Output:

`01_背面全身母版.png`

If the back evidence is insufficient, return `NEEDS_REFERENCE` rather than inventing it.

## Output names and organization

Use:

- `00_服装真值清单.md`
- `01_正面全身母版.png`
- `01_背面全身母版.png` when approved and needed
- `02_棚拍_<序号>.png`
- `03_生活化_<序号>.png`
- `04_时尚大片_<序号>.png`
- `05_上衣微距_<序号>.png`
- `06_裤装微距_<序号>.png`

Move visually failed generations into `rejected/` with a concise reason in the filename when doing so will not overwrite an existing asset. Never place a failed master in the final set.

## Final report

Report:

- approved files and intended usage;
- rejected files and exact failure reasons;
- actual paid-call count, including indeterminate calls;
- approved master path and version used;
- unresolved or unsupported garment facts;
- any current route stopped after repeated failure;
- remaining selected concepts not yet generated.

## Invocation behavior

When invoked as `$model-catalog`:

- complete safe, read-only, non-paid preparation without asking the user to repeat known information;
- ask only for genuinely missing evidence or a required confirmation;
- do not stop after a plan when the next safe preparation step can be completed;
- retain the same evidence, master, paid-call, and QA rules when the user requests only one stage;
- never infer authorization for extra paid images from a previous outfit;
- never hire, contact, or require a human model;
- never introduce an external virtual-try-on service or complex compositing unless the user explicitly requests it.

If the garment directory cannot be resolved safely, request its absolute path rather than guessing.
