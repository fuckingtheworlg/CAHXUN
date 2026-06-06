---
name: Vibrant Campus
colors:
  surface: '#fef7ff'
  surface-dim: '#ded7e4'
  surface-bright: '#fef7ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f8f1fe'
  surface-container: '#f3ebf8'
  surface-container-high: '#ede5f3'
  surface-container-highest: '#e7e0ed'
  on-surface: '#1d1a23'
  on-surface-variant: '#494454'
  inverse-surface: '#322f39'
  inverse-on-surface: '#f5eefb'
  outline: '#7b7486'
  outline-variant: '#cbc3d7'
  surface-tint: '#6d3bd7'
  primary: '#6b38d4'
  on-primary: '#ffffff'
  primary-container: '#8455ef'
  on-primary-container: '#fffbff'
  inverse-primary: '#d0bcff'
  secondary: '#006877'
  on-secondary: '#ffffff'
  secondary-container: '#3fe1fd'
  on-secondary-container: '#00616f'
  tertiary: '#6d5e00'
  on-tertiary: '#ffffff'
  tertiary-container: '#c4ab01'
  on-tertiary-container: '#4a3f00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#a2eeff'
  secondary-fixed-dim: '#2fd9f4'
  on-secondary-fixed: '#001f25'
  on-secondary-fixed-variant: '#004e5a'
  tertiary-fixed: '#ffe24c'
  tertiary-fixed-dim: '#e2c62d'
  on-tertiary-fixed: '#211b00'
  on-tertiary-fixed-variant: '#524600'
  background: '#fef7ff'
  on-background: '#1d1a23'
  surface-variant: '#e7e0ed'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Be Vietnam Pro
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  base: 8px
  container-margin: 24px
  gutter: 16px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style
The design system is anchored in a high-energy, "bubbly" aesthetic tailored for a lively campus community. It balances modern technical precision with a playful, approachable personality. The visual narrative is driven by fluid motion, soft geometry, and a sense of "floating" elements that evoke optimism and social connectivity.

Drawing from **Modernism** and **Glassmorphism**, the style utilizes layered transparency and vibrant mesh gradients to create depth without heaviness. The goal is to make every interaction feel lighthearted and rewarding, transforming routine campus tasks into engaging digital experiences.

## Colors
The palette is built on a foundation of high-vibrancy "electric" pastels. 
- **Primary (Soft Violet):** Used for main actions and brand signifiers, providing a sophisticated yet friendly anchor.
- **Secondary (Bright Cyan):** Injected into interactive elements and success states to provide energy.
- **Accents (Lemon Yellow & Soft Pink):** Reserved for highlights, badges, and celebratory UI moments (like "Event Joined" or "New Message").
- **Gradients:** Use multi-point mesh gradients blending Violet, Cyan, and Pink for large surface areas (headers, hero cards). Ensure the blending is soft and the contrast remains high enough for overlaid white text.
- **Surface:** Avoid pure whites; use a subtle tint of the primary color at 2-5% opacity for backgrounds to maintain the "bubbly" atmosphere.

## Typography
The typography uses **Plus Jakarta Sans** for headlines to leverage its soft, rounded terminals and modern geometric construction. This creates an immediate "friendly" first impression. 

**Be Vietnam Pro** is used for body and labels to ensure maximum legibility at smaller sizes while maintaining a contemporary, approachable feel. 

- **Weight Usage:** Use "ExtraBold" or "Bold" for headlines to create a strong visual hierarchy against the soft shapes of the UI.
- **Scaling:** On mobile, headlines should reduce in size but maintain their tight letter-spacing to preserve the "bold" brand character.

## Layout & Spacing
The layout follows a **fluid grid** system designed for high density on mobile (campus schedules, social feeds) and generous whitespace on desktop.

- **Grid:** 12-column layout for desktop, 4-column for mobile.
- **Rhythm:** An 8px base unit drives all padding and margins. 
- **Bubbly Expansion:** Use generous internal padding within cards and buttons (at least 20px for cards) to ensure content doesn't feel cramped, supporting the "lighthearted" and "approachable" narrative.
- **Floating Margins:** Elements should rarely touch the edges of the viewport; use significant side margins (24px+) to enhance the "floating" aesthetic.

## Elevation & Depth
Depth is created through **Tonal Layers** and **Colored Shadows** rather than traditional gray-scale shadows.

- **Shadow Character:** Use large blur radii (20px-40px) with low opacity (10-15%). The shadow color should match the background of the element or the primary brand color (e.g., a violet shadow for a violet button).
- **Floating Effect:** Increase the Y-offset of shadows as elements gain importance. A "Primary Action Button" should appear to float higher than a "Static Card."
- **Glassmorphism:** Use backdrop blurs (12px to 20px) for navigation bars and overlays. Apply a thin, semi-transparent white border (0.5pt) to these glass elements to define their edges against the mesh gradients.

## Shapes
The shape language is strictly **Pill-shaped** and **Max-rounded**. 
- **Standard UI:** All buttons, input fields, and tags must use a full pill radius.
- **Containers:** Large cards and modals use a `rounded-xl` (3rem/48px) radius to maintain the bubbly feel without losing structural integrity.
- **Icons:** Icons should be contained within circular or super-elliptical backgrounds to reinforce the organic, soft theme. Avoid sharp corners anywhere in the interface.

## Components
- **Buttons:** High-contrast, pill-shaped, and elevated with a colored shadow. Use "Bounce" micro-interactions on hover or tap to reinforce the "bubbly" feel.
- **Chips/Tags:** Use low-contrast background tints of the primary/secondary colors with high-contrast text. They should appear soft and "squishy."
- **Input Fields:** Large, pill-shaped borders with a subtle background tint. The focus state should involve a glowing colored shadow rather than just a border color change.
- **Cards:** White or glass-effect backgrounds with `rounded-xl` corners and a soft, wide-spread colored shadow. Headlines within cards should be centered or use generous left-padding.
- **Checkboxes & Radios:** Fully rounded circles for both types to maintain the shape language. Use the primary violet for the active state.
- **Progress Bars:** Thick, pill-shaped tracks with vibrant gradients for the fill to visualize energy and completion.