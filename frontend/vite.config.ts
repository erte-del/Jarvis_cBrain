import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Built files go in dist/static/, so they can't clash with the backend's /assets/ (images).
    assetsDir: 'static',
    // The 3D viewer (three.js) is ~640 kB. It's loaded separately, only when a 3D
    // model opens, and it's served from this machine, so the size is fine.
    chunkSizeWarningLimit: 800,
  },
  server: {
    host: '127.0.0.1', // this machine only
    port: 5173,
  },
})
