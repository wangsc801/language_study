import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss(), reactRouter()],
  resolve: {
    tsconfigPaths: true,
  },
  server: {
    port: 5070,
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL || "http://127.0.0.1:8070",
        changeOrigin: true,
      },
    },
  },
});