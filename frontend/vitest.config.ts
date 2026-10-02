import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // Pure-logic tests only for now; no DOM needed. UI tests with jsdom arrive with the product pages.
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
