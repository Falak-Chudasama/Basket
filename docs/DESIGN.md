---
name: Fruit Family Design System
version: 1.2.0
reference_app: kiwi
status: authoritative
tokens:
  color:
    base:
      canvas_light: "#F8F9F5"
      canvas_dark: "#121310"
      surface_light: "#FFFFFF"
      surface_dark: "#181915"
      surface_elevated_dark: "#1C1D18"
      surface_well_dark: "#141512"
      ink_primary_light: "#1C1917"
      ink_primary_dark: "#F3F4F1"
      ink_secondary_light: "#57534E"
      ink_secondary_dark: "#A8A29E"
      ink_muted_light: "#78716C"
      ink_muted_dark: "#78716C"
      text_placeholder_light: "#A8A29E"
      text_placeholder_dark: "#78716C"
      separator_light: "rgba(0, 0, 0, 0.06)"
      separator_dark: "rgba(255, 255, 255, 0.08)"
    accent_kiwi:
      seed_primary: "#0DAA26"
      seed_luminous: "#84DD00"
      accent_light: "#0DAA26"
      accent_dark: "#84DD00"
      accent_strong_light: "#007200"
      accent_pressed_light: "#0B8F20"
      accent_pressed_dark: "#72BF00"
      accent_subtle_light: "rgba(13, 170, 38, 0.10)"
      accent_subtle_dark: "rgba(132, 221, 0, 0.10)"
      on_accent_light: "#FFFFFF"
      on_accent_dark: "#121310"
      focus_ring_light: "#0DAA26"
      focus_ring_dark: "#84DD00"
    accent_basket:
      seed_primary: "#DF8A2D"
      seed_luminous: "#FACD8F"
      accent_light: "#DF8A2D"
      accent_dark: "#FACD8F"
      accent_strong_light: "#9B5D17"
      accent_pressed_light: "#C07624"
      accent_pressed_dark: "#DBB37D"
      accent_subtle_light: "rgba(223, 138, 45, 0.10)"
      accent_subtle_dark: "rgba(250, 205, 143, 0.10)"
      on_accent_light: "#FFFFFF"
      on_accent_dark: "#121310"
      focus_ring_light: "#DF8A2D"
      focus_ring_dark: "#FACD8F"
    glass:
      capsule:
        bg_light: "rgba(255, 255, 255, 0.20)"
        bg_dark: "rgba(24, 25, 21, 0.20)"
        border_light: "rgba(0, 0, 0, 0.07)"
        border_dark: "rgba(255, 255, 255, 0.09)"
        blur_px: 15
        saturate_pct: 100
      panel:
        bg_light: "rgba(255, 255, 255, 0.38)"
        bg_dark: "rgba(22, 23, 19, 0.40)"
        border_light: "rgba(255, 255, 255, 0.55)"
        border_dark: "rgba(255, 255, 255, 0.10)"
        blur_px: 12
        saturate_pct: 160
      card:
        bg_light: "rgba(255, 255, 255, 0.28)"
        bg_dark: "rgba(22, 23, 19, 0.34)"
        border_light: "rgba(255, 255, 255, 0.50)"
        border_dark: "rgba(255, 255, 255, 0.08)"
        blur_px: 10
        saturate_pct: 150
  typography:
    family_sans: "Host Grotesk"
    family_display: "Unbounded"
    tracking_default_em: -0.011
    tracking_display_em: -0.03
    scales:
      micro_px: 10
      caption_px: 12
      body_px: 14
      subtitle_px: 16
      title_px: 20
      page_title_px: 24
      hero_px: 36
  radii:
    lg_px: 8
    xl_px: 12
    xxl_px: 16
    xxxl_px: 24
    modal_px: 32
    capsule_px: 9999
  shadows:
    none: "none"
    xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    soft: "0 4px 20px -2px rgba(0, 0, 0, 0.05)"
    floating: "0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 2px 8px -2px rgba(0, 0, 0, 0.04)"
    lift: "0 12px 32px -4px rgba(0, 0, 0, 0.09)"
  motion:
    duration_micro_ms: 140
    duration_short_ms: 180
    duration_medium_ms: 220
    duration_long_ms: 260
    duration_pill_ms: 300
    duration_toast_ms: 4200
    easing_tactile: "cubic-bezier(0.16, 1, 0.3, 1)"
    easing_slide: "cubic-bezier(0.2, 0.8, 0.2, 1)"
  audio:
    sfx_enter: "/sfx/enter.mp3"
    sfx_back: "/sfx/back.mp3"
    sfx_notification: "/sfx/notification.mp3"
    sfx_failed: "/sfx/failed.mp3"
    sfx_scroll: "/sfx/scroll.mp3"
---

# Fruit Family Design System

Authoritative, as-built specification for the Fruit application family (desktop web clients, Android Jetpack Compose apps, and dashboards). Kiwi is the reference gold standard. Every token, transition, sound effect, motion curve, gesture, and component state is captured directly from code and assets.

For Kiwi-only tools and feature specs (camera scanning, crop editor, file format matrix, etc.), see [KIWI.md](kiwi/KIWI.md).

---

## 1. Principles and Anti-Bloat Rules

1. **Extreme Minimalism**: High negative space, zero non-functional containers, zero decorative marketing prose. Surfaces exist solely to group active functional tasks.
2. **Apple-Grade Optical Glass**: Low fill opacities (0.20 to 0.40), optical backdrop blurs (10px to 15px), saturation multipliers (140% to 160%), and hairline interior edge highlights (0.50 to 0.70 white inset/border).
3. **Shared Neutral Substrate**: All apps share the identical canvas, surfaces, typography, radii, shadows, motion curves, and glass formulations. Only the accent palette set and app-specific tools vary.
4. **Deterministic Accent Derivation**: Accent tokens are programmatically extracted from the app icon palette via OKLCH color space rules. No arbitrary hex values.
5. **Tactile Micro-Physics**: Interactive elements compress on press (scale(0.985), translateY(0.5px)), lift on hover (scale(1.015), translateY(-1px)), and trigger subtle haptics or gentle audio feedback.
6. **Hard Anti-Bloat Caps**: Hard maximums enforced across all platforms. Any token or variant outside these caps is forbidden.

### Anti-Bloat Hard Maximums

| Dimension | Hard Cap | Allowed Tokens / Steps | Enforced Constraint |
| :--- | :--- | :--- | :--- |
| **Type Scales** | **7 functional sizes** | Micro (10px / 11sp), Caption (12px / 13sp), Body (14px / 14sp), Subtitle (16px / 16sp), Title (20px / 18sp), PageTitle (24px / 26sp), Hero (36px / 32sp) | No intermediate font sizes. Literal 7-step scale. |
| **Radii Steps** | **6 values** | 8px (lg), 12px (xl), 16px (2xl), 24px (3xl), 32px (modal / 2rem), 9999px (capsule) | No arbitrary border-radius. |
| **Elevation Levels**| **4 levels (+ flat)** | Flat (0), XS (1px / 1dp), Soft (4px / 4dp), Floating (8px / 8dp), Lift (12px / 12dp) | No custom box-shadow strings. |
| **Glass Blur Steps**| **3 material blurs** | 10px (glass-card), 12px (glass-panel), 15px (glass-capsule) | No arbitrary backdrop blur. |
| **Spacing Grid** | **11 steps** | 4px, 6px, 8px, 12px, 16px, 20px, 24px, 28px, 32px, 48px, 64px | Table and Cap strictly match. 4pt/8pt discipline (+ 6px half-step). |
| **Accent Roles** | **7 UI contexts** | Primary Action Button, Focus Ring, Active Pill/Tab Indicator, Progress Fill, Checkbox/Toggle Track, Status Metric, Refraction Field Tint | No accent on neutral card backgrounds or card hover borders. |

---

## 2. Foundations

### 2.1 Color Tokens (Base Palette)

All apps share this base neutral palette. Sourced from index.css (.glass-panel, .glass-card), tailwind.config.ts (colors.kiwi), and CoconutTheme.kt (LemonLightSemanticColors, LemonDarkSemanticColors).

| Token Name | Light Hex | Light OKLCH | Dark Hex | Dark OKLCH | Source Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `canvas.page` | `#F8F9F5` | L=0.9803 C=0.0054 h=117.92 deg | `#121310` | L=0.1844 C=0.0062 h=122.04 deg | index.css (body), CoconutTheme.kt (pageBackground) |
| `surface.fallback` | `#FFFFFF` | L=1.0000 C=0.0000 h=89.88 deg | `#181915` | L=0.2108 C=0.0078 h=118.48 deg | index.css (.glass-fallback), CoconutTheme.kt (cardBackground) |
| `surface.elevated` | `#FFFFFF` | L=1.0000 C=0.0000 h=89.88 deg | `#1C1D18` | L=0.2289 C=0.0084 h=118.91 deg | ResultPanel.tsx, CoconutTheme.kt (cardElevatedBackground) |
| `surface.well` | `#FAFAF9` | L=0.9845 C=0.0024 h=106.42 deg | `#141512` | L=0.1979 C=0.0068 h=120.11 deg | FormatPicker.tsx, CoconutTheme.kt (surfaceWell) |
| `text.primary` | `#1C1917` | L=0.2178 C=0.0000 h=89.88 deg | `#F3F4F1` | L=0.9656 C=0.0041 h=121.56 deg | PageShell.tsx (text-stone-900), CoconutTheme.kt (textPrimary) |
| `text.secondary` | `#57534E` | L=0.4574 C=0.0125 h=68.22 deg | `#A8A29E` | L=0.7223 C=0.0118 h=76.84 deg | PageShell.tsx (text-stone-600), CoconutTheme.kt (textSecondary) |
| `text.muted` | `#78716C` | L=0.5543 C=0.0142 h=70.43 deg | `#78716C` | L=0.5543 C=0.0142 h=70.43 deg | PageShell.tsx (text-stone-500), CoconutTheme.kt (textTertiary) |
| `text.placeholder`| `#A8A29E`| L=0.7223 C=0.0118 h=76.84 deg | `#78716C` | L=0.5543 C=0.0142 h=70.43 deg | TextField.tsx, CoconutTheme.kt (textPlaceholder) |
| `border.separator`| `rgba(0,0,0,0.06)` | -- | `rgba(255,255,255,0.08)` | -- | ResultPanel.tsx, CoconutTheme.kt (separator) |

### 2.2 Typography

Typography uses two typeface families: **Host Grotesk** for interface, headings, and data; **Unbounded** exclusively for brand wordmarks and hero displays. Sourced from index.css (@font-face), tailwind.config.ts (fontFamily), and CoconutTheme.kt (LemonTypography).

The typography scale is strictly capped at **7 functional sizes**:

