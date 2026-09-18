import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ConnectedAccounts } from '../src/components/connected-accounts';
import type { ConnectedAccount } from '../src/lib/api';
vi.mock('../src/components/github-auth', () => ({GitHubButton: () => <button>GitHub hesabımı bağla</button>}));
const github: ConnectedAccount = {provider: 'github', display_name: 'GitHub Üyesi', username: 'github-member', email: '', avatar_url: 'https://avatars.githubusercontent.com/u/123', profile_url: 'https://github.com/github-member'};
const google: ConnectedAccount = {provider: 'google', display_name: 'Google Üyesi', username: '', email: 'google@example.test', avatar_url: '', profile_url: ''};
describe('connected account cards', () => {
  it('renders GitHub profile and compact Google identity without link or unlink actions', () => {
    render(<ConnectedAccounts user={{providers: ['github', 'google'], connected_accounts: [github, google]}}/>);
    expect(screen.getByText('@github-member')).toBeInTheDocument();
    expect(screen.getByText('google@example.test')).toBeInTheDocument();
    expect(screen.getAllByText('Bağlı')).toHaveLength(2);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    const link = screen.getByRole('link', {name: /GitHub profilini görüntüle/});
    expect(link).toHaveAttribute('href', github.profile_url);
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(link).toHaveAttribute('referrerpolicy', 'no-referrer');
  });
  it('shows every connected identity when one provider has multiple accounts', () => {
    render(<ConnectedAccounts user={{providers: ['google'], connected_accounts: [google, {...google, email: 'second@example.test'}]}}/>);
    expect(screen.getByText('google@example.test')).toBeInTheDocument();
    expect(screen.getByText('second@example.test')).toBeInTheDocument();
    expect(screen.getAllByRole('article', {name: 'Google'})).toHaveLength(2);
  });
  it('preserves connection status for legacy accounts without inventing identity data', () => {
    render(<ConnectedAccounts user={{providers: ['github', 'google']}}/>);
    expect(screen.getAllByText(/Profil bilgileri henüz mevcut değil/)).toHaveLength(2);
    expect(screen.getAllByText('Bağlı')).toHaveLength(2);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
  it('offers GitHub linking only, shows unlinked Google clearly', () => {
    render(<ConnectedAccounts user={{providers: [], connected_accounts: []}}/>);
    expect(screen.getAllByText('Bağlı değil')).toHaveLength(2);
    expect(screen.getByRole('button', {name: 'GitHub hesabımı bağla'})).toBeInTheDocument();
    expect(screen.getByText('Bu hesaba bağlı bir Google hesabı yok.')).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });
  it.each(['javascript:alert(1)', 'https://github.com.evil.test/user', 'https://user:pass@github.com/user', 'https://github.com/login/oauth/authorize', 'http://github.com/member', 'https://github.com:8443/member'])('rejects unsafe profile URL %s', (profile_url) => {
    render(<ConnectedAccounts user={{providers: ['github'], connected_accounts: [{...github, profile_url, avatar_url: 'https://untrusted.test/image'}]}}/>);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    const card = screen.getByRole('article', {name: 'GitHub'});
    expect(card.querySelector('img')).toBeNull();
    expect(within(card).getByText('GH')).toBeInTheDocument();
  });
  it('falls back when avatar loading fails and retains the profile link', () => {
    render(<ConnectedAccounts user={{providers: ['github'], connected_accounts: [github]}}/>);
    const card = screen.getByRole('article', {name: 'GitHub'});
    const img = card.querySelector('img')!;
    expect(img).toHaveAttribute('referrerpolicy', 'no-referrer');
    fireEvent.error(img);
    expect(card.querySelector('img')).toBeNull();
    expect(within(card).getByText('GH')).toBeInTheDocument();
    expect(within(card).getByRole('link')).toBeInTheDocument();
  });
});
