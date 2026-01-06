import { defineConfig } from "vite";
import { resolve } from "path";
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': resolve(__dirname, './src'),
    },
  },
  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
  // Configure multi-page app
  build: {
    outDir: 'dist',
    // Use relative paths for assets so they work regardless of where HTML is served from
    base: './',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/index.html'),
        home: resolve(__dirname, 'src/home.html'),
        settings: resolve(__dirname, 'src/settings.html'),
        status: resolve(__dirname, 'src/status.html'),
      },
    },
  },
}));
