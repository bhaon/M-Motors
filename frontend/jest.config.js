const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  testEnvironment: "jest-environment-jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
  modulePathIgnorePatterns: ["<rootDir>/.next/standalone/"],
  collectCoverageFrom: [
    "src/components/**/*.{ts,tsx}",
    "src/hooks/**/*.ts",
    "src/lib/**/*.ts",
    "src/data/**/*.ts",
    "!src/**/*.test.{ts,tsx,js,jsx}",
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
