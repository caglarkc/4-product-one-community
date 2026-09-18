import { VerifySocialEmail } from './social-email';
export function VerifyGoogleEmail({token}: {token: string}) {return <VerifySocialEmail provider="google" token={token}/>;}
