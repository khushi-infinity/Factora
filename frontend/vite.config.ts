import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev proxy: the SPA calls `/api/*` on its own origin, Vite forwards it to FastAPI.
// This keeps the browser free of CORS concerns and means no env file is needed in dev.
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
  preview: { port: 4173 },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // three.js is inherently ~1 MB minified. The 3D panel is lazy-loaded (see App.tsx), so the
    // initial route stays small; raise the reporter threshold instead of pretending otherwise.
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Keep the heavy 3D and chart bundles out of the app chunk.
        // Rollup 5 (shipped with Vite 8) only accepts the function form of manualChunks.
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('three') || id.includes('@react-three')) return 'three-vendor'
          if (id.includes('recharts') || id.includes('d3-')) return 'charts'
          if (id.includes('react-dom') || id.includes('react/') || id.includes('scheduler')) {
            return 'react-vendor'
          }
          return undefined
        },
      },
    },
  },
})
