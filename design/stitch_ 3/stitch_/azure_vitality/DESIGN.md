---
name: Azure Vitality
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3f4852'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6f7883'
  outline-variant: '#bec7d4'
  surface-tint: '#00629d'
  primary: '#00629d'
  on-primary: '#ffffff'
  primary-container: '#00a3ff'
  on-primary-container: '#00375a'
  inverse-primary: '#98cbff'
  secondary: '#006b5b'
  on-secondary: '#ffffff'
  secondary-container: '#26fedc'
  on-secondary-container: '#007261'
  tertiary: '#a53b29'
  on-tertiary: '#ffffff'
  tertiary-container: '#f57760'
  on-tertiary-container: '#6a1004'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cfe5ff'
  primary-fixed-dim: '#98cbff'
  on-primary-fixed: '#001d33'
  on-primary-fixed-variant: '#004a77'
  secondary-fixed: '#26fedc'
  secondary-fixed-dim: '#00dfc1'
  on-secondary-fixed: '#00201a'
  on-secondary-fixed-variant: '#005144'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a6'
  on-tertiary-fixed: '#3f0300'
  on-tertiary-fixed-variant: '#842415'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display:
    fontFamily: Manrope
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

The brand personality is defined by an high-kinetic energy that feels fresh, modern, and light. It targets a forward-thinking audience that values clarity and momentum. The design system leverages a **Modern Minimalist** style infused with **Vibrant Color Theory**, where whitespace is not just empty but serves as a pressurized containment for high-saturation accents.

The emotional response should be one of "effortless speed" and "clarity." By using a bright oceanic palette with increased saturation, the UI feels alive and responsive. The visual language balances professional structure with an optimistic, youthful spirit through the use of soft blurs and rhythmic spacing.

## Colors

The palette is anchored by an energetic **Azure Blue** (#00A3FF) that acts as the primary driver for interaction and focus. This is complemented by a **Vibrant Mint** (#00F5D4) for success states and secondary actions, adding a refreshing "cool" factor. **Soft Coral** (#FF7E67) provides a warm, energetic counter-point for high-attention callouts.

Backgrounds are kept exceptionally clean using #F8FAFC, while secondary containers use a #E0F2FE tint to maintain the "Oceanic" lineage without sacrificing legibility. Neutral tones avoid pure blacks, opting instead for a deep Slate (#0F172A) to keep the shadows and text feeling organic to the blue-dominant ecosystem.

## Typography

This design system utilizes **Manrope** exclusively to maintain a modern, technical, yet approachable aesthetic. The type scale is optimized for high-information environments, using tight letter-spacing on larger headings to create a "locked-in" professional feel.

Hierarchy is established through significant weight contrast rather than just size. Display styles utilize ExtraBold (800) for a punchy, energetic impact, while body text remains in Medium (400/500) weights to ensure breathability and legibility against the vibrant color palette.

## Layout & Spacing

The layout follows a **Fluid Grid** philosophy based on an 8px base unit. This ensures vertical rhythm and consistent density across all screen sizes. For desktop, a 12-column grid with generous 64px outer margins is preferred to create a sense of lightness and "open water" expanse.

Mobile layouts transition to a 4-column structure with 16px margins. Padding within containers should be generous (md: 24px) to prevent the energetic colors from feeling cramped or overwhelming the content.

## Elevation & Depth

Hierarchy is achieved through **Tonal Layers** and **Ambient Shadows**. Surfaces do not use heavy dark shadows; instead, they utilize "Azure Glows"—low-opacity shadows tinted with the primary blue color (e.g., `rgba(0, 163, 255, 0.12)`).

- **Level 0 (Floor):** The base background (#F8FAFC).
- **Level 1 (Cards):** Pure white surfaces with a 1px border of #E2E8F0.
- **Level 2 (Floating):** Soft, diffused shadows with a 12px blur, used for hover states and menus.
- **Level 3 (Modals):** High-contrast depth with a 32px blur and a subtle glassmorphic backdrop filter (10px blur) on the overlay to maintain the "Modern" ethos.

## Shapes

The design system employs a **Rounded** (Level 2) shape language. This provides a professional structural foundation while the 0.5rem (8px) base radius ensures the interface feels friendly and accessible. 

- **Standard Elements:** 8px radius (buttons, inputs, small cards).
- **Large Containers:** 16px radius (main content areas, large cards).
- **Feature Elements:** 24px radius (call-to-action banners, hero images).

## Components

### Buttons
- **Primary:** Solid #00A3FF background with white text. Use a slight scale-up transform (1.02x) on hover.
- **Secondary:** White background with #00A3FF border and text.
- **Ghost:** No border, #00A3FF text, with a light #E0F2FE background appearing only on hover.

### Inputs & Form Fields
Fields use a clean white background with a subtle 1px #CBD5E1 border. Upon focus, the border transitions to Primary Azure with a soft 4px outer glow of the same color. Labels use `label-md` for maximum clarity.

### Chips & Badges
Badges use high-saturation backgrounds with 10% opacity for the fill and 100% opacity for the text. For example, a "Success" badge uses a #00F5D4 tint with dark teal text.

### Cards
Cards are the primary container. They feature a white background, the 8px corner radius, and a 1px #F1F5F9 stroke. Shadows should only be applied to cards that are interactive or elevated in the hierarchy.

### Lists
List items are separated by whitespace and light #F1F5F9 dividers. Use the Primary Azure for icons within lists to guide the eye downward through the information.