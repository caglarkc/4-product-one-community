import { proxyAuth } from '../../../../../lib/backend-proxy';
export const dynamic = 'force-dynamic';
export async function GET(request: Request) {
  const response = await proxyAuth(request, ['google', 'callback']);
  let destination = '/giris?google_error=failed';
  try {
    const body = await response.json();
    if (response.ok) {
      const routes: Record<string, string> = {authenticated: '/', profile_required: '/kayit/google', reauthenticated: '/hesap'};
      destination = routes[body.status] || destination;
    } else if (new URL(request.url).searchParams.get('error') === 'access_denied') {
      destination = '/giris?google_error=cancelled';
    }
  } catch { /* Use a fixed, token-free failure destination. */ }
  const headers = new Headers({'Location': destination, 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'});
  for (const cookie of response.headers.getSetCookie()) headers.append('Set-Cookie', cookie);
  return new Response(null, {status: 303, headers});
}
