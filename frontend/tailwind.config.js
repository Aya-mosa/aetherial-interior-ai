/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)', 'serif'],
        body: ['var(--font-body)', 'sans-serif'],
      },
      colors: {
        obsidian: { DEFAULT: '#0A0A0B', 900: '#0A0A0B', 800: '#111113', 700: '#18181C', 600: '#1E1E24', 500: '#26262E' },
        gold: { DEFAULT: '#C9A84C', light: '#E8C96A', dark: '#9A7830', muted: '#8A6E3C' },
        marble: { DEFAULT: '#F5F0EA', dark: '#E8E0D5', deeper: '#D4C9BC' },
        sage: { DEFAULT: '#8BA888', dark: '#5E7A5B' },
        rust: { DEFAULT: '#B85C38', light: '#D4714A' },
      },
      backdropBlur: { xs: '2px', '4xl': '80px' },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in': 'fadeIn 0.4s ease forwards',
      },
      keyframes: {
        float: { '0%,100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-8px)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        slideUp: { from: { opacity: 0, transform: 'translateY(20px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)',
        'gold-glow': '0 0 30px rgba(201,168,76,0.3), 0 0 60px rgba(201,168,76,0.1)',
        'luxury': '0 20px 60px rgba(0,0,0,0.6), 0 2px 8px rgba(201,168,76,0.1)',
      },
    },
  },
  plugins: [],
}
