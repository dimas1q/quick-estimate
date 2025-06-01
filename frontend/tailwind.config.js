/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    './node_modules/@headlessui/vue/**/*.{js,ts}',
    './node_modules/@heroicons/vue/**/*.{js,ts}',
  ],
  theme: {
    extend: {
      colors: {
        'qe-black': '#1A1D1F',
        'qe-black2': '#25282D'
      }
    },
  },
  plugins: [],
  darkMode: 'class', // Enable dark mode support
}