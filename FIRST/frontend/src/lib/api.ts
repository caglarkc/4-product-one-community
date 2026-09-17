export type User = {id:number;email:string;username:string;full_name:string;birth_date:string|null;gender:string;phone:string;email_verified:boolean;phone_verified:boolean;profile_complete:boolean;providers:string[];capabilities:{can_apply:boolean;can_create_listing:boolean}};
export class ApiError extends Error {
  constructor(message:string, public status:number, public errors:Record<string,string[]> = {}, public code?:string){super(message);}
}
async function read<T>(response:Response):Promise<T>{
  const body = await response.json().catch(()=>null);
  if(!response.ok) throw new ApiError(body?.detail || 'İşlem tamamlanamadı. Lütfen tekrar deneyin.',response.status,body?.errors,body?.code);
  if(!body) throw new ApiError('Sunucudan geçersiz yanıt alındı.',502);
  return body as T;
}
export async function api<T>(path:string, body?:unknown, method='POST'):Promise<T>{
  try {
    const options:RequestInit={credentials:'same-origin',cache:'no-store'};
    if(body!==undefined){
      const csrf=await read<{csrfToken:string}>(await fetch('/api/auth/csrf/',options));
      if(!csrf.csrfToken) throw new ApiError('Güvenlik doğrulaması alınamadı.',403);
      Object.assign(options,{method,headers:{'Content-Type':'application/json','X-CSRFToken':csrf.csrfToken},body:JSON.stringify(body)});
    }
    return await read<T>(await fetch(`/api/auth/${path}/`,options));
  } catch(error){
    if(error instanceof ApiError) throw error;
    throw new ApiError('Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin.',503);
  }
}
