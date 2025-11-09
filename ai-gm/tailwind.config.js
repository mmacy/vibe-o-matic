/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          dark: '#2563eb',
        },
        background: {
          DEFAULT: '#0f172a',
          lighter: '#1e293b',
        },
        text: {
          DEFAULT: '#e2e8f0',
          muted: '#94a3b8',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
