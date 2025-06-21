import { nextui } from "@nextui-org/theme";
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "schemes-lightgray": "#fafbfe",
        "schemes-gray": "#a1a1aa",
        "schemes-darkgray": "#718096",
        "schemes-blue": "#008AFF",
        "schemes-lightblue": "#D9E8FF",
        "schemes-darkblue": "#171347",
      },
    }
  },
  plugins: [nextui()],
};
export default config;
