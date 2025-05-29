# Materiatek Visual Design Guidelines

## Brand Identity Analysis
*Based on authentic source material from materiatek.eu - March 2025*

### Core Design Philosophy
**Sophisticated minimalism with tactile authenticity** - Materiatek emphasizes the physical, tangible nature of materials while maintaining a clean, professional digital presence. The design reflects their position as Belgium's largest independent materials library for spatial design.

---

## Color Palette

### Primary Colors (Light Mode)
- **Background**: `oklch(.995 0 0)` - Nearly pure white, clean base
- **Foreground/Text**: `oklch(.3 .02 322.03)` - Deep charcoal with subtle warmth
- **Card/Surface**: `oklch(.99 0 0)` - Off-white for elevated surfaces

### Accent Colors
- **Primary Accent**: `oklch(.9 .01 67.72)` - Warm cream/yellow tone
- **Secondary Green**: `oklch(.95 .15 112.61)` - Muted sage green
- **Tertiary Purple**: `oklch(.89 .05 259.03)` - Soft lavender
- **Border/Subtle**: `oklch(.88 0 0)` - Light gray for divisions

### Dark Mode Variants
- **Background**: `oklch(.31 .01 325.74)` - Deep charcoal
- **Foreground**: `oklch(.95 0 0)` - Near white
- **Surfaces**: `oklch(.21 0 0)` - Dark gray cards

---

## Typography

### Font Families
- **Primary Serif**: `antique` - Custom serif font for headings and brand elements
- **Sans-serif**: System font stack for body text and UI elements
  ```css
  ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif
  ```

### Font Scale (Custom)
- **xs**: `.625rem` (10px)
- **sm**: `.75rem` (12px) 
- **base**: `.875rem` (14px)
- **lg**: `1.125rem` (18px)
- **xl**: `1.25rem` (20px)
- **2xl**: `1.475rem` (23.6px)
- **3xl**: `1.85rem` (29.6px)
- **4xl**: `2.65rem` (42.4px)
- **5xl**: `3.25rem` (52px)
- **6xl**: `4.125rem` (66px)
- **7xl**: `5.675rem` (90.8px)

---

## Visual Characteristics

### Design Approach
- **Minimal aesthetic**: Clean, uncluttered layouts with generous whitespace
- **Material focus**: Emphasis on physical textures and tactile elements
- **Professional restraint**: Avoids bright colors or flashy design elements
- **Sophisticated neutrals**: Relies on subtle, refined color variations
- **Industrial elegance**: Clean lines with functional beauty (evident in materials library imagery)

### Layout Principles
- **Container-based**: Uses responsive container system with defined breakpoints
- **Grid systems**: 12-column grid for complex layouts, flexible for simpler ones
- **Spacing scale**: Precise spacing system based on `.25rem` increments
- **Border radius**: Minimal (`0rem` default) - sharp, clean edges preferred

### Interactive Elements
- **Subtle transitions**: `150ms` default timing with easing
- **Hover states**: Gentle background color changes, no dramatic effects
- **Focus states**: Clear but understated ring indicators
- **Button styles**: Clean, minimal styling with appropriate padding

---

## Shadow System
- **Minimal shadows**: Very subtle depth indicators
- **2xs/xs**: `0 1px 3px 0px #0000000d` - Barely perceptible
- **sm/default**: `0 1px 3px 0px #0000001a, 0 1px 2px -1px #0000001a`
- **md to xl**: Progressively stronger but still very restrained

---

## Material Connection

### Physical Inspiration
The design reflects the tactile, hands-on nature of their materials library:
- **Industrial organization**: Clean metal drawers and systematic organization
- **Material authenticity**: Focus on real textures and surfaces
- **Professional workspace**: Clean, organized, functional environment
- **Hand interaction**: Design that invites touch and exploration

### Digital Translation
- **Clean surfaces**: Digital elements mirror physical organization systems
- **Tactile metaphors**: UI elements suggest physical interaction
- **Authentic imagery**: Real photography over illustrations
- **Functional beauty**: Form follows function, beauty emerges from utility

---

## Brand Positioning
- **Independent authority**: Not corporate, but professional and trustworthy
- **Spatial design focus**: Serves architects, interior designers, creative professionals
- **Belgian heritage**: European sophistication and craftsmanship values
- **Innovation + tradition**: Modern approach to traditional materials expertise

---

## Implementation Guidelines

### Do:
- Use authentic materials photography when possible
- Maintain generous whitespace and clean layouts
- Apply colors sparingly - rely on neutrals with subtle accents
- Emphasize functionality and usability
- Use the custom Antique serif font for headings only
- Keep shadows minimal and subtle

### Don't:
- Use bright, saturated colors or gradients
- Apply excessive visual effects or animations
- Clutter layouts with unnecessary elements
- Use generic stock photography
- Over-brand - let the materials be the focus
- Use heavy shadows or dramatic depth effects

---

## File Sources
- **CSS Analysis**: `_page_.8ErK0ujO.css` from materiatek.eu
- **Visual Reference**: Material library photography showing organized drawers and tactile interaction
- **Website Context**: Belgium's largest independent materials library for spatial design

*Generated from authentic Materiatek source materials - March 2025*