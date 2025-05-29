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
      {
        source: '/api/agents/:path*',
        destination: 'http://localhost:8000/agents/:path*', // Added rule for /api/agents
      },
      // You also have /api/terminals defined in main.py, so let's add that too for completeness
      {
        source: '/api/terminals/:path*',
        destination: 'http://localhost:8000/terminals/:path*', 
      },
      // And /api/system from main.py
      {
        source: '/api/system/:path*',
        destination: 'http://localhost:8000/system/:path*', 
      },
      // The commented out generic /api/:path* to http://localhost:8000/:path* 
      // is problematic because your FastAPI backend prefixes its routes with /api, 
      // e.g. /api/agents, not just /agents. 
      // So the destination should be http://localhost:8000/api/:path* if using a generic source: '/api/:path*'
      // For now, specific routes are safer.
    ];
  },
};

module.exports = nextConfig; 