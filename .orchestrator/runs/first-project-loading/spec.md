# FIRST loading latency diagnosis and fix

User reports long project loading and asks whether API is still routed through Vercel. Read-only live diagnosis is authorized by this request; no test suite or browser was requested.

## Observations

Production frontend JS includes direct https://167.235.158.118 API origin. Local frontend env values match; Next config has no proxy/rewrite route. Vercel hosts frontend only. One external measurement: feed 206ms, anonymous me 172ms, backend health162ms, Vercel home221ms. Internal feed23ms. All three FIRST containers healthy, backend CPU0.02%, RAM126.6MiB/512MiB; no error markers in latest bounded logs. These snapshots do not measure the user's authenticated browser or establish its precise wait duration.

Source shows all frontend API calls share one serialized queue. A slow provider-backed request from an old route can block public home feed; network timeout starts only when queued fetch starts. Mine endpoint unnecessarily enumerates GitHub repositories although current own cards/editor consume stored project fields only.

## Fix scope

- Dedicated explicitly anonymous public project GET outside auth queue, no Authorization or localStorage/session response handling. Abort obsolete home feed request on cleanup. Existing auth mutation/OAuth queue and session identity fences unchanged.
- Mine remains authenticated and owner-filtered, returns existing project_data schema with conservative missing-repo proof values. No GitHub enumeration; stored owner README remains available. Detail/create/update continue live provider proof.
- No schema change, credentials, new cache or security relaxation.
- Independent review and manager source verification, normal commit/push/backend deploy and Vercel status. No tests/lint/typecheck/local build/browser.

Additional bounded six-hour log aggregate before fix: successful /projects/ GET n=6 median31ms max42.5ms; /me/ n=6 median39.5ms max126.6ms; /projects/mine/ n=1 1585.5ms; project detail n=1 2343.4ms. No account/project IDs or raw logs stored. Small sample, server processing time only. Detail remains provider-dependent by design; no claim that all project requests are now provider-independent.
