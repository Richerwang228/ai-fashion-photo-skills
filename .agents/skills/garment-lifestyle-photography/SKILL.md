---
name: garment-lifestyle-photography
description: Generate lifestyle photography of garments in real-world contexts with models in natural environments. Use when creating aspirational fashion content, social media imagery, or editorial-style product photography that shows garments in authentic lifestyle settings.
license: Apache-2.0
metadata:
  author: ShopOS
  version: "1.0"
  category: image-generation
  source: workflow_garments_v2/implementation/usecases/flatlay_to_model.py
  requires: image-generation-tool
---

# Garment Lifestyle Photography

## When to Use This Skill

Use this skill when you need to:
- Create lifestyle fashion photography with models in natural settings
- Generate aspirational content showing garments in real-world contexts
- Produce social media content with authentic, relatable imagery
- Create editorial-style fashion photography for campaigns
- Show garments being worn in everyday situations
- Generate content that tells a lifestyle story around the product

## Core Concepts

### Lifestyle vs Studio Photography

**Lifestyle Photography:**
- Real-world environments (cafes, streets, parks, homes)
- Natural lighting and authentic settings
- Models in natural, unposed moments
- Contextual storytelling
- Aspirational yet relatable

**Studio Photography:**
- Controlled environments with backdrops
- Professional lighting setups
- Clean, product-focused compositions
- Minimal distractions

This skill focuses on **lifestyle photography** to create emotional connections and show products in context.

### Key Elements

1. **Authentic Environments**: Real locations that match target audience lifestyle
2. **Natural Moments**: Mid-breath, candid-feeling captures
3. **Contextual Props**: Elements that support the lifestyle narrative
4. **Relatable Scenarios**: Situations the target audience experiences
5. **Emotional Connection**: Images that evoke feelings and aspirations

## Step-by-Step Instructions

### Step 1: Analyze Garment and Target Audience

Extract from product:
- Garment type and style (casual, formal, sporty, elegant)
- Target demographic (age, gender, lifestyle)
- Brand positioning (budget, mid-market, premium, luxury)
- Occasion suitability (everyday, work, weekend, special events)
- Season and climate considerations

### Step 2: Select Lifestyle Context

Choose environment based on garment and audience:

**Urban Lifestyle:**
- City streets, coffee shops, rooftop terraces
- Modern architecture, industrial spaces
- Public transportation, bike paths
- Urban parks, street markets

**Casual Lifestyle:**
- Home environments, cozy interiors
- Neighborhood cafes, local shops
- Parks, gardens, outdoor spaces
- Relaxed social settings

**Active Lifestyle:**
- Outdoor activities, hiking trails
- Beach, waterfront, nature settings
- Sports venues, fitness contexts
- Adventure and exploration scenes

**Professional Lifestyle:**
- Office environments, co-working spaces
- Business districts, corporate settings
- Professional events, meetings
- Commute scenarios

**Social Lifestyle:**
- Restaurants, bars, social venues
- Events, gatherings, celebrations
- Cultural venues, galleries, theaters
- Group activities, friend gatherings

### Step 3: Define Model and Styling

**Model Characteristics:**
- Demographics matching target audience
- Natural, relatable appearance
- Authentic expressions and body language
- Appropriate for lifestyle context

**Styling Approach:**
- Featured garment as hero piece
- Complementary items from product analysis
- Accessories appropriate to context
- Natural, effortless styling

### Step 4: Compose the Scene

**Environmental Elements:**
- Specific location details (materials, textures, colors)
- Contextual props that support narrative
- Background activity or elements (soft focus)
- Lighting conditions (natural, golden hour, overcast)

**Model Positioning:**
- Natural, unposed moments
- Interaction with environment
- Authentic activities (walking, sitting, talking)
- Genuine expressions and gestures

**Camera Approach:**
- Documentary-style framing
- Environmental context visible
- Natural perspective (eye-level, slight angles)
- Depth and layering

### Step 5: Construct Lifestyle Photography Prompt

