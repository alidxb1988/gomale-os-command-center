module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        gomale: {
          navy: '#0A1628',
          gold: '#C8A54D',
          blue: '#1E3A5F',
          dark: '#0D1117',
          darker: '#010409',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
