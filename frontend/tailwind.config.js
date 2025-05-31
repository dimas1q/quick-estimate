/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    './node_modules/@headlessui/vue/**/*.{js,ts}',
    './node_modules/@heroicons/vue/**/*.{js,ts}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  darkMode: 'class', // Enable dark mode support
}