```
Professional lifestyle fashion photography of [MODEL DESCRIPTION] wearing [GARMENT] in [SPECIFIC LOCATION].

SCENE & CONTEXT:
[Detailed environment description with specific location, time of day, atmosphere]

MODEL:
- Demographics: [Age, gender, ethnicity, body type]
- Appearance: [Natural features, hair, expression]
- Activity: [What they're doing - walking, sitting, interacting]
- Expression: [Genuine emotion - relaxed, confident, joyful]

GARMENT (HERO PIECE):
- [Exact garment from product image]
- [How it's being worn - naturally, casually styled]

STYLING:
- Complementary items: [Specific pieces]
- Footwear: [Appropriate to context]
- Accessories: [Minimal, contextual]

ENVIRONMENT:
- Location: [Specific setting with details]
- Props: [Contextual elements - coffee cup, book, bike, etc.]
- Background: [What's visible in soft focus]
- Lighting: [Natural light quality and direction]

PHOTOGRAPHY:
- Camera: [DSLR/mirrorless, documentary style]
- Lens: [35mm or 50mm for environmental context]
- Aperture: [f/2.8-f/4 for subject focus with context]
- Angle: [Eye-level or slight variation]
- Composition: [Environmental, rule of thirds]

MOOD: [Authentic, relatable, aspirational, lifestyle-specific emotion]

Professional lifestyle fashion photography, editorial quality, natural moments, 
authentic storytelling, photorealistic, natural camera detail.
```

## Examples

### Example 1: Casual Weekend Brunch

**Input:**
- Garment: Oversized cream knit sweater
- Target: Women 25-35, urban professionals
- Context: Weekend lifestyle

**Prompt:**
```
Professional lifestyle fashion photography of a 28-year-old woman wearing an oversized cream knit sweater at a trendy neighborhood cafe during weekend brunch.

SCENE & CONTEXT:
Bright, airy cafe with large windows, natural morning light streaming in. Warm, inviting atmosphere with wooden tables, potted plants, and soft background chatter. Late morning, relaxed weekend vibe.

MODEL:
- Demographics: 28-year-old female, European descent, slim build
- Appearance: Natural wavy brown hair, minimal makeup, genuine warm smile
- Activity: Sitting at cafe table, hands wrapped around coffee mug, mid-conversation
- Expression: Relaxed, content, genuinely enjoying the moment

GARMENT (HERO PIECE):
- Oversized cream knit sweater with ribbed texture
- Worn casually with sleeves slightly pushed up
- Natural drape showing cozy, comfortable fit

STYLING:
- Complementary items: High-waisted light wash jeans (partially visible)
- Accessories: Simple gold hoop earrings, delicate necklace
- Natural, effortless weekend styling

ENVIRONMENT:
- Location: Corner table by large window in modern cafe
- Props: Ceramic coffee mug, small plate with pastry, open book
- Background: Soft focus cafe interior, other patrons blurred, plants
- Lighting: Natural window light from left, soft and diffused

PHOTOGRAPHY:
- Camera: Professional DSLR, documentary style
- Lens: 50mm for natural perspective
- Aperture: f/2.8 for subject focus with environmental context
- Angle: Eye-level, slight three-quarter view
- Composition: Rule of thirds, model on right, window light on left

MOOD: Relaxed, cozy, aspirational weekend lifestyle, authentic contentment

Professional lifestyle fashion photography, editorial quality, natural moment, 
authentic storytelling, photorealistic, natural camera detail.
```

### Example 2: Urban Commute

**Input:**
- Garment: Navy blue blazer
- Target: Men 30-40, professionals
- Context: Work commute

