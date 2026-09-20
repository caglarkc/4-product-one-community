# Bug Issue selector acceptance

User revision: GitHub Issue applies only to bug listings. Feature retains current state and desired outcome without Issue setup. Private repositories cannot publish bug listings; stored repository privacy must drive options and backend enforcement. Select recent 50 open Issues from the selected repository rather than entering a number or retrieving the entire history.

## Planned checks

- Backend current-user/repository authorization and private exclusion on Issue lookup; cap50 with PR exclusion; no complete history traversal.
- Bug create requires a selected existing Issue or explicit new Issue. Feature has no Issue dependency in create, discovery, apply and retry paths.
- Public selection offers all four needs and three modes; feature shows descriptions without Issue; bug shows selector/create choice.
- Private selection offers teammate/contributor/feature and excludes bug and PR mode. Switching from public bug/PR clears incompatible selection and stale Issue data.
- Explicit Issue load handles loading/empty/error; selection is tied to current repo and late responses cannot replace newer state.
- Push accepted source, standard backend release, Vercel automatic deployment; browser verify authenticated public/private preparation and contribution choices without publishing private data or creating GitHub Issues.

Runtime outcomes are recorded in delivery.md only after observed. No need for new live GitHub mutations to validate these form changes.
