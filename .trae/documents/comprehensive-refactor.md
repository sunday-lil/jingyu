# Comprehensive Refactor: AI News System (Flask)

## Context

The AI news system is a working Flask 2.3 app (~30 source files, ~13 KLOC of Python, ~4.8 KLOC of CSS, 9 Jinja templates). It's functionally complete but has accumulated debt:

- **`database.py` (62 KB, 1 file)** — uses raw `sqlite3` despite `SQLAlchemy` being in `requirements.txt`; every method opens/closes its own connection (unsafe under Flask's threaded serving); four near-identical SQL branches in `update_news`; defensive `len(result) > N` indexing in user lookups; ~9 methods that all hand-roll the same comment-load + date-parse loop.
- **Pre-existing bug (latent crash)** — `routes/news.py` calls `logger_manager.logger_manager.error(...)` in 9 places. `logger_manager` is an instance; the second `.logger_manager` raises `AttributeError` if any error path fires. Must be fixed.
- **`routes/news.py` (44 KB, 30+ handlers)** — every page handler repeats: cache lookup → load → paginate → fetch recommendations → render. No shared pagination helper. No shared image-upload helper. No shared try/log/flash pattern.
- **No tests** — `tests/` directory doesn't exist.
- **No base template** — `login.html`, `register.html`, `index.html`, `new.html`, `profile.html`, `admin.html` each repeat `<head>`, flash messages, nav, and footer markup. `admin.html` is 1,090 lines including inline CSS and inline JS.
- **`static/style.css` (110 KB, 4,790 lines)** — single file with no module split, but well-organized CSS variables at the top.
- **No type hints** anywhere except `CrawlerConfig` and `crawler/main.py`.
- **Hardcoded `SECRET_KEY` default** — `'your-secret-key-change-in-production'`.
- **Inconsistent imports** — `from database import db_manager` at top in some files, inside functions in others.

The user wants a **full pass** (backend, templates, static, tests, config) with **aggressive modernization** and **tests added as I go**. Behavior is allowed to drift in internals but all public URLs, endpoints, template names, and DB schemas must remain compatible with the existing `news.db`.

## Approach

Six phases. Each phase ends at a stable, runnable, test-passing checkpoint. We can stop after any phase.

### Phase 0 — Bug fix + safety (no API change)

1. Fix the `logger_manager.logger_manager.error(...)` typo in `routes/news.py` (9 occurrences) → `logger_manager.error(...)`.
2. Add `.env.example` and switch `config.py` to read from `python-dotenv` (already in `requirements.txt`) with a startup-time warning when `SECRET_KEY` is the default in non-development mode.
3. Update `.gitignore` to allow committing `.env.example`.

**Stop point:** `python app.py` still runs, the existing `news.db` still loads, all routes still respond.

### Phase 1 — Database layer cleanup

Goal: turn `database.py` from a 1,257-line god module into a thin package of focused modules **without changing the public surface** (the `db_manager` singleton still exists with the same methods, signatures, and return shapes).

1. Create `database/` package with:
   - `database/__init__.py` — exports `db_manager` and `DatabaseManager` (the public names other modules import).
   - `database/connection.py` — `Connection` context manager wrapping `sqlite3.connect(check_same_thread=False)`, with a per-request `g._db_conn` cache and `teardown_appcontext` close hook. Fixes the threading concern.
   - `database/schema.py` — `init_db()` and the ALTER TABLE dance, extracted as a list of `(column, ddl)` migrations so it's data-driven.
   - `database/users.py`, `database/news.py`, `database/comments.py`, `database/sessions.py`, `database/interactions.py`, `database/stats.py` — each a mixin class with the table-specific methods. The `DatabaseManager` inherits from all of them.
2. Add `_row_to_dict` and `_parse_iso_datetime` helpers in `database/_helpers.py` to kill the `result[7] if len(result) > 7 else 0` pattern and the repeated `try/except ValueError` date parsing.
3. Collapse `update_news`'s 4 SQL branches into one query built with optional column updates.
4. Add type hints to all public methods.
5. Delete the old `database.py` (or keep it as a 5-line shim that re-exports from `database/` for one release — TBD with user).

**Stop point:** `python app.py` runs, `pytest tests/test_database.py` passes.

### Phase 2 — Tests scaffold

1. Add `tests/` with `conftest.py` providing:
   - `app` fixture: `create_app('testing')` with a temp SQLite DB.
   - `client` fixture: Flask test client.
   - `db` fixture: bootstrapped schema, per-test transaction rollback.
   - `auth_client` fixture: pre-logged-in client.
2. Add `pytest`, `pytest-flask` to `requirements-dev.txt` (and a `[project.optional-dependencies]` section if we move to `pyproject.toml`).
3. Write initial tests:
   - `test_database.py` — users CRUD, news CRUD, comment thread build, interactions.
   - `test_auth.py` — register, login, logout, profile access control.
   - `test_news_routes.py` — index, latest, hot, category, search, add/edit/delete.
   - `test_admin_routes.py` — admin panel loads, role change works, super-admin gating.

**Stop point:** `pytest` runs green on a fresh checkout.

### Phase 3 — Routes & helpers refactor

1. Add `routes/_helpers.py`:
   - `paginate(items, page, per_page)` → `(page_items, page, total_pages)`. Replaces 3 copies of the same calculation in `latest_news`, `hot_news`, `category_news`.
   - `fetch_recommended(current_user)` → wraps the `try/except` around `db_manager.recommend_news_hybrid` and the bogus `logger_manager.logger_manager.error` log.
   - `handle_image_upload(file_storage)` → filename uuid, save, thumbnail via Pillow, return URL.
   - `log_api_call(user_id, action, details=None)` → wraps the 3-line "记录API调用" pattern.
2. Add `routes/_validators.py`:
   - `validate_credentials(username, email, password, confirm_password)` → returns either a dict of validated fields or a flash-messages list. Replaces the 5 sequential `if/flash` blocks in `auth.register`.
3. Refactor each route handler to use the helpers. Routes stay where they are, names stay the same.
4. Centralize the `cache_manager.clear_news_cache()` calls behind a single `invalidate_news_caches()` helper that knows which keys to nuke (`latest`, `hot`, `category_*`).

**Stop point:** `pytest` still green; route count and endpoint names unchanged.

### Phase 4 — Templates

1. Create `templates/_base.html` — the common `<head>`, background decoration, header, nav, footer. Blocks: `title`, `content`, `extra_js`, `extra_css`.
2. Create partials:
   - `templates/_macros.html` — `render_flashes()`, `render_pagination()`, `card(news)`, `user_avatar(user)`.
   - `templates/_nav.html` — top nav (extracted from `index.html`).
   - `templates/_flash.html` — flash messages partial.
3. Convert each template to `{% extends "_base.html" %}` (or a page-specific base that extends `_base.html`):
   - `login.html`, `register.html` — full conversion, simple.
   - `index.html`, `new.html`, `search_results.html` — extract the inline `<script>` blocks into `static/js/pages/<name>.js` and load with `<script defer src=...>`.
   - `profile.html`, `admin.html` — same. The admin inline CSS gets pulled out to `static/css/pages/admin.css`.
   - `add_news.html`, `edit_news.html` — convert, minor changes.
4. All existing CSS classes and HTML structure preserved so `style.css` doesn't need to change to support the new templates (we re-style in the next phase).
5. Add a `static/js/app.js` for shared utilities (CSRF token helper, fetch wrapper).

**Stop point:** All pages render identically; `pytest` still green; manual smoke test of all 9 pages.

### Phase 5 — CSS split

1. Add `static/css/` with `@import` manifest in `static/style.css`:
   - `00-variables.css` — the `:root` block, untouched.
   - `01-reset.css` — base reset + html/body.
   - `02-layout.css` — container, header, grid.
   - `03-components.css` — buttons, cards, alerts, badges, forms.
   - `04-pages.css` — page-specific styles for index, new, search_results, profile.
   - `05-auth.css` — login/register specific.
   - `06-admin.css` — admin panel specific (extracted from inline `<style>` in admin.html).
2. Verify byte-for-byte the same compiled output by visual diff in browser at 4 viewports (mobile, tablet, laptop, desktop). Use the browser MCP to screenshot the index page before & after.

**Stop point:** Identical visual output, smaller per-file sizes, no style regressions in the manual smoke test.

### Phase 6 — Crawler polish + final docs

1. Type hints + module docstrings for `crawler/`.
2. Extract duplicated `sys.path.append(...)` hack (only `crawler/main.py` does it; remove since all entry points run from project root).
3. Update `docs/merged_document.md` to reflect the new directory layout.
4. Add a `README.md` with quickstart, env vars, test command.

**Stop point:** everything green, docs current.

## Critical files to modify

**Phase 0**
- `routes/news.py` (9 typo fixes)
- `config.py` (env loading)
- new `.env.example`

**Phase 1**
- new `database/` package (6 modules + helpers + connection)
- delete or shim `database.py`

**Phase 2**
- new `tests/` directory (4 test files + `conftest.py`)
- new `requirements-dev.txt`

**Phase 3**
- new `routes/_helpers.py`, `routes/_validators.py`
- `routes/auth.py`, `routes/news.py`, `routes/admin.py` (consume helpers)

**Phase 4**
- new `templates/_base.html`, `templates/_macros.html`, `templates/_nav.html`, `templates/_flash.html`
- rewrite 9 templates
- new `static/js/app.js`, `static/js/pages/*.js`

**Phase 5**
- split `static/style.css` into 7 files in `static/css/`
- new `static/css/pages/admin.css` (extracted from admin.html)

**Phase 6**
- crawler type hints
- `docs/merged_document.md`
- new `README.md`

## Existing utilities to reuse

- `utils/auth.py` — `login_required`, `admin_required`, `editor_required`, `super_admin_required`, `get_current_user`, `hash_password`, `check_password` are already the right abstractions; we just add type hints and consolidate the inline `from flask import jsonify` imports.
- `utils/cache.py` — `cache_manager` API stays; we add `invalidate_news_caches()` to the class.
- `utils/logger.py` — `logger_manager` API stays; we fix the typo callers and ensure all new code uses `logger_manager.error/info/...` directly.
- `utils/anti_crawler.py` — `anti_crawler_required` and `anti_crawler.is_suspicious_request` are reused as-is.
- `config.CrawlerConfig` — reused unchanged.
- The existing `init_db` schema (users, news, comments, sessions, user_stats, news_interactions, daily_login) is preserved exactly so the existing `news.db` keeps working.

## Verification

End-to-end test after each phase:

1. `python app.py` — server starts, prints "🚀 AI新闻系统启动成功", responds 200 on `http://127.0.0.1:5000/`.
2. `pytest -q` — full suite passes.
3. Manual smoke (use the integrated browser MCP at the end of Phase 4, 5, 6):
   - `/` redirects to `/latest` → news cards render.
   - `/register` → create a test user → auto-redirects to `/login`.
   - `/login` → log in → `/profile` shows user info.
   - `/add_news` → post a news → redirects to detail page.
   - `/new?title=...` → detail renders with comments form.
   - `/admin` (as admin) → panel renders.
   - `/search?query=...` → results render.
   - `POST /api/news/<id>/like` → returns updated interactions.
4. `git diff` on `news.db` — should be empty (schema preserved).
5. Compare screenshots of `/`, `/admin`, `/profile` before and after to confirm visual parity.

## Risks & rollback

- **Schema risk:** Phase 1 connection-pooling could surface latent bugs. Mitigation: keep `DatabaseManager` API frozen; run full pytest after every method extraction.
- **CSS split risk:** Phase 5 could break specificity. Mitigation: use the same CSS variables and selector order; visual diff with browser MCP.
- **Template risk:** Phase 4 inline-JS extraction could break event handlers. Mitigation: keep all existing `id`/`class` attributes; load JS with `defer`; smoke test all interactive pages.
- **Time:** Full pass is ~6 phases of meaningful work. We commit after each phase so we can `git revert` to any checkpoint.

We will commit incrementally (one commit per phase) so the user can stop or redirect at any point.
