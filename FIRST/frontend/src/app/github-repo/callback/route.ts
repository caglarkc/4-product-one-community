import {proxyAuth} from '../../../lib/backend-proxy';
import {githubNext} from '../../../lib/github-onboarding';
export const dynamic = 'force-dynamic';
export async function GET(request:Request){
 const response=await proxyAuth(request,['projects','github','callback']);
 let destination='/github-kurulum?github=failed';
 try {const body=await response.json();if(response.ok&&body.status==='connected')destination=`/github-kurulum?github=connected&next=${encodeURIComponent(githubNext(body.return_to))}`;}catch{/* Fixed failure destination. */}
 const headers=new Headers({'Location':destination,'Cache-Control':'no-store','Referrer-Policy':'no-referrer'});
 for(const cookie of response.headers.getSetCookie())headers.append('Set-Cookie',cookie);
 return new Response(null,{status:303,headers});
}
