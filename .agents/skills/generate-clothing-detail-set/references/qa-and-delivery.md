# QA and delivery contract

## Contents

- [Evidence lanes](#evidence-lanes)
- [Acceptance matrix](#acceptance-matrix)
- [Garment and human checks](#garment-and-human-checks)
- [Text and claims checks](#text-and-claims-checks)
- [Rights and technical checks](#rights-and-technical-checks)
- [Severity, stop, and retry](#severity-stop-and-retry)
- [Delivery package](#delivery-package)
- [Adopted source structures](#adopted-source-structures)

## Evidence lanes

Every QA note identifies its evidence lane:

1. **Documented fact** — a user-approved truth sheet, source image, project
   standard, provider capability, or dated platform specification.
2. **Empirical observation** — what was inspected in the actual output: pixel
   comparison, file probe, render, user text review, or a recorded call result.
3. **Production heuristic** — a practical choice where no binding specification
   exists, clearly labelled as a heuristic.

Do not claim that a saved file, successful API response, or attractive frame has
passed visual QA. Keep local/package evidence separate from simulator, device,
production, or business-loop evidence.

## Acceptance matrix

| Area | Pass evidence | Reject/hold evidence |
|---|---|---|
| Brief and blueprint | Correct SKU, role, direction, count, crop, and copy status | Wrong screen, variant, model group, locale, or unapproved direction |
| Product truth | Color, silhouette, layer, length, pockets, closures, hardware, seams, hems, and detail locations match references | Changed construction, invented material/mark, merged trousers, hidden critical feature, or unsupported back view |
| Model and fit | Identity, anatomy, hands, feet, grounding, body proportions, natural folds/tension, and plausible garment-body physics | Face/identity drift, body morphing, missing limbs, floating feet, or pose that hides a fit defect |
| Text and claims | Approved Chinese text only; user visual review; factual claims trace to ledger | Invented wording, wrong numbers/units, fake marks/reviews, unreadable mobile copy, price/stock/“缺货” |
| Art direction | Brand mood, light, composition, and props support the garment; product remains readable | Generic direction, props covering hero areas, third-party marks, misleading scale or scene |
| Set-level visual system | Exactly one clean truth screen, coherent 2-3 color palette, at least four visual families, designed information/selling-point role, and editorial/lifestyle/brand-close role | Six near-identical white product-only frames, random unrelated backgrounds, or missing persuasion/context roles |
| Page composition | Approved 750px blueprint, ordered buyer questions, AI-embedded approved text, correct callout endpoints, module slices and full-page mobile render | Unplanned posters concatenated vertically, invented or unreadable text, missing geometry, callouts that do not land on evidence, or no mobile preview |
| Technical file | Non-empty image, opens, expected dimensions/aspect, valid color/alpha, clear filename/version | Corrupt/truncated file, wrong crop, partial frame accepted as final, stale or overwritten version |
| Rights/provenance | Inputs, model identity, marks, provider/model, prompt, edits, approvals, and disclosure status recorded | Missing permission, lookalike real person, unlicensed mark/property, or unknown source on a release candidate |
| Delivery readiness | Master, derivatives, manifest, QA report, truth/copy ledger, and residual risks agree | Missing asset, mismatch in manifest/hash, or unresolved blocker presented as “ready” |

Inspect every still at 100% and at its intended mobile size. Review the whole set
for continuity, not only the hero. A crop is not allowed to conceal a known
defect that would be visible in another required screen.

Review the contact sheet before calling the package complete. If all frames are
white-background product-only views, classify the result as a product evidence
pack and keep the complete-detail status blocked. Existing passed evidence
images remain reusable truth masters; do not regenerate them merely to satisfy
the page-design contract.

Also review the assembly-only full-page render at 100% and at target mobile
width. Check text hierarchy, contrast, safe margins, crop consistency, module
rhythm, callout endpoints and whether each module answers a different buyer
question. Correct a module-level problem through an explicitly recorded
regeneration; never hide it with a local overlay.

## Garment and human checks

For each image compare against the exact reference-role map:

- category, layer order, color family, finish, silhouette, fit, length, rise,
  sleeve/shoulder, neckline, cuffs, waistband, hem, and drape;
- count and side of pockets, zippers/sliders, buttons, drawstrings, hardware,
  logos, seams, panels, and deliberately absent details;
- natural contact shadows, cloth tension, wrinkles, and occlusion;
- model face, hair, build, proportions, hands, fingers, feet, eyes, and pose;
- whether the camera angle or prop hides a required shopper-facing feature.

For the project balanced extra-wide trouser standard, verify width establishes
below the waistband, two legs remain separate, upper-thigh width is at least
knee width, knee width is at least hem width, the hem covers roughly half to
two-thirds of the shoe, and no A-line, flare, merged-leg, low/drop-crotch, or
skirt-like reading appears. Treat a failure as a garment truth failure, not an
art-direction preference.

## Text and claims checks

GPT Image 2 renders approved Chinese copy inside each final module by default.
Compare the visible module with the ledger, then review the full page at mobile
size. Perform a normal visual check and ask the user for the final decision. Do
not claim OCR certification, use a dedicated OCR gate, or add a local correction
layer over the generated image.

Reject or hold when an image contains:

- a number, unit, color code, material, certification, performance, care,
  country-of-origin, price, discount, availability, inventory, or scarcity
  statement not in the approved ledger;
- a fake logo, badge, rating, review, testimonial, endorsement, or social proof;
- Chinese copy that changes the approved meaning or a text block in a language
  not requested;
- a body transformation, “fix your body” message, universal-fit implication, or
  unsupported before/after result.

If the user identifies a live-layer text error, correct it without a paid image
call. For an AI-embedded exception, allow one explicit paid correction and
record it; stop that route if the same error remains. This exception cannot
repair a wrong pocket, body, garment, callout target or numeric fact.

## Rights and technical checks

Record for every final or rejected candidate:

- source path, SHA-256 when available, reference role, and source/permission;
- model identity pack or synthetic-model status; no real-person likeness without
  the required release scope;
- provider/model/date, prompt version, reference list, paid-call id or
  indeterminate status, local edit chain, and approval timestamp;
- visible brand marks, third-party marks, property, props, fonts, and any
  required AI/provenance disclosure;
- output path, dimensions, aspect, file type, color profile, version, and
  whether metadata survived export.

Use the existing project provider's completed-event route for final assets. A
partial or ghosted preview is diagnostic evidence only. Do not auto-retry a paid
request; a late connection drop is an indeterminate call until consumption is
checked. Candidate commercial provider APIs, CLIs, and hidden templates are not
accepted as runtime evidence.

## Severity, stop, and retry

Use these practical severities:

- **Critical / Reject:** wrong SKU or garment identity, wrong numeric fact,
  unauthorized likeness/mark, fabricated claim, missing required disclosure,
  corrupt final, or a trust-breaking face/hand/product error.
- **Major / Revise:** visible construction or fit error, wrong color, identity
  drift, unreadable required text, bad crop, or a rights/provenance gap that
  blocks the intended scope.
- **Minor / Note:** small non-critical background artifact that is not visible
  at intended size and does not touch the garment, copy, model, or trust signal.
- **Observation:** record without blocking when the issue is a documented
  heuristic or a non-material stylistic variance.

Verdicts are `PASS`, `PASS_WITH_NOTES`, `REVISE`, `NEEDS_REFERENCE`, `REJECT`, or
`STOP_CURRENT_ROUTE`. A repair must name the changed fact and then receive a
delta review around that region plus one complete pass. The same structural
failure twice triggers `STOP_CURRENT_ROUTE`; changing only adjectives or
background does not reset the count.

## Delivery package

For each SKU, deliver a portable folder (or equivalent manifest) containing:

```text
00_服装真值清单.md
01_商品独立主视觉_master.png
01_<model-id>_中性穿着母版_master.png
02_详情_<role>_<id>_master.png
03_朋友圈_M1..M6.md
blueprint.md
copy-ledger.md
reference-role-map.json
provenance-ledger.json
qa-report.md
delivery-manifest.json
exports/<sku>_<role>_<aspect>_<locale>_vNN.png
rejected/<asset>__<reason>.<ext>
```

The sample package after Gate 1 contains exactly three paid outputs: one
selected main-visual master (normally the first model's neutral worn master when
model imagery is required, otherwise the independent product hero), one final
designed selling-point/information screen, and one final
editorial/lifestyle/brand-close screen. For `model_count=0`, the last role uses
a non-model scene. It also contains local previews of those two representative
detail screens; previews are not paid calls. The other hero and any second-model master
wait for Gate 2. Gate 2 must list the sample assets plus every remaining planned
screen, model group, and exact call count. Keep failed candidates out of the
final folder while retaining their reason and provenance in the report.

The manifest should include SKU/variant, source references, screen role,
master/version, output path, aspect, copy ids, QA verdict, paid-call count (and
indeterminate calls), rejected reason, and residual risk. Generate checksums
after the final files are in the delivery package; do not reuse a filename for
changed pixels.

A complete-page manifest additionally requires `delivery_classification`,
`page_blueprint`, `composed_page`, `page_render_manifest`, module geometry and
mobile-page QA. Without them, validate and deliver only as an asset pack.

## Adopted source structures

- **Generated Media QA** (`MIT`, commit `8c85352d5d75d4dcbe58480bd138e37b9742bab1`),
  `.../governance-delivery/generated-media-qa/SKILL.md`: evidence lanes,
  acceptance matrix, generated-image defect checks, severity triage, and delta
  review, independently narrowed to garment stills.
- **Media QC and Delivery** (`MIT`, same commit),
  `.../governance-delivery/media-qc-delivery/SKILL.md`: delivery-sheet,
  versioning, checksums, manifests, and final-file review patterns.
- **Media Provenance and Rights** (`MIT`, same commit),
  `.../governance-delivery/media-provenance-rights/SKILL.md`: asset ledger,
  provider/model metadata, release scope, C2PA/IPTC caveat, and rights blocker
  categories.
- **Claude Ads** (`MIT`, commit `669c7608ecb50dd95c941a71fa3ca0a1c0e40512`),
  `skills/ads-photoshoot/SKILL.md`: human review, source hashes, prompt/model
  record, and atomic run-directory idea, adapted without ad scope.
- **Project `model-catalog` and provider skills** (`AI 模特照/.agents/skills/`):
  master inspection gates, route-stop rule, no automatic paid retries, and
  completed-event output discipline.

The references describe a release contract; they do not claim production or
real-device evidence when only local/package checks were run.
