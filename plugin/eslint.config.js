// Analyse statique du plugin (ESLint, configuration « flat »).
const js = require('@eslint/js');
const globals = require('globals');

module.exports = [
  { ignores: ['com.foufou-exe.profil-ia.sdPlugin/**', 'node_modules/**'] },
  js.configs.recommended,
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: { ...globals.node },
    },
    rules: {
      'no-unused-vars': ['error', { args: 'after-used', caughtErrors: 'none' }],
      eqeqeq: ['error', 'smart'],
      'no-var': 'error',
      'prefer-const': 'error',
    },
  },
];