| Role | Font Family | Weight | Web Size / Leading / Tracking | Android Size / LineHeight / Spacing | Usage Rule & Platform Difference Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Display** | Unbounded | Bold (800) | `36px` / `1.1` / `-0.03em` | `32sp` / `38sp` / `-0.8sp` | Landing screen hero titles. Android uses 32sp to prevent 3-line headline wrap on 360dp phone viewports. |
| **Page Title** | Host Grotesk | ExtraBold (800)| `24px` / `1.2` / `-0.025em`| `26sp` / `32sp` / `-0.6sp` | PageShell header (h1). Android uses 26sp for prominent top-bar authority. |
| **Section Title**| Host Grotesk | Bold (700) | `20px` / `1.3` / `-0.02em` | `18sp` / `24sp` / `-0.2sp` | Dialog title, card title (h3). Scaled down slightly on Android for compact card headers. |
| **Subtitle** | Host Grotesk | Bold (700) | `16px` / `1.4` / `-0.015em`| `16sp` / `22sp` / `-0.2sp` | List item title, dropzone subhead. Identical 1:1 scale across platforms. |
| **Body Regular** | Host Grotesk | Regular (400)| `14px` / `1.5` / `-0.011em`| `14sp` / `20sp` / `-0.1sp` | Standard body text, form input value, settings description. Identical 1:1 scale. |
| **UI Caption** | Host Grotesk | SemiBold (600)| `12px` / `1.4` / `0.0em` | `13sp` / `18sp` / `0.0sp` | Navigation labels, tags, tooltips. Android uses 13sp for improved mobile touch legibility. |
| **Micro** | Host Grotesk | Bold (700) | `10px` / `1.2` / `+0.05em` | `11sp` / `15sp` / `+0.3sp` | Uppercase category overline, badge count. Android uses 11sp minimum for legibility standards. |

Note: Unbounded wordmarks (16px / 17sp) inherit the Subtitle size step with display tracking (-0.03em), introducing zero new font sizes. Intermediate sizes (11px, 30px, 48px, 60px) are removed from the system scale.

### 2.3 Spacing Scale

Base grid unit is **4px / 4dp**. Core spacing steps are multiples of 4 and 8, with one 6px half-step for dense pill badges. Sourced from CoconutTheme.kt (LemonSpacing) and PageShell.tsx.

| Token | Web Value | Android Value | Usage Rule |
| :--- | :--- | :--- | :--- |
| `spacing.xxs` | `4px` (0.25rem) | `4.dp` | Micro badge padding, icon gap |
| `spacing.6px` | `6px` (0.375rem) | `6.dp` | Half-step: segmented control pill padding, tag spacing |
| `spacing.xs` | `8px` (0.5rem) | `8.dp` | Compact button padding, grid gap |
| `spacing.sm` | `12px` (0.75rem) | `12.dp` | Input vertical padding, list item gap |
| `spacing.md` | `16px` (1.0rem) | `16.dp` | Standard container padding, dialog inner margins |
| `spacing.lg` | `20px` (1.25rem) | `20.dp` | Card interior padding, section separation |
| `spacing.xl` | `24px` (1.5rem) | `24.dp` | Large container padding, mobile screen gutters |
| `spacing.28px`| `28px` (1.75rem) | `28.dp` | FeatureCard interior padding |
| `spacing.xxl` | `32px` (2.0rem) | `32.dp` | Major section vertical margins, modal spacing |
| `spacing.xxxl`| `48px` (3.0rem) | `48.dp` | Touch target bounding box, hero vertical spacing |
| `spacing.64px`| `64px` (4.0rem) | `64.dp` | Dropzone padding, empty state frame size |

### 2.4 Radii Scale

Disciplined geometric radii scale strictly capped at 6 values. Sourced from tailwind.config.ts (borderRadius) and CoconutTheme.kt (LemonShapes).

| Token | Web Value | Android Value | Usage Scope |
| :--- | :--- | :--- | :--- |
| `radius.lg` | `8px` (0.5rem) | `8.dp` | Tooltips, toast dismiss button, micro badges |
| `radius.xl` | `12px` (0.75rem) | `12.dp` | Text fields, form inputs, format selection tiles |
| `radius.2xl` | `16px` (1.0rem) | `16.dp` | Standard cards (.glass-card), list rows, toasts |
| `radius.3xl` | `24px` (1.5rem) | `24.dp` | Large feature cards, bottom sheets (LemonShapes.sheet) |
| `radius.modal`| `32px` (2.0rem) | `24.dp` | Modal popup dialogs. Web uses 32px for Apple-like soft curve; Android intentionally uses 24dp to prevent content clipping on narrow mobile screens. |
| `radius.capsule`| `9999px` | `100.dp` | Buttons, navigation capsules, segmented pills, toggle switches |

### 2.5 Elevation and Shadows

Sourced from tailwind.config.ts (boxShadow) and FloatingBottomBar.kt. Capped at **4 elevation levels (+ flat base)**:

| Token | CSS Box Shadow Spec | Android Elevation | Usage Scope |
| :--- | :--- | :--- | :--- |
| `shadow.none` | `none` | `0.dp` | Resting surface wells, disabled buttons, flat inputs |
| `shadow.xs` | `0 1px 2px 0 rgba(0, 0, 0, 0.05)` | `1.dp` | Sliding segmented control pill, active tab indicator |
| `shadow.soft` | `0 4px 20px -2px rgba(0, 0, 0, 0.05)` | `4.dp` | Standard cards, progress panels, floating toasts |
| `shadow.floating`| `0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 2px 8px -2px rgba(0, 0, 0, 0.04)` | `8.dp` | Floating top capsule navbar, modal dialogs |
| `shadow.lift` | `0 12px 32px -4px rgba(0, 0, 0, 0.09)` | `12.dp` | Hovered cards, drag active elements, bottom dock |

### 2.6 Glass Material System (Optical Specification)

Three optical tiers with mathematically calibrated blur, opacity, saturation, and hairline inset borders. Sourced from index.css (.glass-capsule, .glass-panel, .glass-card) and GlassComponents.kt (GlassSurface, GlassCard).

| Material Tier | Mode | Background Fill Opacity | Perimeter Border | Inner Inset Highlight | Blur & Saturation | Fallback (No Blur) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`.glass-capsule`** | Light | `rgba(255, 255, 255, 0.20)` | `1px solid rgba(0, 0, 0, 0.07)` | None | `blur(15px)` | `#FFFFFF` |
| | Dark | `rgba(24, 25, 21, 0.20)` | `1px solid rgba(255, 255, 255, 0.09)` | None | `blur(15px)` | `#181915` |
| **`.glass-panel`** | Light | `rgba(255, 255, 255, 0.38)` | `1px solid rgba(255, 255, 255, 0.55)` | `inset 0 1px 1px 0 rgba(255,255,255,0.7)` | `blur(12px) saturate(160%)` | `#FFFFFF` |
| | Dark | `rgba(22, 23, 19, 0.40)` | `1px solid rgba(255, 255, 255, 0.10)` | `inset 0 1px 1px 0 rgba(255,255,255,0.08)`| `blur(12px) saturate(160%)` | `#181915` |
| **`.glass-card`** | Light | `rgba(255, 255, 255, 0.28)` | `1px solid rgba(255, 255, 255, 0.50)` | `inset 0 1px 0 0 rgba(255,255,255,0.5)` | `blur(10px) saturate(150%)` | `#FFFFFF` |
| | Dark | `rgba(22, 23, 19, 0.34)` | `1px solid rgba(255, 255, 255, 0.08)` | `inset 0 1px 0 0 rgba(255,255,255,0.08)`| `blur(10px) saturate(150%)` | `#181915` |

### 2.7 Iconography

- **Library**: Lucide (`lucide-react`) on Web; Material Symbols / Lucide Vector XML on Android.
- **Stroke Width**: Strict 2.0px stroke weight across all sizes.
- **Size Grid**:
  - Micro / Inline: `h-3.5 w-3.5` (14px)
  - Standard Action / Nav: `h-4 w-4` (16px / 16.dp)
  - Floating Dock / Header Brand: `h-5 w-5` (20px / 20.dp)
  - Section Header / Card Feature: `h-6 w-6` (24px / 24.dp)
  - Hero Display / Empty Frame: `h-8 w-8` (32px / 32.dp)

### 2.8 Ambient Canvas Background Treatment

Sourced directly from index.css (body background-image) and App.tsx (ambient orbs). Subtle atmospheric glow provides chromatic refraction for glass surfaces.

| Layer | Light Mode Spec | Dark Mode Spec | Execution Behavior |
| :--- | :--- | :--- | :--- |
| **Canvas Base** | Solid `#F8F9F5` | Solid `#121310` | Static body background |
| **Radial Field 1 (Top-Left)** | `at 15% 15%, rgba(accent_light, 0.05) 0px, transparent 55%` | `at 15% 15%, rgba(accent_dark, 0.05) 0px, transparent 55%` | Fixed viewport CSS radial gradient |
| **Radial Field 2 (Bottom-Right)**| `at 85% 85%, rgba(accent_dark, 0.04) 0px, transparent 50%` | `at 85% 85%, rgba(accent_light, 0.045) 0px, transparent 50%`| Fixed viewport CSS radial gradient |
| **Radial Field 3 (Top-Right)** | `at 85% 15%, rgba(accent_light, 0.03) 0px, transparent 45%` | `at 80% 20%, rgba(accent_dark, 0.035) 0px, transparent 45%`| Fixed viewport CSS radial gradient |
| **Refraction Orbs (Desktop Web)**| 3 fixed divs: `w-[500px] h-[500px] blur-[110px]` with accent at 4% to 6% alpha | Matching dark accent tokens | Pointer-events none, fixed positioning |

Performance Fallback: The 3 blurred refraction divs are desktop web-only. They are forbidden on Android and low-end web (@media (max-width: 640px) or when navigator.hardwareConcurrency <= 4). Those environments use only the lightweight CSS radial gradient fields.

### 2.9 Complete Motion & Transition Specification

Sourced from index.css (.btn-interactive, .animate-*), tailwind.config.ts (keyframes), and CoconutMotion.kt.

#### Motion Constants & Timing Curves

