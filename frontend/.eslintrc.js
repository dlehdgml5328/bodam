module.exports = {
  root: true,
  parserOptions: {
    project: './tsconfig.json'
  },
  extends: [
    'next/core-web-vitals',
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier'
  ],
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/explicit-module-boundary-types': 'off'
  }
};
