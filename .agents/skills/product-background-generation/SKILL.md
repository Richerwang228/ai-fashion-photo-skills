---
name: product-background-generation
description: Generate professional studio or lifestyle backgrounds for product photography that match product aesthetics, brand positioning, and target audience. Use when creating product shoots, fashion photography, or e-commerce visuals requiring contextual backgrounds.
license: Apache-2.0
metadata:
  author: ShopOS
  version: "1.0"
  category: image-generation
  source: workflow_garments_v2/utils/background_generation.py
---

# Product Background Generation

## When to Use This Skill

Use this skill when you need to:
- Create professional product photography with appropriate backgrounds
- Generate studio or lifestyle settings for e-commerce images
- Match backgrounds to product style and brand positioning
- Create contextual environments for fashion photography
- Design backgrounds that enhance product presentation

## Core Concepts

### Background Types

**Studio Mode** - Clean, professional product photography:
- Solid color backdrops (white, black, neutral, colored)
- Gradient backgrounds with subtle transitions
- Textured studio backdrops (canvas, paper, fabric)
- Seamless paper backgrounds
- Minimalist studio environments
- Colored gel lighting backgrounds
- High-key or low-key studio setups

**Lifestyle Mode** - Contextual, aspirational imagery:
- Indoor environments (modern interiors, minimalist spaces)
- Outdoor settings (urban streets, parks, nature)
- Lifestyle contexts (cafes, workspaces, homes)
- Architectural elements (walls, floors, surfaces)
- Natural materials (wood, marble, concrete, fabric)

### Material Specificity

Always use three-level material specificity:
1. **Base Material**: Cotton, leather, metal, ceramic, wood
2. **Construction**: Weave type, grain pattern, metal type
3. **Surface Finish**: Smooth, textured, napped, brushed, matte, glossy

Example: "warm terracotta plaster wall with matte finish" not "orange wall"

## Step-by-Step Instructions

### Step 1: Analyze Product Context

Extract from product images:
- Product category (garment, accessory, furniture, electronics)
- Product style (casual, formal, luxury, minimalist, traditional)
- Color palette (specific color names, not generic)
- Material properties (fabric, metal, leather, plastic, wood)

### Step 2: Determine Background Type

Choose based on use case:
- **E-commerce**: Studio mode with clean backgrounds
- **Editorial**: Lifestyle mode with contextual environments
- **Social Media**: Mix of both depending on platform
- **Advertising**: Lifestyle mode for storytelling

### Step 3: Apply Fashion/Brand Aesthetics

- Match background to product's brand positioning
- Consider target audience sophistication
- Use fashion-specific terminology
- Apply color theory for harmony or contrast
- Reference editorial photography language

### Step 4: Generate Background Description

Create 2-4 sentence description including:
- Specific material names
- Lighting characteristics
- Texture details
- Atmospheric qualities
- Fashion-forward terminology

### Step 5: Construct Image Generation Prompt

```
Professional [studio/lifestyle] photography background for [product type].

BACKGROUND:
[Detailed description from Step 4]

LIGHTING:
- [Specific lighting setup]
- [Direction and quality]
- [Color temperature]

CAMERA:
- [Camera type and lens]
- [Aperture for depth effect]
- [Angle and framing]

MOOD: [Atmospheric qualities]

Professional product photography, commercial quality, natural camera detail.
```

## Examples

### Example 1: Luxury Watch (Studio)

**Input:**
- Product: Gold luxury watch
- Style: Premium, sophisticated
- Use: E-commerce hero image

**Background Description:**
"Elevated studio setup with gradient backdrop transitioning from deep charcoal to warm graphite, creating dimensional depth. Brushed metal accent panel on left third adds subtle industrial sophistication. Soft key light from 45-degree angle with fill light creating gentle shadows that emphasize the watch's metallic finish. Matte surface treatment prevents glare while maintaining rich tonal depth."

