import type { NextConfig } from 'next';
const config: NextConfig = { poweredByHeader: false, skipTrailingSlashRedirect: true, async headers() {return [{source:"/:path*", headers:[{key:"Referrer-Policy",value:"no-referrer"}]}];} };
export default config;
