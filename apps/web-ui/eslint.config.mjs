import next from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  {
    ignores: [".next/**", "node_modules/**", "out/**", "next-env.d.ts"],
  },
  ...next,
  {
    rules: {
      // Mount-time localStorage hydration and the connectivity probe are
      // intentional client-only effects; this app does not use the React
      // Compiler, so these synchronous setState-in-effect calls are expected.
      "react-hooks/set-state-in-effect": "off",
    },
  },
];

export default eslintConfig;
