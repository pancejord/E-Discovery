import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17202A",
        panel: "#F7F9FB",
        line: "#D8DEE6",
        accent: "#1D6F6B",
        warning: "#B7791F",
      },
    },
  },
  plugins: [],
};

export default config;
