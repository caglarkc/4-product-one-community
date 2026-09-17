import { proxyAuth } from '../../../../lib/backend-proxy';
export const dynamic='force-dynamic';
async function handler(request:Request, context:{params:Promise<{path:string[]}>}){
  return proxyAuth(request,(await context.params).path);
}
export {handler as GET,handler as POST,handler as PATCH,handler as DELETE};
