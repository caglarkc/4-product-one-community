# FIRST project loading — 20 September 2026

## Diagnosis

Live frontend bundle confirmed direct Hetzner API address, no Vercel API proxy. Vercel serves frontend. Timing and anonymized log aggregate in spec.md: public list server median31ms, external206ms/internal23ms snapshots; own list1.59s and detail2.34s provider-dependent samples. Containers healthy and low resource utilization. Samples do not establish exact latency in user's browser.

## Changes and source review

Removed GitHub enumeration from authenticated owner-filtered MineView. Existing response fields preserved with conservative repository privacy defaults. Detail/create/update live provider proof retained.

Dedicated fixed anonymous public feed transport bypasses auth request queue, does not read/write localStorage or session headers, and aborts on home effect cleanup. Existing authentication queue and identity fences preserved. Independent source review accepted without P0/P1/P2; manager verified final diff and consumer usage.

No test suite, lint/typecheck, local build or browser. Read-only HTTP timing, deployed-JS origin inspection and anonymized backend resource/log observations were performed for the explicit diagnosis request. No authenticated after-fix performance measurement; no claim of measured user-specific speed improvement. Detail still waits for GitHub proof.

## Delivery

Application `caf2b2dbeb866df63de609ed64e3e30f450f8ebe` pushed to origin/main, remote hash matched. Backend release `20260920T183404-caf2b2dbeb86` healthy. Django checks, PostgreSQL/Redis connectivity and all three container health checks passed; no pending migrations; health returned status ok. Vercel automatic deployment for caf2b2d reported success.
