# DESIGN.md

## Design read
Product landing for Linux power users, craft-tool language, signal emerald on pure iron surfaces. Not SaaS cream, not purple mesh, not editorial magazine.

## Dials
- DESIGN_VARIANCE: 7
- MOTION_INTENSITY: 5
- VISUAL_DENSITY: 4

## Color strategy: Committed
Emerald carries identity. Surfaces stay pure (white / near-black). No multi-accent rainbow icons.

| Role | Light | Dark |
|------|-------|------|
| bg | #FFFFFF | #0C0C0E |
| surface | #F4F4F5 | #16161A |
| ink | #09090B | #FAFAFA |
| muted | #52525B | #A1A1AA |
| primary | #2F9E5F | #50C878 |
| border | #E4E4E7 | #27272A |

## Typography
- Display/body: Geist Sans (project standard)
- Code/terminal: Geist Mono
- Scale: bold display, relaxed body, tight mono for install

## Shape
Radius 10–12px for panels, full-pill only for small chips. No 32px soft cards.

## Layout families on the page
1. Compact sticky nav
2. Asymmetric split hero (copy + real screenshot)
3. Full-bleed terminal install strip
4. Spec rail (offline / X11 / engines as text, not icon cards)
5. Live demo island
6. Asymmetric feature bento with screenshot cells
7. Process steps (install → configure → dictate)
8. Engine comparison as dense list, not rainbow cards
9. FAQ details stack
10. Ecosystem + footer

## Motion
Entrance fade/slide on hero only; section reveals via whileInView. Ease-out expo. Honor prefers-reduced-motion.

## Imagery
Real app screenshots from `/public/screenshots/`. No fake div UIs. No decorative SVG illustrations.
