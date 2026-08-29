/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        saffron: { DEFAULT: "#FF9933", light: "#FFF3E0", dark: "#E67E22" },
        indiaBlue: { DEFAULT: "#0B2239", light: "#123A5A" },
        ink: "#0F172A",
        stone: { 50: "#FAFAF9", 100: "#F5F5F4" }
      },
      fontFamily: {
        serif: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.06)",
        toggle: "0 2px 12px rgba(0,0,0,0.10)"
      }
    }
  },
  plugins: []
};
