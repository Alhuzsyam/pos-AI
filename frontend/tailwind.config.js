/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        // Brand = Claude warm orange. Kebanyakan komponen pake shade 600/700 buat primary action.
        brand: {
          50:  '#fbf0ec',
          100: '#f8e2d8',
          200: '#f1c6b2',
          300: '#e6a185',
          400: '#d87e5a',
          500: '#c96442',
          600: '#b5573a',
          700: '#9b4831',
          800: '#7a3826',
          900: '#59281b',
        },
        // Claude paper/ink palette buat teks, border, surface.
        claude: {
          paper:   '#faf9f5',  // main page background
          surface: '#f3f0e8',  // secondary surface (cards hover, tables)
          ink:     '#1f1e1d',  // heading ink
          graphite:'#3d3929',  // label ink
          slate:   '#6b6558',  // body text muted
          dust:    '#a8a195',  // very muted
          line:    '#e5e1d8',  // default border
          hairline:'#efece3',  // soft separator
        },
        surface: '#faf9f5',  // alias for backward compat
      },
      fontFamily: {
        // 'serif' = display/heading; 'sans' = body/UI
        serif: ['"Tiempos Text"', '"Charter"', '"Iowan Old Style"', 'Georgia', 'Cambria', 'serif'],
        sans:  ['Inter', '"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        'claude-sm': '0 1px 2px 0 rgba(63, 56, 41, 0.04)',
        'claude':    '0 1px 3px 0 rgba(63, 56, 41, 0.06), 0 1px 2px -1px rgba(63, 56, 41, 0.04)',
        'claude-lg': '0 10px 25px -5px rgba(63, 56, 41, 0.08), 0 4px 10px -4px rgba(63, 56, 41, 0.05)',
      },
    },
  },
  plugins: [],
}
