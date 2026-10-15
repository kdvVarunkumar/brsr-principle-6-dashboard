import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// `npm run build` writes web/dist, which `python flow.py serve` serves. The page imports its stylesheets from ../brsr_p6/rendering/templates/.
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: [".."] } },
});
