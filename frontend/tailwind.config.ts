import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    './src/app/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#F17349',
          dark: '#D25A32'
        }
      }
    }
  },
  plugins: []
};

export default config;