**Prompt:**
```
Professional lifestyle fashion photography of a 32-year-old man wearing a navy blue blazer walking through modern city streets during morning commute.

SCENE & CONTEXT:
Urban downtown area with glass buildings and morning light. Professional district atmosphere, other commuters in soft focus background. Early morning, energetic city vibe.

MODEL:
- Demographics: 32-year-old male, mixed ethnicity, athletic build
- Appearance: Short styled hair, clean-shaven, confident expression
- Activity: Walking purposefully, coffee cup in hand, mid-stride
- Expression: Focused, confident, ready for the day

GARMENT (HERO PIECE):
- Navy blue tailored blazer with modern slim fit
- Worn over white shirt, professional yet contemporary
- Natural movement captured mid-walk

STYLING:
- Complementary items: White dress shirt, dark grey trousers
- Footwear: Brown leather oxford shoes
- Accessories: Leather messenger bag, simple watch
- Professional but not overly formal

ENVIRONMENT:
- Location: Modern city sidewalk with glass building facades
- Props: Reusable coffee cup, messenger bag strap visible
- Background: Blurred urban architecture, other professionals walking
- Lighting: Natural morning sunlight creating dynamic shadows

PHOTOGRAPHY:
- Camera: Professional DSLR, street photography style
- Lens: 35mm for environmental storytelling
- Aperture: f/4 for balanced subject and context
- Angle: Eye-level, slight side angle capturing movement
- Composition: Dynamic, model in left third, walking into frame

MOOD: Confident, professional, urban energy, modern lifestyle

Professional lifestyle fashion photography, editorial quality, authentic moment, 
urban storytelling, photorealistic, natural camera detail.
```

### Example 3: Outdoor Adventure

**Input:**
- Garment: Olive green utility jacket
- Target: Unisex 25-35, outdoor enthusiasts
- Context: Weekend hiking

**Prompt:**
```
Professional lifestyle fashion photography of a 27-year-old person wearing an olive green utility jacket on a scenic hiking trail during golden hour.

SCENE & CONTEXT:
Mountain hiking trail with forest surroundings, golden hour light filtering through trees. Peaceful outdoor atmosphere, connection with nature. Late afternoon, warm glow.

MODEL:
- Demographics: 27-year-old, gender-neutral, fit athletic build
- Appearance: Natural windswept hair, sun-kissed skin, genuine smile
- Activity: Pausing on trail, looking at scenic view, backpack on
- Expression: Peaceful, adventurous, connected with nature

GARMENT (HERO PIECE):
- Olive green utility jacket with multiple pockets
- Worn open over base layer, practical outdoor styling
- Natural wear showing functionality

STYLING:
- Complementary items: Grey base layer tee, dark hiking pants
- Footwear: Hiking boots (partially visible)
- Accessories: Backpack straps visible, simple watch
- Practical, adventure-ready styling

ENVIRONMENT:
- Location: Forest hiking trail with mountain vista in background
- Props: Hiking backpack, water bottle attached to pack
- Background: Soft focus forest, mountain peaks, natural landscape
- Lighting: Golden hour sunlight from side, warm natural glow

PHOTOGRAPHY:
- Camera: Professional DSLR, outdoor adventure style
- Lens: 35mm for environmental context
- Aperture: f/4 for subject focus with scenic background
- Angle: Eye-level, slight low angle showing landscape
- Composition: Rule of thirds, model on right, vista on left

MOOD: Adventurous, peaceful, connected with nature, authentic outdoor lifestyle

Professional lifestyle fashion photography, editorial quality, natural outdoor moment, 
adventure storytelling, photorealistic, natural camera detail.
```

## Key Principles

1. **Authenticity Over Perfection**: Natural moments trump posed perfection
2. **Context Tells Story**: Environment should support lifestyle narrative
3. **Relatable Scenarios**: Situations target audience experiences
4. **Natural Lighting**: Prefer natural light for authentic feel
5. **Environmental Depth**: Show context, not just subject
6. **Genuine Expressions**: Real emotions, not forced smiles
7. **Appropriate Props**: Elements that belong in the scene

## Common Mistakes to Avoid

- ❌ Overly posed, catalog-style shots
- ❌ Generic "lifestyle" without specific context
- ❌ Inappropriate environments for garment style
- ❌ Forced, unnatural expressions
- ❌ Too many competing elements in scene
- ❌ Ignoring target audience lifestyle
- ❌ Studio lighting in "lifestyle" settings

## Integration Pattern

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "<natural lifestyle prompt>" \
  "output/lifestyle.png" \
  1 \
  "/absolute/path/to/model.jpg" \
  "/absolute/path/to/top.jpg" \
  "/absolute/path/to/bottom.jpg" \
  --credential-name RIGHT_CODES_API_KEY \
  --model gpt-image-2 \
  --image-size 1K
```

## References

- Related Skills: product-analysis-styling, fashion-model-photography
- Provider: openai-compatible-image-provider
