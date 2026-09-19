import {GitHubOnboarding} from '../../components/github-onboarding';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
  const query = await searchParams;
  return <GitHubOnboarding next={typeof query.next === 'string' ? query.next : undefined} failed={query.github === 'failed'} authorizationReturn={query.github === 'connected'} installationReturn={query.github_setup === '1'} manage={query.manage === '1'}/>;
}
