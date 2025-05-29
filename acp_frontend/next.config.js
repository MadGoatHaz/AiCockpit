/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:8000/:path*' // Proxy to Backend
  //     }
  //   ]
  // }
  async rewrites() {
    return [
      {
        source: '/api/workspaces/:path*',
        destination: 'http://localhost:8000/workspaces/:path*', // Proxy /api/workspaces requests to FastAPI backend
      },
      {
        source: '/api/llm/:path*',
        destination: 'http://localhost:8000/llm/:path*', // Proxy /api/llm requests to FastAPI backend
      },
      {
        source: '/api/sessions/:path*',
        destination: 'http://localhost:8000/sessions/:path*', // Proxy /api/sessions requests to FastAPI backend
      },
      // Potentially other rewrites for different backend modules if needed
      // Example: Proxy all /api calls if the backend handles all of them
      // {
      //   source: '/api/:path*',
      //   destination: 'http://localhost:8000/:path*', 
      // },
    ];
  },
};

module.exports = nextConfig; 