/**
 * ESLint Configuration for Modern JavaScript
 * This suggests modern JavaScript patterns but allows flexibility for experiments
 * - Warnings encourage modern syntax without blocking development
 * - Errors only for actual bugs (undefined variables, etc.)
 */

module.exports = {
  env: {
    browser: true,
    es2020: true,
    node: true
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module'
  },
  rules: {
    // Suggest modern variable declarations but allow var for quick experiments
    'no-var': 'warn',           // Changed from 'error' to 'warn'
    'prefer-const': 'warn',     // Changed from 'error' to 'warn'
    
    // Suggest modern string handling
    'prefer-template': 'warn',  // Changed from 'error' to 'warn'
    'template-curly-spacing': ['warn', 'never'],
    
    // Suggest arrow functions but allow traditional functions
    'prefer-arrow-callback': 'warn',  // Changed from 'error' to 'warn'
    'arrow-spacing': 'warn',
    
    // Suggest modern array methods
    'prefer-spread': 'warn',          // Changed from 'error' to 'warn'
    'prefer-rest-params': 'warn',
    
    // Suggest destructuring but don't enforce
    'prefer-destructuring': ['warn', {  // Changed from 'error' to 'warn'
      'array': false,   // More lenient for arrays
      'object': true
    }],
    
    // Suggest modern object patterns
    'object-shorthand': 'warn',       // Changed from 'error' to 'warn'
    'quote-props': ['warn', 'as-needed'],
    
    // General code quality - keep these as errors for actual problems
    'no-unused-vars': 'warn',         // Changed to warn for development
    'no-console': 'off',              // Allow console for development
    'no-undef': 'error',              // Keep this as error - undefined variables are usually bugs
    'no-redeclare': 'warn',           // Warn about redeclarations but allow them
    'prefer-promise-reject-errors': 'warn'
  }
};