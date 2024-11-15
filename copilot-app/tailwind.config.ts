import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: "#1f2937", // Dark blue
        secondary: "#f3f4f6", // Light gray
        accent: "#3b82f6", // Bright blue
      },
    },
  },
  plugins: [],
} satisfies Config;
