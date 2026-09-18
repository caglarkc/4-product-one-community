# Independent review notes

Review performed by google_review separately from backend/frontend writers. Root also
inspected integration and deployment boundaries. These are intermediate findings, not
an assertion that final acceptance occurred.

- P1: authoritative recovery of an unverified account invalidated password/sessions but
  retained an earlier untrusted social identity. Backend removes pre-existing identities
  under the same user transaction before recording the proved identity; regression added.
- P1: identity loaded before waiting for user lock could authorize after recovery removed
  it. Backend must recheck identity under the user lock for login and reauth.
- Root: preventing activation of untrusted-address social signup until FIRST mailbox proof
  avoids retaining attacker identity through ordinary email verify/password reset paths.
  Existing pending-email proof endpoints support this gate; frontend explains it.
- Root: default gunicorn access logging included callback queries. Use path-only request
  logging. Actual FIRST nginx location already has access_log off (read-only confirmed).
- Social reauthentication max_age=0 requires validating fresh signed auth_time, not just
  requesting it. Signed-token regressions cover this condition.
- Provider email fallback must bind exact pending signup, subject, browser session, email,
  existing user id/security version and one-time token. Google authoritative email and
  subsequent stable subject lookup are separate trust conditions.

Google Console observed read-only: External, Testing; intended test user configured;
Branding incomplete prevents Publish app. No Google Console configuration was changed.