**Full Prompt:**
```
Professional studio photography background for luxury gold watch.

BACKGROUND:
Gradient backdrop transitioning from deep charcoal to warm graphite with dimensional depth, brushed metal accent panel on left creating industrial sophistication. Matte surface treatment, no glare.

LIGHTING:
- Soft diffused key light at 45 degrees with subtle fill
- Creating gentle shadows
- Cool neutral color temperature (5500K)

CAMERA:
- Medium format camera
- 85mm lens, f/5.6 for balanced depth
- Eye-level straight-on angle

MOOD: Refined, sophisticated, premium

Professional product photography, commercial quality, natural camera detail.
```

### Example 2: Casual Streetwear (Lifestyle)

**Input:**
- Product: Urban streetwear hoodie
- Style: Casual, authentic
- Use: Social media campaign

**Background Description:**
"Urban outdoor setting with textured concrete wall featuring natural weathering and subtle graffiti remnants, creating authentic street culture context. Warm afternoon sunlight casting diagonal shadows across the surface. Visible urban elements in soft focus background - metal fire escape, brick building corner. Raw, unpolished aesthetic with genuine environmental texture."

**Full Prompt:**
```
Professional lifestyle photography background for urban streetwear hoodie.

BACKGROUND:
Textured concrete wall with natural weathering and subtle graffiti remnants, authentic street culture aesthetic. Soft focus urban elements in background - metal fire escape, brick building. Raw, unpolished texture.

LIGHTING:
- Warm afternoon sunlight creating diagonal shadows
- Natural outdoor light
- Golden hour color temperature (3500K)

CAMERA:
- DSLR, 50mm lens, f/2.8 for shallow depth
- Eye-level angle
- Medium framing

MOOD: Authentic, urban, energetic

Professional fashion photography, editorial quality, natural camera detail.
```

### Example 3: Minimalist Home Decor (Lifestyle)

**Input:**
- Product: Ceramic vase
- Style: Minimalist, Scandinavian
- Use: Product catalog

**Background Description:**
"Modern minimalist interior with smooth plaster wall in warm off-white, natural oak floating shelf creating horizontal line. Soft diffused window light from right creating gentle gradient across wall. Subtle texture visible in plaster finish. Clean, serene Scandinavian aesthetic with emphasis on negative space and natural materials."

**Full Prompt:**
```
Professional lifestyle photography background for ceramic vase.

BACKGROUND:
Modern minimalist interior, smooth plaster wall in warm off-white, natural oak floating shelf. Subtle plaster texture visible. Clean Scandinavian aesthetic, emphasis on negative space.

LIGHTING:
- Soft diffused window light from right
- Creating gentle gradient
- Warm neutral color temperature (4500K)

CAMERA:
- Full-frame camera, 35mm lens, f/4
- Eye-level angle
- Environmental context framing

MOOD: Serene, minimal, natural

Professional interior photography, commercial quality, natural camera detail.
```

## Key Principles

1. **Specificity Over Generic**: Use "warm terracotta plaster" not "orange wall"
2. **Three-Level Material Specificity**: Base + construction + finish
3. **Fashion-Forward Language**: Editorial terminology, not basic descriptions
4. **Color Harmony**: Strategic complementary or contrasting palettes
5. **Lighting as Character**: Describe quality, direction, emotional impact
6. **Avoid Clichés**: No "modern," "dynamic," "sleek" without context
7. **Brand Alignment**: Background must elevate product's perceived value

## Common Mistakes to Avoid

- ❌ Generic descriptions: "nice background," "modern setting"
- ❌ Ignoring product style: luxury product with cheap-looking background
- ❌ Color clashes: competing colors that distract from product
- ❌ Over-complexity: too many elements competing for attention
- ❌ Flat lighting: no dimension or depth in the scene
- ❌ Inconsistent style: mixing studio and lifestyle awkwardly

## Integration Pattern

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "<background and integration prompt>" \
  "output/studio.png" \
  1 \
  "/absolute/path/to/model.jpg" \
  "/absolute/path/to/product.jpg" \
  --credential-name RIGHT_CODES_API_KEY \
  --model gpt-image-2 \
  --image-size 1K
```

## References

- Related Skills: product-analysis-styling, fashion-model-photography
- Provider: openai-compatible-image-provider
