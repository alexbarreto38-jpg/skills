import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image.
  output: "standalone",
  transpilePackages: ["@videodna/api-client"],
  // Media is served through short-lived signed URLs; never proxy/cache it here.
  images: { unoptimized: true },
  poweredByHeader: false,
};

export default nextConfig;
