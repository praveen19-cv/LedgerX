/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d7fe',
          300: '#a5bcfc',
          400: '#8199f9',
          500: '#6174f3',
          600: '#4f56e8',
          700: '#3f42d0',
          800: '#3438a8',
          900: '#2e3485',
        },
        surface: {
          900: '#0a0b14',
          800: '#12141f',
          700: '#1a1d2e',
          600: '#242840',
          500: '#2f3352',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
