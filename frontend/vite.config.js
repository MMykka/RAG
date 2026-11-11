import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Forward every /api/... call to FastAPI, so React never hardcodes a host
    // and the browser sees one origin (the httpOnly auth cookie just works).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