| Motion Token | Duration | Timing Easing Curve | Application Scope | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| `motion.micro` | `140ms` | `cubic-bezier(0.2, 0.0, 0.0, 1.0)` (EmphasizedEasing) | Icon toggle, checkbox mark, switch thumb | CoconutMotion.kt (DURATION_MICRO) |
| `motion.short` | `180ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | Tactile button press, popup scale-in, slide-up | tailwind.config.ts (scale-in) |
| `motion.medium` | `220ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | Page enter fade, card expand | CoconutMotion.kt (DURATION_MEDIUM) |
| `motion.slide` | `260ms` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Two-layer directional route sliding | index.css (slide-out-to-left) |
| `motion.subpage`| `280ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | Sub-page slide entrance from left/right | index.css (slide-from-right) |
| `motion.pill` | `300ms` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Sliding navigation capsule indicator pill | Header.tsx |
| `motion.toast` | `4200ms`| `linear` | Toast notification auto-dismiss lifetime | ToastProvider.tsx |

#### Exhaustive Keyframe Definitions (Web CSS)

| Animation Name | Duration & Easing | Keyframe Percentages & Transform Values | Trigger / Usage |
| :--- | :--- | :--- | :--- |
| **`fade-in`** | `150ms ease-out` | `from { opacity: 0; }`<br>`to { opacity: 1; }` | Popup modal backdrop scrim |
| **`scale-in`** | `180ms cubic-bezier(0.16, 1, 0.3, 1)` | `from { opacity: 0; transform: scale(0.97); }`<br>`to { opacity: 1; transform: scale(1); }` | Popup dialogs, ProgressPanel, ResultPanel |
| **`slide-up`** | `180ms ease-out` | `from { opacity: 0; transform: translateY(6px); }`<br>`to { opacity: 1; transform: translateY(0); }` | Toast notifications container enter |
| **`page-enter`** | `220ms cubic-bezier(0.16, 1, 0.3, 1)` | `from { opacity: 0; transform: translateY(6px) scale(0.996); }`<br>`to { opacity: 1; transform: translateY(0) scale(1); }` | Standard view route enter |
| **`slide-from-right`** | `280ms cubic-bezier(0.16, 1, 0.3, 1)` | `from { opacity: 0; transform: translate3d(40px, 0, 0); }`<br>`to { opacity: 1; transform: translate3d(0, 0, 0); }` | Sub-page route forward transition |
| **`slide-from-left`** | `280ms cubic-bezier(0.16, 1, 0.3, 1)` | `from { opacity: 0; transform: translate3d(-40px, 0, 0); }`<br>`to { opacity: 1; transform: translate3d(0, 0, 0); }` | Sub-page route backward transition |
| **`slide-out-to-left`** | `260ms cubic-bezier(0.2, 0.8, 0.2, 1)` | `0% { opacity: 1; transform: translate3d(0, 0, 0); }`<br>`100% { opacity: 0; transform: translate3d(-60px, 0, 0); }` | Directional exit when moving forward |
| **`slide-in-from-right`** | `260ms cubic-bezier(0.2, 0.8, 0.2, 1)` | `0% { opacity: 0; transform: translate3d(60px, 0, 0); }`<br>`100% { opacity: 1; transform: translate3d(0, 0, 0); }` | Directional enter when moving forward |
| **`slide-out-to-right`** | `260ms cubic-bezier(0.2, 0.8, 0.2, 1)` | `0% { opacity: 1; transform: translate3d(0, 0, 0); }`<br>`100% { opacity: 0; transform: translate3d(60px, 0, 0); }` | Directional exit when moving backward |
| **`slide-in-from-left`** | `260ms cubic-bezier(0.2, 0.8, 0.2, 1)` | `0% { opacity: 0; transform: translate3d(-60px, 0, 0); }`<br>`100% { opacity: 1; transform: translate3d(0, 0, 0); }` | Directional enter when moving backward |
| **`animate-spin`** | `1000ms linear infinite` | `from { transform: rotate(0deg); }`<br>`to { transform: rotate(360deg); }` | SpinnerIcon loading states |

#### Tactile Interactive Micro-Transforms

| Selector / Element | Pseudo-State | Transform Spec | Easing & Transition | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| **`.btn-interactive`** | `:hover` | `translateY(-1px) scale(1.015)` | `0.18s cubic-bezier(0.16, 1, 0.3, 1)` | index.css (.btn-interactive) |
| **`.btn-interactive`** | `:active` | `translateY(0.5px) scale(0.985)` | `0.18s cubic-bezier(0.16, 1, 0.3, 1)` | index.css (.btn-interactive:active) |
| **Theme Sun Icon** | `hover` | `rotate(45deg)` (hover:rotate-45) | `duration-200 ease-out` | Header.tsx |
| **Theme Moon Icon** | `hover` | `rotate(-12deg)` (hover:-rotate-12) | `duration-200 ease-out` | Header.tsx |
| **Select Chevron** | Open state | `rotate(180deg)` (rotate-180) | `duration-200 ease-out` | CustomSelect.tsx |

#### Mini-Physics Engine & Interactive State Mechanics

The Fruit Family user interface applies physically grounded micro-mechanics to convey tactile substance:

1. **Spring-Damper Press Dynamics**:
   - **Resting State**: `transform: translateY(0) scale(1.0)`, baseline resting shadow elevation.
   - **Hover Anticipation**: Subtly pre-arms the interaction with an elastic lift: `transform: translateY(-1px) scale(1.015)` using `0.18s cubic-bezier(0.16, 1, 0.3, 1)`.
   - **Tactile Depression**: On click or touch-down, elements compress: `transform: translateY(0.5px) scale(0.985)` with instantaneous response and zero uncontrolled rebound upon release.
   - **Flat Primary Action Variant**: When an application implements flat primary buttons, tactile micro-transforms are suppressed (`transform: none`, `box-shadow: none`) to maintain a completely flat, non-distorting silhouette. In this variant, physical confirmation is delivered exclusively through instantaneous solid chromatic shift (`0.15s ease`) paired with the `enter` audio SFX tick.
2. **Frictionless Magnetic Pill Dynamics**:
   - The active tab/route indicator pill glides between anchor items with `300ms cubic-bezier(0.2, 0.8, 0.2, 1)` (Web) or `Spring.DampingRatioNoBouncy` with `Spring.StiffnessMediumLow` (Android).
   - Simulates a magnetic slider snapping over targets with zero overshoot or geometric distortion.
3. **Switch Thumb Kinetic Travel**:
   - Switch thumb travels an exact 22dp linear stroke across a 50dp pill track.
   - Rest gap is strictly 2dp from outer bezel. Driven by low-bouncy spring dynamics (`DampingRatioLowBouncy`) paired with the Android `TextHandleMove` haptic tick or Web `enter` audio click.

#### Stutter-Free 60fps / 120fps Compositing Rules

To guarantee fluid, stutter-free performance across 60Hz and 120Hz ProMotion displays:

1. **Compositor-Only Layer Strategy**: All transitions, page entrance animations, and micro-physics must animate **strictly GPU-accelerated compositing properties**: `transform` (using `translate3d`, `translateY`, `scale`) and `opacity`.
2. **Strict Layout Reflow Ban**: Never animate geometric layout properties (`width`, `height`, `top`, `left`, `margin`, `padding`) during route switches or state updates. Geometric changes trigger synchronous style recalculation, layout reflow, and paint cycles that cause frame drops and UI stutter.
3. **Subpixel Glass Stability**: Translucent glass layers (`.glass-capsule`, `.glass-panel`, `.glass-card`) with optical backdrop blurs must declare `transform: translateZ(0)` or `backface-visibility: hidden`. This forces GPU composite layer promotion and prevents subpixel jitter or backdrop re-render hitching during viewport scrolling.
4. **Lifecycle-Bound `will-change`**: If `will-change: transform, opacity` is applied for complex multi-card entrances, it must be removed upon animation completion to release GPU memory surfaces.
5. **Frame Budget Discipline**: Strict budget of **16.6ms** (60fps) or **8.3ms** (120fps). JavaScript event handlers (such as scroll or resize listeners) must never execute synchronous DOM measurements that force layout thrashing.

#### Android Jetpack Compose Animation Specs

Sourced directly from CoconutMotion.kt:

| Spec Name | Spec Type | Parameters | Application Scope | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| **`MicroInteraction`** | `tween<Float>` | `durationMillis = 140, easing = CubicBezierEasing(0.2f, 0.0f, 0.0f, 1.0f)` | Icon toggles, quick checks | CoconutMotion.kt |
| **`StatusTransition`** | `tween<Float>` | `durationMillis = 180, easing = FastOutSlowInEasing` | Badge status updates | CoconutMotion.kt |
| **`SpringSubtle`** | `spring<Float>` | `dampingRatio = Spring.DampingRatioLowBouncy, stiffness = Spring.StiffnessMediumLow` | General responsive springs | CoconutMotion.kt |
| **`CardExpand`** | `tween<Float>` | `durationMillis = 220, easing = CubicBezierEasing(0.2f, 0.0f, 0.0f, 1.0f)` | Card expand / collapse | CoconutMotion.kt |
| **`ScreenTransition`**| `tween<Float>` | `durationMillis = 260, easing = FastOutSlowInEasing` | Screen nav transition | CoconutMotion.kt |
| **`SwitchThumb`** | `spring<Dp>` | `dampingRatio = Spring.DampingRatioLowBouncy, stiffness = Spring.StiffnessMediumLow` | LemonSwitch thumb travel | LemonSwitch.kt |
| **`SegmentPillSlide`**| `spring<Float>`| `dampingRatio = Spring.DampingRatioNoBouncy, stiffness = Spring.StiffnessMediumLow` | LemonSegmentedControl pill | LemonSegmentedControl.kt |
| **`BannerVisibility`**| `AnimatedVisibility` | `fadeIn() + slideInVertically(initialOffsetY = { -it })`<br>`fadeOut() + slideOutVertically(targetOffsetY = { -it })` | LemonFeedbackBanner | LemonFeedbackBanner.kt |

#### Reduced Motion Policy

- **Web Standard**: `@media (prefers-reduced-motion: reduce)` in index.css. Sets `animation-duration: 0.01ms !important`, `animation-iteration-count: 1 !important`, and `transition-duration: 0.01ms !important`.
- **Android Standard**: Queries `Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1.0f)` in LemonSwitch.kt and LemonSegmentedControl.kt. If animatorScale == 0f, all animation specs substitute snap().

### 2.10 Sound Effects (SFX) Subsystem

Tactile audio feedback provides subtle physical confirmation for users. Shared across all apps in the family. Sourced from sound.ts and public/sfx/guide.txt.

#### Audio Engine Architecture

1. **Preloading and Audio Pool**: Each category is lazily loaded into audioCache with `audio.preload = 'auto'` and cached permanently for rapid zero-lag replay.
2. **Overlap Playback**: Subsequent triggers reset `audio.currentTime = 0` to immediately replay without awaiting audio element termination.
3. **Scroll Throttling**: Scroll sound calls are strictly throttled by `SCROLL_THROTTLE_MS = 140ms` to prevent acoustic saturation during rapid keyboard strokes.
4. **Resilient Silent Failure**: All invocations wrap `.play()` in `.catch(() => {})`. If browser autoplay policies block audio, or audio files are absent, execution continues completely silently with zero console warnings or thrown exceptions.
5. **Permanent Ambient Sound (No Header Toggle)**: Tactile audio SFX is an intrinsic ambient layer of the Fruit family experience. The navigation bar chrome must remain uncluttered and bloat-free; applications do NOT expose a sound toggle button in the header. Sound stays permanently active (`isSoundEnabled() => true`). Where a user preferences menu exists in system settings, sound may be globally silenced, but primary navigation chrome is reserved strictly for routing and theme controls.

#### Master Volume & Audio Specification

| Event Category | Filename | Master Vol | Duration | Triggering Interaction Rule | Audio Characteristic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`enter`** | `/sfx/enter.mp3` | `0.40` | ~80 to 150ms | Primary action click, format select, modal confirm | Crisp Apple-like positive affirmation click |
| **`back`** | `/sfx/back.mp3` | `0.35` | ~70 to 120ms | Chip removal, modal close, cancel/reset action | Gentle descending tone, subtle dismiss pop |
| **`notification`**| `/sfx/notification.mp3` | `0.45` | ~120 to 250ms | Success/info toast appear, job download complete | Friendly glass ding, soft marimba chime |
| **`failed`** | `/sfx/failed.mp3` | `0.45` | ~150 to 250ms | Error toast appear, upload rejected, job failed | Non-jarring low alert, double-tap error tone |
| **`scroll`** | `/sfx/scroll.mp3` | `0.25` | ~30 to 60ms | Keyboard route/tab cycle (throttled 140ms) | Soft tactile tick or paper-friction click |

#### Android Audio SFX Specification

- **Requirement Status**: Required specification across all fruit apps; not yet implemented in existing Compose codebases.
- **Implementation API**: Low-latency Android `SoundPool` configured with `AudioAttributes.USAGE_ASSISTANCE_SONIFICATION` and `CONTENT_TYPE_SONIFICATION`.
- **Coexistence with Haptics**: Audio clicks and physical tactile haptics fire concurrently (the SoundPool sound plays simultaneously with the TextHandleMove haptic tick when sound is unmuted).

### 2.11 Haptics Subsystem (Android Jetpack Compose)

Tactile physical vibration provides physical confirmation on Android devices. Sourced from LemonSwitch.kt, LemonSegmentedControl.kt, and FloatingBottomBar.kt.

| Component | Trigger Event | Haptic Spec | Source Reference |
| :--- | :--- | :--- | :--- |
| **`LemonSwitch`** | Value toggle on/off | `LocalHapticFeedback.current.performHapticFeedback(HapticFeedbackType.TextHandleMove)` | LemonSwitch.kt |
| **`LemonSegmentedControl`**| Tab / Segment item click | `LocalHapticFeedback.current.performHapticFeedback(HapticFeedbackType.TextHandleMove)` | LemonSegmentedControl.kt |
| **`FloatingBottomBar`** | Navigation tab tap | `LocalHapticFeedback.current.performHapticFeedback(HapticFeedbackType.TextHandleMove)` | FloatingBottomBar.kt |

---

## 3. Accent System

### 3.1 Reference Icon Anatomy (`kiwi-icon.svg`)

The Kiwi app icon is an asymmetric kiwi fruit cross-section enclosed by dark contours. Source: kiwi/client/src/assets/kiwi-icon.svg (viewBox 0 0 75 73) and kiwi/client/src/assets/kiwi-icon.png.

#### Measured Icon Palette Table

Extracted programmatically from vector paths and raster pixel sampling:

| Path / Role | Measured Hex | OKLCH Coordinates | Area % | Anatomical Role in Icon |
| :--- | :--- | :--- | :--- | :--- |
| **Contour Outline** | `#000000` | L=0.0000 C=0.0000 h=0.0 deg | 18.4% | Structural perimeter ink |
| **Primary Flesh** | `#0DAA26` | L=0.6417 C=0.2047 h=143.98 deg | 38.2% | Dominant saturated fruit flesh (Seed_Light) |
| **Electric Lime** | `#84DD00` | L=0.8093 C=0.2268 h=128.53 deg | 21.6% | Inner luminous flesh highlight (Seed_Dark) |
| **Pastel Core** | `#E4FFB0` | L=0.9614 C=0.0886 h=120.35 deg | 12.1% | Asymmetric center core |
| **Seeds (Rind)** | `#000000` | L=0.0000 C=0.0000 h=0.0 deg | 5.8% | Radiating seed cluster |
| **Coral Accent** | `#FF6767` | L=0.6865 C=0.1873 h=25.29 deg | 3.9% | Secondary contrast accent |

