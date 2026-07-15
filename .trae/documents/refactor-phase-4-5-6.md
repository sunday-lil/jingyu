# Refactor Phases 4-6: Templates, CSS Split, and Final Polish

## Context

The AI news system refactor is in progress. Phases 0-3 are complete:
- **Phase 0**: Fixed `logger_manager.logger_manager.error` typo, added `.env.example` with `python-dotenv` loading
- **Phase 1**: Split `database.py` (62 KB god module) into `database/` package with mixin classes
- **Phase 2**: Built `tests/` directory with `conftest.py` and 4 test files (71 tests passing)
- **Phase 3**: Created `routes/_helpers.py` (paginate, fetch_recommended, handle_image_upload, invalidate_news_caches, log_api_call) and `routes/_validators.py` (validate_credentials), refactored `routes/auth.py` and `routes/news.py`

**Current state of the 9 templates**: All repeat `<head>`, nav, footer, and flash-messages markup inline. None of them extend a base template. `index.html` and `new.html` each carry ~300 lines of inline `<script>`. `admin.html` is 1,090 lines with ~340 lines of inline `<style>` plus ~500 lines of inline `<script>`. `static/style.css` is a single 110 KB / 4,790-line file with no module split. There is no `static/js/` or `static/css/` subdirectory yet.

**Pending (Phases 4-6):**
- Phase 4 — Templates: create `_base.html` + partials, convert all 9 templates to extend it, extract inline JS to `static/js/pages/*.js`
- Phase 5 — CSS: split `static/style.css` into `static/css/*.css` modules
- Phase 6 — Crawler type hints + `sys.path.append` removal, update `docs/merged_document.md`, add `README.md`

The user already approved the overall direction in `.trae/documents/comprehensive-refactor.md` and explicitly chose "Aggressive — modernize liberally" plus "Add a small test suite as I go". Public URLs, template names, DB schema, and route names must remain compatible with the existing `news.db` and existing tests.

## Approach

Three phases, each ending at a green-pytest + smoke-tested checkpoint. CSS and templates use the existing class names so no template re-style is needed; we only restructure the source files.

### Phase 4 — Templates & JS extraction

Goal: eliminate the `<head>`/nav/footer/flash duplication across 9 templates and move the inline JS into per-page modules loaded with `<script defer>`. The rendered HTML structure and CSS class names are preserved exactly.

**New files:**

1. `templates/_base.html` — common structure:
   - `<!DOCTYPE html>` + `<head>` (charset, viewport, Inter font preconnect, `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`)
   - Background-decoration block
   - `<div class="container">` with `{% include "_nav.html" %}` then `{% block content %}{% endblock %}`
   - Footer
   - Blocks: `title`, `content`, `extra_css`, `extra_js`
   - Loads `static/js/app.js` with `defer` at the end of `<body>`
2. `templates/_nav.html` — extracted nav from `index.html` (the rich version with avatar, user-info, role badge, login/register buttons) and the simpler nav from `new.html` / `profile.html` / `search_results.html` — provided as two macros `render_full_nav()` and `render_simple_nav()`
3. `templates/_flash.html` — single {% with get_flashed_messages %} block, included from `_base.html`
4. `templates/_macros.html` — Jinja macros:
   - `render_flashes()` — wraps the flash-message block
   - `render_pagination(page, total_pages, base_url)` — replaces the 3 copies of the pagination block in `index.html`
   - `user_avatar(user, size="md")` — the avatar circle used in `index.html` and `profile.html`
5. `static/js/app.js` — small shared utilities:
   - `window.AIN = window.AIN || {}`
   - `AIN.csrfToken()` — reads meta tag (placeholder for future)
   - `AIN.fetchJSON(url, opts)` — `fetch` wrapper that throws on `!response.ok` and parses JSON
   - `AIN.confirmThen(message, fn)` — wraps the 6 `if (!confirm(...))` blocks in admin.js
6. `static/js/pages/index.js` — DOMContentLoaded handler for category dropdown, search focus, card hover, filter button, share, scroll animations, performance monitor. Loaded with `defer` from `index.html`.
7. `static/js/pages/news.js` — `likeNews`, `showCoinModal`, `closeCoinModal`, `selectCoinAmount`, `useCustomAmount`, `coinNews`, `window.onclick` modal close. Loaded from `new.html`.
8. `static/js/pages/profile.js` — `exchangeCoins` and the input validator. Loaded from `profile.html`.
9. `static/js/pages/admin.js` — all admin JS: `showTab`, `filterUsers`, `filterNews`, `startOnlineStatusUpdates`, `updateOnlineStatus`, `sendHeartbeat`, modal handlers, `editUserStats`, `updateUserStats`, `changeRole`, `deleteUser`, `deleteNews`, `clearCache`, `optimizeDB`, `editNews`, `clearPycFiles`, `createUser`, `getLogStats`, `viewLogs`, `clearLogs`, `downloadLogs`. Loaded from `admin.html`.

