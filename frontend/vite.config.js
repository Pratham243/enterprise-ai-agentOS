import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/health': 'http://localhost:8000',
      '/agent': 'http://localhost:8000',
      '/workflow': 'http://localhost:8000',
      '/rag': 'http://localhost:8000',
      '/approvals': 'http://localhost:8000',
      '/risk': 'http://localhost:8000',
      '/evaluation': 'http://localhost:8000',
      '/mcp': 'http://localhost:8000',
      '/multi-agent': 'http://localhost:8000',
      '/webhooks': 'http://localhost:8000',
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
})
