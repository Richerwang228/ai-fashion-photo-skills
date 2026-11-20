---
name: product-tryon-visualization
description: Generate realistic product try-on visualizations showing how garments, accessories, or products look when worn or used. Use for virtual try-on experiences, fit visualization, and helping customers see products in use before purchase.
license: Apache-2.0
metadata:
  author: ShopOS
  version: "1.0"
  category: image-generation
  source: workflow_garments_v2/implementation/usecases/flatlay_to_model.py
  requires: image-generation-tool
---

# Product Try-On Visualization

## When to Use This Skill

Use this skill when you need to:
- Create virtual try-on experiences for e-commerce
- Show how garments fit and drape on different body types
- Visualize accessories (jewelry, bags, shoes) being worn
- Help customers understand product scale and proportions
- Generate fit guides showing products on various models
- Create size comparison visualizations
- Reduce returns by showing accurate product representation

## Core Concepts

### Virtual Try-On vs Product Photography

**Virtual Try-On:**
- Shows product on model matching customer demographics
- Emphasizes fit, drape, and how product looks when worn
- Multiple body types and sizes for inclusivity
- Accurate scale and proportions
- Functional, clear product representation

**Product Photography:**
- Artistic, editorial styling
- Aspirational lifestyle contexts
- Brand storytelling focus
- May prioritize aesthetics over fit clarity

This skill focuses on **accurate try-on visualization** to help purchase decisions.

### Key Requirements

1. **Fit Accuracy**: Product must drape and fit realistically
2. **Scale Precision**: Correct proportions relative to body
3. **Material Behavior**: Fabric/material moves naturally
4. **Body Diversity**: Multiple body types for inclusivity
5. **Clear Visibility**: Product details clearly shown
6. **Realistic Integration**: Product looks naturally worn, not pasted on

## Step-by-Step Instructions

### Step 1: Analyze Product for Try-On

Extract critical information:
- **Product Type**: Garment, accessory, footwear, jewelry
- **Fit Type**: Slim, regular, relaxed, oversized
- **Material Properties**: Stiff, flowing, structured, stretchy
- **Key Features**: Details that must be visible
- **Size Information**: Dimensions, measurements
- **Wear Method**: How product is worn/used

### Step 2: Define Model Specifications

