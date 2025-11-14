/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ghost: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        spooky: {
          purple: '#6b46c1',
          green: '#10b981',
          orange: '#f59e0b',
          red: '#ef4444',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      animation: {
        'ghost-float': 'ghostFloat 3s ease-in-out infinite',
        'spooky-glow': 'spookyGlow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        ghostFloat: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        spookyGlow: {
          '0%': { boxShadow: '0 0 5px rgba(107, 70, 193, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(107, 70, 193, 0.8)' },
        },
      },
    },
  },
  plugins: [],
}