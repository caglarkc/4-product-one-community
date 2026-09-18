'use client';
import { useId, useState } from 'react';
import type { ConnectedAccount, User } from '../lib/api';
import { GitHubButton } from './github-auth';
import { ActionLink, Surface } from './ui';

function providerUrl(value: string | undefined, kind: 'profile' | 'avatar') {
  if (!value) return '';
  try {
    const url = new URL(value);
    const host = kind === 'profile' ? 'github.com' : 'avatars.githubusercontent.com';
    if (url.protocol !== 'https:' || url.hostname !== host || url.port || url.username || url.password) return '';
    if (kind === 'profile' && !/^\/[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,38})\/?$/.test(url.pathname)) return '';
    return url.href;
  } catch { return ''; }
}

function ConnectionStatus({connected}: {connected: boolean}) {
  return <span className={`connection-status${connected ? ' connection-status--connected' : ''}`}>{connected ? 'Bağlı' : 'Bağlı değil'}</span>;
}

function ProviderCard({provider, connected, account}: {provider: ConnectedAccount['provider']; connected: boolean; account?: ConnectedAccount}) {
  const headingId = useId();
  const [failedAvatar, setFailedAvatar] = useState('');
  const github = provider === 'github';
  const title = github ? 'GitHub' : 'Google';
  const avatar = github ? providerUrl(account?.avatar_url, 'avatar') : '';
  const profile = github ? providerUrl(account?.profile_url, 'profile') : '';
  const hasIdentity = !!(account?.display_name || account?.username || account?.email);
  return <article className="provider-card" aria-labelledby={headingId}>
    <div className="provider-card-heading"><h3 id={headingId}>{title}</h3><ConnectionStatus connected={connected}/></div>
    {connected ? <>
      <div className="provider-identity">
        {github && <div className="provider-avatar" aria-hidden="true">{avatar && failedAvatar !== avatar ?
          // Provider images use an allowlisted host without a Next image proxy or referrer.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatar} alt="" width={64} height={64} referrerPolicy="no-referrer" onError={() => setFailedAvatar(avatar)}/> : <span>GH</span>}</div>}
        <div className="provider-details">
          {account?.display_name && <p className="provider-name">{account.display_name}</p>}
          {github && account?.username && <p className="provider-handle">@{account.username}</p>}
          {account?.email && <p className="provider-email">{account.email}</p>}
          {!hasIdentity && <p>{title} hesabınız bağlı. Profil bilgileri henüz mevcut değil.</p>}
        </div>
      </div>
      {github && profile && <ActionLink variant="quiet" href={profile} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">GitHub profilini görüntüle <span className="provider-link-hint">(yeni sekme)</span></ActionLink>}
    </> : <><p className="provider-description">{github ? 'GitHub profilinizi FIRST hesabınıza bağlayın.' : 'Bu hesaba bağlı bir Google hesabı yok.'}</p>{github && <GitHubButton purpose="link"/>}</>}
  </article>;
}

export function ConnectedAccounts({user}: {user: Pick<User, 'providers' | 'connected_accounts'>}) {
  return <Surface className="account-section connected-accounts"><h2>Bağlı hesaplar</h2><p>Giriş yaptığınız hesaplar ve GitHub profiliniz.</p>
    <div className="provider-list">{(['github', 'google'] as const).map(provider => {
      const accounts = user.connected_accounts?.filter(item => item.provider === provider) ?? [];
      return accounts.length ? accounts.map((account, index) => <ProviderCard key={`${provider}-${index}`} provider={provider} connected account={account}/>) :
        <ProviderCard key={provider} provider={provider} connected={!!user.providers?.includes(provider)}/>;
    })}</div>
  </Surface>;
}
