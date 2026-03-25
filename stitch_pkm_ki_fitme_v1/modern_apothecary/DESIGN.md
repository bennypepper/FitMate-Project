# Design System: Modern Apothecary Editorial

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Curator"**

This design system moves away from the sterile, "app-like" feel of traditional health platforms toward a **High-End Editorial** experience. It blends the heritage of Traditional Chinese Medicine (TCM) with modern medical precision. 

The aesthetic is built on **Intentional Asymmetry** and **Tonal Depth**. We avoid rigid, boxed-in layouts in favor of breathing room and layered surfaces. By utilizing high-contrast typography scales (the tension between the elegant serif and the functional sans-serif), we create an environment that feels authoritative yet deeply personal—like a bespoke prescription from a master practitioner.

---

## 2. Colors & Surface Philosophy

The palette is rooted in deep cinnabar reds and medicinal golds, balanced by soft, paper-like neutrals.

### The Color Tokens
- **Primary / Brand:** `primary` (#69000B) & `primary_container` (#930014). Used for brand expression and high-importance elements.
- **Secondary / Action:** `secondary` (#B12D20). Reserved for supportive interactive elements.
- **Tertiary / Accent:** `tertiary_container` (#CBA72F). Inspired by #D4AF37, this is reserved **strictly for CTAs** to ensure they pierce through the red-dominant layout.
- **Neutral / Surface:** `surface` (#FFF8F7) and `surface_container` (#FFE9E7).

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders for sectioning content. Visual boundaries must be defined solely through background color shifts. 
- *Implementation:* Place a `surface_container_low` card on a `surface` background to create a "ghost" boundary. This creates a more organic, premium feel that mimics fine stationery.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of fine washi paper.
- **Level 0 (Background):** `surface` (#FFF8F7)
- **Level 1 (Sections):** `surface_container_low` (#FFF0EF)
- **Level 2 (Cards/Interactives):** `surface_container` (#FFE9E7)
- **Level 3 (Floating/Pop-overs):** `surface_container_highest` (#FFDAD7)

### The "Glass & Gradient" Rule
To elevate the "Modern Apothecary" look, use **Glassmorphism** for floating elements (Top Navigation, Bottom Sheets). Use a `surface` color at 80% opacity with a `20px` backdrop blur. 
*Signature Texture:* For Hero backgrounds, use a subtle radial gradient from `primary_container` (#930014) to `primary` (#69000B) to provide depth that flat hex codes cannot achieve.

---

## 3. Typography: The Editorial Scale

We use a "High-Contrast" pairing to signal both tradition and scientific rigor.

| Role | Font Family | Weight | Size (Rem) | Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Display LG** | Newsreader (Serif) | Bold | 3.5rem | High-impact marketing headers. |
| **Headline MD** | Newsreader (Serif) | SemiBold | 1.75rem | Section titles / Editorial stories. |
| **Title LG** | Inter (Sans) | Medium | 1.375rem | Information architecture / Medical categories. |
| **Body LG** | Inter (Sans) | Regular | 1rem | Primary reading experience (Indonesian). |
| **Label MD** | Inter (Sans) | Bold | 0.75rem | Micro-copy / Metadata. |
| **CJK Text** | Noto Sans SC | Regular | - | Optimized for Chinese herbal nomenclature. |

*Note: The use of Newsreader (Serif) conveys the "Apothecary" heritage, while Inter (Sans) provides the "Modern Medical" reliability.*

---

## 4. Elevation & Depth

We eschew traditional "Material" drop shadows in favor of **Tonal Layering**.

- **The Layering Principle:** Depth is achieved by stacking `surface-container` tiers. A `surface_container_lowest` card placed on a `surface_container_low` section creates a natural, soft lift.
- **Ambient Shadows:** When a floating effect is required (e.g., a "Pesan Sekarang" button), use an extra-diffused shadow: `blur: 32px`, `opacity: 6%`, color: `on_surface` (#410006). This mimics natural light rather than a digital effect.
- **The Ghost Border Fallback:** If a border is required for accessibility, use `outline_variant` at **15% opacity**. Never use 100% opaque borders.

---

## 5. Component Guidelines

### Buttons (Tombol)
- **Primary:** `tertiary_container` (#CBA72F) background with `on_tertiary_fixed` (#241A00) text. 
- **Secondary:** `surface_container_highest` background.
- **Shape:** Border-radius `md` (12px).
- **Style:** No borders. High-end buttons should feel like tactile "tabs."

### Cards (Kartu)
- **Constraint:** **Forbid the use of divider lines.**
- **Separation:** Use vertical white space from the Spacing Scale (e.g., `8` / 2rem) or a shift from `surface` to `surface_container_low`.
- **Radius:** `xl` (1.5rem / 24px) for a soft, approachable feel.

### Input Fields (Kolom Input)
- **Style:** "Underline Only" or "Soft Surface" (no box-border).
- **Active State:** Change background to `surface_container_high`.
- **Validation:** Use `error` (#BA1A1A) for text, but keep the container background subtle (`error_container`).

### Additional Contextual Components
- **Herbal Chip:** Use for ingredients. Pill-shaped (`full` radius), background `surface_container_highest`, text `on_surface_variant`.
- **Prescription Modal:** Uses Glassmorphism (80% `surface` + blur) to overlay current activity without losing context.

---

## 6. Do’s and Don’ts

### Do
- **Do** use `XXLarge` (80px) spacing between major editorial sections to allow the brand to "breathe."
- **Do** use Indonesian for all functional labels (e.g., "Mulai Konsultasi" vs "Start").
- **Do** align Chinese text (Noto Sans SC) slightly higher than Inter to visually balance different x-heights.
- **Do** use the `Accent` gold (#D4AF37) **only** for the final conversion point in a user journey.

### Don't
- **Don't** use pure black (#000000). Use `on_surface` (#410006) for a warmer, more premium feel.
- **Don't** use 1px solid dividers. If you must separate content, use a `2px` wide space or a subtle `surface_variant` block.
- **Don't** use standard "Blue" for links. All interactive elements must stay within the Red/Gold/Cream spectrum.
- **Don't** use sharp corners. Everything follows the `md` to `xl` roundedness scale to maintain "Medical Safety" and softness.

---

## 7. Spacing Scale Reference
- **Compact:** `2` (0.5rem / 8px) — For internal element padding.
- **Standard:** `4` (1rem / 16px) — For component gutters.
- **Editorial:** `8` (2rem / 32px) — For card spacing.
- **Hero:** `20` (5rem / 80px) — For section transitions.