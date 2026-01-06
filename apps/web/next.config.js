/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: false,
  experimental: {
    webpackBuildWorker: false
  }
};

module.exports = nextConfig;
