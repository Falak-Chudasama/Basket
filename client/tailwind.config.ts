import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Basket Flat Vibrant Orange Accent Tokens (No gradients, no brown)
        basket: {
          DEFAULT: '#F97316', // Pure flat vibrant orange
          dark: '#FB923C',    // Flat luminous orange
          strong: '#EA580C',  // Flat pressed/hover orange
          50: '#FFF7ED',
          100: '#FFEDD5',
          200: '#FED7AA',
          300: '#FDBA74',
          400: '#FB923C',
          500: '#F97316',
          600: '#EA580C',
          700: '#C2410C',
          800: '#9A3412',
          900: '#7C2D12',
        },
        // Base Neutral Substrate Tokens (DESIGN.md Section 2.1)
        canvas: {
          light: '#F8F9F5',
          dark: '#121310',
        },
        surface: {
          light: '#FFFFFF',
          dark: '#181915',
          elevated: '#1C1D18',
          well: '#141512',
        },
      },
      fontFamily: {
        sans: ['"Host Grotesk"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Unbounded"', 'sans-serif'],
        mono: ['"Azeret Mono"', 'ui-monospace', 'monospace'],
      },
      // Anti-Bloat Cap 1: Strictly 7 Functional Type Sizes (DESIGN.md Section 1 & 2.2)
      fontSize: {
        micro: ['0.625rem', { lineHeight: '1.2', letterSpacing: '0.05em', fontWeight: '700' }],      // 10px
        caption: ['0.75rem', { lineHeight: '1.4', letterSpacing: '0em', fontWeight: '600' }],        // 12px
        body: ['0.875rem', { lineHeight: '1.5', letterSpacing: '-0.011em', fontWeight: '400' }],     // 14px
        subtitle: ['1rem', { lineHeight: '1.4', letterSpacing: '-0.015em', fontWeight: '700' }],      // 16px
        title: ['1.25rem', { lineHeight: '1.3', letterSpacing: '-0.02em', fontWeight: '700' }],       // 20px
        pagetitle: ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.025em', fontWeight: '800' }],   // 24px
        hero: ['2.25rem', { lineHeight: '1.1', letterSpacing: '-0.03em', fontWeight: '800' }],        // 36px
      },
      // Anti-Bloat Cap 2: Strictly 6 Radii Values (DESIGN.md Section 1 & 2.4)
      borderRadius: {
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
        '3xl': '24px',
        modal: '32px',
        capsule: '9999px',
      },
      // Anti-Bloat Cap 3: Strictly 4 Elevation Levels + Flat Base (DESIGN.md Section 1 & 2.5)
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        soft: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        floating: '0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 2px 8px -2px rgba(0, 0, 0, 0.04)',
        lift: '0 12px 32px -4px rgba(0, 0, 0, 0.09)',
      },
      // Anti-Bloat Cap 5: Disciplined Spacing Steps (DESIGN.md Section 1 & 2.3)
      spacing: {
        '6px': '6px',
        '28px': '28px',
      },
      // Motion Timing and Curves (DESIGN.md Section 2.9)
      transitionTimingFunction: {
        tactile: 'cubic-bezier(0.16, 1, 0.3, 1)',
        slide: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
      transitionDuration: {
        micro: '140ms',
        short: '180ms',
        medium: '220ms',
        slide: '260ms',
        subpage: '280ms',
        pill: '300ms',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'page-enter': {
          from: { opacity: '0', transform: 'translateY(6px) scale(0.996)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.15s ease-out',
        'scale-in': 'scale-in 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slide-up 0.18s ease-out',
        'page-enter': 'page-enter 0.22s cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
} satisfies Config
