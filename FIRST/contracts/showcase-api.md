# Private file showcase API

Approved 25 September 2026; implementation tracked in `first-release-completion`.
Base `/api/auth/showcase/projects/<project_id>/`. These are published snapshots, not live repo browsing for visitors.

- GET `files/`: visible published file metadata, following project visibility at every request.
- GET `browse/?path=...`: owner only, fresh GitHub App identity/repo admin authorization; bounded direct directory listing with file name/path/type/size; never follows symlinks, submodules or LFS pointers. Private repository only.
- POST `prepare/`: `{path}`; fresh owner/repo authorization, resolve branch HEAD to commit SHA then fetch regular blob by pinned commit; returns `{preview}` with opaque preview ID, filename/kind/size/source_commit/created_at and sanitized preview content. This does not publish.
- DELETE `prepare/<preview_id>/`: owner cancels own unpublished preview; idempotent `{removed:true}` response, no GitHub access required.
- POST `publish/`: `{preview_id,replace_id?,confirmed:true}`; explicit confirmation publishes exactly prepared bytes (or replaces an existing file). Revalidate owner and current repo rights before publishing. Preview expires after 30 minutes and is bound to actor, project and GitHub identity. Prepared/actual bytes bounded.
- DELETE `files/<file_id>/`: owner removes publication. Does not modify GitHub.
- GET `files/<file_id>/preview/`: checks current listing visibility then returns sanitized text/CSV or safe raster/page images; source bytes never a public storage URL.

3 published files max/project. Text/code/Markdown/CSV 1 MiB max/file, images/PDF 10 MiB max/file, total original published bytes 20 MiB/project. Unknown binary, HTML execution, archives, executables, SVG and external references not supported in first version. Markdown rendered as escaped/limited safe content; no raw HTML or remote/private dependent asset fetching. CSV preview limited rows/columns. Code is never executed. Raster images decoded/re-encoded with bounded pixels; PDF rendered to bounded raster pages in isolated bounded converter, no active original PDF served inline. Oversized page/pixel/row limits explicitly shown, no silent full-content claims. No original download button. Preview data still copyable.

Private original/prepared bytes kept outside public static/media access with database ownership metadata. Prefer database binary snapshots for these small bounded files to reuse existing private PostgreSQL backup/restore; no extra public object storage integration. Publisher content can include secrets: block obvious credential filenames, show exact publication preview and explicit disclosure confirmation; do not promise complete secret detection. Protected responses no-store/nosniff. UI fetches authenticated JSON previews; no token-bearing URLs/iframes. Removal and visibility changes invalidate subsequent reads.

Preview content: `{kind,text?,rows?:string[][],images?:[{data_url,width,height}],truncated,total_pages?}`. File metadata `{id,filename,kind,size,source_commit,created_at}`. Prepare returns `{preview:{...metadata,expires_at,content}}`, published preview `{file:{...metadata,content}}`. Image/PDF previews are bounded raster JSON, not authenticated iframe URLs.

Implementation limits: preparation GitHub fetch uses a shared 12-second deadline, isolated raster conversion 12 seconds. CSV uses at most 200 rows, 30 columns and 2,000 characters/cell; PDF at most first 6 pages; images at most 8 megapixels. Animated images publish only first frame, with a truncation notice. Markdown is escaped plain text in v1. System-font substitution is blocked by the converter filesystem sandbox; some PDFs can differ in typography or fail, and the user reviews the exact raster before approval. Runtime converter compatibility and container memory headroom have not been independently exercised.
