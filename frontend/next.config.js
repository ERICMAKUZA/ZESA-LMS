/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_MOODLE_URL: process.env.NEXT_PUBLIC_MOODLE_URL,
  },
  images: {
    domains: ['localhost', 'learning.kenac.tech'],
  },
}

module.exports = nextConfig
