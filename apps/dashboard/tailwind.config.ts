import type { Config } from 'tailwindcss'

export default <Config>{
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      colors: {
        zs: {
          bg: {
            primary: '#050505',
            secondary: '#0f1117',
            surface: 'rgba(255, 255, 255, 0.035)',
            'surface-hover': 'rgba(255, 255, 255, 0.07)',
            overlay: 'rgba(5, 5, 5, 0.85)',
          },
          border: 'rgba(255, 255, 255, 0.06)',
          'border-hover': 'rgba(255, 255, 255, 0.12)',
          blue: {
            DEFAULT: '#2563eb',
            lt: '#3b82f6',
          },
          cyan: '#06b6d4',
          violet: '#8b5cf6',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          text: {
            primary: '#f8fafc',
            secondary: '#94a3b8',
            muted: '#64748b',
          }
        }
      },
      boxShadow: {
        'zs-glow-blue': '0 0 20px rgba(37, 99, 235, 0.45)',
        'zs-glow-cyan': '0 0 20px rgba(6, 182, 212, 0.40)',
        'zs-glow-violet': '0 0 20px rgba(139, 92, 246, 0.45)',
        'zs-glow-emerald': '0 0 20px rgba(16, 185, 129, 0.35)',
        'zs-glow-rose': '0 0 20px rgba(244, 63, 94, 0.40)',
        'zs-glass': '0 8px 32px 0 rgba(0, 0, 0, 0.40)',
        'zs-card': '0 4px 24px rgba(0, 0, 0, 0.30)',
      },
      transitionDuration: {
        'instant': '80ms',
        'fast': '150ms',
        'normal': '250ms',
        'slow': '400ms',
        'reveal': '600ms',
        'cinematic': '1200ms',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.22, 1, 0.36, 1)',
        'bounce': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'sharp': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backgroundImage: {
        'zs-gradient-blue': 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
        'zs-gradient-brand': 'linear-gradient(135deg, #2563eb 0%, #8b5cf6 100%)',
      }
    },
  },
  plugins: [],
}