### 3.2 Derivation Recipe (Deterministic Algorithm)

A step-by-step mathematical algorithm translating any fruit icon SVG into an authoritative, WCAG-compliant accent token set.

#### Step 1: Palette Extraction and Filtering
1. Parse all vector fill paths or sample icon pixels.
2. Discard pure neutrals (chroma C < 0.08), structural black contours (L < 0.15), and white backgrounds (L > 0.95).
3. Rank remaining candidate colors by area and chroma.

#### Step 2: Seed Assignment Branches

- **Branch A: Dual-Seed Moderate Lightness (Standard Fruit Case)**:
  - If the icon contains two distinct non-neutral fills sharing a similar hue family (|dh| < 30 deg):
    - `Seed_Light`: Lower-lightness fill (0.50 <= L <= 0.70).
    - `Seed_Dark`: Higher-lightness fill (0.75 <= L <= 0.88).
- **Branch B: Single-Seed Standard**:
  - If only one dominant saturated seed exists with L <= 0.70:
    - Set `accent_light = Seed`.
    - Derive `accent_dark` by: L_dark = min(0.85, L + 0.20), C_dark = min(0.10, C * 0.50), h_dark = h.
- **Branch C: High-Lightness Yellow Hues (L > 0.75, e.g., Lemon, Banana)**:
  - Seeds with L > 0.75 and yellow hue (70 deg <= h <= 100 deg) lack contrast on white canvas.
  - Set `accent_dark = Seed` (luminous on obsidian).
  - Derive high-contrast `accent_text` / `accent_strong_light`: L_strong = L - 0.374, C_strong = C * 0.90, h_strong = h.

#### Step 3: Role Transform Formulas (OKLCH Space)

| Role | Light Mode Formula | Dark Mode Formula | Target Visual Quality |
| :--- | :--- | :--- | :--- |
| **`accent`** | `Seed_Light` | `Seed_Dark` | Primary brand statement |
| **`accent_strong_light`**| L_strong = L - 0.17, C_strong = C * 0.85, h_strong = h | `Seed_Dark` | Accessible 4.5:1 primary button fill for white text |
| **`accent-pressed`** | L_pressed = L - 0.076, C_pressed = C * 0.90, h_pressed = h | L_pressed = L - 0.083, C_pressed = C * 0.90, h_pressed = h | Tactile depression feedback |
| **`accent-subtle`** | `rgba(r, g, b, 0.10)` using `accent_light` | `rgba(r, g, b, 0.10)` using `accent_dark` | Selected row & pill backings |
| **`on-accent`** | `#FFFFFF` (on `accent_strong_light`) | `#121310` (when L > 0.70) else `#FFFFFF` | Contrast-safe label on primary accent |
| **`focus-ring`** | Inner `2px #FFFFFF`, Outer `4px accent_light` | Inner `2px #181915`, Outer `4px accent_dark` | Two-layer high-visibility ring |
| **`accent-glow`** | `0 0 24px -4px rgba(r, g, b, 0.25)` | `0 0 24px -4px rgba(r, g, b, 0.35)` | Ambient hover & status halos |

