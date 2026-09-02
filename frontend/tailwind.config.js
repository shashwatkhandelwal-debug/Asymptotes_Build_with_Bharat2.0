/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#0a0d14',
          card: '#111726',
          border: '#1e293b',
          accent: '#38bdf8',
          danger: '#f43f5e',
          warning: '#f59e0b',
          success: '#10b981',
          purple: '#a855f7'
        }
      },
      fontFamily: {
        mono: ['Fira Code', 'JetBrains Mono', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
