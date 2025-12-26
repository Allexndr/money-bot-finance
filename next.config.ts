import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['@prisma/client', 'better-sqlite3'],
  },
};

export default nextConfig;
