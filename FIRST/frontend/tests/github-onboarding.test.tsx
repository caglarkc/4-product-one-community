import {StrictMode} from 'react';
import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import {beforeEach, expect, it, vi} from 'vitest';
import {api} from '../src/lib/api';
import {navigateToGitHub} from '../src/lib/github-onboarding';
import {GitHubOnboarding} from '../src/components/github-onboarding';
const router = vi.hoisted(() => ({replace: vi.fn(), refresh: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => router}));
vi.mock('../src/lib/api', () => ({api: vi.fn()}));
vi.mock('../src/lib/github-onboarding', async original => ({...await original<typeof import('../src/lib/github-onboarding')>(), navigateToGitHub: vi.fn()}));
const user = {providers: ['github'], email_verified: false};
const status = {enabled: true, connected: false, installation_url: 'https://github.com/apps/first-community-repositories/installations/new'};
beforeEach(() => {vi.clearAllMocks();sessionStorage.clear();});
function setup(connected = false, repositories: unknown[] = []) {
 vi.mocked(api).mockImplementation(async path => path === 'me' ? {user} : path === 'projects/github/status' ? {...status, connected} : path === 'projects/github/repositories' ? {repositories} : {authorization_url: 'https://github.com/login/oauth/authorize?client_id=test'});
}
it('starts App grant once in StrictMode even before email verification', async () => {
 setup();render(<StrictMode><GitHubOnboarding next="/hesap"/></StrictMode>);
 await waitFor(() => expect(navigateToGitHub).toHaveBeenCalledTimes(1));
 expect(vi.mocked(api).mock.calls.filter(([path]) => path === 'projects/github/start')).toEqual([['projects/github/start', {return_to: '/hesap'}]]);
});
it('skips consent for already authorized repos', async () => {
 setup(true, [{id: 1}]);render(<GitHubOnboarding next="/"/>);
 await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/'));expect(navigateToGitHub).not.toHaveBeenCalled();
});
it('sends missing installation to repo selection preserving destination', async () => {
 setup(true);render(<GitHubOnboarding next="/hesap"/>);
 await waitFor(() => expect(navigateToGitHub).toHaveBeenCalledWith(status.installation_url, true));expect(sessionStorage.getItem('first.github.setup.next')).toBe('/hesap');
});
it('stops after installation return with no repos including retry', async () => {
 setup(true);render(<GitHubOnboarding installationReturn/>);
 expect(await screen.findByText(/Henüz erişilebilir repo/)).toBeInTheDocument();expect(navigateToGitHub).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button', {name: 'Repo listesini yeniden kontrol et'}));expect(await screen.findByText(/Henüz erişilebilir repo/)).toBeInTheDocument();expect(navigateToGitHub).not.toHaveBeenCalled();
});
it('preserves safe destination across installation return', async () => {
 setup(true, [{id: 1}]);sessionStorage.setItem('first.github.setup.next', '/hesap');render(<GitHubOnboarding installationReturn/>);
 await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/hesap'));expect(sessionStorage.getItem('first.github.setup.next')).toBeNull();
});
it('requires explicit retry after cancelled authorization', async () => {
 setup();render(<GitHubOnboarding failed/>);
 const retry = await screen.findByRole('button', {name: 'İzinleri tamamlamayı yeniden dene'});expect(navigateToGitHub).not.toHaveBeenCalled();fireEvent.click(retry);
 await waitFor(() => expect(navigateToGitHub).toHaveBeenCalledTimes(1));
});
it.each([null, {providers: ['google']}])('requires linked identity', async user => {
 vi.mocked(api).mockResolvedValue({user});render(<GitHubOnboarding/>);expect(await screen.findByRole('link', {name: user ? 'Hesabıma git' : 'Giriş yap'})).toBeInTheDocument();expect(api).toHaveBeenCalledTimes(1);expect(navigateToGitHub).not.toHaveBeenCalled();
});
it('bounds external next to fixed local paths', async () => {
 setup(true, [{id: 1}]);render(<GitHubOnboarding next="https://evil.example/"/>);await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/projelerim/yeni'));
});
it('manage opens installation even with existing repos', async () => {
 setup(true, [{id: 1}]);render(<GitHubOnboarding next="/projelerim/yeni" manage/>);await waitFor(() => expect(navigateToGitHub).toHaveBeenCalledWith(status.installation_url, true));expect(router.replace).not.toHaveBeenCalled();
});
it('does not navigate after unmount during pending start', async () => {
 setup();let resolve!: (value: unknown) => void;const normal = vi.mocked(api).getMockImplementation()!;
 vi.mocked(api).mockImplementation(path => path === 'projects/github/start' ? new Promise(done => {resolve = done;}) : normal(path));
 const view = render(<GitHubOnboarding/>);await waitFor(() => expect(resolve).toBeDefined());view.unmount();resolve({authorization_url: 'https://github.com/login/oauth/authorize'});await new Promise(done => setTimeout(done, 0));expect(navigateToGitHub).not.toHaveBeenCalled();
});
it('storage denial cannot block an authorized login', async () => {
 setup(true, [{id: 1}]);vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {throw new Error('denied');});vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {throw new Error('denied');});
 render(<GitHubOnboarding installationReturn/>);await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/projelerim/yeni'));vi.restoreAllMocks();
});
it.each([{authorizationReturn: true}, {installationReturn: true}])('stops reauthorization loop after provider return %j', async props => {
 setup();render(<GitHubOnboarding {...props}/>);expect(await screen.findByRole('button', {name: 'İzinleri tamamlamayı yeniden dene'})).toBeInTheDocument();expect(navigateToGitHub).not.toHaveBeenCalled();
});
it('retains manage intent through OAuth then clears it before installation', async () => {
 setup(true, [{id: 1}]);sessionStorage.setItem('first.github.setup.manage', '1');render(<GitHubOnboarding authorizationReturn/>);
 await waitFor(() => expect(navigateToGitHub).toHaveBeenCalledWith(status.installation_url, true));expect(sessionStorage.getItem('first.github.setup.manage')).toBeNull();
});
it('fresh login ignores abandoned manage intent', async () => {
 setup(true, [{id: 1}]);sessionStorage.setItem('first.github.setup.manage', '1');render(<GitHubOnboarding next="/"/>);await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/'));expect(navigateToGitHub).not.toHaveBeenCalled();
});
