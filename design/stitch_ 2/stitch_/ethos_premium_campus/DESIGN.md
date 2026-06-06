---
name: Ethos Premium Campus
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#414845'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#727975'
  outline-variant: '#c1c8c4'
  surface-tint: '#46645b'
  primary: '#001610'
  on-primary: '#ffffff'
  primary-container: '#0d2c24'
  on-primary-container: '#75958a'
  inverse-primary: '#adcec1'
  secondary: '#3a675a'
  on-secondary: '#ffffff'
  secondary-container: '#bceddd'
  on-secondary-container: '#406d60'
  tertiary: '#161209'
  on-tertiary: '#ffffff'
  tertiary-container: '#2b261c'
  on-tertiary-container: '#958d7f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c8eadd'
  primary-fixed-dim: '#adcec1'
  on-primary-fixed: '#012019'
  on-primary-fixed-variant: '#2f4c43'
  secondary-fixed: '#bceddd'
  secondary-fixed-dim: '#a1d0c1'
  on-secondary-fixed: '#002019'
  on-secondary-fixed-variant: '#214e43'
  tertiary-fixed: '#ece1d2'
  tertiary-fixed-dim: '#cfc5b6'
  on-tertiary-fixed: '#201b12'
  on-tertiary-fixed-variant: '#4c463b'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-lg:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  meta-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 20px
  gutter: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is built on a foundation of **Minimalism** and **Modern Corporate** aesthetics, specifically tailored for a premium campus environment. It moves away from youthful, high-saturation gradients toward a sophisticated, academic, and high-end tech feel. 

The brand personality is intellectual, calm, and exclusive. It targets university students and faculty who value clarity of information over visual noise. The emotional response should be one of "quiet confidence"—where the UI recedes to let campus discourse and AI interactions take center stage. Key stylistic pillars include generous white space (breathing room), precise typography, and a "tonal layer" approach to depth that replaces traditional heavy dropshadows or vibrant blurs.

## Colors

This design system utilizes a refined **Deep Charcoal & Emerald** palette, balanced by Morandi-inspired neutrals. 

- **Primary (#0D2C24):** A deep, near-black emerald used for primary headings, active states, and high-impact branding elements.
- **Secondary (#2D5A4E):** A muted forest green for accents, action icons, and subtle highlights.
- **Tertiary (#A89F91):** A warm, stony Morandi grey used for secondary text, metadata, and decorative borders.
- **Neutral (#F8F9FA):** A clinical, clean off-white for the main background to reduce eye strain and enhance the premium feel.

The "Color Mode" is strictly light-based to maintain the academic, paper-like quality of a premium journal, though surfaces use varying degrees of grey-washes to denote hierarchy.

## Typography

Typography is the core of this design system's premium identity. 
- **Manrope** is used for headings to provide a modern, geometric, yet approachable feel.
- **Inter** handles all body copy, ensuring maximum readability for long-form campus posts.
- **JetBrains Mono** is introduced sparingly for labels and tags (e.g., "#CampusLife"), lending a precise, technical edge that fits the "AI Assistant" context.

Spacing between lines (line-height) is intentionally generous to facilitate a relaxed reading experience. Headings use slight negative letter-spacing to appear tighter and more professional.

## Layout & Spacing

The layout follows a **Fixed-Fluid hybrid grid**. On mobile, it utilizes a 4-column system with 20px side margins to create a "framed" look that feels more premium than edge-to-edge designs.

The spacing rhythm is based on a 4px baseline grid. Elements are grouped using "Stack" variables to ensure vertical consistency. Increased whitespace is used between major sections (stack-lg) to clearly demarcate the "AI Hero" area from the "Community Feed." Cards and containers should never feel cramped; internal padding should gravitate toward the higher end of the scale (20px - 24px).

## Elevation & Depth

This design system rejects heavy, colored shadows in favor of **Tonal Layers** and **Soft Ambient Occlusion**.

- **Level 0 (Background):** #F8F9FA.
- **Level 1 (Cards/Surface):** Pure white (#FFFFFF) with a very thin 1px border in #E9ECEF.
- **Level 2 (Active/Floating):** Pure white with a subtle, 12% opacity neutral shadow (0px 4px 12px) to suggest light lift.

Depth is primarily communicated through color shifts (e.g., a slightly darker grey for a search bar background) rather than physical shadows, maintaining the minimalist ethos.

## Shapes

The shape language is **Soft (Level 1)**. 

To maintain a "high-end" and "architectural" feel, we avoid the overly bubbly appearance of the previous design. Standard components (Cards, Buttons) use a 4px - 8px radius. This provides a clean, professional edge while remaining modern. Large hero containers may use `rounded-lg` (8px), but never pill-shapes except for specific utility tags or the search input.

## Components

### Buttons
- **Primary:** Solid #0D2C24 with white text. No gradient. 8px corner radius.
- **Secondary:** Transparent background with a 1px border of #2D5A4E and matching text color.

### Cards
Cards are the primary container for the feed. They should feature a white background, a subtle 1px light grey border, and 20px of internal padding. Titles should use `headline-md` in the primary emerald-charcoal.

### AI Assistant Hero
Instead of the current blue gradient background, use a subtle, very light grey (#F1F3F5) background with a centered, high-resolution minimalist icon. The "AI Answer" prompt should feel like a premium search interface—clean, centered, and high-contrast.

### Chips & Tags
Use the `label-caps` typography. Backgrounds should be very desaturated Morandi tones (e.g., a very pale sage for #CampusLife) with dark text to ensure high-end legibility.

### Input Fields
Search bars and text inputs should use a light grey fill (#F1F3F5) with no border, becoming white with a primary-colored 1px border upon focus. This creates a "recessed-to-active" tactile feel.