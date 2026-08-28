# Worked Example — Photo of Two Monitors (big left, small right)

Session 2026-08-12: Nishant sent a photo of two screens — a big monitor on the left and a smaller screen on the right — and asked to crop out the big screen.

## Input
- File: `/data/hermes/image_cache/img_9ee05c59163c.jpg`
- Size: 1280 × 593, RGB

## Boundary analysis (what the profiles showed)

**Column brightness profile (step w//100 ≈ 12px):**
- x 0 → 840: brightness 70-126 (left screen content, darker tones)
- x ~852 → 864: jumps to 155-195 (right screen starts)
- So left content ≈ x 0-828, boundary zone x 829-856

**Fine scan x 760-920, per row band (Δ>20 transitions):**
- top (y 0-120): bright jump at x 829-835 (all white — environment/bezel band)
- mid (y 120-400): 829 (59→124), 830 (124→230), 834 (237→178), 835 (178→69) — bright strip at 830-834, back to dark
- bottom (y 400-593): 830 (92→132), 834 (136→90), 835 (90→24), 855 (24→47), 856 (47→169), 857 (169→248) — right screen truly begins at 856

**RGB at y=250 (disambiguation):**
- x 810-828: content tones (51-133)
- x 830-833: near-white (245-254) = bright bezel/edge strip of the LEFT screen
- x 835-855: dark (122 → 13) = gap between screens
- x 858+: near-black then content — right screen

**Row profile (left region x 0-834):**
- y 0-48: 220-255 (white environment band — ceiling/wall, NOT screen)
- y 50+: 83-113 (screen content starts at y ≈ 49-50)
- Bottom: content to y 592 (no bottom black bar)

## Crop decision
- Left big screen: x 0 → 834, y 49 → 593 (exclude top environment band)
- Output: 834 × 544 PNG (and 95-quality JPEG)
- Right screen: starts x ≈ 856 — excluded by the crop

## Key lesson encoded
The bright strip at x 830-834 belongs to the LEFT screen (its bright edge/bezel), while the dark zone x 835-855 is the separator gap. The right screen's first real content column is 856. Always use the dark gap, not the bright strip, as the crop separator.