#### Step 4: Contrast Clamping and Gamut Mapping
- Convert OKLCH coordinates back to linear sRGB, clamping values to [0.0, 1.0]. If out-of-gamut, iteratively reduce chroma C by 0.01 holding L and h constant until all channels fall in [0, 255].
- **WCAG AA Compliance Rule (Owner Decision: White on Accent Strong)**:
  - Primary button in light mode uses white text (`#FFFFFF`) on `accent_strong_light` (for Kiwi: `#007200`, L=0.4717).
  - Effective contrast is **6.16:1** solid (and **4.65:1** blended at 0.85 alpha over canvas #F8F9F5), cleanly passing the WCAG AA 4.5:1 threshold for 14px bold text.

### 3.3 Recipe Validation Matrix (Programmatically Computed)

The deterministic algorithm was run programmatically across all fruit app icons in the repository. Threshold evaluation:
- `pass`: dE(OKLab) <= 0.02 (within one just-noticeable difference)
- `near`: 0.02 < dE(OKLab) <= 0.05 (near match, minor framework rounding)
- `exception`: dE(OKLab) > 0.05 (documented hand-picked app token)

| App | Role | Actual Token | Source Symbol | Derived Value | Measured dE (OKLab) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kiwi** | `accent_light` | `#0DAA26` | tailwind colors.kiwi.flesh | `#0DAA26` | dE = 0.0000 | pass |
| | `accent_dark` | `#84DD00` | tailwind colors.kiwi.lime | `#84DD00` | dE = 0.0000 | pass |
| | `accent_strong_light` | `#007200` | formula (L - 0.17) | `#007200` | dE = 0.0000 | pass |
| | `pressed_light` | `#0B8F20` | tailwind colors.kiwi.flesh-600 | `#00901A` | dE = 0.0057 | pass |
| | `pressed_dark` | `#72BF00` | tailwind colors.kiwi.lime-600 | `#71BF00` | dE = 0.0010 | pass |
| | `on_accent_light` | `#FFFFFF` | button label ink | `#FFFFFF` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(13, 170, 38, 0.10)` | bg-kiwi-flesh/10 | `rgba(13, 170, 38, 0.10)` | dE = 0.0000 | pass |
| **Plum** | `accent_light` | `#B266E6` | index.css --accent-light | `#B266E6` | dE = 0.0000 | pass |
| | `accent_dark` | `#DBBFFF` | index.css --accent-dark | `#E1BDFE` | dE = 0.0094 | pass |
| | `accent_strong_light` | `#7E36B2` | formula (L - 0.17) | `#7E36B2` | dE = 0.0000 | pass |
| | `pressed_light` | `#8F40C7` | index.css --accent-pressed-light | `#9754C4` | dE = 0.0449 | near |
| | `pressed_dark` | `#5C207E` | index.css --accent-pressed-dark | `#C5A5E8` | dE = 0.3943 | exception |
| | `on_accent_light` | `#FFFFFF` | index.css text-white | `#FFFFFF` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(178, 102, 230, 0.10)` | bg-plum/10 | `rgba(178, 102, 230, 0.10)` | dE = 0.0000 | pass |
| **Cherry** | `accent_light` | `#FF5252` | cherry-icon.svg fill | `#FF5252` | dE = 0.0000 | pass |
| | `accent_dark` | `#FFCCCC` | cherry-icon.svg highlight | `#FFAAAA` | dE = 0.0810 | exception |
| | `accent_strong_light` | `#CB2328` | formula (L - 0.17) | `#CB2328` | dE = 0.0000 | pass |
| | `pressed_light` | `#E03E3E` | drawable/bg_cherry_button.xml | `#E53A3D` | dE = 0.0096 | pass |
| | `pressed_dark` | `#FF7070` | cherry theme pressed_dark | `#E58A8A` | dE = 0.0647 | exception |
| | `on_accent_light` | `#FFFFFF` | button label ink | `#FFFFFF` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(255, 82, 82, 0.10)` | bg-cherry/10 | `rgba(255, 82, 82, 0.10)` | dE = 0.0000 | pass |
| **Banana** | `accent_light` | `#F9B04A` | tailwind colors.banana.amber | `#F9B04A` | dE = 0.0000 | pass |
| | `accent_dark` | `#FCDD82` | tailwind colors.banana.peel | `#FCDD82` | dE = 0.0000 | pass |
| | `accent_strong_light` | `#9A5D00` | formula Branch C (L - 0.374) | `#9A5D00` | dE = 0.0000 | pass |
| | `pressed_light` | `#D97706` | tailwind colors.banana.600 | `#DA9A41` | dE = 0.0803 | exception |
| | `pressed_dark` | `#FBBF24` | tailwind colors.banana.400 | `#E1C26D` | dE = 0.0571 | exception |
| | `on_accent_light` | `#1C1917` | text-stone-900 | `#1C1917` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(249, 176, 74, 0.10)` | bg-banana/10 | `rgba(249, 176, 74, 0.10)` | dE = 0.0000 | pass |
| **Lemon** | `accent_light` | `#FBDB7B` | LemonTheme primaryAccent | `#FBDB7B` | dE = 0.0000 | pass |
| | `accent_dark` | `#FBDB7B` | LemonTheme primaryAccent | `#FBDB7B` | dE = 0.0000 | pass |
| | `accent_strong_light` | `#8A6200` | LemonTheme textAccent (Branch C)| `#816700` | dE = 0.0202 | near |
| | `pressed_light` | `#E5C564` | drawable/bg_lemon_button.xml | `#E0C164` | dE = 0.0133 | pass |
| | `pressed_dark` | `#FFE082` | drawable/bg_lemon_button.xml | `#FFE186` | dE = 0.0041 | pass |
| | `on_accent_light` | `#1C1B14` | LemonTheme onPrimaryAccent | `#1C1917` | dE = 0.0108 | pass |
| | `subtle_light` | `rgba(251, 219, 123, 0.12)` | LemonCard alpha | `rgba(251, 219, 123, 0.10)` | dE = 0.0000 | pass |
| **Quince** | `accent_light` | `#F9768C` | theme.py PRIMARY | `#F9768C` | dE = 0.0000 | pass |
| | `accent_dark` | `#FFD71C` | theme.py SECONDARY | `#FFD71C` | dE = 0.0000 | pass |
| | `accent_strong_light` | `#C63F59` | formula (L - 0.17) | `#C63F59` | dE = 0.0000 | pass |
| | `pressed_light` | `#E05D73` | theme.py log.error | `#DD5D73` | dE = 0.0056 | pass |
| | `pressed_dark` | `#E5BF14` | theme.py log.warning | `#E2BD10` | dE = 0.0072 | pass |
| | `on_accent_light` | `#FFFFFF` | theme.py critical text | `#FFFFFF` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(249, 118, 140, 0.10)` | theme.py subtle | `rgba(249, 118, 140, 0.10)` | dE = 0.0000 | pass |
| **Basket** | `accent_light` | `#DF8A2D` | basket-icon.svg flesh | `#DF8A2D` | dE = 0.0000 | pass |
| | `accent_dark` | `#FACD8F` | basket-icon.svg highlight | `#FACD8F` | dE = 0.0000 | pass |
| | `accent_strong_light` | `#9B5D17` | formula (L - 0.17) | `#9B5D17` | dE = 0.0000 | pass |
| | `pressed_light` | `#C07624` | formula (L - 0.076) | `#C07624` | dE = 0.0000 | pass |
| | `pressed_dark` | `#DBB37D` | formula (L - 0.083) | `#DBB37D` | dE = 0.0000 | pass |
| | `on_accent_light` | `#FFFFFF` | button label ink (5.27:1) | `#FFFFFF` | dE = 0.0000 | pass |
| | `subtle_light` | `rgba(223, 138, 45, 0.10)` | bg-basket/10 | `rgba(223, 138, 45, 0.10)` | dE = 0.0000 | pass |

#### Documented Exceptions (Hand-Picked App Tokens)

The following roles represent intentional hand-picked exceptions where apps deliberately deviated from purely mathematical recipe formulas:

1. **Banana Pressed Tokens**: Banana's client uses pre-existing Tailwind CSS palette steps `banana-600` (`#D97706`, dE = 0.0803) and `banana-400` (`#FBBF24`, dE = 0.0571) instead of formula-generated values.
2. **Plum Dark Pressed**: Plum's client uses deep purple `#5C207E` (dE = 0.3943) to create strong contrast against light backings, rather than lightening it via formula.
3. **Cherry Dark Accent**: Cherry's vector asset uses pale pink `#FFCCCC` (dE = 0.0810) as an anatomical vector highlight, whereas formula derivation generates `#FFAAAA`.
4. **Lemon Text Accent**: Lemon uses hand-picked `#8A6200` (dE = 0.0202, near match) to guarantee readable body text contrast against white canvas.

### 3.4 New-App Implementation Template

Fill this block when creating any new fruit application:

```yaml
# ================================================================
# APP: <FruitName> ACCENT SPECIFICATION TEMPLATE
# Input Icon: public/<fruit>-icon.svg
# ================================================================
app_name: "<FruitName>"
icon_asset: "public/<fruit>-icon.svg"

seeds:
  primary: "<seed_hex>"      # Saturated non-neutral fill (OKLCH L, C, h)
  luminous: "<luminous_hex>" # High-lightness inner flesh or highlight

derived_tokens:
  accent_light: "<accent_light_hex>"
  accent_dark: "<accent_dark_hex>"
  accent_strong_light: "<accent_strong_hex>" # Derived via L - 0.17 for white text
  accent_pressed_light: "<pressed_light_hex>"
  accent_pressed_dark: "<pressed_dark_hex>"
  accent_subtle_light: "rgba(<r>, <g>, <b>, 0.10)"
  accent_subtle_dark: "rgba(<r>, <g>, <b>, 0.10)"
  on_accent_light: "#FFFFFF" # White text on accent_strong_light
  on_accent_dark: "#121310"
  focus_ring_light: "<accent_light_hex>"
  focus_ring_dark: "<accent_dark_hex>"
```

### 3.5 Accent Budget (Whitelist)

To preserve the quiet, bloat-free Apple aesthetic, the accent color is strictly permitted in only **7 UI contexts**. Anything else MUST use base neutrals:

1. **Primary Action Buttons**: Container fill using `accent_strong_light` with white text.
2. **Focus Rings**: Two-layer high-visibility accessibility halo.
3. **Active Navigation Pill / Tab Indicator**: Sliding active indicator capsule.
4. **Active Selection Toggles**: Switch thumb/track, checkbox checked container, radio dot.
5. **Progress Bar Fill**: Active determinate/indeterminate progress indicator.
6. **Status Badges & Metrics**: Numeric counters, positive status dot.
7. **Refraction Field Tint**: Viewport ambient background radial gradients (capped at 3% to 5% opacity).

Forbidden Usages: Generic card backgrounds, card hover borders, secondary buttons, neutral list rows, dialog backdrops, and body text.

---

## 4. Layout and Navigation

### 4.1 Shell Geometry and Breakpoints

| Breakpoint | Viewport Width | Navigation Pattern | Layout Max Width | Outer Gutters |
| :--- | :--- | :--- | :--- | :--- |
| **Desktop (Focused Utility)** | >= 1024px | Top Viewport-Fixed Glass Capsule (`top-3`) | max-w-4xl (896px) | px-6 (24px) |
| **Desktop (Cockpit / Dashboard)** | >= 1024px | Top Viewport-Fixed Glass Capsule (`top-3`) | max-w-7xl (1280px) | px-4 sm:px-6 lg:px-8 |
| **Tablet (sm to md)** | 640px to 1023px | Top Floating Capsule or Docked Bottom Bar | max-w-2xl (672px) | px-5 (20px) |
| **Mobile (<sm)** | < 640px | Top Header (top-0) + Floating Bottom Bar (bottom-3) | Full width (100%) | px-4 (16px) |

### 4.2 Viewport-Fixed Stationary Navigation Chrome

Desktop web navigation is permanently pinned and stationary:

1. **Fixed Viewport Docking**:
   - Navigation header wrapper declares `position: fixed; top: 0.75rem (12px); left: 0; right: 0; z-index: 50; pointer-events: none;`.
   - The inner capsule specifies `pointer-events: auto; margin-left: auto; margin-right: auto;` with width matching the app's layout scale (`max-w-4xl` for focused single-column utilities, `max-w-7xl` for expansive dashboards).
   - The navbar capsule **never scrolls out of view** or moves vertically with page scroll.
2. **Dedicated Content Top Offset**:
   - The `<main>` container must declare a top offset padding (`pt-20` / 80px for standard 52px capsules, `pt-24` / 96px for tall capsules).
   - This guarantees that page titles, hero headers, and top metrics start cleanly below the floating capsule without occlusion or visual clipping.
3. **Fluid Optical Refraction Beneath Chrome**:
   - Page content scrolls smoothly *underneath* the stationary translucent glass capsule (`backdrop-filter: blur(15px)`), creating an authentic Apple-grade optical glass depth effect.

### 4.3 Global Keyboard Navigation (Tab & Route Cycling)

All desktop fruit applications must implement global keyboard shortcuts for primary tab and view navigation:

1. **Cycling Shortcuts**:
   - `Ctrl + ArrowRight` (and `Cmd + ArrowRight` on macOS): Advances circularly to the next primary route/tab (`(currentIndex + 1) % tabs.length`).
   - `Ctrl + ArrowLeft` (and `Cmd + ArrowLeft` on macOS): Returns circularly to the previous primary route/tab (`(currentIndex - 1 + tabs.length) % tabs.length`).
2. **Form & Text Input Evasion**:
   - Global keyboard event listener must inspect the event target before firing.
   - If `e.target` is an interactive text input (`HTMLInputElement`, `HTMLTextAreaElement`, `HTMLSelectElement`, or `isContentEditable`), shortcut handling is bypassed immediately. Keystrokes pass through untouched to preserve normal text editing and cursor navigation.
3. **Audio & Motion Integration**:
   - Every shortcut-driven tab switch triggers the throttled `scroll` audio SFX tick (`SCROLL_THROTTLE_MS = 140ms`).
   - Glides the 300ms magnetic indicator pill (`motion.pill`) smoothly to the new active tab.

---

## 5. Components Matrix (Shared Primitives)

Every component specified across all required states.

### 5.1 Buttons (`.btn-glass-primary` and `.btn-glass-secondary`)

- **Anatomy**: Label text, optional leading/trailing icon (h-4 w-4), pill container.
- **Dimensions**: Padding `py-[0.6rem] px-[1.35rem]` (9.6px x 21.6px), height ~38px (Web) / 48dp touch target (Android). Font size 14px (text-sm font-bold). Shape: 9999px (rounded-full).

| State | Primary Light (White on Accent Strong) | Primary Dark | Secondary Light | Secondary Dark |
| :--- | :--- | :--- | :--- | :--- |
| **Default** | `bg: #007200` (accent_strong_light)<br>`text: #FFFFFF` (6.16:1)<br>`border: 1px solid rgba(255,255,255,0.40)` | `bg: rgba(accent_dark, 0.70)`<br>`text: #121310` (10.94:1)<br>`border: 1px solid rgba(255,255,255,0.25)` | `bg: rgba(255,255,255,0.35)`<br>`text: #1C1917`<br>`border: 1px solid rgba(255,255,255,0.65)` | `bg: rgba(22,23,19,0.40)`<br>`text: #F3F4F1`<br>`border: 1px solid rgba(255,255,255,0.12)` |
| **Hover** | `bg: #008200`<br>`translateY(-1px) scale(1.015)` | `bg: rgba(accent_dark, 0.85)`<br>`translateY(-1px) scale(1.015)` | `bg: rgba(255,255,255,0.55)`<br>`translateY(-1px) scale(1.015)` | `bg: rgba(22,23,19,0.60)`<br>`translateY(-1px) scale(1.015)` |
| **Pressed** | `translateY(0.5px) scale(0.985)` | `translateY(0.5px) scale(0.985)` | `translateY(0.5px) scale(0.985)` | `translateY(0.5px) scale(0.985)` |
| **Focus** | Two-layer ring (2px #FFFFFF, 4px accent_light) | Two-layer ring (2px #181915, 4px accent_dark) | Two-layer ring | Two-layer ring |
| **Disabled**| `opacity: 0.45`, `cursor: not-allowed` | `opacity: 0.45`, `cursor: not-allowed` | `opacity: 0.45` | `opacity: 0.45` |
| **Loading** | `opacity: 0.85`, spinner replaces lead icon | Identical | Identical | Identical |

#### Flat Action Button Standard

When an application specifies flat primary buttons (rather than optical glass with glow shadows):
- **Background**: Solid flat accent color (e.g. `accent_strong_light` or solid primary token) with zero linear or radial gradients (`background-image: none !important`).
- **Shadow**: `box-shadow: none !important`. No drop shadows, outer glow halos, or inset bevel lines.
- **Border**: `border: none !important`. Zero translucent white border rims.
- **Hover / Active**: Flat solid darkened states (`0.15s ease`) with `transform: none !important` (no translateY lift or depression).
- **Physical Feedback**: Delivered via instant color transition paired with the tactile `enter` audio SFX tick.

### 5.2 Toggle Switch (`LemonSwitch`)

- **Anatomy**: Pill track with 2px inset circular thumb.
- **Dimensions**: Track: 50dp width x 30dp height. Thumb: 26dp diameter. Travel distance: 22dp. Bounding touch box: 48dp x 48dp minimum (sizeIn(minWidth=48.dp, minHeight=48.dp)). Shape: RoundedCornerShape(100.dp).

| State | Track Color (Light) | Track Color (Dark) | Thumb Color | Haptics / Motion |
| :--- | :--- | :--- | :--- | :--- |
| **Off (Unchecked)**| `#E7E5E4` (stone-200) | `#292524` (stone-800) | `#FFFFFF` (Light) / `#E0DDD5` (Dark) | thumbOffset = 2.dp |
| **On (Checked)** | `primaryAccent` token | `primaryAccent` token | `#FFFFFF` | thumbOffset = 22.dp, spring animation |
| **Press / Drag** | Track color maintained | Track color maintained | Elevation expands slightly | TextHandleMove haptic on toggle |
| **Disabled** | `opacity: 0.45` | `opacity: 0.45` | `opacity: 0.80` | Non-interactive |

### 5.3 Text Inputs (`TextField` and Search Fields)

- **Anatomy**: Container with optional leading search icon, text input, placeholder, clear button.
- **Dimensions**: Height 44px to 48px, padding px-4 py-3 (16px x 12px), radius 12px (rounded-xl / RoundedCornerShape(12.dp)). Font size 14px (text-sm).

| State | Light Styling | Dark Styling |
| :--- | :--- | :--- |
| **Default** | `glass-card`, `border: 1px solid rgba(0,0,0,0.08)`, `text: #1C1917` | `glass-card`, `border: 1px solid rgba(255,255,255,0.10)`, `text: #FAFAF9` |
| **Hover** | `border: #D6D3D1` (border-stone-300) | `border: #44403C` (border-stone-700) |
| **Focus** | Two-layer focus ring (2px #FFFFFF, 4px accent_light) | Two-layer focus ring (2px #181915, 4px accent_dark) |
| **Disabled** | `opacity: 0.50`, `cursor: not-allowed` | `opacity: 0.50` |
| **Error** | `border: #DC2626` (red-600), `ring: 2px rgba(220,38,38,0.20)` | `border: #F87171` (red-400), `ring: 2px rgba(248,113,113,0.30)` |

### 5.4 Cards (`.glass-card`, `FeatureCard`, `LemonCard`)

- **Anatomy**: Rounded surface container, optional icon box, title, description, footer action.
- **Dimensions**: Radius 16px (rounded-2xl) or 24px (rounded-3xl for large containers). Padding 16px to 24px (p-4 to p-6).
- **Glass Token**: `.glass-card` (blur(10px) saturate(150%)).
- **States**:
  - Default: Border `rgba(255,255,255,0.50)` (Light) / `rgba(255,255,255,0.08)` (Dark). Shadow elevation.soft.
  - Hover: `hover:border-stone-300 dark:hover:border-stone-700`, `hover:shadow-lift`, `hover:bg-white/45 dark:hover:bg-white/[0.05]`.
  - Disabled: `opacity: 0.50`.

### 5.5 List Rows (`ResultPanel` item, `LemonGroupedRow`)

- **Anatomy**: Leading icon/content, title text, subtitle, trailing action/content, hairline divider.
- **Dimensions**: Radius 16px (rounded-2xl), padding px-5 py-4 (Web) / 16.dp (Android), gap 14px. Divider start inset: 16dp on Android.
- **Surface**: `bg-white/70 dark:bg-[#1C1D18]/70` with backdrop-blur-md and shadow-2xs.
- **States**: Hover lifts row by translateY(-1px) and shows subtle stone border darkening.

### 5.6 Navigation Bar / Floating Capsule (`Header`, `FloatingBottomBar`)

- **Anatomy**: Wordmark logo, optional live status badge, primary router tabs, 300ms sliding indicator pill, theme mode toggle (Sun/Moon), and optional utility action (e.g. manual refresh). **No sound toggle button** (sound effects stay permanently enabled; primary navigation chrome remains uncluttered).
- **Dimensions**:
  - Desktop: Max width matches application layout scale (`max-w-4xl` for focused single-column tools, `max-w-7xl` for cockpits/dashboards), padding `px-4 sm:px-6 lg:px-8`, height ~52px, viewport-fixed stationary at `top-3` (`fixed top-3 left-0 right-0 z-50 pointer-events-none` with inner capsule `pointer-events-auto mx-auto`). Capsule shape 9999px.
  - Android: Docked bottom bar with WindowInsets.navigationBars, height (64 * fontScale.coerceIn(1.0f, 1.25f)).dp, RoundedCornerShape(100.dp).
- **Surface**: `.glass-capsule` (blur(15px), fill 0.20 opacity).
- **Stationary Viewport Anchoring**: The capsule never scrolls out of the viewport. Page content passes smoothly underneath, visible through the optical backdrop refraction blur.
- **Active Pill Indicator**: Solid indicator pill (rounded-full bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900). Glides smoothly with 300ms cubic-bezier(0.2, 0.8, 0.2, 1).

### 5.7 Tabs / Segmented Control (`CustomSelect`, `LemonSegmentedControl`)

- **Anatomy**: Capsule track hosting segmented pills with text and optional count badge.
- **Dimensions**: Height 42dp to 44px (scales dynamically up to 1.5x with user font scaling on Android). Capsule shape 9999px / RoundedCornerShape(100.dp).
- **Indicator**: Sliding pill with shadow-xs and spring(dampingRatio = NoBouncy, stiffness = MediumLow).

### 5.8 Dialogs and Bottom Sheets (`Popup`, `LemonShapes.sheet`)

- **Anatomy**: Dimmed backdrop scrim, glass panel container, title bar, close dismiss button, content body, footer actions.
- **Dimensions**:
  - Web Dialog: Radius 32px (rounded-[2rem]), widths sm (384px), md (448px), lg (576px).
  - Android Dialog: Radius 24dp (LemonShapes.dialog).
  - Android Bottom Sheet: RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp).
- **Backdrop**: Scrim rgba(17, 24, 39, 0.45) with backdrop-blur-sm. Body scroll locked (overflow: hidden). Escape key closes dialog.

### 5.9 Toast Notifications (`ToastProvider`, `LemonFeedbackBanner`)

- **Anatomy**: Status icon (CheckCircle, AlertCircle), message text, 48dp dismiss button.
- **Dimensions**: Width max-w-sm (384px), padding px-4 py-3, radius 16px (rounded-2xl).
- **Auto-Dismiss**: Exact duration **`4200ms`** (4.2 seconds).
- **Audio Pairing**: Emitting success/info triggers playNotification(); error triggers playFailed().

### 5.10 Badges (`LemonBadge`)

- **Anatomy**: Capsule pill with 6dp color-matched indicator dot, uppercase label text.
- **Dimensions**: Radius 100.dp, padding horizontal = 9.dp, vertical = 3.5.dp, text 11sp font-bold. Single-line guarantee with maxLines = 1, softWrap = false, overflow = TextOverflow.Ellipsis.
- **Variants**: SUCCESS (green), WARNING (amber), DANGER (red), INFO (blue), INACTIVE (stone).

### 5.11 Empty, Loading, and Error States

- **Loading Spinner**: Rotating circular spinner 16px x 16px (SpinnerIcon animate-spin), color accent_light (Light) / accent_dark (Dark).
- **Progress Track**: Height 6px (h-1.5), radius 9999px. Track: stone-100 / stone-800. Fill: accent_light / accent_dark with transition-all duration-300.
- **Empty State Frame**: Centered column, circular icon container 64px x 64px (64.dp CircleShape) in surface.well with 28px icon, title, description, and optional action button.
- **Error Banner**: Background rgba(220, 38, 38, 0.08), border rgba(220, 38, 38, 0.20), text #DC2626 / #F87171.

### 5.12 App Icon System Rules

- **Subject**: Single cross-section or fruit silhouette enclosed by dark contour.
- **Outlines**: Prominent black contour lines (#000000) of weight 1.8px to 3.7px in SVG space.
- **Palette Constraint**: Max 3 core colors (Dominant flesh, highlight/core, accent seed/leaf).
- **Android Adaptive Icon**: 108dp x 108dp canvas with 72dp center safe mask. Background layer = neutral cream (#F8F9F5) or dark obsidian (#121310). Foreground layer = fruit vector mark.

---

## 6. Platform Mapping: Web <-> Android

### 6.1 Unit Mapping

| Dimension | Web CSS Unit | Android Compose Unit | Conversion Formula |
| :--- | :--- | :--- | :--- |
| **Layout Spacing** | `px` or `rem` (1rem = 16px) | `dp` | 1px = 1dp (at 160dpi baseline) |
| **Font Sizing** | `px` or `rem` | `sp` | Literal mapping from 7-size scale (14px = 14sp) |
| **Line Height** | Unitless multiplier (e.g. 1.4) or `px` | `sp` | lineHeight = fontSize * multiplier in sp |
| **Letter Spacing** | `em` (e.g. -0.011em) | `sp` | tracking_sp = fontSize_sp * tracking_em |
| **Radius** | `px` or `rem` | `dp` | 16px = 16.dp |
| **Blur Radius** | `px` (blur(12px)) | `Float` | RenderEffect.createBlurEffect(12f, 12f, TileMode.CLAMP) |

### 6.2 Token Naming Translation

| Concept | Web CSS Variable / Class | Android Jetpack Compose Token | Source Origin |
| :--- | :--- | :--- | :--- |
| Page Canvas | `--canvas` / `bg-[#F8F9F5]` | `LemonTheme.colors.pageBackground` | Kiwi reference / LemonTheme |
| Standard Surface | `.glass-card` / `bg-white` | `LemonTheme.colors.cardBackground` | Kiwi reference / LemonTheme |
| Elevated Surface | `bg-[#1C1D18]` | `LemonTheme.colors.cardElevatedBackground` | Kiwi reference / LemonTheme |
| Primary Accent | `--accent` / `kiwi-flesh` | `LemonTheme.colors.primaryAccent` | Derived / LemonTheme |
| Accessible Accent Strong| `--accent-strong` / `#007200` | `LemonTheme.colors.primaryAccent` (darkened) | Derived formula L - 0.17 |
| On-Accent Text | `text-white` | `LemonTheme.colors.onPrimaryAccent` | Derived / LemonTheme |
| Subtle Accent Fill | `bg-accent/10` | `LemonTheme.colors.primaryAccent.copy(alpha = 0.10f)` | Derived / LemonTheme |
| Card Radius | `rounded-2xl` (16px) | `LemonTheme.shapes.card` (16.dp) | LemonShapes.kt |
| Dialog Radius | `rounded-[2rem]` (32px) | `LemonShapes.dialog` (24.dp) | Intentional platform difference |
| Capsule Radius | `rounded-full` (9999px) | `LemonTheme.shapes.button` (100.dp) | LemonShapes.kt |
| Soft Shadow | `shadow-soft` | `Modifier.shadow(elevation = 4.dp, shape = ...)` | tailwind.config / Compose |

### 6.3 Interaction and Platform Differences

| Interaction / Feature | Desktop Web | Android (Jetpack Compose) | Status / Rationale |
| :--- | :--- | :--- | :--- |
| **Touch Target Size** | 38px desktop button height accepted | Strict 48dp x 48dp minimum (sizeIn(minWidth=48.dp, minHeight=48.dp)) | Intentional platform ergonomic rule |
| **Hover vs Pressed** | CSS :hover (translateY(-1px) scale(1.015)) | No hover state; immediate pressed state (scale(0.985)) on touch down | Intentional touch interface rule |
| **Physical Feedback** | Tactile audio SFX (enter, back, scroll, notification, failed) | Tactile haptics (TextHandleMove) + Audio SFX (SoundPool, required spec, not yet implemented) | Audio and haptics fire concurrently |
| **Reduced Motion** | @media (prefers-reduced-motion: reduce) sets animation/transition duration to 0.01ms | Queries Settings.Global.ANIMATOR_DURATION_SCALE == 0f to substitute snap() | Intentional platform accessibility sync |
| **Dynamic Font Scaling** | Browser zoom (rem root font scale) | User font scale (density.fontScale). Navigation and segmented controls expand height up to 1.5x | Intentional mobile accessibility feature |
| **Navigation Chrome** | Floating capsule docked top center (max-w-4xl, top-3) | Floating bottom capsule docked above navigation bar insets (FloatingBottomBar) | Intentional platform ergonomics |
| **Glass / Blur Fallback**| @supports not (backdrop-filter) -> solid surface | Android API < 31 (Build.VERSION_CODES.S) -> solid surface without RenderEffect | Intentional hardware fallback |
| **System Bar Sync** | Browser `<meta name="theme-color">` update | `WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !isDark`<br>`isAppearanceLightNavigationBars = !isDark` | Intentional platform chrome integration |

---

## 7. Accessibility

### 7.1 Authoritative Contrast Ratios (WCAG 2.1 AA)

All contrast ratios recomputed programmatically via WCAG relative luminance formulas against base canvas and surfaces:

| Text / Foreground Token | Background Surface | Relative Luminances | Effective Contrast Ratio | WCAG AA Status | Notes / Exceptions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ink_primary_light` (`#1C1917`) | `canvas_light` (`#F8F9F5`) | 0.0100 on 0.9430 | **16.54:1** | PASS (>= 4.5:1) | Maximum primary readability |
| `ink_primary_light` (`#1C1917`) | `surface_light` (`#FFFFFF`)| 0.0100 on 1.0000 | **17.49:1** | PASS (>= 4.5:1) | Standard light surface reading |
| `ink_secondary_light` (`#57534E`) | `canvas_light` (`#F8F9F5`) | 0.0876 on 0.9430 | **7.22:1** | PASS (>= 4.5:1) | Secondary helper text |
| `ink_secondary_light` (`#57534E`) | `surface_light` (`#FFFFFF`)| 0.0876 on 1.0000 | **7.63:1** | PASS (>= 4.5:1) | Form input labels |
| `ink_muted_light` (`#78716C`) | `canvas_light` (`#F8F9F5`) | 0.1689 on 0.9430 | **4.54:1** | PASS (>= 4.5:1) | Muted caption metadata |
| `text_placeholder_light` (`#A8A29E`) | `canvas_light` (`#F8F9F5`) | 0.3663 on 0.9430 | **2.39:1** | FAIL (< 4.5:1) | **Documented Exception**: Subtle placeholder text is non-essential under WCAG 1.4.3. Accessible alternative token: `#78716C` (4.54:1). |
| `ink_primary_dark` (`#F3F4F1`) | `canvas_dark` (`#121310`) | 0.9011 on 0.0063 | **16.89:1** | PASS (>= 4.5:1) | Dark canvas primary text |
| `ink_primary_dark` (`#F3F4F1`) | `surface_dark` (`#181915`) | 0.9011 on 0.0094 | **16.00:1** | PASS (>= 4.5:1) | Dark card primary text |
| `ink_secondary_dark` (`#A8A29E`) | `canvas_dark` (`#121310`) | 0.3663 on 0.0063 | **7.39:1** | PASS (>= 4.5:1) | Dark secondary text |
| `ink_muted_dark` (`#78716C`) | `canvas_dark` (`#121310`) | 0.1689 on 0.0063 | **3.89:1** | FAIL (< 4.5:1) | **Documented Exception**: Passes 3:1 for incidental text. Preserves visual hierarchy below secondary text. Accessible alternative token: `#8E8883` (4.53:1). |
| `white` (`#FFFFFF`) | `accent_light` (`#0DAA26`) | 1.0000 on 0.2897 | **3.09:1** | FAIL (< 4.5:1) | Solid raw accent fails 4.5:1 for 14px text |
| `white` (`#FFFFFF`) | `accent_light` (0.70 glass)| 1.0000 on 0.4150 | **2.26:1** | FAIL (< 4.5:1) | Blended over glass fails severely |
| `white` (`#FFFFFF`) | `accent_strong_light` (`#007200`)| 1.0000 on 0.1203 | **6.16:1** | PASS (>= 4.5:1) | Solid primary button fill |
| `white` (`#FFFFFF`) | `accent_strong_light` (0.85 alpha)| 1.0000 on 0.1764 | **4.65:1** | PASS (>= 4.5:1) | Blended over canvas passes WCAG AA |
| `obsidian` (`#121310`) | `accent_dark` (`#84DD00`) | 0.0063 on 0.5662 | **10.94:1** | PASS (>= 4.5:1) | Luminous dark mode button label |

### 7.2 Minimum Text Size and Focus Rings

1. **Minimum Text Size**: Hard minimum `10px` on web, `11sp` on Android. No text element may render smaller than these minimums.
2. **Two-Layer Focus Ring**: All interactive elements render a two-layer high-visibility ring on `:focus-visible`:
   - Light Mode: `2px solid #FFFFFF` inner ring + `4px solid accent_light` outer ring.
   - Dark Mode: `2px solid #181915` inner ring + `4px solid accent_dark` outer ring.
3. **Font-Scale Resilience**: All container heights enclosing single-line text (badges, buttons, segmented controls) must use dynamic height scaling on Android (`barHeight = (64 * density.fontScale.coerceIn(1.0f, 1.25f)).dp`) to guarantee zero text truncation.
4. **Reduced Motion**: Respects user OS reduced-motion preferences without exception.

---

## 8. Do / Don't

Concrete rules derived from real code errors and discrepancies found in the codebase:

- **DO** use dual accent seeds for light and dark modes when the icon has both dark rind and vibrant flesh colors (#0DAA26 in light, #84DD00 in dark).
- **DON'T** use `bg-kiwi-flesh` in dark mode buttons or active tiles (spotted in CompressionLevelSelector active state and PdfOperationTile active state).
- **DO** set glass-capsule background fill opacity to 0.20 (rgba(255, 255, 255, 0.20)).
- **DON'T** raise glass-capsule fill opacity to 0.88 or 0.82 (spotted in Banana .glass-capsule and Plum .glass-capsule).
- **DO** use `white on accent_strong_light` (#007200) for primary buttons in light mode to meet WCAG AA 4.5:1 contrast.
- **DON'T** place white text directly on raw accent_light (#0DAA26) without darkening it to accent_strong_light (effective contrast drops to 2.26:1 on glass, failing WCAG AA).
- **DO** keep neutral cards and list rows neutral on hover (hover:border-stone-300 dark:hover:border-stone-700).
- **DON'T** bleed accent color onto neutral card hover borders (hover:border-kiwi-flesh/50 error in ResultPanel).
- **DO** enforce minimum 48dp touch targets on Android using Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).
- **DON'T** create sub-40dp touchable icon buttons on mobile.
- **DO** provide solid fallback backgrounds (#FFFFFF in light, #181915 in dark) when backdrop blur is unsupported.
- **DON'T** leave glass panels transparent when running on devices without backdrop-filter support.
- **DO** use `Host Grotesk` for all component UI, forms, and headings.
- **DON'T** use `Unbounded` for body paragraphs, buttons, form inputs, or tooltips (Unbounded is strictly display-only).
- **DO** keep the top navigation capsule stationary (`position: fixed; top: 0.75rem`) so it remains docked while page content scrolls fluidly underneath.
- **DON'T** let the navigation bar scroll out of view or get pushed offscreen.
- **DO** keep tactile audio sound effects permanently enabled without cluttering the navigation chrome with a sound toggle button.
- **DON'T** add a dedicated sound toggle button to the top navigation capsule.
- **DO** wire standardized `Ctrl + ArrowLeft` and `Ctrl + ArrowRight` circular tab navigation shortcuts, evading inputs and textareas.
- **DON'T** intercept arrow keystrokes when the user is actively typing in text inputs, textareas, or select dropdowns.
- **DO** guarantee stutter-free 60fps/120fps transitions by animating strictly GPU-composited properties (`transform` and `opacity`).
- **DON'T** animate geometric layout properties (`width`, `height`, `margin`, `padding`, `top`, `left`) during route transitions.
- **DO** support strictly flat solid buttons without gradients, bevels, or bright glow shadows when an application specifies flat button styling.

---

## 9. New-App Conformance Checklist

A reviewer or automated test can verify any fruit application against this checklist (Pass/Fail):

- [ ] **Canvas Color**: Light mode body canvas is exact `#F8F9F5`; Dark mode canvas is exact `#121310`.
- [ ] **Primary Ink**: Body primary ink is exact `#1C1917` (Light) and `#F3F4F1` (Dark).
- [ ] **Surface Fallback**: Non-blurred surfaces fall back to `#FFFFFF` (Light) and `#181915` (Dark).
- [ ] **Typography**: Host Grotesk is loaded for UI/body; Unbounded is loaded strictly for wordmark/hero display.
- [ ] **Literal 7-Size Scale**: All type sizing maps strictly to the 7 functional sizes (Micro, Caption, Body, Subtitle, Title, PageTitle, Hero). No rogue font sizes.
- [ ] **Stationary Capsule Navigation**: Desktop navigation is a floating fixed capsule docked at top-3 (`position: fixed`) with matching container width, top padding offset, and 300ms sliding active pill.
- [ ] **Glass Optical Values**: Capsule is 15px blur (0.20 fill); Panel is 12px blur (0.38 fill, 160% sat); Card is 10px blur (0.28 fill, 150% sat).
- [ ] **Accent Derivation**: Accent tokens are derived from the icon palette via Section 3 OKLCH recipe; exact hex and OKLCH values documented.
- [ ] **Accent Budget**: Accent color is restricted to primary buttons, focus rings, active tabs, progress bars, switches, and refraction field tint. Cards remain neutral.
- [ ] **Button Contrast (4.5:1)**: Light mode primary button uses white text on accent_strong_light, achieving >= 4.5:1 contrast against effective button fill.
- [ ] **Anti-Bloat Caps**: App uses <= 7 type sizes, <= 6 radii, <= 4 shadow levels (+ flat), <= 3 glass blur levels, and 11 spacing steps.
- [ ] **Touch Target**: All interactive controls on Android or mobile web meet minimum 48dp x 48dp hit area.
- [ ] **Focus Rings**: All interactive elements render the two-layer focus ring (2px white/obsidian + 4px accent).
- [ ] **Sound Effects**: All five audio categories (enter, back, notification, failed, scroll) are wired, sound stays permanently enabled without header clutter, and silent failure is verified.
- [ ] **Global Keyboard Shortcuts**: `Ctrl + ArrowLeft` and `Ctrl + ArrowRight` circular tab navigation is implemented with text input element evasion.
- [ ] **Stutter-Free Motion**: All route transitions and interactive micro-physics animate strictly via `transform` and `opacity` with zero layout thrashing or geometry reflows.
- [ ] **Reduced Motion**: Prefers-reduced-motion collapses all transitions to 0.01ms (Web) or snap() (Compose).

---

## 10. Discrepancies and Open Questions

### 10.1 As-Built Code Discrepancies

1. **Primary Button Contrast Violation in Light Mode (`index.css`)**:
   - *Code*: `.btn-glass-primary` uses `background: rgba(13, 170, 38, 0.70)` with `color: #FFFFFF`.
   - *Measured Contrast*: Effective contrast over canvas #F8F9F5 is **2.26:1** (fails WCAG AA 4.5:1 threshold for 14px bold text).
   - *Resolution*: Enforce `accent_strong_light` (`#007200`, **6.16:1** solid, **4.65:1** over canvas) as the light-mode container fill when white text is used.
2. **Card Hover Border Using Accent (`ResultPanel.tsx`, `Dropzone.tsx`, `FormatPicker.tsx`)**:
   - *Code*: `hover:border-kiwi-flesh/50 dark:hover:border-kiwi-lime/50` on generic result items and dropzones.
   - *Violation*: Violates Section 3.5 Accent Budget (cards must remain neutral).
   - *Resolution*: Neutral cards must hover to `hover:border-stone-300 dark:hover:border-stone-700` and elevation lift. Accent hover border is reserved exclusively for actively selectable interactive tiles.
3. **Switch ON Track Color Not Matching Accent Tokens (`LemonSwitch.kt`)**:
   - *Code*: `LemonSwitch.kt` hardcodes `brandGreen = Color(0xFF2FA84F)` in light and `Color(0xFF30B955)` in dark for `switchTrackOn`.
   - *Violation*: Breaks the family rule that active controls use that app's derived primaryAccent.
   - *Resolution*: `switchTrackOn` must bind to `LemonTheme.colors.primaryAccent`.
4. **BorderRadius.card (1.25rem / 20px) Outside Radii Scale (`tailwind.config.ts`)**:
   - *Code*: `tailwind.config.ts` defines `card: '1.25rem'` (20px), which falls outside the 6-radius scale (8, 12, 16, 24, 32, 9999px).
   - *Resolution*: Kept as an as-built Tailwind theme alias in Kiwi, but all new components across the family must use `rounded-2xl` (16px) or `rounded-3xl` (24px).
5. **Button and Badge Micro-Padding Off Spacing Grid (`index.css`, `LemonBadge.kt`)**:
   - *Code*: `.btn-glass-primary` uses padding `0.6rem` (9.6px) / `1.35rem` (21.6px); `LemonBadge.kt` uses `horizontal = 9.dp, vertical = 3.5.dp`.
   - *Resolution*: Kept as intentional optical micro-padding exceptions to vertically center glyphs and typography within capsule borders, while outer margins strictly adhere to the 4pt/8pt grid.
6. **Dark Mode Accent in Selected Tiles (`CompressionLevelSelector.tsx` & `PdfOperationTile.tsx`)**:
   - *Code*: Active state hardcodes `dark:bg-kiwi-flesh` instead of `dark:bg-kiwi-lime`.
   - *Resolution*: Active items in dark mode must use `dark:bg-kiwi-lime dark:text-stone-900`.
7. **Glass Capsule Alpha Drift in Sibling Apps (`banana` & `plum`)**:
   - *Code*: Banana uses `rgba(255, 255, 255, 0.88)` and Plum uses `rgba(255, 255, 255, 0.82)`.
   - *Resolution*: All apps must adhere to Kiwi's crystal glass 0.20 alpha.

### 10.2 Open Questions

1. **Secondary Accent Derivation for Single-Hue Icons**:
   - *Status*: `UNDECIDED`.
   - *Question*: For single-hue fruit icons (e.g., Lemon or Cherry), should the secondary contrast accent (like Kiwi's coral #FF6767) be derived via a deterministic complementary angle (+180 deg) or a triadic shift (+120 deg)?

---

## 11. Appendix: Token -> Source Symbol Map

Traceable mapping of design tokens to symbols and selectors across the codebase:

| Token Category | Token Symbol | Source File | Source Selector / Definition |
| :--- | :--- | :--- | :--- |
| **Canvas** | `canvas.page` | `client/src/index.css` | `body { background-color: #F8F9F5; }` |
| **Canvas** | `canvas.page (dark)` | `client/src/index.css` | `body.dark { background-color: #121310; }` |
| **Surface** | `surface.well` | `client/src/components/features/FormatPicker.tsx` | `bg-stone-50/50 dark:bg-[#141512]/50` |
| **Ink** | `text.primary` | `client/src/components/layout/PageShell.tsx` | `text-stone-900 dark:text-stone-100` |
| **Ink** | `text.secondary` | `client/src/components/layout/PageShell.tsx` | `text-stone-600 dark:text-stone-400` |
| **Accent** | `accent.kiwi.flesh` | `client/tailwind.config.ts` | `colors.kiwi.flesh: '#0DAA26'` |
| **Accent** | `accent.kiwi.lime` | `client/tailwind.config.ts` | `colors.kiwi.lime: '#84DD00'` |
| **Glass** | `.glass-capsule` | `client/src/index.css` | `.glass-capsule { backdrop-filter: blur(15px); }` |
| **Glass** | `.glass-panel` | `client/src/index.css` | `.glass-panel { backdrop-filter: blur(12px) saturate(160%); }` |
| **Glass** | `.glass-card` | `client/src/index.css` | `.glass-card { backdrop-filter: blur(10px) saturate(150%); }` |
| **Typography** | `family.sans` | `client/src/index.css` | `@font-face { font-family: 'Host Grotesk'; }` |
| **Typography** | `family.display`| `client/src/index.css` | `@font-face { font-family: 'Unbounded'; }` |
| **Radii** | `radius.card` | `client/tailwind.config.ts` | `borderRadius.card: '1.25rem'` |
| **Radii** | `radius.capsule`| `client/tailwind.config.ts` | `borderRadius.capsule: '9999px'` |
| **Shadow** | `shadow.soft` | `client/tailwind.config.ts` | `boxShadow.soft` |
| **Shadow** | `shadow.floating`| `client/tailwind.config.ts` | `boxShadow.floating` |
| **Shadow** | `shadow.lift` | `client/tailwind.config.ts` | `boxShadow.lift` |
| **Motion** | `motion.tactile`| `client/src/index.css` | `.btn-interactive:hover / :active` |
| **Motion** | `motion.slide` | `client/src/index.css` | `@keyframes slide-out-to-left / slide-in-from-right` |
| **Motion** | `motion.android`| `lemon/.../CoconutMotion.kt`| `object CoconutMotion` |
| **Audio** | `audio.engine` | `client/src/lib/sound.ts` | `export function playSound(category)` |
| **Android Theme**| `theme.android`| `lemon/.../CoconutTheme.kt` | `val LemonLightSemanticColors` / `LemonTypography` |
| **Android Bottom**| `bar.android` | `lemon/.../FloatingBottomBar.kt` | `@Composable fun FloatingBottomBar` |
