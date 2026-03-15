import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: path.resolve('../backend/certs/key.pem'),
      cert: path.resolve('../backend/certs/cert.pem'),
    },
    port: 5173,
    host: '0.0.0.0',  // Allow connections from other devices on your network
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
})