**Template conversions (each becomes ~30-50% of its current size):**

- `login.html` — `{% extends "_base.html" %}` + auth body class
- `register.html` — same pattern
- `index.html` — extends `_base.html`, removes inline `<script>` (replaced with `<script defer src="{{ url_for('static', filename='js/pages/index.js') }}"></script>` in `extra_js` block)
- `new.html` — extends `_base.html`, removes inline `<script>` (replaced with news.js)
- `search_results.html` — extends `_base.html`
- `profile.html` — extends `_base.html`, removes inline `<script>` (replaced with profile.js)
- `admin.html` — extends `_base.html`, replaces the inline `<style>` block with `<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/admin.css') }}">` in `extra_css` block; removes inline `<script>` (replaced with admin.js)
- `add_news.html` — extends `_base.html` (page has a custom user-info strip; preserved as a `{% block user_strip %}`)
- `edit_news.html` — extends `_base.html` (same user-strip handling)

**Behavior preservation rules:**
- All existing CSS classes/IDs are preserved so `style.css` and the new `css/pages/admin.css` work without changes
- All `url_for(...)` calls stay the same
- All `id="..."` attributes that the JS touches (categoryTab, categoryMenu, like-btn, coin-modal, etc.) are preserved
- The `<body class="auth-body">` and `<body class="admin-body">` (and absence-of-class for the index) behavior is preserved via a `body_class` variable in the base template

**Stop point:** all 9 pages render identically (visual diff via browser MCP), `pytest -q` still 71 green.

### Phase 5 — CSS split

Goal: turn `static/style.css` (110 KB, 4,790 lines) into a directory of focused modules. Visual output must be byte-for-byte equivalent.

**New file structure:**

- `static/css/00-variables.css` — the `:root { ... }` block (lines 3-76, untouched)
- `static/css/01-reset.css` — the `*` reset, html/body styles, `animate-gpu`, `will-change-*` helpers (lines 78-115ish)
- `static/css/02-layout.css` — `.container`, `.header`, `.background-decoration`, `.bg-circle`, `.bg-blur`, `.hero-section`, `.navigation-section`
- `static/css/03-components.css` — `.btn*`, `.card*`, `.alert*`, `.badge*`, `.modal*`, `.form-*`, `.pagination*`
- `static/css/04-pages.css` — index page, news detail, search results, profile
- `static/css/05-auth.css` — login + register + add_news + edit_news (`auth-body`, `auth-container`, `auth-form`)
- `static/css/06-admin.css` — admin panel styles (the ~340 lines of inline CSS from `admin.html`, moved here for consistency)
- `static/css/pages/admin.css` — admin-specific tweaks (replaces the inline `<style>` in admin.html; same content)
- `static/css/style.css` — the new entry-point manifest:

```css
@import url('00-variables.css');
@import url('01-reset.css');
@import url('02-layout.css');
@import url('03-components.css');
@import url('04-pages.css');
@import url('05-auth.css');
@import url('06-admin.css');
```

**Migration approach:**

1. Open the existing `static/style.css` and locate the section boundaries by hand (CSS comments already mark most sections: `/* ===== 基础重置 ===== */`, etc.).
2. Cut each section into its own file. The new modules are byte-identical copies of the original blocks — no reformatting.
3. Write the new `static/css/style.css` manifest.
4. Delete the old `static/style.css`.
5. Update `templates/_base.html` to link `{{ url_for('static', filename='css/style.css') }}` instead of the old path.
6. Update `templates/admin.html` to add `<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/admin.css') }}">` in the `extra_css` block.

**Risk mitigation:**
- Use the same selector order — CSS cascade is order-sensitive when specificity ties.
- The variables file is `@import`-ed first, so `var(--primary-color)` etc. resolve in all downstream files.
- `@import` is synchronous; the browser blocks first paint until all modules load. Mitigation: HTTP/2 multiplexing on a localhost dev server, plus a single cache-bust query string per file.
- Visual diff: capture screenshots of `/`, `/admin`, `/profile`, `/new?title=...`, `/login`, `/register` at 4 viewports (375 / 768 / 1280 / 1920) before and after; compare via the integrated browser MCP.

