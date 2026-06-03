/** @type {import('next').NextConfig} */
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://54.180.83.249";

const nextConfig = {
  // /api/* 요청을 EC2 백엔드로 프록시 (브라우저는 같은 origin으로만 통신 → Mixed Content/CORS 회피)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_ORIGIN}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
