import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep Turbopack rooted to this app so CSS/PostCSS deps resolve from web/node_modules.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