**Stop point:** identical visual output, smaller per-file sizes, all 71 tests pass, manual smoke test green.

### Phase 6 — Crawler polish + final docs

Goal: add type hints, remove the `sys.path` hack, refresh the merged doc, and add a top-level `README.md`.

**Changes:**

1. `crawler/base_crawler.py` — add module docstring + type hints to public methods
2. `crawler/database_handler.py` — same
3. `crawler/site_crawlers.py` — same
4. `crawler/main.py` — same; **remove the `sys.path.append(...)` hack** since `app.py` is the only entry point in the project (the crawler is imported by `main()` and run from project root)
5. `docs/merged_document.md` — refresh the directory tree, file list, and any outdated "lines-of-code" callouts to match the post-refactor layout
6. `README.md` (new) — quickstart:
   - `python -m venv venv && pip install -r requirements.txt`
   - `cp .env.example .env`, edit `SECRET_KEY`
   - `python app.py` → `http://127.0.0.1:5000`
   - `pip install -r requirements-dev.txt && pytest -q` for tests
   - Brief architecture overview, env-var table, project layout

**Stop point:** all tests green, `crawler/main.py` runs cleanly, README and docs are accurate.

## Critical files to modify

**Phase 4**
- new `templates/_base.html`, `templates/_macros.html`, `templates/_nav.html`, `templates/_flash.html`
- rewrite 9 templates in `templates/`
- new `static/js/app.js`, `static/js/pages/{index,news,profile,admin}.js`

**Phase 5**
- new `static/css/00-variables.css` through `06-admin.css`
- new `static/css/pages/admin.css`
- new `static/css/style.css` (manifest)
- delete old `static/style.css`
- update `templates/_base.html` and `templates/admin.html` link paths

**Phase 6**
- `crawler/main.py`, `crawler/base_crawler.py`, `crawler/database_handler.py`, `crawler/site_crawlers.py`
- `docs/merged_document.md`
- new `README.md`

## Existing utilities to reuse

- All routes, helpers, and validators from Phases 1-3 stay as-is. No backend changes.
- All CSS variables from the `:root` block in the current `style.css` are kept verbatim in `00-variables.css`. The downstream modules reference them by `var(--name)`, which is the same as today.
- The Jinja `url_for('static', filename='...')` helper is used in all new template `<link>` and `<script>` tags — no new utility functions needed.

## Verification

After each phase, run:

1. `python app.py` — server starts cleanly, no template errors, no static-file 404s. Manually browse `/`, `/login`, `/register`, `/profile`, `/add_news`, `/edit_news/1`, `/new?title=...`, `/admin`, `/search?query=test`.
2. `pytest -q` — all 71 tests still green.
3. Browser MCP smoke test at the end of Phase 5: capture `/`, `/admin`, `/profile` screenshots at 4 viewports and visually diff against pre-Phase-5 screenshots.
4. `git status` — no unexpected new files (we want a clean diff: templates reorganized, css split, js extracted, crawler typed, README added).
5. `python -c "from app import create_app; create_app('testing')"` — app boots in testing config without warnings.

## Risks & rollback

- **Template refactor risk:** breaking a route because the base template doesn't supply a context variable the child used to inline. Mitigation: every converted template preserves its original root-level variables (e.g. `current_user`, `current_view`, `page`, `total_pages`, `category_name`, `news`, `recommended_news`); the new `_base.html` only adds wrapping, not new required context.
- **JS extraction risk:** an event handler that referenced a variable now defined in a different file. Mitigation: keep all top-level function names identical (`likeNews`, `shareNews`, `editUserStats`, etc.) — they remain accessible from inline `onclick="..."` attributes because `defer`-loaded scripts still expose globals on `window`.
- **CSS split risk:** selector order changes break cascade. Mitigation: copy blocks in their original order from the existing `style.css`; visual diff at 4 viewports.
- **`@import` cost:** first paint is slightly delayed because the browser must resolve 7 CSS files. On a localhost dev server this is < 5 ms; on a production server with HTTP/2 multiplexing and `Cache-Control: max-age=31536000`, only the first visit pays the cost.
- **Crawler `sys.path` removal risk:** the crawler is run as `python -m crawler.main` from project root, so the hack is unnecessary. If the user's deployment runs it from another cwd, we document `cd $PROJECT_ROOT` instead.

We commit after each phase so the user can `git revert` to any checkpoint.
