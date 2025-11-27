import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // AuthorFlow Studios - Midnight Indigo Glow theme
        'af-midnight': '#0a0a1a',
        'af-ink': '#12122a',
        'af-purple': '#7c3aed',
        'af-purple-soft': '#a78bfa',
        'af-purple-glow': '#8b5cf6',
        'af-lavender': '#c4b5fd',
        'af-card': 'rgba(255, 255, 255, 0.05)',
        'af-card-border': 'rgba(255, 255, 255, 0.1)',
        'af-pink': '#ec4899',
        'af-pink-soft': '#f472b6',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'af-gradient': 'linear-gradient(135deg, #0a0a1a 0%, #1e1b4b 50%, #0a0a1a 100%)',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glow-lg': '0 0 40px rgba(139, 92, 246, 0.4)',
        'glow-pink': '0 0 20px rgba(236, 72, 153, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
    },
  },
  plugins: [],
}

export default config