**Body Type Selection:**
- Petite (5'0"-5'4", smaller frame)
- Average (5'5"-5'8", medium frame)
- Tall (5'9"+, taller frame)
- Plus-size (various heights, fuller figure)
- Athletic (muscular, fit build)

**Demographics:**
- Age range matching target customer
- Ethnicity representing customer base
- Gender appropriate to product
- Skin tone diversity

**Pose Requirements:**
- Standing straight for fit assessment
- Arms at sides or natural position
- Front view as primary
- Optional: side view, back view for complete visualization

### Step 3: Specify Fit and Drape Behavior

**For Garments:**
- How fabric drapes over body
- Where garment sits (waist, hips, shoulders)
- Length relative to body (hem position)
- Sleeve length and fit
- Neckline position
- Natural wrinkles and folds

**For Accessories:**
- Scale relative to body/face
- Positioning (earrings on ears, bag on shoulder)
- How item hangs or sits
- Interaction with body/clothing

**For Footwear:**
- Foot positioning and angle
- How shoe fits foot
- Heel height effect on posture
- Visible details (laces, buckles, etc.)

### Step 4: Set Photography Parameters

**Lighting:**
- Even, clear lighting for product visibility
- No dramatic shadows that hide details
- Sufficient brightness to show colors accurately
- Soft shadows for dimension

**Camera:**
- Straight-on angle for fit assessment
- Full-body or appropriate crop for product type
- Sufficient distance to show proportions
- Clear focus on product

**Background:**
- Clean, neutral (white, light grey, soft color)
- No distractions from product
- Professional e-commerce standard

### Step 5: Construct Try-On Visualization Prompt

```
Professional product try-on photography of [MODEL DESCRIPTION] wearing [PRODUCT].

PURPOSE: Virtual try-on visualization for e-commerce, showing accurate fit and drape.

MODEL SPECIFICATIONS:
- Body Type: [Specific type - petite/average/tall/plus-size/athletic]
- Height: [Specific height]
- Build: [Specific build description]
- Demographics: [Age, gender, ethnicity]
- Skin Tone: [Specific description]

PRODUCT (EXACT FROM REFERENCE):
- [Product name and type]
- [Material and construction]
- [Color and finish]
- [Size being shown]

FIT AND DRAPE:
- [How product sits on body - specific positions]
- [Length relative to body - where hem/edge falls]
- [Fit type - how snug or loose]
- [Natural folds and drape behavior]
- [Key measurements visible]

POSE:
- Standing straight, front-facing
- Arms [at sides/natural position]
- Weight evenly distributed
- Natural, relaxed posture
- Clear view of product fit

PHOTOGRAPHY:
- Camera: Straight-on, eye-level
- Distance: [Full-body/three-quarter/appropriate for product]
- Lighting: Even, clear, no dramatic shadows
- Background: Clean [white/light grey/neutral]
- Focus: Sharp on product, showing all details

CRITICAL REQUIREMENTS:
- Product must fit realistically on this body type
- Fabric/material must drape naturally
- Scale and proportions must be accurate
- All product details must be clearly visible
- No artistic styling that obscures fit
- Professional e-commerce quality

Professional product try-on photography, accurate fit visualization, 
e-commerce standard, photorealistic, natural camera detail, clear product details.
```

## Examples

### Example 1: Dress Try-On (Multiple Body Types)

**Input:**
- Product: Floral midi dress
- Purpose: Show fit on different body types
- Sizes: S, M, L, XL

**Prompt for Average Build:**
```
Professional product try-on photography of a 5'6" woman with average build wearing a floral midi dress.

PURPOSE: Virtual try-on visualization showing accurate fit for size Medium.

MODEL SPECIFICATIONS:
- Body Type: Average build, proportional figure
- Height: 5'6" (168cm)
- Build: Size 6-8, medium frame, balanced proportions
- Demographics: 28 years old, female, mixed ethnicity
- Skin Tone: Medium with warm undertones

PRODUCT (EXACT FROM REFERENCE):
- Floral midi dress with V-neckline
- Lightweight cotton blend with slight stretch
- Navy blue base with pink floral print
- Size Medium being shown

FIT AND DRAPE:
- Dress sits naturally at shoulders, no pulling
- V-neckline positioned 3 inches below collarbone
- Waist seam sits at natural waistline
- Skirt drapes smoothly over hips
- Hem falls mid-calf, approximately 12 inches from floor
- Sleeves (if present) sit comfortably on arms
- Natural fabric movement, slight A-line silhouette

POSE:
- Standing straight, front-facing
- Arms relaxed at sides
- Weight evenly distributed on both feet
- Natural, comfortable posture
- Slight smile, approachable expression

PHOTOGRAPHY:
- Camera: Straight-on, eye-level
- Distance: Full-body shot with small margin above head and below feet
- Lighting: Even studio lighting, no harsh shadows
- Background: Clean white backdrop
- Focus: Sharp on dress, showing print details and drape

CRITICAL REQUIREMENTS:
- Dress must fit true to size Medium on this body type
- Fabric must drape naturally, showing how it moves
- Length must be accurate to product specifications
- Floral print must be clearly visible
- No styling that obscures fit (no belts, layers unless part of product)
- Professional e-commerce quality for online shopping

Professional product try-on photography, accurate fit visualization for size Medium,
e-commerce standard, photorealistic, natural camera detail, clear product details.
```

**Prompt for Plus-Size:**
```
[Same structure but with:]

MODEL SPECIFICATIONS:
- Body Type: Plus-size, fuller figure
- Height: 5'7" (170cm)
- Build: Size 16-18, curvy proportions, fuller bust and hips
- Demographics: 32 years old, female, African American
- Skin Tone: Deep brown with warm undertones

PRODUCT:
- Size XL being shown

FIT AND DRAPE:
- Dress accommodates fuller bust comfortably
- Waist seam sits at natural waistline without pulling
- Skirt drapes smoothly over curves
- Fabric has enough ease for comfortable movement
- Hem falls mid-calf as designed
- No strain at seams, comfortable fit throughout
```

### Example 2: Jewelry Try-On

**Input:**
- Product: Statement necklace
- Purpose: Show scale and positioning

**Prompt:**
```
Professional product try-on photography of a woman wearing a gold statement necklace.

PURPOSE: Virtual try-on showing necklace scale, positioning, and how it looks when worn.

MODEL SPECIFICATIONS:
- Body Type: Average build, medium frame
- Height: 5'6"
- Build: Proportional, size 6-8
- Demographics: 30 years old, female, South Asian
- Skin Tone: Medium with golden undertones

PRODUCT (EXACT FROM REFERENCE):
- Gold-tone statement necklace with geometric pendant
- Chain length: 18 inches
- Pendant dimensions: 2 inches wide, 3 inches long
- Brushed gold finish

FIT AND POSITIONING:
- Chain sits at collarbone level (18-inch length)
- Pendant hangs centered on chest
- Pendant positioned approximately 4 inches below collarbone
- Chain drapes naturally around neck
- Clasp at back of neck (not visible)
- No tangling or twisting

POSE:
- Standing straight, front-facing, chest-up shot
- Shoulders back, good posture
- Head straight, looking at camera
- Neck clearly visible
- Arms not visible (cropped at shoulders)

STYLING:
- Simple solid-color top (black or white) to not compete with necklace
- No other jewelry visible
- Hair pulled back or styled away from necklace
- Minimal makeup, focus on necklace

PHOTOGRAPHY:
- Camera: Straight-on, chest-level
- Distance: Chest-up portrait, showing necklace clearly
- Lighting: Even lighting on necklace and skin
- Background: Clean white backdrop
- Focus: Sharp on necklace, showing metal finish and details

CRITICAL REQUIREMENTS:
- Necklace scale must be accurate to actual size
- Positioning must show where 18-inch chain sits
- Pendant must hang naturally, not stiff
- Metal finish must be clearly visible
- No other elements competing for attention
- Professional jewelry e-commerce quality

Professional jewelry try-on photography, accurate scale visualization,
e-commerce standard, photorealistic, natural camera detail, clear product details.
```

### Example 3: Footwear Try-On

**Input:**
- Product: Ankle boots
- Purpose: Show fit and heel height effect

**Prompt:**
```
Professional product try-on photography showing ankle boots being worn.

PURPOSE: Virtual try-on showing boot fit, heel height, and how they look on foot.

MODEL SPECIFICATIONS:
- Body Type: Average build
- Height: 5'7"
- Foot: Women's size 8, average width
- Demographics: 27 years old, female, European descent
- Skin Tone: Fair with neutral undertones

PRODUCT (EXACT FROM REFERENCE):
- Black leather ankle boots
- 3-inch block heel
- Side zipper closure
- Pointed toe
- Size 8 being shown

FIT AND POSITIONING:
- Boots fit snugly around ankle
- Shaft height: 6 inches from floor
- Heel adds 3 inches to height
- Toe box fits comfortably, no squeezing
- Zipper fully closed, lying flat
- Boots positioned naturally on feet

POSE:
- Standing straight, slight angle to show boot profile
- Weight on both feet evenly
- Feet positioned naturally, slight V-stance
- Lower body visible (knees to feet)
- Wearing fitted dark jeans to show boot shaft clearly

PHOTOGRAPHY:
- Camera: Slight high angle looking down at 30 degrees
- Distance: Knees to feet visible, boots as focal point
- Lighting: Even lighting showing leather texture
- Background: Clean white floor/backdrop
- Focus: Sharp on boots, showing leather finish and details

CRITICAL REQUIREMENTS:
- Boot fit must look realistic on foot
- Heel height effect on posture must be accurate
- Leather texture and finish must be visible
- Boot shaft height relative to ankle must be clear
- Zipper and hardware details must be shown
- Professional footwear e-commerce quality

Professional footwear try-on photography, accurate fit and heel height visualization,
e-commerce standard, photorealistic, natural camera detail, clear product details.
```

## Key Principles

1. **Fit Accuracy First**: Realistic fit trumps artistic styling
2. **Scale Precision**: Correct proportions are critical
3. **Body Diversity**: Show multiple body types for inclusivity
4. **Clear Visibility**: All product details must be seen
5. **Natural Drape**: Materials must behave realistically
6. **E-commerce Standard**: Professional, clean, clear imagery
7. **Purchase Decision Support**: Help customers visualize ownership

## Common Mistakes to Avoid

- ❌ Unrealistic fit (too perfect, doesn't account for body shape)
- ❌ Wrong scale (product too large or small for body)
- ❌ Artistic styling that obscures fit
- ❌ Dramatic lighting that hides details
- ❌ Only showing one body type
- ❌ Unnatural draping or stiff materials
- ❌ Busy backgrounds that distract

## Integration Pattern

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "<try-on prompt identifying reference order>" \
  "output/base-tryon.png" \
  1 \
  "/absolute/path/to/model.jpg" \
  "/absolute/path/to/top-front.jpg" \
  "/absolute/path/to/bottom-front.jpg" \
  --credential-name RIGHT_CODES_API_KEY \
  --model gpt-image-2 \
  --image-size 1K
```

## References

- Related Skills: product-analysis-styling, fashion-model-photography
- Provider: openai-compatible-image-provider
