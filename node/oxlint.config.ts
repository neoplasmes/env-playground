import { defineConfig } from "oxlint";

export default defineConfig({
  plugins: ["typescript", "react", "nextjs", "jsx-a11y", "import", "vitest"],
  jsPlugins: ["@stylistic/eslint-plugin"],
  rules: {
    "@stylistic/padding-line-between-statements": [
      "error",
      {
        blankLine: "always",
        prev: "*",
        next: ["return", "throw", "break", "continue"],
      },
    ],
    "react/rules-of-hooks": "error",
  },
  ignorePatterns: ["**/node_modules/**", "**/.next/**", "**/dist/**", "**/next-env.d.ts"],
});
