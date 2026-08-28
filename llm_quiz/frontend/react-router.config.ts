import type { Config } from "@react-router/dev/config";

export default {
  // Config options...
  // SPA mode: emit a static index.html so the FastAPI backend can serve the
  // frontend directly (no node server needed). Change to `true` for SSR.
  ssr: false,
} satisfies Config;
