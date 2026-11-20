# Source provenance and reuse ledger

## Contents

- [Purpose and scope](#purpose-and-scope)
- [Mobile PDP architecture research](#mobile-pdp-architecture-research)
- [Reusable source ledger](#reusable-source-ledger)
- [Project capability ledger](#project-capability-ledger)
- [Excluded runtime material](#excluded-runtime-material)
- [Per-asset provenance record](#per-asset-provenance-record)
- [Review and re-use rules](#review-and-re-use-rules)

## Purpose and scope

This ledger records where a reusable idea, prompt structure, template field, or
QA rule came from, which license was visible at the fixed research commit, how
it was independently re-authored, and where it enters the final clothing skill.
It is an audit trail, not a list of provider recommendations. Source paths are
relative to the private research workspace unless stated; the researched
repositories are identified by name and commit below.

The research candidates all exposed a repository license at the commits below:
MIT for Claude Ads, Generative Media Skills, Higgsfield, LinkFox, Nexscope, and
Samurai; Apache-2.0 for Open Design. Re-check license files before redistributing
outside this workspace. A license for source code does not grant rights to a
third-party logo, model likeness, product photo, prompt from another author, or
provider output.

## Mobile PDP architecture research

The structured long-page architecture is an original project implementation
informed by public structures, not copied prompts or vendor runtime code:

- Alibaba/Taobao public documentation and accessible 2025 design cases:
  separate gallery/video assets from the scrolling product-detail story and
  treat fit, material, detail and sizing as distinct decision modules.
- Amazon apparel image and A+ module guides: separate clean product imagery,
  alternate views, feature modules, comparison/specification and brand story.
- Baymard mobile PDP research: make image, variation, fit, detail, FAQ and trust
  information discoverable in ordered mobile sections.
- OpenAI Academy image guidance: iterate one visual element at a time and polish
  dense infographics in design tools.
- Adobe Firefly Services public guide: modular generation and rendition ideas;
  this project intentionally assigns Chinese layout to GPT Image 2 and keeps
  only vertical page assembly deterministic.
- Bingran You `ecommerce-image-workflow`: role-based visual slots, identity
  lock, negative-space planning and manifest structure. No source code or
  provider dependency is imported.

The project scripts `build_page_blueprint.py` and `compose_detail_page.py` were
implemented locally for this skill. They do not call or depend on the researched
commercial services.

## Reusable source ledger

| Source / fixed commit / license | Original path(s) inspected | Reused structure | Final destination and adaptation |
|---|---|---|---|
| `claude-ads` / `669c7608ecb50dd95c941a71fa3ca0a1c0e40512` / MIT | `skills/ads-photoshoot/SKILL.md`, `README.md` | rights check, distinct production hypotheses, hashes, human review, atomic run record | `product-truth.md`, `qa-and-delivery.md`; narrowed to clothing and organic/commerce separation; no ad execution. |
| `generative-media-skills` / `8c85352d5d75d4dcbe58480bd138e37b9742bab1` / MIT | `skills/production/content-formats/ecommerce-product-imagery/{SKILL,EVAL}.md`; `fashion-campaign-production/{SKILL,EVAL}.md` | truth packet, SKU continuity, fixed facts vs creative direction, garment shot grammar, claims and release gates | `product-truth.md`, `detail-blueprint.md`, `prompt-patterns.md`, `copy-and-moments.md`, `qa-and-delivery.md`; wording and examples independently rebuilt. |
| `generative-media-skills` / same commit / MIT | `skills/production/governance-delivery/{generated-media-qa,media-provenance-rights,media-qc-delivery}/{SKILL,EVAL}.md` | evidence lanes, acceptance matrix, severity/retest, rights ledger, provenance and checksum fields | `qa-and-delivery.md`, `source-provenance.md`; media-only rules narrowed to clothing stills. |
| `higgsfield-skills` / `91051d3f260ae0792708c5eb0a87b07122ad3830` / MIT | `higgsfield-product-photoshoot/SKILL.md`, `higgsfield-marketplace-cards/SKILL.md`, `COOKBOOK.md` | intent-based mode routing, compact interview, multi-variant visual-system thinking, identity reuse | `detail-blueprint.md`, `prompt-patterns.md`; provider CLI, backend prompt enhancer, and proprietary modes excluded. |
| `linkfox-skills` / `87750632f9bd538ac6a9989e3c9f6b00fc3c6949` / MIT | `skills/linkfox-aigc-imagegen-cloth/{SKILL.md,references/runtime/*,references/types/*,references/maintainer/collection/*}`; corresponding product files | empty-reference guard, role/type routing, S0→S1→S2 plan confirmation, layout tags, exact-language field, size-analysis warning, two-stage delivery idea | `product-truth.md`, `detail-blueprint.md`, `copy-and-moments.md`, `prompt-patterns.md`; supplier scripts, textgen/imagegen calls, default counts, and Chinese prompt prose are not copied. |
| `nexscope-amazon-skills` / `bdc556233805bbc3b5d8d865f3f3bd153864970f` / MIT | `amazon-product-photography/SKILL.md`, `amazon-listing-images/SKILL.md`, `amazon-a-plus-content/SKILL.md` | separate main compliance from secondary persuasion, one shopper question per screen, mobile-first hierarchy, staged plan/review/handoff | `detail-blueprint.md`, `copy-and-moments.md`, `qa-and-delivery.md`; Amazon-specific requirements remain volatile and are not hard-coded. |
| `open-design` / `2523669517f1f508f630e918c86cd6ef4afdb725` / Apache-2.0 | `skills/ecommerce-image-workflow/SKILL.md`, `references/checklist.md` | reference-required mode, identity anchors, main/feature/lifestyle roles, manifest and gallery handoff, no-fabrication checklist | `product-truth.md`, `detail-blueprint.md`, `qa-and-delivery.md`; three generic slots expanded to clothing dual heroes and six-to-ten screens. |
| `samurai-generative-media-skills` / `920ca785a721070fc6e6e86eac2d1bb0d915cf5c` / MIT | `library/visual/amazon-product-listing/SKILL.md` | hero/lifestyle/infographic/detail role split and “present in order” delivery idea | `detail-blueprint.md`; Muapi models/CLI and one-size-fits-all product wording excluded. |

No source was used merely because it was a product webpage. Candidate EVAL files
were read as acceptance signals only; EVAL text is not shipped or referenced by
the runtime skill.

## Project capability ledger

The final skill orchestrates existing project capabilities rather than copying
their implementation. These files were inspected:

| Workspace path | Visible license/status | Reused capability |
|---|---|---|
| `AI 模特照/.agents/skills/model-catalog/SKILL.md` | project file; no frontmatter license shown | four-view identity pack, four-image baseline, reference-role map, neutral master, master QA, selected concepts, route stop, output naming |
| `AI 模特照/.agents/skills/product-analysis-styling/SKILL.md` | Apache-2.0 in frontmatter | three-level material specificity and structured color/construction/styling analysis |
| `AI 模特照/.agents/skills/product-tryon-visualization/SKILL.md` | Apache-2.0 in frontmatter | fit/drape, straight-on neutral pose, scale and body-integrity checks |
| `AI 模特照/.agents/skills/fashion-model-photography/SKILL.md` | Apache-2.0 in frontmatter | model direction, pose, lighting, camera and garment behavior fields |
| `AI 模特照/.agents/skills/garment-lifestyle-photography/SKILL.md` | Apache-2.0 in frontmatter | contextual scene, natural action, documentary composition, no-obstruction rules |
| `AI 模特照/.agents/skills/macro-product-photography/SKILL.md` | Apache-2.0 in frontmatter | evidence-only macro, count visible elements, note absences, 20–45° dimensional angle |
| `AI 模特照/.agents/skills/brand-consistent-visuals/SKILL.md` | project file; no frontmatter license shown | brand brief, distinct directions, negative space and no-duplicate-background principle |
| `AI 模特照/.agents/skills/openai-compatible-image-provider/SKILL.md` | project file; no frontmatter license shown | verified Right.codes async task route, GPT Image 2, zero paid POST retries, resumable polling and local-output checks |
| `AI 模特照/.agents/references/wide-leg-standard/STANDARD.md` | user/project standard | approved A/B balanced-wide-straight bounds and prohibited silhouette cues |

The requested `garment-reference-capture` and `garment-fidelity-qa` paths were
not present under `AI 模特照/.agents/skills/` in this research checkout. Their
expected responsibilities are represented by the available `model-catalog`,
`product-analysis-styling`, `macro-product-photography`, and QA rules above;
this ledger does not claim to have reused absent files.

## Excluded runtime material

The following are intentionally not dependencies of the final skill:

- Higgsfield product-photoshoot/marketplace CLI, LinkFox imagegen/textgen and
  brand-gene services, Muapi/Samurai commands, Nexscope's hosted generator, and
  any candidate backend prompt enhancer.
- Vendor-specific model IDs, account login/bootstrap steps, API routes,
  per-vendor aspect/resolution defaults, credit handling, or hidden templates.
- Amazon-only, Meta-only, TikTok-only, or Google-only rules as permanent
  clothing requirements. Platform facts must be checked for the actual target
  at delivery time.
- Any source wording that asks for default Western models, auto-generated size
  numbers, smart claims, or unrestricted image text. The final contract uses an
  approved model catalog, real size sources only, and user text review.
- The retired project wide-leg image `reference_02_front_hakama.jpg` and all
  hakama/skirt-pants/deep-drop-crotch wording.

Exclusion is deliberate: an open-source repository can be useful research while
its commercial API, data terms, or output contract remains unsuitable for this
runtime.

## Per-asset provenance record

For every output, candidate, and rejected call, write a ledger row with:

```yaml
asset_id: "sku-role-vNN"
file_path: "/absolute/path/to/file.png"
sha256: "computed after final package placement"
role: "reference | product_hero | model_master | detail | moment_crop | rejected"
sku_variant: "confirmed identifier or null"
source_inputs:
  - path: "/absolute/reference/path.jpg"
    role: "MODEL_IDENTITY / TOP_FRONT / DETAIL_<name>"
    rights_basis: "user supplied / project-owned / license or not established"
license_and_permission: "exact license or approval scope; do not infer"
ai_process:
  provider: "existing project image provider"
  model: "gpt-image-2 or configured approved model"
  prompt_version: "prompt-pattern version"
  generation_time: "timestamp"
  paid_call_id: "id or indeterminate"
  edit_chain: "master -> variant -> correction"
human_approval:
  truth: "confirmed / pending / rejected"
  copy: "user reviewed / pending / not applicable"
  qa: "PASS / REVISE / REJECT / STOP_CURRENT_ROUTE"
provenance:
  c2pa_or_xmp: "present / absent / not tested"
  disclosure: "required / not required / pending review"
notes: "residual risk and next action"
```

Do not treat a C2PA/IPTC credential as proof that the garment is true or rights
are cleared. It is one provenance signal alongside source permission, product
truth, approvals, and final-pixel review.

## Review and re-use rules

Before reusing a source-derived prompt or template, confirm:

1. the source commit and license still match this ledger;
2. the copied structure has been rewritten for clothing-first scope and the
   active project provider;
3. no vendor API, hidden template, unlicensed image, model likeness, logo,
   trade dress, or unsupported claim entered the prompt;
4. the final output has a source role, truth verdict, copy verdict, rights note,
   and destination scope;
5. a changed scope (new channel, locale, SKU, model, paid media, or public
   release) receives a fresh review.

This ledger supports traceability; it is not legal advice or a warranty of
commercial clearance.
