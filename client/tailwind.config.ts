import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        basket: {
          DEFAULT: '#DF8A2D',
          50: '#FDF8F0',
          100: '#FBDBAC',
          200: '#FACD8F',
          300: '#F5B05C',
          400: '#EE9228',
          500: '#DF8A2D',
          600: '#C27018',
          700: '#9B540E',
          800: '#753C0B',
          900: '#522807',
        },
        kiwi: {
          flesh: '#0DAA26',
          'flesh-50': '#F0FDF2',
          'flesh-100': '#E4FFB0',
          'flesh-600': '#0B8F20',
          lime: '#84DD00',
          coral: '#FF6767',
        },
      },
      fontFamily: {
        sans: ['"Host Grotesk"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Unbounded"', 'sans-serif'],
        mono: ['"Azeret Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '1.25rem',
        capsule: '9999px',
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        lift: '0 12px 32px -4px rgba(0, 0, 0, 0.09)',
        floating: '0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 2px 8px -2px rgba(0, 0, 0, 0.04)',
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
      },
      animation: {
        'fade-in': 'fade-in 0.15s ease-out',
        'scale-in': 'scale-in 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slide-up 0.18s ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config

