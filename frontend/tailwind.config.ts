import type { Config } from 'tailwindcss';
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        mmx: {
          bg: '#07080d', surface: '#0d1018', elevated: '#141823',
          border: '#1e2330', accent: '#00e5a0', 'accent-2': '#00b8ff',
          'accent-3': '#7c5cff', danger: '#ff4d6d', warn: '#ffb84d',
          text: '#e8ecf4', muted: '#7a8194', dim: '#4a5060',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn .4s ease-out',
        'slide-up': 'slideUp .5s cubic-bezier(.16,1,.3,1)',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        glowPulse: { '0%,100%': { boxShadow: '0 0 20px rgba(0,229,160,.15)' }, '50%': { boxShadow: '0 0 40px rgba(0,229,160,.35)' } },
      },
    },
  },
  plugins: [],
};
export default config;