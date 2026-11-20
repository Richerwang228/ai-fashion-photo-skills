---
name: macro-product-photography
description: Generate extreme close-up macro shots of product details including fabric texture, stitching, hardware, and materials. Use when showcasing product quality, craftsmanship, or material details for e-commerce or marketing. Emphasizes accuracy over aesthetics with three-level material specificity.
license: Apache-2.0
metadata:
  author: ShopOS
  version: "1.0"
  category: image-generation
  source: workflow_product_closeup/workflows/Fabric_closeup.py
---

# Macro Product Photography

## When to Use This Skill

Use this skill when you need to:
- Showcase product quality and craftsmanship
- Highlight material textures and finishes
- Display construction details (stitching, seams, hardware)
- Create detail shots for e-commerce listings
- Demonstrate product authenticity and quality
- Generate close-up shots of fabric weaves, leather grain, metal finishes

## Core Principle

**ACCURACY > AESTHETICS**

If a detail looks plain, simple, or undecorated in the source image, it must remain plain, simple, and undecorated in the macro shot. Your job is to faithfully reproduce visible details, not to enhance or embellish them.

## Critical Constraints

### NEVER:
- Imagine or extrapolate sides/angles not visible in source
- Add decorative elements, engravings, or patterns not present
- Assume "typical" features (e.g., "glasses usually have engravings")
- Use generic descriptions when specific ones are needed
- Guess at details you cannot clearly see
- Create flat, perpendicular 2D zooms
- Repeat the exact same detail and angle in multiple shots

### ALWAYS:
- Document exactly what you see before generating prompts
- Count quantifiable elements (stitch lines, holes in buckles)
- Specify surface finish (smooth, textured, napped, brushed, matte, glossy)
- Note what is NOT present (plain hardware = "no engravings")
- Use precise color descriptions
- Create dimensional macro photography angles (20-45 degrees)
- Use three-level material specificity

## Step-by-Step Instructions

### Step 1: Identify Photographable Details

Analyze product images to find macro-worthy elements:
- **Fabric/Material**: Weave patterns, texture, surface finish
- **Stitching**: Single/double/triple needle, stitch count, thread color
- **Hardware**: Buttons, zippers, buckles, clasps, rivets
- **Embellishments**: Embroidery, prints, logos, labels
- **Construction**: Seams, hems, edges, joints
- **Surface Details**: Grain, patina, finish, texture

### Step 2: Material Analysis (Three Levels)

For each detail, specify:
- **Level 1 - Base Material**: Cotton, leather, metal, plastic
- **Level 2 - Construction**: Weave type, grain pattern, metal type
- **Level 3 - Surface Finish**: Smooth, textured, napped, brushed, matte, glossy

Example: "leather with napped suede finish" not just "leather"

### Step 3: Quantify Observable Elements

Count and measure:
- Stitch count per inch
- Number of needle lines (single, double, triple)
- Hardware dimensions and features
- Pattern density and spacing
- Visible texture depth

### Step 4: Document What's NOT Present

Explicitly note absent elements to prevent AI hallucination:
- "No decorative stitching patterns"
- "Plain hardware with no engravings"
- "No additional embellishments"
- "Simple, undecorated surface"

### Step 5: Generate Macro Photography Prompt

```
Extreme close-up macro photography of [SPECIFIC DETAIL with LOCATION],
[BASE MATERIAL] with [CONSTRUCTION TYPE] and [SURFACE FINISH],
shot at [20-45 degree] angle showing dimensional texture and depth,
[EXACT COLORS with specific shades],
[QUANTIFIABLE DETAILS - counts, measurements, configuration],
[GEOMETRIC SHAPES and specific design],
[EXPLICITLY STATE IF PLAIN/SIMPLE],
professional product lighting with soft shadows emphasizing the [SURFACE FINISH] texture,
shallow depth of field,
photorealistic macro detail capturing only what is visible in the source image,
natural camera detail, true-to-source texture, professional macro product photography
```

**Negative Prompt:**
```
different material finish than observed,
[opposite of surface finish],
added engravings not in source,
added patterns not in source,
decorative elements not visible in original,
extrapolated unseen angles,
flat perpendicular view,
blurry, out of focus, low quality
```

## Examples

### Example 1: Denim Stitching

**Observation:**
- Location: Front collar seam
- Material: Cotton denim, right-hand twill weave, stone-washed matte finish
- Stitching: Single-needle top-stitch, 8-10 stitches per inch
- Thread: White polyester on medium indigo fabric
- Absent: No decorative patterns

