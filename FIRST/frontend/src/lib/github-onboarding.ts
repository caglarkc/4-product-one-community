export const githubNextPaths = ['/', '/hesap', '/projelerim/yeni'] as const;
export function githubNext(value: unknown): string {
  return typeof value === 'string' && (githubNextPaths as readonly string[]).includes(value) ? value : '/projelerim/yeni';
}
export function githubOnboarding(next: string): string {
  return `/github-kurulum?next=${encodeURIComponent(githubNext(next))}`;
}
export function navigateToGitHub(value: string, installation = false) {
  const target = new URL(value);
  const path = installation ? /^\/apps\/[a-zA-Z0-9-]+\/installations\/new$/.test(target.pathname) : target.pathname === '/login/oauth/authorize';
  if (target.origin !== 'https://github.com' || target.username || target.password || target.hash || !path) throw new Error('GitHub bağlantı adresi doğrulanamadı.');
  window.location.assign(target.href);
}
