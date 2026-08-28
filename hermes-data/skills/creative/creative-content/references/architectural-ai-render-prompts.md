# Architectural AI Render Prompts

Methodology for creating detailed architectural material prompts for AI image generation (GPT, Midjourney, etc.) — especially for real estate marketing offices, sales galleries, and villa project presentation materials.

## When to Use

- User asks to create/refine prompts for architectural renders
- User shares a base render or reference image and wants material variations
- User needs to generate marketing/presentation images for a real estate project
- Creating prompt libraries for design exploration

## Core Methodology

### Step 1: Analyze the Base Image

When the user shares a reference image, extract:
- **Dominant colors** via PIL: sample pixels in vertical bands (sky, upper facade, mid facade, lower facade, landscape)
- **Material palette** from the user's description of what they want
- **Architectural composition**: single/two-storey, roof type, fenestration, fin/screen details

### Step 2: Structure Every Prompt in These Sections

Each prompt MUST have these 7 blocks:

1. **Opening line**: "Architectural exterior 3D render of a modern luxury marketing office building for '[PROJECT NAME]'..."

2. **MATERIALS** — list each element with exact material name, finish, color:
   - Walls (primary cladding)
   - Fins / brise-soleil (vertical screening)
   - Soffits (roof ceiling)
   - Roof edge trim / coping
   - Glazing (glass type and frame color)
   - Base / plinth
   - Any accent features

3. **SIGNAGE & BRANDING** — always include:
   - Prominent feature wall for project signage
   - Dedicated wayfinder signage wall
   - Wall space for project logo display
   - Monument sign area near entrance

4. **ARCHITECTURE** — describe the form and style:
   - Modern villa-inspired / contemporary / traditional
   - Number of storeys, roof type
   - Key architectural features (fin walls, overhangs, etc.)
   - Entrance treatment

5. **LANDSCAPING** — planting style and features

6. **SETTING** — sky type, time of day, color palette summary

7. **Final line**: "Photorealistic architectural visualization, V-Ray quality. Ground-level perspective, slight eye-level angle looking up."

### Step 3: Create Variations by Swapping the MATERIALS Block Only

Keep the SIGNAGE, ARCHITECTURE, LANDSCAPING, and SETTING sections identical. Only change the MATERIALS section. This ensures the composition stays the same while the look changes.

### Step 4: Present Each Prompt as a Separate Code Block

The user needs to copy-paste each prompt individually into an LLM with their base image. Format each as:

    ```
    [full prompt text here]
    ```

Separate code blocks with dividers so each one gets its own Copy button.

## Local Indian Stone Reference

Common natural stones available in Bangalore/India for architectural cladding:

| Stone | Color | Best For |
|-------|-------|----------|
| **Kadappa Black** | Dark grey-black limestone | Plinths, blockwork walls, flooring |
| **Cuddapah** | Dark grey-black | Vertical fins, paving |
| **Jaisalmer Yellow** | Warm honey-yellow | Wall cladding, feature walls |
| **Dholpur Grey** | Khaki/olive-grey | Wall cladding, contemporary |
| **Kota Brown** | Warm brown | Flooring, wall cladding |
| **Travertine** | Cream-beige with veins | Premium wall cladding |
| **White Blush** | White with pink undertone | Contemporary facades |
| **Granite (Black)** | Black | Plinths, base, paving |

## Example Material Combinations

### Warm Earthy (Travertine + Bronze)
- Walls: Vein-cut travertine, cream-beige
- Fins: Champagne bronze anodized aluminium
- Soffits: Teak wood finish
- Roof: Brushed bronze
- Glass: Warm grey low-E

### Dark Dramatic (Kadappa Black + Brass)
- Walls: Black Kadappa stone, lateral blockwork, honed
- Accent: White marble or cream travertine
- Fins: Brushed brass or antique gold aluminium
- Soffits: Warm teak or dark walnut
- Roof: Blackened steel
- Glass: Warm grey low-E, black frames

### Mediterranean (White Plaster + Blue)
- Walls: Smooth white lime plaster/stucco
- Fins: White-painted metal or white-washed timber
- Soffits: White-washed timber
- Accent: Deep Aegean blue details
- Glass: Clear low-E

### Indian Vernacular (Terracotta + Stone)
- Walls: Travertine brick stone blockwork
- Fins: Terracotta or Jaisalmer sandstone jaali
- Soffits: Recycled teak or jackfruit wood
- Glass: Clear with grey tint, dark bronze frames
- Base: Kuddapah black stone

### Urban Luxe (Grey + Brass)
- Walls: Dholpur grey / khaki grey stone
- Fins: Brass or brushed gold aluminium
- Soffits: Dark walnut
- Glass: Grey tinted low-E with brass frames

## Formatting Rule (User Preference)

Always present LLM-bound prompts as separate code blocks (``` ... ```) with spacing between them so each one gets its own Copy button on Telegram. Never embed prompts inside paragraphs, tables, or as raw text.