**Prompt:**
```
Extreme close-up macro photography of the single-needle top-stitching along the front collar seam, cotton denim with right-hand twill weave and stone-washed matte finish, shot at 30-degree angle showing dimensional detail and fabric texture, medium indigo blue denim with white polyester thread, single-needle construction with approximately 8-10 straight stitches per inch, simple industrial stitching with no decorative patterns, professional product lighting with soft shadows emphasizing the matte denim texture and twill weave pattern, shallow depth of field, photorealistic macro detail, natural camera detail, true-to-source texture, professional macro product photography, sharp focus on stitching and fabric weave
```

**Negative Prompt:**
```
double-needle stitching, multiple stitch lines, decorative stitch patterns, glossy fabric finish, smooth fabric texture without twill pattern, different thread color, added embellishments, blurry, poor quality, artificial, flat perpendicular view
```

### Example 2: Metal Buckle

**Observation:**
- Location: Front strap
- Material: Nickel metal with brushed matte finish
- Shape: Rectangular, 2cm x 3cm
- Features: Single prong, no holes, simple design
- Absent: No engravings, logos, or decorative elements
- Surface: Fine linear brush marks visible

**Prompt:**
```
Extreme close-up macro photography of the rectangular metal buckle on the front strap, nickel metal with brushed matte finish, shot at 35-degree angle showing dimensional form and surface texture, single-prong simple design measuring approximately 2cm x 3cm, plain undecorated surface with no engravings or logos, fine linear brush marks visible on the matte metal surface creating subtle texture, professional product lighting emphasizing the brushed texture and metal grain, shallow depth of field, photorealistic macro detail capturing the simple hardware as shown, natural camera detail, true-to-source texture, professional macro product photography
```

**Negative Prompt:**
```
engraved designs, logos, decorative patterns, embossed details, polished finish, glossy surface, multiple prongs, ornate hardware, added decorative elements not in source, different metal finish, blurry, poor quality, artificial, flat view
```

### Example 3: Leather Suede Finish

**Observation:**
- Location: Jacket front panel
- Material: Leather with napped suede finish
- Color: Tan/camel
- Texture: Soft, fuzzy from napping process
- Finish: Matte, non-reflective
- Absent: No smooth leather areas, no glossy finish

**Prompt:**
```
Extreme close-up macro photography of the jacket material on the visible front panel, leather with napped suede finish, shot at 30-degree angle showing dimensional texture and fiber detail, tan/camel color, soft fuzzy napped surface texture characteristic of suede, matte non-reflective appearance, fine fiber texture from the napping process clearly visible, professional product lighting with soft shadows emphasizing the napped suede texture and individual fibers, shallow depth of field, photorealistic macro detail of the suede finish, natural camera detail, true-to-source texture, professional macro product photography
```

**Negative Prompt:**
```
smooth leather finish, glossy leather, polished surface, full-grain leather appearance, shiny texture, different leather treatment, reflective surface, blurry, poor quality, artificial, wrong material finish, flat view
```

## Key Principles

1. **Accuracy Over Aesthetics**: Reproduce exactly what's visible
2. **Three-Level Material Specificity**: Base + construction + finish (always)
3. **Quantify Everything**: Count stitches, measure dimensions
4. **Explicit Simplicity**: State when things are plain/undecorated
5. **Dimensional Angles**: 20-45 degrees, never flat perpendicular
6. **Source Fidelity**: Only capture details from visible parts
7. **Prevent Hallucination**: Use negative prompts for opposites

## Material Specification Examples

Always use THREE-LEVEL specificity:

❌ **Wrong:** "fabric"
✅ **Correct:** "cotton canvas weave with matte, medium-textured finish"

❌ **Wrong:** "leather"
✅ **Correct:** "leather with napped suede finish" OR "full-grain leather with smooth, slightly pebbled finish"

❌ **Wrong:** "polyester"
✅ **Correct:** "polyester with smooth, matte finish" OR "polyester ripstop weave with subtle texture"

❌ **Wrong:** "metal button"
✅ **Correct:** "brass button with brushed, matte finish" OR "zinc alloy button with polished, glossy surface"

## Accuracy Checklist

Before finalizing each prompt, verify:

✓ Did I specify the exact surface finish?
✓ Did I count quantifiable elements?
✓ Did I use precise colors?
✓ Did I explicitly state if hardware is plain/undecorated?
✓ Did I note what's NOT present?
✓ Did I use three-level material specificity?
✓ Is this detail actually visible in the source image?
✓ Am I describing only what I can see?

## Integration Pattern

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "<macro prompt based only on visible details>" \
  "output/macro-top.png" \
  1 \
  "/absolute/path/to/top-detail.jpg" \
  --credential-name RIGHT_CODES_API_KEY \
  --model gpt-image-2 \
  --image-size 1K
```

## References

- Related Skills: product-analysis-styling
- Provider: openai-compatible-image-provider
