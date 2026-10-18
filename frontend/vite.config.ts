import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // NUEVO (Jonathan, 2026-10-18): en desarrollo, las llamadas a /api van a Django (python manage.py runserver).
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
