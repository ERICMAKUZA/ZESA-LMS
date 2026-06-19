import type { Config } from 'tailwindcss'
import forms from '@tailwindcss/forms'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1B3A6B',
          light: '#2D5AA0',
          dark: '#0F2040',
        },
        accent: {
          DEFAULT: '#F5A623',
          light: '#F7B84B',
        },
        success: '#16A34A',
        warning: '#D97706',
        danger: '#DC2626',
      },
    },
  },
  plugins: [forms],
}

export default config
